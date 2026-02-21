#!/usr/bin/env python3
"""Build Phase 19 folio alignment benchmark manifest."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase19_alignment.data import (  # noqa: E402
    build_folio_map,
    build_schedule_map,
    folio_sort_key,
    load_folio_data,
    load_page_schedule,
)

OUTPUT_PATH = PROJECT_ROOT / "results/data/phase19_alignment/folio_match_benchmark.json"


def stable_hash(value: str, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def split_section(folios: list[str], seed: int) -> tuple[list[str], list[str], list[str]]:
    ordered = sorted(folios, key=lambda folio_id: stable_hash(folio_id, seed))
    n = len(ordered)
    if n == 0:
        return [], [], []

    test_n = 0
    val_n = 0
    if n >= 3:
        test_n = max(1, int(round(n * 0.2)))
    if n >= 6:
        val_n = max(1, int(round(n * 0.1)))

    if test_n + val_n >= n:
        if val_n > 0:
            val_n -= 1
        elif test_n > 1:
            test_n -= 1

    test_ids = ordered[:test_n]
    val_ids = ordered[test_n : test_n + val_n]
    train_ids = ordered[test_n + val_n :]

    if not train_ids:
        if val_ids:
            train_ids.append(val_ids.pop())
        elif test_ids:
            train_ids.append(test_ids.pop())

    return train_ids, val_ids, test_ids


def marker_from_location(location: str) -> str:
    if "," not in location:
        return ""
    return location.split(",", 1)[1].strip()


def main() -> None:
    seed = 19042
    folio_payload = load_folio_data(PROJECT_ROOT)
    schedule_payload = load_page_schedule(PROJECT_ROOT)

    folio_map = build_folio_map(folio_payload)
    schedule_map = build_schedule_map(schedule_payload)

    by_section: dict[str, list[str]] = defaultdict(list)
    folio_meta: dict[str, dict] = {}

    for folio_id in sorted(folio_map.keys(), key=folio_sort_key):
        folio = folio_map[folio_id]
        schedule = schedule_map.get(folio_id, {})
        section = str(schedule.get("section") or "Other")
        hand = str(schedule.get("hand") or "Unknown")
        side = "r" if folio_id.endswith("r") else ("v" if folio_id.endswith("v") else "unknown")

        marker_counts: dict[str, int] = defaultdict(int)
        marker_sequence: list[str] = []
        for idx, line in enumerate(folio.get("lines", [])):
            marker = marker_from_location(str(line.get("location", "")))
            if not marker:
                marker = "@P0" if idx == 0 else "+P0"
            marker_sequence.append(marker)
            marker_counts[marker] += 1

        by_section[section].append(folio_id)
        folio_meta[folio_id] = {
            "section": section,
            "hand": hand,
            "side": side,
            "line_count": int(folio.get("line_count", len(folio.get("lines", [])))),
            "marker_histogram": dict(sorted(marker_counts.items())),
            "marker_sequence": marker_sequence,
        }

    train_ids: list[str] = []
    val_ids: list[str] = []
    test_ids: list[str] = []
    split_counts: dict[str, dict[str, int]] = {}

    for section, folios in sorted(by_section.items()):
        train_part, val_part, test_part = split_section(folios, seed)
        train_ids.extend(train_part)
        val_ids.extend(val_part)
        test_ids.extend(test_part)
        split_counts[section] = {
            "total": len(folios),
            "train": len(train_part),
            "val": len(val_part),
            "test": len(test_part),
        }

    train_ids = sorted(train_ids, key=folio_sort_key)
    val_ids = sorted(val_ids, key=folio_sort_key)
    test_ids = sorted(test_ids, key=folio_sort_key)

    long_folios = sorted(
        folio_meta.keys(),
        key=lambda folio_id: folio_meta[folio_id]["line_count"],
        reverse=True,
    )[:20]
    sparse_sections = [
        section for section, rows in sorted(by_section.items()) if len(rows) <= 5
    ]
    stress_sparse = sorted(
        [
            folio_id
            for folio_id in folio_meta
            if folio_meta[folio_id]["section"] in sparse_sections
        ],
        key=folio_sort_key,
    )

    marker_variety = sorted(
        folio_meta.keys(),
        key=lambda folio_id: len(folio_meta[folio_id]["marker_histogram"]),
        reverse=True,
    )[:20]

    fingerprint_payload = {
        "seed": seed,
        "train": train_ids,
        "val": val_ids,
        "test": test_ids,
        "split_counts": split_counts,
    }
    split_hash = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    payload = {
        "schema_version": "phase19_benchmark_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "sources": {
            "folio_data": "tools/workbench/data/folio_data.js",
            "page_schedule": "results/data/phase18_generate/folio_state_schedule.json",
        },
        "splits": {
            "train": train_ids,
            "val": val_ids,
            "test": test_ids,
        },
        "split_counts_by_section": split_counts,
        "stress_sets": {
            "long_folios": long_folios,
            "sparse_section_folios": stress_sparse,
            "high_marker_variety": marker_variety,
        },
        "folio_metadata": folio_meta,
        "summary": {
            "folio_count": len(folio_meta),
            "train_count": len(train_ids),
            "val_count": len(val_ids),
            "test_count": len(test_ids),
            "section_count": len(by_section),
            "sparse_sections": sparse_sections,
            "split_hash": split_hash,
            "average_lines_per_folio": sum(v["line_count"] for v in folio_meta.values())
            / max(len(folio_meta), 1),
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(payload, OUTPUT_PATH)

    print("Phase 19 benchmark manifest created:")
    print(f"  - {OUTPUT_PATH}")
    print(
        "  - counts: "
        f"train={len(train_ids)}, val={len(val_ids)}, test={len(test_ids)}, hash={split_hash[:12]}"
    )


if __name__ == "__main__":
    with active_run(config={"seed": 19042, "command": "build_folio_match_benchmark"}):
        main()
