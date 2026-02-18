from __future__ import annotations

import datetime
import math
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances

from phase1_foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase10_admissibility.stage1_pipeline import (
    compression_bits_per_token,
    conditional_entropy_metrics,
    token_entropy,
    type_token_ratio,
    zipf_alpha,
)

FOLIO_PATTERN = re.compile(r"^f(\d+)([rv])(\d*)$")
SCAN_FOLIO_PATTERN = re.compile(r"(\d+)([rv])", re.IGNORECASE)
# Unicode-aware word pattern: matches alphabetic runs across scripts.
WORD_PATTERN = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)?", flags=re.UNICODE)
_CJK_BLOCKS: tuple[tuple[int, int], ...] = (
    (0x3400, 0x4DBF),  # CJK Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3040, 0x309F),  # Hiragana
    (0x30A0, 0x30FF),  # Katakana
    (0x31F0, 0x31FF),  # Katakana Phonetic Extensions
    (0xAC00, 0xD7AF),  # Hangul Syllables
)

SECTION_RANGES: dict[str, tuple[int, int]] = {
    "herbal": (1, 66),
    "astronomical": (67, 73),
    "biological": (75, 84),
    "cosmological": (85, 86),
    "pharmaceutical": (87, 102),
    "stars": (103, 116),
}

TYPOLOGY_MAP: dict[str, str] = {
    "latin": "fusional",
    "english": "fusional",
    "german": "fusional",
    "russian": "fusional",
    "greek": "fusional",
    "turkish": "agglutinative",
    "finnish": "agglutinative",
    "hungarian": "agglutinative",
    "nahuatl": "agglutinative",
    "mandarin": "isolating",
    "vietnamese": "isolating",
    "arabic": "abjad",
    "hebrew": "abjad",
    "japanese": "syllabic",
    "cherokee": "syllabic",
}


@dataclass
class Stage2Config:
    seed: int = 42
    scan_resolution: str = "folios_2000"
    scan_fallbacks: tuple[str, ...] = ("folios_full", "tiff", "folios_1000")
    image_max_side: int = 1400
    method_g_permutations: int = 1000
    method_i_bootstrap: int = 500
    method_i_min_languages: int = 12
    language_token_cap: int = 50000


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return (10**9, 10**9, 10**9, folio_id)
    folio_num = int(match.group(1))
    side = 0 if match.group(2) == "r" else 1
    suffix = int(match.group(3)) if match.group(3) else 0
    return (folio_num, side, suffix, folio_id)


def section_for_folio(folio_id: str) -> str:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return "unknown"
    folio_num = int(match.group(1))
    for section, (start, end) in SECTION_RANGES.items():
        if start <= folio_num <= end:
            return section
    return "unknown"


def scan_data_resource_inventory(
    store: MetadataStore,
    scans_root: Path,
    external_corpora_dir: Path,
) -> dict[str, Any]:
    session = store.Session()
    try:
        rows = (
            session.query(PageRecord.dataset_id)
            .group_by(PageRecord.dataset_id)
            .order_by(PageRecord.dataset_id)
            .all()
        )
        datasets = [str(row[0]) for row in rows]
    finally:
        session.close()

    jpg_root = scans_root / "jpg"
    tiff_root = scans_root / "tiff"
    jpg_counts: dict[str, int] = {}
    if jpg_root.exists():
        for child in sorted(path for path in jpg_root.iterdir() if path.is_dir()):
            jpg_counts[child.name] = len(list(child.glob("*.jpg")))

    external_corpora: list[dict[str, Any]] = []
    if external_corpora_dir.exists():
        for file in sorted(path for path in external_corpora_dir.iterdir() if path.is_file()):
            external_corpora.append(
                {
                    "path": str(file),
                    "bytes": file.stat().st_size,
                }
            )

    return {
        "status": "ok",
        "generated_at": now_utc_iso(),
        "data_root": "data/",
        "scan_inventory": {
            "jpg_variants": jpg_counts,
            "tiff_count": len(list(tiff_root.glob("*.tif"))) if tiff_root.exists() else 0,
        },
        "external_corpora_files": external_corpora,
        "datasets_registered_in_db": datasets,
        "notes": [
            "Resolution-aware extraction available: folios_1000, folios_2000, folios_full, tiff.",
            "Stage 2 defaults to folios_2000 for throughput/quality balance.",
            "Label tagging remains machine-only unless explicit annotation resources are provided.",
        ],
    }


def _scan_dir_for_resolution(scans_root: Path, resolution: str) -> Path:
    if resolution == "tiff":
        return scans_root / "tiff"
    return scans_root / "jpg" / resolution


