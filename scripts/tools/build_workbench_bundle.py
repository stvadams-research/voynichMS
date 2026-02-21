#!/usr/bin/env python3
"""Build standalone data bundles for tools/workbench.

Reads canonical JSON artifacts and emits browser-friendly JS files for
file:// execution without fetch().
"""

from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SLIPS_PATH = PROJECT_ROOT / "results/data/phase13_demonstration/slip_viz_data.json"
LATTICE_PATH = PROJECT_ROOT / "results/data/phase14_machine/full_palette_grid.json"
FOLIO_PATH = PROJECT_ROOT / "data/raw/transliterations/ivtff2.0/ZL3b-n.txt"
PAGE_SCHEDULE_PATH = (
    PROJECT_ROOT / "results/data/phase18_generate/folio_state_schedule.json"
)
PAGE_PRIORS_PATH = (
    PROJECT_ROOT / "results/data/phase18_generate/page_priors.json"
)
SCAN_1000_DIR = PROJECT_ROOT / "data/raw/scans/jpg/folios_1000"
SCAN_2000_DIR = PROJECT_ROOT / "data/raw/scans/jpg/folios_2000"
SCAN_MANIFEST_PATH = SCAN_1000_DIR / "manifest_mapping.csv"
SCAN_REL_PREFIX = "../../data/raw/scans/jpg"
OUT_DIR = PROJECT_ROOT / "tools/workbench/data"
LINE_PATTERN = re.compile(r"^<([^>]+)>\s*(.*)$")
FOLIO_META_PATTERN = re.compile(r"^f\d+[rv]\d*$")
FOLIO_ID_PATTERN = re.compile(r"^f(\d+)([rv])(\d*)$")
OID_PATTERN = re.compile(r".*_(\d+)\.jpg$")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_results(payload: dict) -> dict:
    results = payload.get("results")
    return results if isinstance(results, dict) else payload


def write_js(path: Path, variable_name: str, payload: dict) -> None:
    serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    content = f"window.{variable_name} = {serialized};\n"
    path.write_text(content, encoding="utf-8")


def folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
    match = FOLIO_ID_PATTERN.match(folio_id)
    if not match:
        return (10**9, 1, 10**9, folio_id)
    number = int(match.group(1))
    side = 0 if match.group(2) == "r" else 1
    suffix = int(match.group(3) or "0")
    return (number, side, suffix, folio_id)


def parse_line_no(location: str) -> int | None:
    if "." not in location:
        return None
    tail = location.split(".", 1)[1]
    head = tail.split(",", 1)[0]
    return int(head) if head.isdigit() else None


def build_oid_to_filename(scan_dir: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not scan_dir.exists():
        return mapping
    for image_path in sorted(scan_dir.glob("*.jpg")):
        match = OID_PATTERN.match(image_path.name)
        if not match:
            continue
        oid = match.group(1)
        mapping.setdefault(oid, image_path.name)
    return mapping


def normalize_scan_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())


def folio_scan_keys(folio_id: str) -> list[str]:
    raw = folio_id.lower().strip()
    if raw.startswith("f"):
        raw = raw[1:]
    keys = [raw]

    suffix_match = re.match(r"^(\d+[rv])\d+$", raw)
    if suffix_match:
        keys.append(suffix_match.group(1))
    else:
        keys.append(raw)

    # Preserve order while removing duplicates.
    unique: list[str] = []
    for key in keys:
        if key not in unique:
            unique.append(key)
    return unique


def load_scan_manifest() -> list[dict[str, str]]:
    if not SCAN_MANIFEST_PATH.exists():
        return []

    by_oid_1000 = build_oid_to_filename(SCAN_1000_DIR)
    by_oid_2000 = build_oid_to_filename(SCAN_2000_DIR)
    rows: list[dict[str, str]] = []

    with SCAN_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = str(row.get("label", "")).strip()
            oid = str(row.get("oid", "")).strip()
            if not label or not oid:
                continue
            file_1000 = by_oid_1000.get(oid, "")
            file_2000 = by_oid_2000.get(oid, "")
            if not file_1000 and not file_2000:
                continue
            rows.append(
                {
                    "label": label,
                    "label_norm": normalize_scan_label(label),
                    "oid": oid,
                    "file_1000": file_1000,
                    "file_2000": file_2000,
                }
            )

    return rows


