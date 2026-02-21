from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "results/data/phase19_alignment/folio_match_benchmark.json"
LINE_CONDITIONED_PATH = ROOT / "results/data/phase19_alignment/line_conditioned_decoder.json"
RETRIEVAL_EDIT_PATH = ROOT / "results/data/phase19_alignment/retrieval_edit.json"
ALIGNMENT_EVAL_PATH = ROOT / "results/data/phase19_alignment/alignment_eval.json"
BASELINE_REPORT_PATH = ROOT / "results/reports/phase19_alignment/BASELINE_ALIGNMENT_REPORT.md"
FINAL_REPORT_PATH = ROOT / "results/reports/phase19_alignment/PHASE19_CONVERGENCE_REPORT.md"
WORKBENCH_PAGE_VIEW_PATH = ROOT / "tools/workbench/js/views/page_generator_view.js"
WORKBENCH_INDEX_PATH = ROOT / "tools/workbench/index.html"


def _load_result_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def test_phase19_benchmark_manifest_schema() -> None:
    assert BENCHMARK_PATH.exists(), f"Missing benchmark artifact: {BENCHMARK_PATH}"
    benchmark = _load_result_json(BENCHMARK_PATH)

    assert benchmark.get("schema_version") == "phase19_benchmark_v1"
    splits = benchmark.get("splits", {})
    summary = benchmark.get("summary", {})

    assert isinstance(splits.get("train"), list)
    assert isinstance(splits.get("val"), list)
    assert isinstance(splits.get("test"), list)
    assert summary.get("folio_count", 0) > 0

    split_total = len(splits["train"]) + len(splits["val"]) + len(splits["test"])
    assert split_total == summary.get("folio_count")
    assert summary.get("split_hash")


def test_phase19_method_artifacts_exist_and_match_split_counts() -> None:
    benchmark = _load_result_json(BENCHMARK_PATH)
    expected_counts = {
        split_name: len(benchmark.get("splits", {}).get(split_name, []))
        for split_name in ["train", "val", "test"]
    }

    line_conditioned = _load_result_json(LINE_CONDITIONED_PATH)
    retrieval_edit = _load_result_json(RETRIEVAL_EDIT_PATH)

    assert line_conditioned.get("schema_version") == "phase19_line_conditioned_v1"
    assert retrieval_edit.get("schema_version") == "phase19_retrieval_edit_v1"

    for split_name, expected in expected_counts.items():
        line_count = line_conditioned["results_by_split"][split_name]["summary"]["folio_count"]
        retrieval_count = retrieval_edit["results_by_split"][split_name]["summary"]["folio_count"]
        assert line_count == expected
        assert retrieval_count == expected


def test_phase19_alignment_eval_contains_holdout_improvement() -> None:
    alignment = _load_result_json(ALIGNMENT_EVAL_PATH)
    assert alignment.get("schema_version") == "phase19_alignment_eval_v1"

    methods = alignment.get("methods", {})
    required_methods = {
        "phase18_baseline",
        "unigram_window_control",
        "line_conditioned_decoder",
        "retrieval_edit",
        "hybrid_oracle_selector",
    }
    assert required_methods.issubset(set(methods.keys()))

    baseline = methods["phase18_baseline"]["test"]["metrics"]["composite_score"]["summary"]["mean"]
    contenders = [
        methods["line_conditioned_decoder"]["test"]["metrics"]["composite_score"]["summary"]["mean"],
        methods["retrieval_edit"]["test"]["metrics"]["composite_score"]["summary"]["mean"],
        methods["hybrid_oracle_selector"]["test"]["metrics"]["composite_score"]["summary"]["mean"],
    ]

    assert any(score > baseline for score in contenders)


def test_phase19_reports_and_workbench_hooks_exist() -> None:
    assert BASELINE_REPORT_PATH.exists(), f"Missing report: {BASELINE_REPORT_PATH}"
    assert FINAL_REPORT_PATH.exists(), f"Missing report: {FINAL_REPORT_PATH}"

    page_view = WORKBENCH_PAGE_VIEW_PATH.read_text(encoding="utf-8")
    index_html = WORKBENCH_INDEX_PATH.read_text(encoding="utf-8")

    assert "scoreGeneratedAgainstActual" in page_view
    assert 'id="page-alignment"' in index_html