def _extract_scan_tokens(stem: str) -> list[str]:
    out: list[str] = []
    for number, side in SCAN_FOLIO_PATTERN.findall(stem):
        out.append(f"{int(number)}{side.lower()}")
    return out


def _build_scan_index(
    scans_root: Path,
    primary_resolution: str,
    fallback_resolutions: tuple[str, ...],
) -> dict[str, list[dict[str, Any]]]:
    resolutions = (primary_resolution, *fallback_resolutions)
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for priority, resolution in enumerate(resolutions):
        directory = _scan_dir_for_resolution(scans_root, resolution)
        if not directory.exists():
            continue
        patterns = ("*.jpg", "*.jpeg") if resolution != "tiff" else ("*.tif", "*.tiff")
        files: list[Path] = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))

        for file in sorted(files):
            tokens = _extract_scan_tokens(file.stem.lower())
            if not tokens:
                continue
            for token in tokens:
                index[token].append(
                    {
                        "path": file,
                        "resolution": resolution,
                        "priority": priority,
                    }
                )

    for token in index:
        index[token].sort(key=lambda row: (row["priority"], str(row["path"])))
    return dict(index)


def _match_scan_for_folio(
    folio_id: str,
    scan_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return None
    token = f"{int(match.group(1))}{match.group(2)}"
    suffix = int(match.group(3)) if match.group(3) else 1
    candidates = scan_index.get(token, [])
    if not candidates:
        return None

    # Prefer the highest-priority available resolution; use suffix only within that pool.
    best_priority = min(int(row["priority"]) for row in candidates)
    preferred = [row for row in candidates if int(row["priority"]) == best_priority]
    chosen = preferred[(suffix - 1) % len(preferred)] if len(preferred) > 1 else preferred[0]
    return {
        "token": token,
        "candidate_count": len(candidates),
        "preferred_candidate_count": len(preferred),
        "chosen": chosen,
    }


def _projection_entropy(values: np.ndarray) -> float:
    total = float(np.sum(values))
    if total <= 0:
        return 0.0
    probs = values / total
    probs = probs[probs > 0]
    if probs.size == 0:
        return 0.0
    return float(-np.sum(probs * np.log2(probs)))


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) <= 1e-12:
        return 0.0
    return float(numerator / denominator)