def resolve_scan_paths(folio_id: str, scan_manifest: list[dict[str, str]]) -> dict[str, str | None]:
    if not scan_manifest:
        return {"scan_thumb": None, "scan_full": None, "scan_label": None}

    keys = folio_scan_keys(folio_id)
    key_norms = [normalize_scan_label(k) for k in keys]

    def pick(predicate):
        for entry in scan_manifest:
            if predicate(entry):
                return entry
        return None

    match = None
    for key in keys:
        match = pick(lambda entry, k=key: entry["label"].lower() == k)
        if match:
            break

    if not match:
        for key_norm in key_norms:
            match = pick(lambda entry, k=key_norm: entry["label_norm"].startswith(k))
            if match:
                break

    if not match:
        for key_norm in key_norms:
            match = pick(lambda entry, k=key_norm: k in entry["label_norm"])
            if match:
                break

    if not match:
        return {"scan_thumb": None, "scan_full": None, "scan_label": None}

    thumb = (
        f"{SCAN_REL_PREFIX}/folios_1000/{match['file_1000']}"
        if match.get("file_1000")
        else None
    )
    full = (
        f"{SCAN_REL_PREFIX}/folios_2000/{match['file_2000']}"
        if match.get("file_2000")
        else None
    )
    return {
        "scan_thumb": thumb,
        "scan_full": full,
        "scan_label": match.get("label"),
    }


def build_folio_bundle(path: Path, scan_manifest: list[dict[str, str]]) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing folio source: {path}")

    by_folio: dict[str, list[dict]] = {}

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            match = LINE_PATTERN.match(line)
            if not match:
                continue

            location = match.group(1).strip()
            content = match.group(2).strip()

            # Skip page-level metadata lines like <f1r> <! ...>
            if FOLIO_META_PATTERN.match(location):
                continue
            if not content:
                continue

            folio_id = location.split(".", 1)[0]
            entry = {
                "location": location,
                "line_no": parse_line_no(location),
                "content": content,
            }
            by_folio.setdefault(folio_id, []).append(entry)

    folio_ids = sorted(by_folio.keys(), key=folio_sort_key)
    folios = []
    mapped_scans = 0
    for folio_id in folio_ids:
        scan_info = resolve_scan_paths(folio_id, scan_manifest)
        if scan_info["scan_thumb"] or scan_info["scan_full"]:
            mapped_scans += 1
        folios.append(
            {
                "folio": folio_id,
                "line_count": len(by_folio[folio_id]),
                "lines": by_folio[folio_id],
                "scan_thumb": scan_info["scan_thumb"],
                "scan_full": scan_info["scan_full"],
                "scan_label": scan_info["scan_label"],
            }
        )

    return {
        "source_id": "zandbergen_landini",
        "transliteration_file": str(path.relative_to(PROJECT_ROOT)),
        "scan_manifest_file": str(SCAN_MANIFEST_PATH.relative_to(PROJECT_ROOT)),
        "folio_count": len(folios),
        "line_count": sum(f["line_count"] for f in folios),
        "scan_mapped_folios": mapped_scans,
        "folios": folios,
    }


