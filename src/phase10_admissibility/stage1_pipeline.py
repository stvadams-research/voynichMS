from __future__ import annotations

import datetime
import math
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from sqlalchemy import func

from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
)
from phase4_inference.projection_diagnostics.line_reset_backoff import (
    LineResetBackoffConfig,
    LineResetBackoffGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_markov import (
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_persistence import (
    LineResetPersistenceConfig,
    LineResetPersistenceGenerator,
)

EXTRACTION_RULES: dict[str, str] = {
    "line_initial_tokens": "First token of each line",
    "line_final_tokens": "Last token of each line",
    "word_initial_glyphs": "First glyph proxy (first character) of each word",
    "nth_token_2": "Every 2nd token from stream",
    "nth_token_3": "Every 3rd token from stream",
    "nth_token_5": "Every 5th token from stream",
    "nth_token_7": "Every 7th token from stream",
    "slot_position_3_glyphs": "Third glyph proxy (third character) from each token",
    "paragraph_initial_tokens": "First token of each page",
}

METHOD_J_EDGE_RULES = {"line_initial_tokens", "paragraph_initial_tokens"}


TYPOLOGY_PROTOTYPES: dict[str, dict[str, Any]] = {
    "alphabet": {
        "center": {
            "glyph_count": 30.0,
            "mean_word_length": 5.2,
            "ttr_10000": 0.26,
            "productivity_log_ratio": -4.8,
        },
        "range": {"glyph_count": (18.0, 55.0), "mean_word_length": (3.0, 8.5)},
    },
    "abjad": {
        "center": {
            "glyph_count": 28.0,
            "mean_word_length": 4.4,
            "ttr_10000": 0.23,
            "productivity_log_ratio": -4.4,
        },
        "range": {"glyph_count": (18.0, 45.0), "mean_word_length": (2.5, 7.5)},
    },
    "abugida": {
        "center": {
            "glyph_count": 48.0,
            "mean_word_length": 4.2,
            "ttr_10000": 0.2,
            "productivity_log_ratio": -4.1,
        },
        "range": {"glyph_count": (30.0, 90.0), "mean_word_length": (2.5, 7.0)},
    },
    "syllabary": {
        "center": {
            "glyph_count": 90.0,
            "mean_word_length": 2.8,
            "ttr_10000": 0.14,
            "productivity_log_ratio": -3.1,
        },
        "range": {"glyph_count": (45.0, 180.0), "mean_word_length": (1.5, 4.5)},
    },
    "logographic": {
        "center": {
            "glyph_count": 1500.0,
            "mean_word_length": 1.6,
            "ttr_10000": 0.55,
            "productivity_log_ratio": -1.0,
        },
        "range": {"glyph_count": (400.0, 8000.0), "mean_word_length": (1.0, 2.8)},
    },
}


@dataclass
class CorpusBundle:
    dataset_id: str
    label: str
    tokens: list[str]
    lines: list[list[str]]
    pages: list[list[list[str]]]


@dataclass
class Stage1Config:
    seed: int = 42
    target_tokens: int = 120000
    method_j_null_runs: int = 100
    method_k_runs: int = 100


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _flatten(lines: list[list[str]]) -> list[str]:
    return [token for line in lines for token in line]


def _mean_lines_per_page(bundle: CorpusBundle) -> int:
    if not bundle.pages:
        return 100
    return max(1, int(round(sum(len(page) for page in bundle.pages) / len(bundle.pages))))


def _chunk_lines_into_pages(lines: list[list[str]], lines_per_page: int) -> list[list[list[str]]]:
    if not lines:
        return []
    pages: list[list[list[str]]] = []
    for start in range(0, len(lines), max(1, lines_per_page)):
        pages.append(lines[start : start + max(1, lines_per_page)])
    return pages


def load_dataset_bundle(store: MetadataStore, dataset_id: str, label: str) -> CorpusBundle:
    lines = get_lines_from_store(store, dataset_id)
    tokens = _flatten(lines)

    session = store.Session()
    try:
        page_line_counts = (
            session.query(PageRecord.id, func.count(TranscriptionLineRecord.id))
            .join(TranscriptionLineRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .group_by(PageRecord.id)
            .order_by(PageRecord.id)
            .all()
        )
    finally:
        session.close()

    pages: list[list[list[str]]] = []
    cursor = 0
    for _, line_count in page_line_counts:
        count = int(line_count)
        pages.append(lines[cursor : cursor + count])
        cursor += count
    if cursor < len(lines):
        pages.append(lines[cursor:])

    return CorpusBundle(
        dataset_id=dataset_id,
        label=label,
        tokens=tokens,
        lines=lines,
        pages=pages,
    )


def build_reference_generators(
    voynich_lines: list[list[str]], seed: int
) -> dict[str, Any]:
    markov = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=seed))
    markov.fit(voynich_lines)

    backoff = LineResetBackoffGenerator(LineResetBackoffConfig(random_state=seed))
    backoff.fit(voynich_lines)

    persistence = LineResetPersistenceGenerator(LineResetPersistenceConfig(random_state=seed))
    persistence.fit(voynich_lines)

    return {
        "line_reset_markov": markov,
        "line_reset_backoff": backoff,
        "line_reset_persistence": persistence,
    }


def generate_bundle_from_generator(
    generator: Any,
    dataset_id: str,
    label: str,
    target_tokens: int,
    lines_per_page: int,
) -> CorpusBundle:
    generated = generator.generate(target_tokens=target_tokens)
    lines = [list(line) for line in generated["lines"]]
    tokens = _flatten(lines)
    pages = _chunk_lines_into_pages(lines, lines_per_page)
    return CorpusBundle(
        dataset_id=dataset_id,
        label=label,
        tokens=tokens,
        lines=lines,
        pages=pages,
    )


def token_entropy(sequence: list[str]) -> float:
    if not sequence:
        return 0.0
    counts = Counter(sequence)
    n = len(sequence)
    entropy = 0.0
    for count in counts.values():
        p = count / n
        entropy -= p * math.log2(p)
    return float(entropy)


def compression_bits_per_token(sequence: list[str]) -> float:
    if not sequence:
        return 0.0
    import zlib

    payload = " ".join(sequence).encode("utf-8", errors="ignore")
    compressed = zlib.compress(payload, level=9)
    return float((8.0 * len(compressed)) / len(sequence))


def compression_ratio(sequence: list[str]) -> float:
    if not sequence:
        return 0.0
    import zlib

    payload = " ".join(sequence).encode("utf-8", errors="ignore")
    if not payload:
        return 0.0
    compressed = zlib.compress(payload, level=9)
    return float(len(compressed) / len(payload))


def type_token_ratio(sequence: list[str]) -> float:
    if not sequence:
        return 0.0
    return float(len(set(sequence)) / len(sequence))


def bigram_mutual_information(sequence: list[str]) -> float:
    if len(sequence) < 2:
        return 0.0
    prev = sequence[:-1]
    nxt = sequence[1:]
    n = len(prev)

    prev_counts = Counter(prev)
    next_counts = Counter(nxt)
    joint_counts = Counter(zip(prev, nxt, strict=False))

    mi = 0.0
    for (a, b), c_ab in joint_counts.items():
        p_ab = c_ab / n
        p_a = prev_counts[a] / n
        p_b = next_counts[b] / n
        mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return float(mi)


def _encode_tokens(tokens: list[str]) -> np.ndarray:
    vocab: dict[str, int] = {}
    ids = np.empty(len(tokens), dtype=np.int64)
    next_id = 0
    for i, token in enumerate(tokens):
        idx = vocab.get(token)
        if idx is None:
            idx = next_id
            vocab[token] = idx
            next_id += 1
        ids[i] = idx
    return ids


def _entropy_from_counts(counts: np.ndarray) -> float:
    if counts.size == 0:
        return 0.0
    probs = counts.astype(np.float64)
    probs /= probs.sum()
    return float(-np.sum(probs * np.log2(probs)))


def conditional_entropy_metrics(sequence: list[str]) -> dict[str, float]:
    if len(sequence) < 3:
        return {
            "bigram_cond_entropy": 0.0,
            "trigram_cond_entropy": 0.0,
            "bigram_mutual_information": 0.0,
        }

    ids = _encode_tokens(sequence)
    vocab_size = int(ids.max()) + 1

    prev = ids[:-1]
    nxt = ids[1:]
    bigram_codes = prev * vocab_size + nxt

    h_nxt = _entropy_from_counts(np.unique(nxt, return_counts=True)[1])
    h_prev = _entropy_from_counts(np.unique(prev, return_counts=True)[1])
    h_bigram_joint = _entropy_from_counts(np.unique(bigram_codes, return_counts=True)[1])

    bigram_cond = h_bigram_joint - h_prev
    mi2 = h_nxt - bigram_cond

    prev2 = ids[:-2]
    prev1 = ids[1:-1]
    nxt2 = ids[2:]
    context2_codes = prev2 * vocab_size + prev1
    trigram_codes = context2_codes * vocab_size + nxt2

    h_context2 = _entropy_from_counts(np.unique(context2_codes, return_counts=True)[1])
    h_trigram_joint = _entropy_from_counts(np.unique(trigram_codes, return_counts=True)[1])
    trigram_cond = h_trigram_joint - h_context2

    return {
        "bigram_cond_entropy": float(bigram_cond),
        "trigram_cond_entropy": float(trigram_cond),
        "bigram_mutual_information": float(mi2),
    }


def zipf_alpha(sequence: list[str], rank_limit: int = 500) -> float:
    if not sequence:
        return 0.0
    counts = Counter(sequence)
    freqs = sorted(counts.values(), reverse=True)
    limit = min(rank_limit, len(freqs))
    if limit <= 5:
        return 0.0
    ranks = np.arange(1, limit + 1)
    log_ranks = np.log(ranks)
    log_freqs = np.log(np.array(freqs[:limit], dtype=np.float64))
    slope, _ = np.polyfit(log_ranks, log_freqs, 1)
    return float(-slope)


def line_edge_entropies(lines: list[list[str]]) -> dict[str, float]:
    starts = [line[0] for line in lines if line]
    ends = [line[-1] for line in lines if line]
    return {
        "line_initial_entropy": token_entropy(starts),
        "line_final_entropy": token_entropy(ends),
    }


def _distribution_summary(values: list[float], observed: float) -> dict[str, float | int]:
    arr = np.array(values, dtype=np.float64)
    mean = float(np.mean(arr)) if arr.size else 0.0
    std = float(np.std(arr)) if arr.size else 0.0
    z = float((observed - mean) / std) if std > 0 else 0.0
    if arr.size:
        deviations = np.abs(arr - mean)
        obs_dev = abs(observed - mean)
        p_two_sided = float((np.sum(deviations >= obs_dev) + 1) / (arr.size + 1))
    else:
        p_two_sided = 1.0
    return {
        "mean": mean,
        "std": std,
        "z_score": z,
        "p_two_sided": p_two_sided,
        "n": int(arr.size),
    }


def sequence_metrics(sequence: list[str]) -> dict[str, float]:
    cond = conditional_entropy_metrics(sequence)
    return {
        "entropy": token_entropy(sequence),
        "compression_ratio": compression_ratio(sequence),
        "bits_per_token": compression_bits_per_token(sequence),
        "type_token_ratio": type_token_ratio(sequence),
        "bigram_mutual_information": bigram_mutual_information(sequence),
        "bigram_cond_entropy": cond["bigram_cond_entropy"],
        "trigram_cond_entropy": cond["trigram_cond_entropy"],
    }


def extraction_metrics(sequence: list[str]) -> dict[str, float]:
    return {
        "entropy": token_entropy(sequence),
        "compression_ratio": compression_ratio(sequence),
        "type_token_ratio": type_token_ratio(sequence),
        "bigram_mutual_information": bigram_mutual_information(sequence),
    }


def extract_rule(bundle: CorpusBundle, rule: str) -> list[str]:
    if rule == "line_initial_tokens":
        return [line[0] for line in bundle.lines if line]
    if rule == "line_final_tokens":
        return [line[-1] for line in bundle.lines if line]
    if rule == "word_initial_glyphs":
        return [token[0] for token in bundle.tokens if token]
    if rule == "slot_position_3_glyphs":
        return [token[2] for token in bundle.tokens if len(token) >= 3]
    if rule == "paragraph_initial_tokens":
        firsts: list[str] = []
        for page in bundle.pages:
            for line in page:
                if line:
                    firsts.append(line[0])
                    break
        return firsts
    if rule.startswith("nth_token_"):
        n = int(rule.split("_")[-1])
        return bundle.tokens[n - 1 :: n]
    raise ValueError(f"Unknown extraction rule: {rule}")


def _method_h_features(tokens: list[str]) -> dict[str, Any]:
    if not tokens:
        return {
            "token_count": 0,
            "glyph_count": 0,
            "mean_word_length": 0.0,
            "median_word_length": 0.0,
            "mode_word_length": 0,
            "type_token_ratio": 0.0,
            "ttr_scales": {},
            "ttr_10000": 0.0,
            "combinatorial_productivity_log_ratio": 0.0,
        }

    lengths = [len(token) for token in tokens if token]
    counts = Counter(tokens)
    glyph_count = len({ch for token in tokens for ch in token})

    scales = [1000, 5000, 10000, 50000]
    ttr_scales = {}
    for scale in scales:
        if len(tokens) >= scale:
            ttr_scales[str(scale)] = len(set(tokens[:scale])) / scale

    mean_len = statistics.fmean(lengths) if lengths else 0.0
    rounded_len = max(1, int(round(mean_len)))
    possible_log10 = rounded_len * math.log10(max(glyph_count, 2))
    observed_log10 = math.log10(max(len(counts), 1))

    mode_length = Counter(lengths).most_common(1)[0][0] if lengths else 0

    return {
        "token_count": len(tokens),
        "glyph_count": glyph_count,
        "mean_word_length": mean_len,
        "median_word_length": statistics.median(lengths) if lengths else 0.0,
        "mode_word_length": mode_length,
        "type_token_ratio": len(counts) / len(tokens),
        "ttr_scales": ttr_scales,
        "ttr_10000": ttr_scales.get("10000", len(counts) / len(tokens)),
        "combinatorial_productivity_log_ratio": observed_log10 - possible_log10,
    }


def _typology_distance(features: dict[str, Any], typology: str) -> float:
    center = TYPOLOGY_PROTOTYPES[typology]["center"]
    vals = [
        math.log10(max(features["glyph_count"], 1.0)),
        features["mean_word_length"],
        features["ttr_10000"],
        features["combinatorial_productivity_log_ratio"],
    ]
    center_vals = [
        math.log10(center["glyph_count"]),
        center["mean_word_length"],
        center["ttr_10000"],
        center["productivity_log_ratio"],
    ]
    weights = [1.4, 1.0, 1.0, 0.8]
    squared = [w * ((v - c) ** 2) for w, v, c in zip(weights, vals, center_vals, strict=True)]
    return float(math.sqrt(sum(squared)))


def _excluded_typologies(features: dict[str, Any]) -> list[str]:
    excluded: list[str] = []
    glyph_count = float(features["glyph_count"])
    mean_word_length = float(features["mean_word_length"])

    for typology, data in TYPOLOGY_PROTOTYPES.items():
        g_min, g_max = data["range"]["glyph_count"]
        w_min, w_max = data["range"]["mean_word_length"]
        in_range = g_min <= glyph_count <= g_max and w_min <= mean_word_length <= w_max
        if not in_range:
            excluded.append(typology)
    return excluded


def run_method_h(
    voynich_bundle: CorpusBundle,
    comparison_bundles: list[CorpusBundle],
) -> dict[str, Any]:
    corpora = [voynich_bundle, *comparison_bundles]
    features = {bundle.dataset_id: _method_h_features(bundle.tokens) for bundle in corpora}

    assignments: dict[str, dict[str, Any]] = {}
    for dataset_id, values in features.items():
        distances = {
            typology: _typology_distance(values, typology) for typology in TYPOLOGY_PROTOTYPES
        }
        ranked = sorted(distances.items(), key=lambda item: item[1])
        assignments[dataset_id] = {
            "nearest_typology": ranked[0][0],
            "distance": ranked[0][1],
            "ranked_distances": [
                {"typology": typology, "distance": distance}
                for typology, distance in ranked
            ],
        }

    voynich_assignment = assignments[voynich_bundle.dataset_id]["nearest_typology"]
    generator_same_type = [
        bundle.dataset_id
        for bundle in comparison_bundles
        if assignments[bundle.dataset_id]["nearest_typology"] == voynich_assignment
    ]

    excluded = _excluded_typologies(features[voynich_bundle.dataset_id])

    if not generator_same_type and voynich_assignment not in excluded:
        decision = "closure_weakened"
        reason = (
            "Voynich mapped to a typology distinct from generator controls under the "
            "current feature projection."
        )
    elif generator_same_type or len(excluded) >= 3:
        decision = "closure_strengthened"
        reason = (
            "Voynich occupies the same typological neighborhood as at least one generator "
            "or falls outside most typology ranges."
        )
    else:
        decision = "indeterminate"
        reason = "Voynich typology assignment is weakly separated and not decisive."

    return {
        "method": "H",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "voynich_dataset_id": voynich_bundle.dataset_id,
        "voynich_excluded_typologies": excluded,
        "features": features,
        "assignments": assignments,
        "generator_same_typology": generator_same_type,
    }


def _method_j_rule_metrics(bundle: CorpusBundle) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rule in EXTRACTION_RULES:
        seq = extract_rule(bundle, rule)
        out[rule] = {
            "description": EXTRACTION_RULES[rule],
            "token_count": len(seq),
            "metrics": extraction_metrics(seq),
        }
    return out


def _stability_score(
    voynich_bundle: CorpusBundle,
    rule: str,
    metric: str,
    null_values: list[float],
    seed: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if not null_values:
        return {
            "bootstrap_pass_rate": 0.0,
            "line_permutation_pass_rate": 0.0,
            "stable": False,
        }

    rng = np.random.default_rng(seed)
    base_seq = extract_rule(voynich_bundle, rule)
    max_sequence = 20000
    if len(base_seq) > max_sequence:
        base_seq = base_seq[:max_sequence]
    if len(base_seq) < 8:
        return {
            "bootstrap_pass_rate": 0.0,
            "line_permutation_pass_rate": 0.0,
            "stable": False,
        }

    null_arr = np.array(null_values, dtype=np.float64)
    null_mean = float(np.mean(null_arr))
    null_std = float(np.std(null_arr))
    if null_std == 0:
        return {
            "bootstrap_pass_rate": 0.0,
            "line_permutation_pass_rate": 0.0,
            "stable": False,
        }

    def metric_value(sequence: list[str]) -> float:
        if metric == "entropy":
            return float(token_entropy(sequence))
        if metric == "bigram_mutual_information":
            return float(bigram_mutual_information(sequence))
        metrics = sequence_metrics(sequence)
        return float(metrics.get(metric, 0.0))

    bootstrap_pass = 0
    line_perm_pass = 0
    iterations = 12

    for idx in range(iterations):
        sample_idx = rng.integers(0, len(base_seq), len(base_seq))
        sample = [base_seq[int(i)] for i in sample_idx]
        sample_value = metric_value(sample)
        if abs((sample_value - null_mean) / null_std) >= 3.0:
            bootstrap_pass += 1
        if progress and ((idx + 1) % max(1, iterations // 3) == 0 or idx + 1 == iterations):
            progress(f"Method J stability bootstrap {idx + 1}/{iterations} ({rule}/{metric})")

    for idx in range(iterations):
        perm_lines = [list(line) for line in voynich_bundle.lines]
        rng.shuffle(perm_lines)
        perm_bundle = CorpusBundle(
            dataset_id=voynich_bundle.dataset_id,
            label=voynich_bundle.label,
            tokens=_flatten(perm_lines),
            lines=perm_lines,
            pages=_chunk_lines_into_pages(perm_lines, _mean_lines_per_page(voynich_bundle)),
        )
        seq = extract_rule(perm_bundle, rule)
        if len(seq) > max_sequence:
            seq = seq[:max_sequence]
        perm_value = metric_value(seq)
        if abs((perm_value - null_mean) / null_std) >= 3.0:
            line_perm_pass += 1
        if progress and ((idx + 1) % max(1, iterations // 3) == 0 or idx + 1 == iterations):
            progress(
                f"Method J stability permutation {idx + 1}/{iterations} ({rule}/{metric})"
            )

    bootstrap_rate = bootstrap_pass / iterations
    permutation_rate = line_perm_pass / iterations
    stable = bootstrap_rate >= 0.8 and permutation_rate >= 0.8

    return {
        "bootstrap_pass_rate": bootstrap_rate,
        "line_permutation_pass_rate": permutation_rate,
        "stable": stable,
    }


def run_method_j(
    voynich_bundle: CorpusBundle,
    generators: dict[str, Any],
    target_tokens: int,
    null_runs: int,
    seed: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            "Method J start: "
            f"target_tokens={target_tokens}, null_runs={null_runs}, "
            f"rules={len(EXTRACTION_RULES)}"
        )
    lines_per_page = _mean_lines_per_page(voynich_bundle)

    voynich_metrics = _method_j_rule_metrics(voynich_bundle)

    null_values: dict[str, dict[str, list[float]]] = {
        rule: {
            "entropy": [],
            "compression_ratio": [],
            "type_token_ratio": [],
            "bigram_mutual_information": [],
        }
        for rule in EXTRACTION_RULES
    }

    families = sorted(generators.keys())
    family_counts = {family: 0 for family in families}
    stride = max(1, null_runs // 20)
    for i in range(null_runs):
        family = families[i % len(families)]
        family_counts[family] += 1
        bundle = generate_bundle_from_generator(
            generator=generators[family],
            dataset_id=f"{family}_null_{i + 1}",
            label=f"{family} null {i + 1}",
            target_tokens=target_tokens,
            lines_per_page=lines_per_page,
        )
        metrics_by_rule = _method_j_rule_metrics(bundle)
        for rule, values in metrics_by_rule.items():
            metric_values = values["metrics"]
            for metric_name in null_values[rule]:
                null_values[rule][metric_name].append(float(metric_values[metric_name]))
        if progress and ((i + 1) % stride == 0 or i + 1 == null_runs):
            progress(f"Method J null calibration {i + 1}/{null_runs} (family={family})")

    summary: dict[str, dict[str, Any]] = {}
    raw_anomalies: list[dict[str, Any]] = []
    for rule, metrics in voynich_metrics.items():
        summary[rule] = {}
        for metric_name, observed_value in metrics["metrics"].items():
            if metric_name not in null_values[rule]:
                continue
            stats = _distribution_summary(null_values[rule][metric_name], float(observed_value))
            summary[rule][metric_name] = stats

            if metric_name in {"entropy", "bigram_mutual_information"} and abs(
                float(stats["z_score"])
            ) >= 3.0:
                raw_anomalies.append(
                    {"rule": rule, "metric": metric_name, "z_score": float(stats["z_score"])}
                )
        if progress:
            progress(f"Method J summarized rule: {rule}")

    anomalies: list[dict[str, Any]] = []
    stability_cap = 4
    ranked_anomalies = sorted(raw_anomalies, key=lambda row: abs(row["z_score"]), reverse=True)
    if progress:
        progress(
            f"Method J anomaly review: total={len(raw_anomalies)}, "
            f"stability_checks={min(len(raw_anomalies), stability_cap)}"
        )
    for idx, anomaly in enumerate(ranked_anomalies):
        if idx < stability_cap:
            if progress:
                progress(
                    "Method J stability check "
                    f"{idx + 1}/{min(len(ranked_anomalies), stability_cap)} "
                    f"for {anomaly['rule']} / {anomaly['metric']}"
                )
            stability = _stability_score(
                voynich_bundle=voynich_bundle,
                rule=anomaly["rule"],
                metric=anomaly["metric"],
                null_values=null_values[anomaly["rule"]][anomaly["metric"]],
                seed=seed + idx,
                progress=progress,
            )
        else:
            stability = {
                "bootstrap_pass_rate": 0.0,
                "line_permutation_pass_rate": 0.0,
                "stable": False,
                "skipped_reason": "stability_cap_reached",
            }
        anomalies.append({**anomaly, "stability": stability})

    stable_anomalies = [entry for entry in anomalies if entry["stability"]["stable"]]
    if stable_anomalies:
        decision = "closure_weakened"
        reason = "At least one extraction anomaly is strong and stable under resampling tests."
    elif not anomalies:
        decision = "closure_strengthened"
        reason = "No extraction rule shows a |z| > 3 anomaly on entropy/MI versus generator nulls."
    else:
        decision = "indeterminate"
        reason = "Anomalies were observed but did not survive stability checks."
    if progress:
        progress(f"Method J complete: decision={decision}, anomalies={len(anomalies)}")

    return {
        "method": "J",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "config": {
            "target_tokens": target_tokens,
            "null_runs": null_runs,
            "family_counts": family_counts,
            "seed": seed,
        },
        "voynich_rule_metrics": voynich_metrics,
        "null_summary": summary,
        "anomalies": anomalies,
    }


def analyze_method_j_line_reset_effects(
    method_j_result: dict[str, Any],
    z_threshold: float = 3.0,
    edge_rules: set[str] | None = None,
) -> dict[str, Any]:
    rules = edge_rules or METHOD_J_EDGE_RULES
    anomalies = method_j_result.get("anomalies", [])

    stable_anomalies = [
        row
        for row in anomalies
        if abs(float(row.get("z_score", 0.0))) >= z_threshold
        and bool(row.get("stability", {}).get("stable", False))
    ]
    edge_stable = [row for row in stable_anomalies if row.get("rule") in rules]
    non_edge_stable = [row for row in stable_anomalies if row.get("rule") not in rules]
    permutation_stable_non_edge = [
        row
        for row in non_edge_stable
        if float(row.get("stability", {}).get("line_permutation_pass_rate", 0.0)) >= 0.8
    ]

    if permutation_stable_non_edge:
        ablated_decision = "closure_weakened"
        interpretation = "non_line_reset_signal_present"
    elif edge_stable:
        ablated_decision = "indeterminate"
        interpretation = "line_reset_dominated_anomalies"
    else:
        ablated_decision = "closure_strengthened"
        interpretation = "no_stable_anomalies"

    return {
        "z_threshold": z_threshold,
        "edge_rules": sorted(rules),
        "stable_anomalies_total": len(stable_anomalies),
        "stable_edge_anomalies": edge_stable,
        "stable_non_edge_anomalies": non_edge_stable,
        "permutation_stable_non_edge_anomalies": permutation_stable_non_edge,
        "ablated_decision_without_edge_rules": ablated_decision,
        "interpretation": interpretation,
    }


def evaluate_method_j_upgrade_gate(
    method_j_result: dict[str, Any],
    z_threshold: float = 3.0,
    min_stable_non_edge_anomalies: int = 1,
    edge_rules: set[str] | None = None,
) -> dict[str, Any]:
    ablation = analyze_method_j_line_reset_effects(
        method_j_result=method_j_result,
        z_threshold=z_threshold,
        edge_rules=edge_rules,
    )
    non_edge = ablation["permutation_stable_non_edge_anomalies"]
    pass_gate = len(non_edge) >= min_stable_non_edge_anomalies

    if pass_gate:
        reason = (
            "Method J gate passed: stable |z|>threshold anomalies remain after removing "
            "line-initial/paragraph-initial effects."
        )
    else:
        reason = (
            "Method J gate failed: anomalies are fully explained by line-reset edge rules "
            "or are not stable under folio-order permutation."
        )

    return {
        "pass": pass_gate,
        "reason": reason,
        "z_threshold": z_threshold,
        "min_stable_non_edge_anomalies": min_stable_non_edge_anomalies,
        "ablation": ablation,
    }


def _method_k_features(bundle: CorpusBundle) -> dict[str, float]:
    tokens = bundle.tokens
    cond = conditional_entropy_metrics(tokens)
    line_edge = line_edge_entropies(bundle.lines)
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
        "line_initial_entropy": line_edge["line_initial_entropy"],
        "line_final_entropy": line_edge["line_final_entropy"],
        "hapax_ratio": float(hapax / max(len(counts), 1)),
    }


def _distance_to_voynich(voynich_features: dict[str, float], candidate: dict[str, float]) -> float:
    deltas = []
    for key, v_value in voynich_features.items():
        denom = abs(v_value) if abs(v_value) > 1e-8 else 1.0
        deltas.append(abs(candidate[key] - v_value) / denom)
    return float(statistics.fmean(deltas))


def _candidate_generators_for_k(
    voynich_lines: list[list[str]], seed: int
) -> dict[str, Any]:
    candidates = {
        "line_reset_markov": LineResetMarkovGenerator(LineResetMarkovConfig(random_state=seed)),
        "line_reset_backoff": LineResetBackoffGenerator(LineResetBackoffConfig(random_state=seed)),
        "line_reset_persistence": LineResetPersistenceGenerator(
            LineResetPersistenceConfig(random_state=seed)
        ),
    }
    for generator in candidates.values():
        generator.fit(voynich_lines)
    return candidates


def _parameter_sweep_settings(best_family: str) -> list[dict[str, Any]]:
    if best_family == "line_reset_backoff":
        return [
            {"trigram_use_prob": 0.45, "unigram_noise_prob": 0.01},
            {"trigram_use_prob": 0.65, "unigram_noise_prob": 0.01},
            {"trigram_use_prob": 0.55, "unigram_noise_prob": 0.08},
            {"trigram_use_prob": 0.70, "unigram_noise_prob": 0.03},
        ]
    if best_family == "line_reset_persistence":
        return [
            {
                "boundary_persistence_rho": 0.15,
                "trigram_use_prob": 0.55,
                "unigram_noise_prob": 0.03,
            },
            {
                "boundary_persistence_rho": 0.35,
                "trigram_use_prob": 0.55,
                "unigram_noise_prob": 0.03,
            },
            {
                "boundary_persistence_rho": 0.25,
                "trigram_use_prob": 0.70,
                "unigram_noise_prob": 0.03,
            },
            {
                "boundary_persistence_rho": 0.25,
                "trigram_use_prob": 0.55,
                "unigram_noise_prob": 0.08,
            },
        ]
    return []


def _instantiate_generator(family: str, seed: int, params: dict[str, Any] | None = None) -> Any:
    params = params or {}
    if family == "line_reset_markov":
        return LineResetMarkovGenerator(LineResetMarkovConfig(random_state=seed, **params))
    if family == "line_reset_backoff":
        return LineResetBackoffGenerator(LineResetBackoffConfig(random_state=seed, **params))
    if family == "line_reset_persistence":
        return LineResetPersistenceGenerator(
            LineResetPersistenceConfig(random_state=seed, **params)
        )
    raise ValueError(f"Unknown family: {family}")


def run_method_k(
    voynich_bundle: CorpusBundle,
    latin_bundle: CorpusBundle,
    target_tokens: int,
    num_runs: int,
    seed: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            "Method K start: "
            f"target_tokens={target_tokens}, synthetic_runs={num_runs}"
        )
    lines_per_page = _mean_lines_per_page(voynich_bundle)
    voynich_features = _method_k_features(voynich_bundle)
    latin_features = _method_k_features(latin_bundle)

    candidates = _candidate_generators_for_k(voynich_bundle.lines, seed)

    candidate_scores: dict[str, Any] = {}
    for family, generator in candidates.items():
        sample_bundle = generate_bundle_from_generator(
            generator=generator,
            dataset_id=f"{family}_candidate",
            label=f"{family} candidate",
            target_tokens=target_tokens,
            lines_per_page=lines_per_page,
        )
        sample_features = _method_k_features(sample_bundle)
        score = _distance_to_voynich(voynich_features, sample_features)
        candidate_scores[family] = {
            "distance": score,
            "sample_features": sample_features,
        }
        if progress:
            progress(f"Method K candidate scored: {family} distance={score:.4f}")

    ranked_families = sorted(candidate_scores.items(), key=lambda item: item[1]["distance"])
    best_family = ranked_families[0][0]
    best_generator = candidates[best_family]
    if progress:
        progress(f"Method K best generator family selected: {best_family}")

    synthetic_features: list[dict[str, float]] = []
    stride = max(1, num_runs // 20)
    for i in range(num_runs):
        synthetic_bundle = generate_bundle_from_generator(
            generator=best_generator,
            dataset_id=f"{best_family}_run_{i + 1}",
            label=f"{best_family} run {i + 1}",
            target_tokens=target_tokens,
            lines_per_page=lines_per_page,
        )
        synthetic_features.append(_method_k_features(synthetic_bundle))
        if progress and ((i + 1) % stride == 0 or i + 1 == num_runs):
            progress(f"Method K synthetic run {i + 1}/{num_runs}")

    feature_stats: dict[str, Any] = {}
    outliers: list[str] = []
    for feature in voynich_features:
        values = [row[feature] for row in synthetic_features]
        stats = _distribution_summary(values, voynich_features[feature])
        feature_stats[feature] = {
            "voynich": voynich_features[feature],
            "generator_mean": float(stats["mean"]),
            "generator_std": float(stats["std"]),
            "z_score": float(stats["z_score"]),
        }
        if abs(float(stats["z_score"])) >= 2.0:
            outliers.append(feature)
    if progress:
        progress(f"Method K outlier features identified: {len(outliers)}")

    correlation_matrix: list[list[float]] = []
    mean_abs_correlation = 0.0
    if len(outliers) >= 2:
        matrix = np.array(
            [[row[feature] for feature in outliers] for row in synthetic_features],
            dtype=np.float64,
        )
        corr = np.corrcoef(matrix, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0)
        correlation_matrix = corr.tolist()
        upper = np.abs(corr[np.triu_indices_from(corr, k=1)])
        mean_abs_correlation = float(np.mean(upper)) if upper.size else 0.0

    direction_to_language: dict[str, Any] = {}
    for feature in outliers:
        gen_mean = feature_stats[feature]["generator_mean"]
        voynich_value = feature_stats[feature]["voynich"]
        latin_value = latin_features[feature]

        distance_generator_to_latin = abs(gen_mean - latin_value)
        distance_voynich_to_latin = abs(voynich_value - latin_value)

        direction_to_language[feature] = {
            "toward_language": bool(distance_voynich_to_latin < distance_generator_to_latin),
            "voynich_to_latin_distance": float(distance_voynich_to_latin),
            "generator_to_latin_distance": float(distance_generator_to_latin),
        }

    sweep_settings = _parameter_sweep_settings(best_family)
    modification_difficulty: dict[str, Any] = {}
    if outliers and sweep_settings:
        sweep_results: list[tuple[str, dict[str, float]]] = []
        for idx, setting in enumerate(sweep_settings):
            trial = _instantiate_generator(best_family, seed + 1000 + idx, setting)
            trial.fit(voynich_bundle.lines)
            trial_bundle = generate_bundle_from_generator(
                generator=trial,
                dataset_id=f"{best_family}_sweep_{idx + 1}",
                label=f"{best_family} sweep {idx + 1}",
                target_tokens=target_tokens,
                lines_per_page=lines_per_page,
            )
            trial_features = _method_k_features(trial_bundle)
            sweep_results.append((str(setting), trial_features))
            if progress:
                progress(f"Method K parameter sweep {idx + 1}/{len(sweep_settings)} complete")

        for feature in outliers:
            baseline_diff = abs(
                feature_stats[feature]["voynich"] - feature_stats[feature]["generator_mean"]
            )
            best_setting = "none"
            best_diff = baseline_diff
            for setting_name, trial_features in sweep_results:
                trial_diff = abs(feature_stats[feature]["voynich"] - trial_features[feature])
                if trial_diff < best_diff:
                    best_diff = trial_diff
                    best_setting = setting_name

            if baseline_diff <= 1e-9:
                improvement = 0.0
            else:
                improvement = float((baseline_diff - best_diff) / baseline_diff)

            if improvement >= 0.5:
                difficulty = "trivial_single_parameter"
            elif improvement >= 0.2:
                difficulty = "moderate"
            else:
                difficulty = "hard_framework_shift"

            modification_difficulty[feature] = {
                "difficulty": difficulty,
                "best_setting": best_setting,
                "improvement_ratio": improvement,
                "baseline_difference": baseline_diff,
                "best_difference": best_diff,
            }
    else:
        for feature in outliers:
            modification_difficulty[feature] = {
                "difficulty": "hard_framework_shift",
                "best_setting": "none",
                "improvement_ratio": 0.0,
                "baseline_difference": abs(
                    feature_stats[feature]["voynich"] - feature_stats[feature]["generator_mean"]
                ),
                "best_difference": abs(
                    feature_stats[feature]["voynich"] - feature_stats[feature]["generator_mean"]
                ),
            }

    toward_language_count = sum(
        1 for row in direction_to_language.values() if row["toward_language"]
    )
    hard_count = sum(
        1
        for row in modification_difficulty.values()
        if row["difficulty"] == "hard_framework_shift"
    )

    if (
        len(outliers) >= 2
        and mean_abs_correlation >= 0.4
        and toward_language_count >= 2
        and hard_count >= 2
    ):
        decision = "closure_weakened"
        reason = (
            "Residual outliers are correlated, trend toward language baseline, and are "
            "not closed by small generator parameter changes."
        )
    elif not outliers or (
        mean_abs_correlation < 0.3
        and all(
            row["difficulty"] in {"trivial_single_parameter", "moderate"}
            for row in modification_difficulty.values()
        )
    ):
        decision = "closure_strengthened"
        reason = "Residual gaps are either absent or closable with minor parameter adjustments."
    else:
        decision = "indeterminate"
        reason = "Residual gaps exist but do not form a decisive correlated-language trend."
    if progress:
        progress(
            "Method K complete: "
            f"decision={decision}, outliers={len(outliers)}, best_family={best_family}"
        )

    return {
        "method": "K",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "config": {
            "target_tokens": target_tokens,
            "num_runs": num_runs,
            "seed": seed,
        },
        "best_generator_family": best_family,
        "candidate_scores": candidate_scores,
        "feature_stats": feature_stats,
        "outlier_features": outliers,
        "outlier_correlation_matrix": correlation_matrix,
        "outlier_mean_abs_correlation": mean_abs_correlation,
        "direction_to_language": direction_to_language,
        "modification_difficulty": modification_difficulty,
    }


def summarize_stage1(method_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decisions = {
        method: result.get("decision", "indeterminate")
        for method, result in method_results.items()
    }

    if any(value == "closure_weakened" for value in decisions.values()):
        stage_decision = "closure_weakened"
    elif all(value == "closure_strengthened" for value in decisions.values()):
        stage_decision = "closure_strengthened"
    else:
        stage_decision = "indeterminate"

    return {
        "status": "ok",
        "stage": "10.1",
        "stage_decision": stage_decision,
        "method_decisions": decisions,
        "generated_at": now_utc_iso(),
    }


def build_stage1_markdown(
    summary: dict[str, Any],
    method_artifacts: dict[str, str],
    status_path: str,
) -> str:
    lines = [
        "# Phase 10 Stage 1 Results (Methods H/J/K)",
        "",
        f"Generated: {summary['generated_at']}",
        f"Stage decision: **{summary['stage_decision']}**",
        "",
        "## Method Decisions",
        "",
        f"- Method H (Writing System Typology): `{summary['method_decisions'].get('H', 'n/a')}`",
        f"- Method J (Steganographic Extraction): `{summary['method_decisions'].get('J', 'n/a')}`",
        f"- Method K (Residual Gap Anatomy): `{summary['method_decisions'].get('K', 'n/a')}`",
        "",
        "## Artifacts",
        "",
        f"- Method H artifact: `{method_artifacts.get('H', 'n/a')}`",
        f"- Method J artifact: `{method_artifacts.get('J', 'n/a')}`",
        f"- Method K artifact: `{method_artifacts.get('K', 'n/a')}`",
        f"- Stage 1 summary artifact: `{method_artifacts.get('stage1', 'n/a')}`",
        f"- Restart status tracker: `{status_path}`",
        "",
        "## Restart Guidance",
        "",
        "- The status tracker records completion per method and can be used to resume safely.",
        "- Re-running the Stage 1 script skips completed methods unless `--force` is provided.",
        "",
    ]
    return "\n".join(lines)
