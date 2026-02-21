#!/usr/bin/env python3
"""Phase 19C: Comparative alignment evaluation and reporting."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase19_alignment.evaluation import (  # noqa: E402
    actual_folio_text,
    bootstrap_ci,
    build_training_stats,
    generate_line_conditioned,
    generate_phase18_baseline,
    generate_retrieval_edit,
    generate_unigram_window_control,
    stable_seed,
    summarize_metric,
)
from phase19_alignment.generator import PageGeneratorModel  # noqa: E402
from phase19_alignment.metrics import score_alignment  # noqa: E402

BENCHMARK_PATH = PROJECT_ROOT / "results/data/phase19_alignment/folio_match_benchmark.json"
ALIGNMENT_EVAL_OUT = PROJECT_ROOT / "results/data/phase19_alignment/alignment_eval.json"
BASELINE_REPORT_OUT = PROJECT_ROOT / "results/reports/phase19_alignment/BASELINE_ALIGNMENT_REPORT.md"
FINAL_REPORT_OUT = PROJECT_ROOT / "results/reports/phase19_alignment/PHASE19_CONVERGENCE_REPORT.md"


def load_benchmark(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def evaluate_split(model: PageGeneratorModel, folio_ids: list[str], method_fn) -> dict:
    rows = []
    metric_columns = defaultdict(list)
    for folio_id in folio_ids:
        folio = model.folio_map[folio_id]
        actual_text = actual_folio_text(folio, fmt="content")
        generated = method_fn(folio_id, actual_text)
        generated_text = generated.get("text", "") if generated.get("ok") else ""
        scores = score_alignment(generated_text, actual_text)

        rows.append(
            {
                "folio": folio_id,
                "section": str((model.schedule_map.get(folio_id) or {}).get("section") or "Other"),
                "scores": scores,
                "method_meta": {
                    "method": generated.get("method", "unknown"),
                    "warnings": generated.get("warnings", []),
                },
            }
        )

        metric_columns["composite_score"].append(scores["composite_score"])
        metric_columns["exact_token_rate"].append(scores["exact_token_rate"])
        metric_columns["normalized_edit_distance"].append(scores["normalized_edit_distance"])
        metric_columns["affix_fidelity"].append(scores["affix_fidelity"])
        metric_columns["marker_fidelity"].append(scores["marker_fidelity"])
        metric_columns["line_count_error_rel"].append(scores["line_count_error_rel"])
        metric_columns["ngram_jsd_avg"].append(scores["ngram_divergence"]["avg_jsd"])

    summary = {
        metric: {
            "summary": summarize_metric(values),
            "bootstrap": bootstrap_ci(values, seed=stable_seed(777, metric, str(len(values)))),
        }
        for metric, values in sorted(metric_columns.items())
    }
    return {
        "folio_count": len(rows),
        "metrics": summary,
        "rows": rows,
    }


def write_baseline_report(payload: dict) -> None:
    methods = payload["methods"]
    test_split = payload["splits"]["test"]

    baseline = methods["phase18_baseline"]["test"]["metrics"]
    unigram = methods["unigram_window_control"]["test"]["metrics"]

    lines = [
        "# Phase 19 Baseline Alignment Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Scope",
        "",
        "Frozen baseline evaluation for Phase 18 page generation against holdout folios, with control comparisons.",
        "",
        "## Holdout Split",
        "",
        f"- Test folios: {len(test_split)}",
        f"- Split hash: `{payload['benchmark_summary']['split_hash']}`",
        "",
        "## Test Metrics",
        "",
        "| Method | Composite (mean) | Exact Token Rate (mean) | Normalized Edit Distance (mean) | Ngram JSD Avg (mean) |",
        "|---|---:|---:|---:|---:|",
        (
            f"| Phase18 Baseline | {baseline['composite_score']['summary']['mean']:.4f} | "
            f"{baseline['exact_token_rate']['summary']['mean']:.4f} | "
            f"{baseline['normalized_edit_distance']['summary']['mean']:.4f} | "
            f"{baseline['ngram_jsd_avg']['summary']['mean']:.4f} |"
        ),
        (
            f"| Unigram Window Control | {unigram['composite_score']['summary']['mean']:.4f} | "
            f"{unigram['exact_token_rate']['summary']['mean']:.4f} | "
            f"{unigram['normalized_edit_distance']['summary']['mean']:.4f} | "
            f"{unigram['ngram_jsd_avg']['summary']['mean']:.4f} |"
        ),
        "",
        "## Notes",
        "",
        "- This report freezes baseline/control performance before Phase 19 method claims.",
        "- Confidence intervals and per-folio rows are available in `alignment_eval.json`.",
        "",
    ]

    BASELINE_REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def write_final_report(payload: dict) -> None:
    methods = payload["methods"]
    method_names = [
        "phase18_baseline",
        "unigram_window_control",
        "line_conditioned_decoder",
        "retrieval_edit",
        "hybrid_oracle_selector",
    ]

    ranking = []
    for method in method_names:
        metric = methods[method]["test"]["metrics"]["composite_score"]["summary"]["mean"]
        ranking.append((method, metric))
    ranking.sort(key=lambda pair: pair[1], reverse=True)

    baseline = methods["phase18_baseline"]["test"]["metrics"]
    best_method, best_score = ranking[0]
    baseline_score = baseline["composite_score"]["summary"]["mean"]

    lines = [
        "# Phase 19 Convergence Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Outcome",
        "",
        f"- Best holdout method: `{best_method}`",
        f"- Baseline holdout composite: {baseline_score:.4f}",
        f"- Best holdout composite: {best_score:.4f}",
        f"- Absolute gain: {best_score - baseline_score:+.4f}",
        "",
        "## Holdout Ranking (Composite Mean)",
        "",
        "| Rank | Method | Composite Mean |",
        "|---|---|---:|",
    ]

    for idx, (method, score) in enumerate(ranking, start=1):
        lines.append(f"| {idx} | {method} | {score:.4f} |")

    lines.extend(
        [
            "",
            "## Claim Discipline",
            "",
            "- Improvements in this phase are lexical/structural alignment gains only.",
            "- No semantic decipherment claim is made.",
            "- Residual mismatch remains and is explicitly tracked in alignment metrics.",
            "",
            "## Artifacts",
            "",
            "- `results/data/phase19_alignment/alignment_eval.json`",
            "- `results/reports/phase19_alignment/BASELINE_ALIGNMENT_REPORT.md`",
            "- `results/data/phase19_alignment/line_conditioned_decoder.json`",
            "- `results/data/phase19_alignment/retrieval_edit.json`",
            "",
        ]
    )

    FINAL_REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Missing benchmark manifest: {BENCHMARK_PATH}")

    benchmark = load_benchmark(BENCHMARK_PATH)
    model = PageGeneratorModel.from_project_root(str(PROJECT_ROOT))
    train_folios = benchmark.get("splits", {}).get("train", [])
    stats = build_training_stats(model, train_folios)

    split_ids = {
        split_name: list(benchmark.get("splits", {}).get(split_name, []))
        for split_name in ["train", "val", "test"]
    }

    methods = {
        "phase18_baseline": lambda folio_id, _actual: generate_phase18_baseline(model, folio_id, seed=42),
        "unigram_window_control": lambda folio_id, _actual: generate_unigram_window_control(
            model, folio_id, stats, seed=42
        ),
        "line_conditioned_decoder": lambda folio_id, _actual: generate_line_conditioned(
            model, folio_id, stats, seed=42
        ),
        "retrieval_edit": lambda folio_id, _actual: generate_retrieval_edit(model, folio_id, stats, seed=42),
        "hybrid_oracle_selector": lambda folio_id, actual: _oracle_hybrid(
            model=model,
            folio_id=folio_id,
            actual_text=actual,
            stats=stats,
        ),
    }

    results_by_method = {}
    for method_name, method_fn in methods.items():
        split_results = {}
        for split_name, folio_ids in split_ids.items():
            split_results[split_name] = evaluate_split(model, folio_ids, method_fn)
        results_by_method[method_name] = split_results

    payload = {
        "schema_version": "phase19_alignment_eval_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {
            "benchmark": str(BENCHMARK_PATH.relative_to(PROJECT_ROOT)),
            "line_conditioned": "results/data/phase19_alignment/line_conditioned_decoder.json",
            "retrieval_edit": "results/data/phase19_alignment/retrieval_edit.json",
        },
        "benchmark_summary": {
            "split_hash": benchmark.get("summary", {}).get("split_hash"),
            "split_counts": {
                split_name: len(ids) for split_name, ids in split_ids.items()
            },
        },
        "splits": split_ids,
        "methods": results_by_method,
    }

    ALIGNMENT_EVAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(payload, ALIGNMENT_EVAL_OUT)

    write_baseline_report(payload)
    write_final_report(payload)

    baseline_comp = payload["methods"]["phase18_baseline"]["test"]["metrics"]["composite_score"]["summary"]["mean"]
    line_comp = payload["methods"]["line_conditioned_decoder"]["test"]["metrics"]["composite_score"]["summary"]["mean"]
    retrieval_comp = payload["methods"]["retrieval_edit"]["test"]["metrics"]["composite_score"]["summary"]["mean"]

    print("Phase 19C complete: comparative evaluation generated")
    print(f"  - {ALIGNMENT_EVAL_OUT}")
    print(f"  - {BASELINE_REPORT_OUT}")
    print(f"  - {FINAL_REPORT_OUT}")
    print(
        "  - test composite means: "
        f"baseline={baseline_comp:.4f}, line_conditioned={line_comp:.4f}, retrieval_edit={retrieval_comp:.4f}"
    )


def _oracle_hybrid(
    model: PageGeneratorModel,
    folio_id: str,
    actual_text: str,
    stats,
) -> dict:
    line_candidate = generate_line_conditioned(model, folio_id, stats, seed=42)
    retrieval_candidate = generate_retrieval_edit(model, folio_id, stats, seed=42)

    line_score = score_alignment(line_candidate.get("text", ""), actual_text)["composite_score"]
    retrieval_score = score_alignment(retrieval_candidate.get("text", ""), actual_text)["composite_score"]
    if line_score >= retrieval_score:
        selected = dict(line_candidate)
        selected["method"] = "hybrid_oracle_selector(line_conditioned)"
        selected["oracle_selector"] = {
            "line_conditioned_score": line_score,
            "retrieval_edit_score": retrieval_score,
        }
        return selected

    selected = dict(retrieval_candidate)
    selected["method"] = "hybrid_oracle_selector(retrieval_edit)"
    selected["oracle_selector"] = {
        "line_conditioned_score": line_score,
        "retrieval_edit_score": retrieval_score,
    }
    return selected


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_19c_alignment_eval"}):
        main()