def main() -> None:
    if not SLIPS_PATH.exists():
        raise FileNotFoundError(f"Missing slips artifact: {SLIPS_PATH}")
    if not LATTICE_PATH.exists():
        raise FileNotFoundError(f"Missing lattice artifact: {LATTICE_PATH}")

    slips_raw = load_json(SLIPS_PATH)
    slips = {"slips": slips_raw.get("slips", [])}
    if not slips["slips"]:
        raise ValueError("Slip dataset is empty.")

    lattice_raw = load_json(LATTICE_PATH)
    lattice_results = lattice_raw.get("results", lattice_raw)

    lattice_map = lattice_results.get("lattice_map")
    window_contents = lattice_results.get("window_contents")
    if not isinstance(lattice_map, dict) or not lattice_map:
        raise ValueError("lattice_map missing or empty in palette artifact.")
    if not isinstance(window_contents, dict) or not window_contents:
        raise ValueError("window_contents missing or empty in palette artifact.")

    lattice = {
        "lattice_map": lattice_map,
        "window_contents": window_contents,
    }
    scan_manifest = load_scan_manifest()
    folios = build_folio_bundle(FOLIO_PATH, scan_manifest)
    if PAGE_SCHEDULE_PATH.exists():
        page_schedule = extract_results(load_json(PAGE_SCHEDULE_PATH))
        page_schedule["available"] = True
    else:
        page_schedule = {
            "available": False,
            "reason": (
                "Missing results/data/phase18_generate/folio_state_schedule.json. "
                "Run scripts/phase18_generate/build_page_generation_assets.py."
            ),
        }

    if PAGE_PRIORS_PATH.exists():
        page_priors = extract_results(load_json(PAGE_PRIORS_PATH))
        page_priors["available"] = True
    else:
        page_priors = {
            "available": False,
            "reason": (
                "Missing results/data/phase18_generate/page_priors.json. "
                "Run scripts/phase18_generate/build_page_generation_assets.py."
            ),
        }

    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {
            "slips": str(SLIPS_PATH.relative_to(PROJECT_ROOT)),
            "lattice": str(LATTICE_PATH.relative_to(PROJECT_ROOT)),
            "folios": str(FOLIO_PATH.relative_to(PROJECT_ROOT)),
            "page_schedule": (
                str(PAGE_SCHEDULE_PATH.relative_to(PROJECT_ROOT))
                if PAGE_SCHEDULE_PATH.exists()
                else None
            ),
            "page_priors": (
                str(PAGE_PRIORS_PATH.relative_to(PROJECT_ROOT))
                if PAGE_PRIORS_PATH.exists()
                else None
            ),
        },
        "counts": {
            "slips": len(slips["slips"]),
            "lattice_vocab": len(lattice_map),
            "windows": len(window_contents),
            "folios": folios["folio_count"],
            "folio_lines": folios["line_count"],
            "folio_scans_mapped": folios["scan_mapped_folios"],
            "page_schedule_folios": len(page_schedule.get("folios", []))
            if page_schedule.get("available")
            else 0,
            "page_priors_folios": len(page_priors.get("observed_folios", {}))
            if page_priors.get("available")
            else 0,
        },
        "phase18": {
            "page_schedule_available": bool(page_schedule.get("available")),
            "page_priors_available": bool(page_priors.get("available")),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_js(OUT_DIR / "slips_data.js", "WORKBENCH_SLIPS", slips)
    write_js(OUT_DIR / "lattice_data.js", "WORKBENCH_LATTICE", lattice)
    write_js(OUT_DIR / "folio_data.js", "WORKBENCH_FOLIOS", folios)
    write_js(
        OUT_DIR / "page_schedule_data.js",
        "WORKBENCH_PAGE_SCHEDULE",
        page_schedule,
    )
    write_js(
        OUT_DIR / "page_priors_data.js",
        "WORKBENCH_PAGE_PRIORS",
        page_priors,
    )
    write_js(OUT_DIR / "metadata.js", "WORKBENCH_METADATA", metadata)

    print("Built workbench bundles:")
    print(f"  - {OUT_DIR / 'slips_data.js'}")
    print(f"  - {OUT_DIR / 'lattice_data.js'}")
    print(f"  - {OUT_DIR / 'folio_data.js'}")
    print(f"  - {OUT_DIR / 'page_schedule_data.js'}")
    print(f"  - {OUT_DIR / 'page_priors_data.js'}")
    print(f"  - {OUT_DIR / 'metadata.js'}")
    print("Counts:")
    print(f"  slips={metadata['counts']['slips']}")
    print(f"  lattice_vocab={metadata['counts']['lattice_vocab']}")
    print(f"  windows={metadata['counts']['windows']}")
    print(f"  folios={metadata['counts']['folios']}")
    print(f"  folio_lines={metadata['counts']['folio_lines']}")
    print(f"  folio_scans_mapped={metadata['counts']['folio_scans_mapped']}")
    print(f"  page_schedule_folios={metadata['counts']['page_schedule_folios']}")
    print(f"  page_priors_folios={metadata['counts']['page_priors_folios']}")


if __name__ == "__main__":
    main()