def _extract_visual_features(image_path: Path, max_side: int) -> dict[str, float]:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        try:
            pil_image = Image.open(image_path).convert("RGB")
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as exc:
            raise RuntimeError(f"Failed to read image: {image_path}") from exc

    original_h, original_w = image.shape[:2]
    scale = min(1.0, float(max_side) / max(original_h, original_w))
    if scale < 1.0:
        image = cv2.resize(image, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h_chan, s_chan, v_chan = cv2.split(hsv)

    edges = cv2.Canny(gray, threshold1=80, threshold2=160)
    edge_density = float(np.mean(edges > 0))

    _, ink_mask = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    ink_ratio = float(np.mean(ink_mask > 0))

    num_components, _, stats, _ = cv2.connectedComponentsWithStats(
        ink_mask,
        connectivity=8,
    )
    component_areas = (
        stats[1:, cv2.CC_STAT_AREA]
        if num_components > 1
        else np.array([], dtype=np.float64)
    )
    image_area = float(gray.shape[0] * gray.shape[1])
    component_count = int(component_areas.size)

    contours, _ = cv2.findContours(ink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    circularities: list[float] = []
    large_contours = 0
    min_contour_area = image_area * 0.0005
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_contour_area:
            continue
        large_contours += 1
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter > 0:
            circularities.append(float((4.0 * math.pi * area) / (perimeter * perimeter)))

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    row_projection = np.sum(ink_mask > 0, axis=1).astype(np.float64)
    col_projection = np.sum(ink_mask > 0, axis=0).astype(np.float64)

    grid_features: dict[str, float] = {}
    rows = 4
    cols = 4
    h, w = gray.shape
    for r in range(rows):
        y0 = int(round(r * h / rows))
        y1 = int(round((r + 1) * h / rows))
        for c in range(cols):
            x0 = int(round(c * w / cols))
            x1 = int(round((c + 1) * w / cols))
            patch = ink_mask[y0:y1, x0:x1]
            grid_features[f"ink_grid_r{r}c{c}"] = (
                float(np.mean(patch > 0)) if patch.size else 0.0
            )

    features: dict[str, float] = {
        "gray_mean": float(np.mean(gray)),
        "gray_std": float(np.std(gray)),
        "h_mean": float(np.mean(h_chan)),
        "h_std": float(np.std(h_chan)),
        "s_mean": float(np.mean(s_chan)),
        "s_std": float(np.std(s_chan)),
        "v_mean": float(np.mean(v_chan)),
        "v_std": float(np.std(v_chan)),
        "edge_density": edge_density,
        "ink_ratio": ink_ratio,
        "component_count_per_megapixel": _safe_ratio(
            component_count * 1_000_000.0,
            image_area,
        ),
        "component_area_mean_ratio": _safe_ratio(
            float(np.mean(component_areas)) if component_count else 0.0,
            image_area,
        ),
        "component_area_max_ratio": _safe_ratio(
            float(np.max(component_areas)) if component_count else 0.0,
            image_area,
        ),
        "projection_entropy_rows": _projection_entropy(row_projection),
        "projection_entropy_cols": _projection_entropy(col_projection),
        "large_contour_count_per_megapixel": _safe_ratio(
            large_contours * 1_000_000.0,
            image_area,
        ),
        "mean_circularity": float(statistics.fmean(circularities)) if circularities else 0.0,
        "laplacian_variance": lap_var,
        "effective_width": float(w),
        "effective_height": float(h),
        "resize_scale": float(scale),
    }
    features.update(grid_features)
    return features


def _load_folio_token_map(
    store: MetadataStore,
    dataset_id: str = "voynich_real",
) -> dict[str, list[str]]:
    session = store.Session()
    try:
        rows = (
            session.query(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
                TranscriptionTokenRecord.content,
            )
            .join(TranscriptionLineRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .join(
                TranscriptionTokenRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )
    finally:
        session.close()

    by_folio: dict[str, list[str]] = defaultdict(list)
    for folio_id, _line_idx, _token_idx, content in rows:
        by_folio[str(folio_id)].append(str(content))
    return dict(by_folio)


def build_illustration_features(
    store: MetadataStore,
    scans_root: Path,
    resolution: str,
    fallback_resolutions: tuple[str, ...],
    max_side: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            "Illustration feature extraction start: "
            f"resolution={resolution}, fallbacks={list(fallback_resolutions)}, max_side={max_side}"
        )

    token_map = _load_folio_token_map(store, dataset_id="voynich_real")
    folios = sorted(token_map.keys(), key=folio_sort_key)
    scan_index = _build_scan_index(scans_root, resolution, fallback_resolutions)

    features_by_folio: dict[str, dict[str, Any]] = {}
    missing_scan: list[str] = []
    stride = max(1, len(folios) // 20)

    for idx, folio_id in enumerate(folios):
        match = _match_scan_for_folio(folio_id, scan_index)
        if match is None:
            missing_scan.append(folio_id)
            continue
        chosen = match["chosen"]
        scan_path = Path(chosen["path"])
        visual_features = _extract_visual_features(scan_path, max_side=max_side)
        features_by_folio[folio_id] = {
            "folio_id": folio_id,
            "section": section_for_folio(folio_id),
            "scan_path": str(scan_path),
            "scan_resolution": str(chosen["resolution"]),
            "scan_candidate_count": int(match["candidate_count"]),
            "token_count": len(token_map.get(folio_id, [])),
            "visual_features": visual_features,
        }
        if progress and ((idx + 1) % stride == 0 or idx + 1 == len(folios)):
            progress(f"Illustration feature extraction {idx + 1}/{len(folios)} folios")

    if progress:
        progress(
            "Illustration feature extraction complete: "
            f"processed={len(features_by_folio)}, missing_scan={len(missing_scan)}"
        )

    return {
        "status": "ok",
        "generated_at": now_utc_iso(),
        "config": {
            "resolution": resolution,
            "fallback_resolutions": list(fallback_resolutions),
            "max_side": max_side,
        },
        "coverage": {
            "folio_total": len(folios),
            "folio_processed": len(features_by_folio),
            "missing_scan_count": len(missing_scan),
            "missing_scan_folios": sorted(missing_scan, key=folio_sort_key),
        },
        "folios": features_by_folio,
    }


def _matrix_from_visual_features(
    illustration_features: dict[str, Any],
) -> tuple[list[str], np.ndarray, list[str]]:
    folios = sorted(illustration_features["folios"].keys(), key=folio_sort_key)
    if not folios:
        raise RuntimeError("No folios available in illustration feature payload.")

    feature_keys = sorted(
        illustration_features["folios"][folios[0]]["visual_features"].keys()
    )
    matrix = np.array(
        [
            [
                float(illustration_features["folios"][folio]["visual_features"][key])
                for key in feature_keys
            ]
            for folio in folios
        ],
        dtype=np.float64,
    )
    return folios, matrix, feature_keys


def _matrix_from_text_tokens(
    token_map: dict[str, list[str]],
    folios: list[str],
    max_features: int = 2000,
) -> np.ndarray:
    docs = [" ".join(token_map.get(folio, [])) for folio in folios]
    vectorizer = TfidfVectorizer(max_features=max_features, token_pattern=r"(?u)\b\w+\b")
    matrix = vectorizer.fit_transform(docs).toarray().astype(np.float64)
    return matrix


def _demean_matrix_by_group(matrix: np.ndarray, groups: list[str]) -> np.ndarray:
    out = np.array(matrix, copy=True, dtype=np.float64)
    group_arr = np.array(groups)
    for group in sorted(set(groups)):
        idx = np.where(group_arr == group)[0]
        if idx.size == 0:
            continue
        out[idx, :] = out[idx, :] - np.mean(out[idx, :], axis=0, keepdims=True)

    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms = np.where(norms <= 1e-12, 1.0, norms)
    return out / norms


def _groupwise_permutation_indices(groups: list[str], rng: np.random.Generator) -> np.ndarray:
    groups_arr = np.array(groups)
    out = np.arange(groups_arr.size)
    for group in sorted(set(groups)):
        idx = np.where(groups_arr == group)[0]
        if idx.size <= 1:
            continue
        shuffled = np.array(idx, copy=True)
        rng.shuffle(shuffled)
        out[idx] = shuffled
    return out


def mantel_correlation(
    visual_distance: np.ndarray,
    text_distance: np.ndarray,
    permutations: int,
    seed: int,
    groups: list[str] | None = None,
) -> dict[str, Any]:
    if visual_distance.shape != text_distance.shape:
        raise ValueError("Distance matrices must share shape for Mantel correlation.")
    n = int(visual_distance.shape[0])
    if n < 3:
        raise ValueError("Need at least 3 folios for Mantel correlation.")

    tri = np.triu_indices(n, k=1)
    x = visual_distance[tri]
    y = text_distance[tri]
    observed = float(np.corrcoef(x, y)[0, 1])

    rng = np.random.default_rng(seed)
    null = np.empty(permutations, dtype=np.float64)
    for idx in range(permutations):
        perm = (
            rng.permutation(n)
            if groups is None
            else _groupwise_permutation_indices(groups, rng)
        )
        y_perm = text_distance[np.ix_(perm, perm)][tri]
        null[idx] = float(np.corrcoef(x, y_perm)[0, 1])

    p_one_sided = float((np.sum(null >= observed) + 1) / (permutations + 1))
    p_two_sided = float((np.sum(np.abs(null) >= abs(observed)) + 1) / (permutations + 1))
    return {
        "r_observed": observed,
        "p_one_sided": p_one_sided,
        "p_two_sided": p_two_sided,
        "null_mean": float(np.mean(null)),
        "null_std": float(np.std(null)),
        "null_q05": float(np.quantile(null, 0.05)),
        "null_q95": float(np.quantile(null, 0.95)),
        "permutations": permutations,
    }


def run_method_g(
    store: MetadataStore,
    illustration_features: dict[str, Any],
    permutations: int,
    seed: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            "Method G start: "
            f"folios={illustration_features['coverage']['folio_processed']}, "
            f"permutations={permutations}"
        )

    token_map = _load_folio_token_map(store, dataset_id="voynich_real")
    folios, visual_matrix, visual_feature_keys = _matrix_from_visual_features(illustration_features)
    folios = [folio for folio in folios if folio in token_map and token_map[folio]]
    if len(folios) < 10:
        return {
            "method": "G",
            "status": "failed",
            "decision": "test_invalid",
            "reason": "Insufficient overlap between folio scans and transcription tokens.",
        }

    visual_matrix = np.array(
        [
            [
                float(illustration_features["folios"][folio]["visual_features"][key])
                for key in visual_feature_keys
            ]
            for folio in folios
        ],
        dtype=np.float64,
    )
    text_matrix = _matrix_from_text_tokens(token_map, folios, max_features=2500)
    section_labels = [section_for_folio(folio) for folio in folios]

    visual_distance = pairwise_distances(visual_matrix, metric="cosine")
    text_distance = pairwise_distances(text_matrix, metric="cosine")
    visual_distance = np.nan_to_num(visual_distance, nan=0.0, posinf=1.0, neginf=1.0)
    text_distance = np.nan_to_num(text_distance, nan=0.0, posinf=1.0, neginf=1.0)
    if progress:
        progress("Method G distance matrices computed")

    full = mantel_correlation(
        visual_distance=visual_distance,
        text_distance=text_distance,
        permutations=permutations,
        seed=seed,
        groups=None,
    )
    if progress:
        progress(
            "Method G full Mantel complete: "
            f"r={full['r_observed']:.4f}, p={full['p_one_sided']:.4f}"
        )

    within_section_perm = mantel_correlation(
        visual_distance=visual_distance,
        text_distance=text_distance,
        permutations=permutations,
        seed=seed + 1,
        groups=section_labels,
    )
    if progress:
        progress(
            "Method G within-section permutation complete: "
            f"r={within_section_perm['r_observed']:.4f}, p={within_section_perm['p_one_sided']:.4f}"
        )

    text_residual = _demean_matrix_by_group(text_matrix, section_labels)
    residual_distance = pairwise_distances(text_residual, metric="cosine")
    residual_distance = np.nan_to_num(residual_distance, nan=0.0, posinf=1.0, neginf=1.0)

    residual = mantel_correlation(
        visual_distance=visual_distance,
        text_distance=residual_distance,
        permutations=permutations,
        seed=seed + 2,
        groups=section_labels,
    )
    if progress:
        progress(
            "Method G residual Mantel complete: "
            f"r={residual['r_observed']:.4f}, p={residual['p_one_sided']:.4f}"
        )

    label_specificity = {
        "status": "not_evaluable",
        "reason": (
            "No reliable local machine-readable label-to-illustration alignment resource is "
            "available; manual labeling was intentionally not used."
        ),
    }

    if (
        full["r_observed"] > 0
        and full["p_one_sided"] < 0.01
        and residual["r_observed"] > 0
        and residual["p_one_sided"] < 0.01
    ):
        decision = "closure_weakened"
        reason = (
            "Text-illustration correlation survives section controls and exceeds the "
            "permutation null threshold."
        )
    elif full["p_one_sided"] >= 0.01:
        decision = "closure_strengthened"
        reason = "No significant cross-folio text-illustration coupling was detected."
    else:
        decision = "indeterminate"
        reason = "Section-level coupling exists but residual evidence is not decisive."

    return {
        "method": "G",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "config": {
            "permutations": permutations,
            "seed": seed,
        },
        "folio_count": len(folios),
        "sections_present": sorted(set(section_labels)),
        "correlation": {
            "full": full,
            "within_section_permutation": within_section_perm,
            "residual_after_text_demean": residual,
        },
        "label_specificity": label_specificity,
        "visual_feature_keys": visual_feature_keys,
    }


def _tokenize_text_to_lines(text: str) -> list[list[str]]:
    def _is_cjk_or_kana(char: str) -> bool:
        code = ord(char)
        return any(start <= code <= end for start, end in _CJK_BLOCKS)

    def _tokenize_line_multiscript(raw: str) -> list[str]:
        tokens = WORD_PATTERN.findall(raw.lower())
        if not tokens:
            return []

        expanded: list[str] = []
        for token in tokens:
            if any(_is_cjk_or_kana(char) for char in token):
                expanded.extend(char for char in token if _is_cjk_or_kana(char))
            else:
                expanded.append(token)
        return expanded

    lines: list[list[str]] = []
    for raw in text.splitlines():
        tokens = _tokenize_line_multiscript(raw)
        if tokens:
            lines.append(tokens)
    if lines:
        return lines
    tokens = _tokenize_line_multiscript(text)
    if not tokens:
        return []
    return [tokens[i : i + 12] for i in range(0, len(tokens), 12)]


def _flatten_lines(lines: list[list[str]]) -> list[str]:
    return [token for line in lines for token in line]


def _phase4_feature_vector(tokens: list[str], lines: list[list[str]]) -> dict[str, float]:
    cond = conditional_entropy_metrics(tokens)
    starts = [line[0] for line in lines if line]
    ends = [line[-1] for line in lines if line]
    counts = Counter(tokens)
    hapax = sum(1 for count in counts.values() if count == 1)
    lengths = [len(token) for token in tokens if token]

    return {
        "entropy": token_entropy(tokens),
        "compression_bits_per_token": compression_bits_per_token(tokens),
        "type_token_ratio": type_token_ratio(tokens),
        "zipf_alpha": zipf_alpha(tokens),
        "bigram_cond_entropy": cond["bigram_cond_entropy"],
        "trigram_cond_entropy": cond["trigram_cond_entropy"],
        "bigram_mutual_information": cond["bigram_mutual_information"],
        "mean_word_length": statistics.fmean(lengths) if lengths else 0.0,
        "line_initial_entropy": token_entropy(starts),
        "line_final_entropy": token_entropy(ends),
        "hapax_ratio": float(hapax / max(len(counts), 1)),
    }


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _normalize_language_id(stem: str) -> str:
    normalized = stem.lower().replace("-", "_")
    if normalized in {"latin_corpus", "latin_classic"}:
        return "latin"
    return normalized


def build_cross_linguistic_manifest(
    store: MetadataStore,
    external_corpora_dir: Path,
    token_cap: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    language_corpora: dict[str, dict[str, Any]] = {}

    # Reuse db Latin baseline when available.
    try:
        from phase10_admissibility.stage1_pipeline import load_dataset_bundle

        latin_bundle = load_dataset_bundle(store, "latin_classic", "Latin")
        if latin_bundle.tokens:
            language_corpora["latin"] = {
                "language_id": "latin",
                "display_name": "Latin",
                "typology": TYPOLOGY_MAP.get("latin", "unknown"),
                "source": "db:latin_classic",
                "tokens": (
                    latin_bundle.tokens[:token_cap]
                    if token_cap > 0
                    else list(latin_bundle.tokens)
                ),
                "lines": latin_bundle.lines,
                "raw_token_count": len(latin_bundle.tokens),
            }
            if progress:
                progress("Method I corpus source loaded: latin (db)")
    except Exception:
        # Continue with file-based sources only.
        pass

    if external_corpora_dir.exists():
        for file in sorted(
            path for path in external_corpora_dir.iterdir() if path.suffix.lower() == ".txt"
        ):
            language_id = _normalize_language_id(file.stem)
            text = file.read_text(encoding="utf-8", errors="ignore")
            lines = _tokenize_text_to_lines(text)
            tokens = _flatten_lines(lines)
            if token_cap > 0 and len(tokens) > token_cap:
                tokens = tokens[:token_cap]
                lines = [tokens[i : i + 12] for i in range(0, len(tokens), 12)]

            candidate = {
                "language_id": language_id,
                "display_name": language_id.replace("_", " ").title(),
                "typology": TYPOLOGY_MAP.get(language_id, "unknown"),
                "source": str(file),
                "tokens": tokens,
                "lines": lines,
                "raw_token_count": len(_flatten_lines(_tokenize_text_to_lines(text))),
            }

            existing = language_corpora.get(language_id)
            if existing is None or len(candidate["tokens"]) > len(existing["tokens"]):
                language_corpora[language_id] = candidate
                if progress:
                    progress(
                        "Method I corpus source loaded: "
                        f"{language_id} (tokens={len(candidate['tokens'])})"
                    )

    language_entries: list[dict[str, Any]] = []
    for language_id in sorted(language_corpora.keys()):
        row = language_corpora[language_id]
        language_entries.append(
            {
                "language_id": language_id,
                "display_name": row["display_name"],
                "typology": row["typology"],
                "source": row["source"],
                "token_count": len(row["tokens"]),
                "raw_token_count": int(row["raw_token_count"]),
            }
        )

    typologies = sorted(
        {entry["typology"] for entry in language_entries if entry["typology"] != "unknown"}
    )
    return {
        "status": "ok",
        "generated_at": now_utc_iso(),
        "token_cap": token_cap,
        "language_entries": language_entries,
        "language_count": len(language_entries),
        "typology_classes_present": typologies,
        "typology_class_count": len(typologies),
        "notes": [
            "Manifest built from local /data resources only.",
            "No manual corpus labeling was used; language identity derived from filenames/db IDs.",
        ],
    }


def run_method_i(
    store: MetadataStore,
    cross_linguistic_manifest: dict[str, Any],
    external_corpora_dir: Path,
    bootstrap_iterations: int,
    min_languages: int,
    seed: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            "Method I start: "
            f"bootstrap_iterations={bootstrap_iterations}, min_languages={min_languages}"
        )

    from phase10_admissibility.stage1_pipeline import load_dataset_bundle

    language_payload: dict[str, dict[str, Any]] = {}
    # Reconstruct tokens/lines from sources so features are reproducible.
    for row in cross_linguistic_manifest.get("language_entries", []):
        language_id = str(row["language_id"])
        source = str(row["source"])
        if source.startswith("db:latin_classic"):
            bundle = load_dataset_bundle(store, "latin_classic", "Latin")
            lines = bundle.lines
            tokens = bundle.tokens
        else:
            text = Path(source).read_text(encoding="utf-8", errors="ignore")
            lines = _tokenize_text_to_lines(text)
            tokens = _flatten_lines(lines)
            cap = int(cross_linguistic_manifest.get("token_cap", 0))
            if cap > 0 and len(tokens) > cap:
                tokens = tokens[:cap]
                lines = [tokens[i : i + 12] for i in range(0, len(tokens), 12)]

        if len(tokens) < 2000:
            continue
        language_payload[language_id] = {
            "typology": row.get("typology", "unknown"),
            "tokens": tokens,
            "lines": lines,
            "features": _phase4_feature_vector(tokens, lines),
        }

    voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich")
    voynich_features = _phase4_feature_vector(voynich_bundle.tokens, voynich_bundle.lines)

    generator_ids = [
        "self_citation",
        "table_grille",
        "mechanical_reuse",
        "shuffled_global",
    ]
    generator_payload: dict[str, dict[str, Any]] = {}
    for dataset_id in generator_ids:
        try:
            bundle = load_dataset_bundle(store, dataset_id, dataset_id)
        except Exception:
            continue
        if len(bundle.tokens) < 2000:
            continue
        generator_payload[dataset_id] = {
            "tokens": bundle.tokens,
            "lines": bundle.lines,
            "features": _phase4_feature_vector(bundle.tokens, bundle.lines),
        }
        if progress:
            progress(f"Method I generator feature loaded: {dataset_id}")

    if not language_payload or not generator_payload:
        return {
            "method": "I",
            "status": "failed",
            "decision": "test_invalid",
            "reason": "Insufficient language or generator resources available for Method I.",
        }

    feature_keys = sorted(voynich_features.keys())

    point_ids = [
        "voynich_real",
        *sorted(language_payload.keys()),
        *sorted(generator_payload.keys()),
    ]
    vectors = np.array(
        [
            [float(voynich_features[key]) for key in feature_keys],
            *[
                [float(language_payload[language_id]["features"][key]) for key in feature_keys]
                for language_id in sorted(language_payload.keys())
            ],
            *[
                [float(generator_payload[dataset_id]["features"][key]) for key in feature_keys]
                for dataset_id in sorted(generator_payload.keys())
            ],
        ],
        dtype=np.float64,
    )

    means = np.mean(vectors, axis=0)
    stds = np.std(vectors, axis=0)
    stds = np.where(stds <= 1e-12, 1.0, stds)
    vectors_z = (vectors - means) / stds
    id_to_idx = {point_id: idx for idx, point_id in enumerate(point_ids)}

    voy = vectors_z[id_to_idx["voynich_real"]]
    language_ids = sorted(language_payload.keys())
    generator_point_ids = sorted(generator_payload.keys())

    language_rows = np.array(
        [vectors_z[id_to_idx[language_id]] for language_id in language_ids]
    )
    generator_rows = np.array(
        [vectors_z[id_to_idx[dataset_id]] for dataset_id in generator_point_ids]
    )

    language_distances = {
        language_id: _distance(voy, vectors_z[id_to_idx[language_id]])
        for language_id in language_ids
    }
    generator_distances = {
        dataset_id: _distance(voy, vectors_z[id_to_idx[dataset_id]])
        for dataset_id in generator_point_ids
    }

    nearest_language = min(language_distances.items(), key=lambda item: item[1])
    nearest_generator = min(generator_distances.items(), key=lambda item: item[1])

    language_centroid = np.mean(language_rows, axis=0)
    generator_centroid = np.mean(generator_rows, axis=0)
    dist_to_language_centroid = _distance(voy, language_centroid)
    dist_to_generator_centroid = _distance(voy, generator_centroid)
    margin_language_minus_generator = dist_to_generator_centroid - dist_to_language_centroid

    rng = np.random.default_rng(seed)
    margins = np.empty(bootstrap_iterations, dtype=np.float64)
    for idx in range(bootstrap_iterations):
        l_idx = rng.integers(0, language_rows.shape[0], language_rows.shape[0])
        g_idx = rng.integers(0, generator_rows.shape[0], generator_rows.shape[0])
        l_cent = np.mean(language_rows[l_idx, :], axis=0)
        g_cent = np.mean(generator_rows[g_idx, :], axis=0)
        margins[idx] = _distance(voy, g_cent) - _distance(voy, l_cent)
        if progress and ((idx + 1) % max(1, bootstrap_iterations // 5) == 0):
            progress(f"Method I bootstrap {idx + 1}/{bootstrap_iterations}")

    confidence_language = float(np.mean(margins > 0))
    confidence_generator = float(np.mean(margins < 0))

    typology_count = int(cross_linguistic_manifest.get("typology_class_count", 0))
    coverage = {
        "language_count": len(language_ids),
        "typology_class_count": typology_count,
        "min_languages_required": min_languages,
        "min_typology_classes_required": 4,
        "coverage_ok": len(language_ids) >= min_languages and typology_count >= 4,
    }

    # Null baseline via language-token shuffles.
    real_dist_mean = float(np.mean(list(language_distances.values())))
    shuffled_distance_rows: dict[str, float] = {}
    for language_id in language_ids:
        tokens = list(language_payload[language_id]["tokens"])
        rng.shuffle(tokens)
        shuffled_lines = [tokens[i : i + 12] for i in range(0, len(tokens), 12)]
        shuffled_features = _phase4_feature_vector(tokens, shuffled_lines)
        raw_voy = np.array(
            [float(voynich_features[key]) for key in feature_keys],
            dtype=np.float64,
        )
        raw_shuf = np.array(
            [float(shuffled_features[key]) for key in feature_keys],
            dtype=np.float64,
        )
        shuffled_distance_rows[language_id] = _distance(raw_voy, raw_shuf)
    shuffled_dist_mean = float(np.mean(list(shuffled_distance_rows.values())))

    if not coverage["coverage_ok"]:
        decision = "test_invalid"
        reason = (
            "Cross-linguistic coverage is below pre-registered target "
            f"({len(language_ids)} languages, {typology_count} typology classes)."
        )
    elif (
        dist_to_language_centroid < dist_to_generator_centroid
        and confidence_language >= 0.95
    ):
        decision = "closure_weakened"
        reason = (
            "Voynich is closer to the language cloud than the generator cloud with "
            "bootstrap confidence above 95%."
        )
    elif dist_to_generator_centroid < dist_to_language_centroid and confidence_generator >= 0.80:
        decision = "closure_strengthened"
        reason = "Voynich remains closer to generator controls than to language controls."
    else:
        decision = "indeterminate"
        reason = "Language and generator clouds overlap under current feature coverage."

    return {
        "method": "I",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "config": {
            "bootstrap_iterations": bootstrap_iterations,
            "seed": seed,
            "min_languages": min_languages,
        },
        "coverage": coverage,
        "feature_keys": feature_keys,
        "nearest_language": {
            "language_id": nearest_language[0],
            "distance": nearest_language[1],
            "typology": language_payload[nearest_language[0]]["typology"],
        },
        "nearest_generator": {
            "dataset_id": nearest_generator[0],
            "distance": nearest_generator[1],
        },
        "cloud_distances": {
            "to_language_centroid": dist_to_language_centroid,
            "to_generator_centroid": dist_to_generator_centroid,
            "generator_minus_language_margin": margin_language_minus_generator,
            "bootstrap_margin_q05": float(np.quantile(margins, 0.05)),
            "bootstrap_margin_q95": float(np.quantile(margins, 0.95)),
            "bootstrap_confidence_language_closer": confidence_language,
            "bootstrap_confidence_generator_closer": confidence_generator,
        },
        "null_baseline": {
            "mean_distance_to_real_languages": real_dist_mean,
            "mean_distance_to_shuffled_languages": shuffled_dist_mean,
            "shuffled_minus_real_margin": shuffled_dist_mean - real_dist_mean,
        },
        "language_distances": language_distances,
        "generator_distances": generator_distances,
    }


def summarize_stage2(method_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decisions = {
        method: str(result.get("decision", "indeterminate"))
        for method, result in method_results.items()
    }

    if any(value == "closure_weakened" for value in decisions.values()):
        stage_decision = "closure_weakened"
    elif any(value == "test_invalid" for value in decisions.values()):
        stage_decision = "test_invalid"
    elif all(value == "closure_strengthened" for value in decisions.values()):
        stage_decision = "closure_strengthened"
    else:
        stage_decision = "indeterminate"

    return {
        "status": "ok",
        "stage": "10.2",
        "stage_decision": stage_decision,
        "method_decisions": decisions,
        "generated_at": now_utc_iso(),
    }


def build_stage2_markdown(
    summary: dict[str, Any],
    method_artifacts: dict[str, str],
    status_path: str,
) -> str:
    lines = [
        "# Phase 10 Stage 2 Results (Methods G/I)",
        "",
        f"Generated: {summary['generated_at']}",
        f"Stage decision: **{summary['stage_decision']}**",
        "",
        "## Method Decisions",
        "",
        "- Method G (Text-Illustration Correlation): "
        f"`{summary['method_decisions'].get('G', 'n/a')}`",
        "- Method I (Cross-Linguistic Positioning): "
        f"`{summary['method_decisions'].get('I', 'n/a')}`",
        "",
        "## Artifacts",
        "",
        f"- Data inventory artifact: `{method_artifacts.get('inventory', 'n/a')}`",
        f"- Illustration features artifact: `{method_artifacts.get('illustration', 'n/a')}`",
        f"- Cross-linguistic manifest artifact: `{method_artifacts.get('manifest', 'n/a')}`",
        f"- Method G artifact: `{method_artifacts.get('G', 'n/a')}`",
        f"- Method I artifact: `{method_artifacts.get('I', 'n/a')}`",
        f"- Stage 2 summary artifact: `{method_artifacts.get('stage2', 'n/a')}`",
        f"- Restart status tracker: `{status_path}`",
        "",
        "## Notes",
        "",
        "- Machine-extracted visual features were used; manual folio tagging was not required.",
        "- Resolution strategy defaults to `folios_2000` with fallback to "
        "`folios_full`, `tiff`, and `folios_1000`.",
        "",
    ]
    return "\n".join(lines)
