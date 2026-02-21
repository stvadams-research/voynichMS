#!/usr/bin/env python3
"""Phase 19B: Retrieval-plus-edit baseline evaluation."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase19_alignment.evaluation import (  # noqa: E402
    build_training_stats,
    evaluate_single_method,
    generate_retrieval_edit,
)
from phase19_alignment.generator import PageGeneratorModel  # noqa: E402

BENCHMARK_PATH = PROJECT_ROOT / "results/data/phase19_alignment/folio_match_benchmark.json"
OUTPUT_PATH = PROJECT_ROOT / "results/data/phase19_alignment/retrieval_edit.json"


def load_benchmark(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def main() -> None:
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Missing benchmark manifest: {BENCHMARK_PATH}")

    benchmark = load_benchmark(BENCHMARK_PATH)
    model = PageGeneratorModel.from_project_root(str(PROJECT_ROOT))
    train_folios = benchmark.get("splits", {}).get("train", [])
    stats = build_training_stats(model, train_folios)

    split_results = {}
    for split_name in ["train", "val", "test"]:
        folio_ids = benchmark.get("splits", {}).get(split_name, [])
        split_results[split_name] = evaluate_single_method(
            model=model,
            folio_ids=folio_ids,
            method_name=f"retrieval_edit/{split_name}",
            generator_fn=lambda folio_id, _split=split_name: generate_retrieval_edit(
                model=model,
                folio_id=folio_id,
                stats=stats,
                seed=42,
            ),
        )

    output = {
        "schema_version": "phase19_retrieval_edit_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {
            "benchmark": str(BENCHMARK_PATH.relative_to(PROJECT_ROOT)),
            "folio_data": "tools/workbench/data/folio_data.js",
            "lattice_data": "tools/workbench/data/lattice_data.js",
            "page_schedule": "results/data/phase18_generate/folio_state_schedule.json",
        },
        "summary": {
            "train_folio_count": len(train_folios),
            "split_counts": {
                split_name: len(benchmark.get("splits", {}).get(split_name, []))
                for split_name in ["train", "val", "test"]
            },
        },
        "results_by_split": split_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(output, OUTPUT_PATH)

    test_summary = split_results["test"]["summary"]["metrics"]
    print("Phase 19B complete: retrieval-edit baseline evaluated")
    print(f"  - output: {OUTPUT_PATH}")
    print(
        "  - test composite mean: "
        f"{test_summary['composite_score']['summary']['mean']:.4f}"
    )


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_19b_retrieval_edit"}):
        main()
