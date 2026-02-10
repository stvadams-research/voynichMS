#!/usr/bin/env python3
"""
Sensitivity sweep runner for parameter robustness checks.

Outputs:
- status/audit/sensitivity_sweep.json (with provenance envelope)
- reports/audit/SENSITIVITY_RESULTS.md
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from contextlib import ExitStack, contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rich.console import Console
from rich.table import Table

from analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer
from analysis.models.constructed_system import (
    GlossalialSystemModel,
    MeaningfulConstructModel,
    ProceduralGenerationModel,
)
from analysis.models.disconfirmation import DisconfirmationEngine
from analysis.models.evaluation import CrossModelEvaluator
from analysis.models.visual_grammar import (
    AdjacencyGrammarModel,
    ContainmentGrammarModel,
    DiagramAnnotationModel,
)
from foundation.config import DEFAULT_SEED
from foundation.core.provenance import ProvenanceWriter
from foundation.runs.manager import active_run
from foundation.storage.metadata import (
    DatasetRecord,
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)

console = Console()
MODEL_PARAMS_PATH = PROJECT_ROOT / "configs/functional/model_params.json"
STATUS_PATH = PROJECT_ROOT / "status/audit/sensitivity_sweep.json"
REPORT_PATH = PROJECT_ROOT / "reports/audit/SENSITIVITY_RESULTS.md"
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
DEFAULT_DATASET_ID = "voynich_real"
DEFAULT_SWEEP_MODE = "release"
MIN_VALID_SCENARIO_RATE = 0.80


class WarningCapture(logging.Handler):
    """Collect warning messages for quality reporting."""

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            self.messages.append(record.getMessage())


@contextmanager
def _capture_logger_warnings(logger_name: str):
    logger = logging.getLogger(logger_name)
    handler = WarningCapture()
    previous_level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


@contextmanager
def _scenario_model_params(model_params: Dict[str, Any]):
    """Patch model-parameter lookups so scenario config is fully in-memory."""
    with ExitStack() as stack:
        stack.enter_context(
            patch("foundation.config.get_model_params", return_value=model_params)
        )
        stack.enter_context(
            patch("analysis.models.disconfirmation.get_model_params", return_value=model_params)
        )
        stack.enter_context(
            patch("analysis.models.evaluation.get_model_params", return_value=model_params)
        )
        yield


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return weights
    return {k: float(v) / total for k, v in weights.items()}


def _summarize_warnings(messages: List[str]) -> Dict[str, Any]:
    insufficient_data = sum("Insufficient data for" in m for m in messages)
    nan_sanitized = sum("NaN degradation detected" in m for m in messages)
    return {
        "total_warnings": len(messages),
        "insufficient_data_warnings": insufficient_data,
        "nan_sanitized_warnings": nan_sanitized,
        "sample_messages": messages[:5],
    }


def _load_dataset_profile(store: MetadataStore, dataset_id: str) -> Dict[str, Any]:
    session = store.Session()
    try:
        dataset_exists = (
            session.query(DatasetRecord.id)
            .filter(DatasetRecord.id == dataset_id)
            .first()
            is not None
        )
        page_count = session.query(PageRecord.id).filter(PageRecord.dataset_id == dataset_id).count()
        token_count = (
            session.query(TranscriptionTokenRecord.id)
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .count()
        )
    finally:
        session.close()

    if not dataset_exists:
        raise ValueError(
            f"Dataset '{dataset_id}' does not exist in metadata store. "
            "Run corpus build scripts before sensitivity analysis."
        )
    if page_count == 0:
        raise ValueError(
            f"Dataset '{dataset_id}' has zero pages. Sensitivity sweep cannot proceed."
        )
    if token_count == 0:
        raise ValueError(
            f"Dataset '{dataset_id}' has zero transcription tokens. "
            "Sensitivity sweep cannot proceed."
        )

    return {
        "dataset_id": dataset_id,
        "pages": int(page_count),
        "tokens": int(token_count),
    }


def _run_model_evaluation_scenario(
    db_url: str,
    dataset_id: str,
    model_params: Dict[str, Any],
) -> Dict[str, Any]:
    store = MetadataStore(db_url)
    models = [
        AdjacencyGrammarModel(store),
        ContainmentGrammarModel(store),
        DiagramAnnotationModel(store),
        ProceduralGenerationModel(store),
        GlossalialSystemModel(store),
        MeaningfulConstructModel(store),
    ]

    with _scenario_model_params(model_params):
        with _capture_logger_warnings("analysis.models.perturbation") as warning_capture:
            engine = DisconfirmationEngine(store)
            for model in models:
                engine.run_prediction_tests(model, dataset_id)
                engine.run_full_battery(model, dataset_id)

            eval_report = CrossModelEvaluator(models).generate_report()
            top_model, top_score = eval_report["overall_ranking"][0]
            anomaly_status = AnomalyStabilityAnalyzer().analyze()

    warning_summary = _summarize_warnings(warning_capture.messages)

    metrics = {
        "top_model": top_model,
        "top_score": float(top_score),
        "surviving_models": int(eval_report["surviving_models"]),
        "falsified_models": int(eval_report["falsified_models"]),
        "anomaly_confirmed": bool(anomaly_status["anomaly_confirmed"]),
        "anomaly_stable": bool(anomaly_status["all_stable"]),
    }

    quality_flags: List[str] = []
    if warning_summary["insufficient_data_warnings"] > 0:
        quality_flags.append("insufficient_data")
    if metrics["surviving_models"] == 0:
        quality_flags.append("all_models_falsified")

    return {
        "metrics": metrics,
        "warnings": warning_summary,
        "quality_flags": quality_flags,
        "valid": len(quality_flags) == 0,
    }


def _apply_threshold(cfg: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    out = copy.deepcopy(cfg)
    battery = out.get("disconfirmation", {}).get("perturbation_battery", [])
    for item in battery:
        item["failure_threshold"] = float(threshold)
    return out


def _apply_sensitivity_scale(cfg: Dict[str, Any], factor: float) -> Dict[str, Any]:
    out = copy.deepcopy(cfg)
    models = out.get("models", {})
    for model_data in models.values():
        sensitivities = model_data.get("sensitivities", {})
        for key, value in sensitivities.items():
            sensitivities[key] = round(float(value) * factor, 6)
    return out


def _apply_weight_variant(cfg: Dict[str, Any], focus_dimension: str, factor: float) -> Dict[str, Any]:
    out = copy.deepcopy(cfg)
    weights = out.get("evaluation", {}).get("dimension_weights", {})
    adjusted = {}
    for dim, value in weights.items():
        base = float(value)
        adjusted[dim] = base * factor if dim == focus_dimension else base
    out["evaluation"]["dimension_weights"] = _normalize_weights(adjusted)
    return out


def _build_scenarios(base_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenarios: List[Dict[str, Any]] = [
        {"id": "baseline", "family": "baseline", "config": copy.deepcopy(base_cfg)}
    ]

    threshold = 0.40
    while threshold <= 0.8000001:
        scenarios.append(
            {
                "id": f"threshold_{threshold:.2f}",
                "family": "threshold_sweep",
                "config": _apply_threshold(base_cfg, threshold),
            }
        )
        threshold += 0.05

    for factor in (0.8, 1.2):
        scenarios.append(
            {
                "id": f"sensitivity_x{factor:.2f}",
                "family": "sensitivity_scale",
                "config": _apply_sensitivity_scale(base_cfg, factor),
            }
        )

    for dim in base_cfg.get("evaluation", {}).get("dimension_weights", {}).keys():
        scenarios.append(
            {
                "id": f"weights_focus_{dim}",
                "family": "weight_permutation",
                "config": _apply_weight_variant(base_cfg, dim, 1.2),
            }
        )

    return scenarios


def _decide_robustness(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {
            "total_scenarios": 0,
            "valid_scenarios": 0,
            "valid_scenario_rate": 0.0,
            "top_model_match_rate": 0.0,
            "anomaly_match_rate": 0.0,
            "all_models_falsified_everywhere": True,
            "quality_gate_passed": False,
            "robustness_conclusive": False,
            "robust": False,
            "robustness_decision": "INCONCLUSIVE",
            "caveats": ["No scenarios were executed."],
            "insufficient_data_scenarios": 0,
            "total_warning_count": 0,
        }

    valid = [r for r in results if r["valid"]]
    valid_rate = len(valid) / total
    all_models_falsified_everywhere = all(r["surviving_models"] == 0 for r in results)
    insufficient_data_scenarios = sum(
        1 for r in results if "insufficient_data" in r["quality_flags"]
    )
    total_warning_count = sum(r["warnings"]["total_warnings"] for r in results)

    if valid:
        baseline = valid[0]
        top_model_match_rate = sum(
            1 for r in valid if r["top_model"] == baseline["top_model"]
        ) / len(valid)
        anomaly_match_rate = sum(
            1
            for r in valid
            if r["anomaly_confirmed"] == baseline["anomaly_confirmed"]
        ) / len(valid)
        baseline_top_model = baseline["top_model"]
        baseline_anomaly_confirmed = baseline["anomaly_confirmed"]
    else:
        baseline = results[0]
        top_model_match_rate = 0.0
        anomaly_match_rate = 0.0
        baseline_top_model = baseline["top_model"]
        baseline_anomaly_confirmed = baseline["anomaly_confirmed"]

    caveats: List[str] = []
    if insufficient_data_scenarios > 0:
        caveats.append(
            f"{insufficient_data_scenarios}/{total} scenarios emitted insufficient-data warnings."
        )
    if all_models_falsified_everywhere:
        caveats.append(
            "All scenarios reported zero surviving models; robustness PASS is not defensible."
        )
    if valid_rate < MIN_VALID_SCENARIO_RATE:
        caveats.append(
            f"Valid scenario rate {valid_rate:.2%} is below required {MIN_VALID_SCENARIO_RATE:.0%}."
        )

    robust = (
        not all_models_falsified_everywhere
        and valid_rate >= MIN_VALID_SCENARIO_RATE
        and top_model_match_rate >= 0.9
        and anomaly_match_rate >= 0.9
    )

    if all_models_falsified_everywhere or not valid:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if robust else "FAIL"

    quality_gate_passed = (
        not all_models_falsified_everywhere
        and valid_rate >= MIN_VALID_SCENARIO_RATE
    )
    robustness_conclusive = decision in {"PASS", "FAIL"}

    return {
        "total_scenarios": total,
        "valid_scenarios": len(valid),
        "valid_scenario_rate": valid_rate,
        "baseline_top_model": baseline_top_model,
        "baseline_anomaly_confirmed": baseline_anomaly_confirmed,
        "top_model_match_rate": top_model_match_rate,
        "anomaly_match_rate": anomaly_match_rate,
        "all_models_falsified_everywhere": all_models_falsified_everywhere,
        "quality_gate_passed": quality_gate_passed,
        "robustness_conclusive": robustness_conclusive,
        "insufficient_data_scenarios": insufficient_data_scenarios,
        "total_warning_count": total_warning_count,
        "robust": robust,
        "robustness_decision": decision,
        "caveats": caveats,
    }


def _is_release_evidence_ready(
    summary: Dict[str, Any],
    *,
    mode: str,
    max_scenarios: int | None,
    scenario_count_expected: int,
    scenario_count_executed: int,
) -> bool:
    return (
        mode == "release"
        and max_scenarios is None
        and scenario_count_executed == scenario_count_expected
        and bool(summary.get("quality_gate_passed")) is True
        and bool(summary.get("robustness_conclusive")) is True
    )


def _write_markdown_report(
    summary: Dict[str, Any],
    dataset_profile: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Sensitivity Results\n\n")
        f.write(f"- Sweep date: {summary['date']}\n")
        f.write(f"- Dataset: `{dataset_profile['dataset_id']}`\n")
        f.write(f"- Dataset pages: `{dataset_profile['pages']}`\n")
        f.write(f"- Dataset tokens: `{dataset_profile['tokens']}`\n")
        f.write(f"- Execution mode: `{summary['execution_mode']}`\n")
        f.write(
            f"- Scenario execution: `{summary['scenario_count_executed']}/"
            f"{summary['scenario_count_expected']}`\n"
        )
        f.write(
            "- Release evidence ready "
            "(full sweep + conclusive robustness + quality gate): "
            f"`{summary['release_evidence_ready']}`\n"
        )
        f.write(f"- Total scenarios: {summary['total_scenarios']}\n")
        f.write(f"- Valid scenarios: {summary['valid_scenarios']} ({summary['valid_scenario_rate']:.2%})\n")
        f.write(f"- Baseline top model: `{summary['baseline_top_model']}`\n")
        f.write(f"- Baseline anomaly confirmed: `{summary['baseline_anomaly_confirmed']}`\n")
        f.write(f"- Top-model stability rate (valid scenarios): `{summary['top_model_match_rate']:.2%}`\n")
        f.write(f"- Anomaly-status stability rate (valid scenarios): `{summary['anomaly_match_rate']:.2%}`\n")
        f.write(f"- Robustness decision: `{summary['robustness_decision']}`\n")
        f.write(
            "- Robustness conclusive "
            "(`PASS`/`FAIL`, excludes `INCONCLUSIVE`): "
            f"`{summary['robustness_conclusive']}`\n"
        )
        f.write(
            "- Quality gate passed "
            "(valid-scenario-rate threshold + non-collapse): "
            f"`{summary['quality_gate_passed']}`\n"
        )
        f.write(f"- Robustness gate passed (>90% both + quality gates): `{summary['robust']}`\n\n")

        f.write("## Data Quality Caveats\n\n")
        f.write(f"- Total warnings observed: `{summary['total_warning_count']}`\n")
        f.write(
            f"- Scenarios with insufficient-data warnings: "
            f"`{summary['insufficient_data_scenarios']}/{summary['total_scenarios']}`\n"
        )
        f.write(
            "- All scenarios zero-survivor: "
            f"`{summary['all_models_falsified_everywhere']}`\n"
        )
        if summary["caveats"]:
            for caveat in summary["caveats"]:
                f.write(f"- Caveat: {caveat}\n")
        else:
            f.write("- Caveat: none\n")

        f.write("\n## Scenario Results\n\n")
        f.write(
            "| Scenario | Family | Top Model | Top Score | Surviving | Falsified | "
            "Warnings | Quality Flags | Valid |\n"
        )
        f.write("|---|---|---|---:|---:|---:|---:|---|---|\n")
        for row in results:
            flags = ", ".join(row["quality_flags"]) if row["quality_flags"] else "-"
            f.write(
                f"| `{row['id']}` | {row['family']} | `{row['top_model']}` | "
                f"{row['top_score']:.3f} | {row['surviving_models']} | {row['falsified_models']} | "
                f"{row['warnings']['total_warnings']} | {flags} | {row['valid']} |\n"
            )


def main(
    dataset_id: str = DEFAULT_DATASET_ID,
    db_url: str = DEFAULT_DB_URL,
    max_scenarios: int | None = None,
    mode: str = DEFAULT_SWEEP_MODE,
) -> None:
    if mode not in {"release", "smoke"}:
        raise ValueError(f"Unsupported sensitivity sweep mode: {mode}")
    if mode == "release" and max_scenarios is not None:
        raise ValueError(
            "Release mode requires full scenario execution; "
            "do not pass --max-scenarios."
        )

    with active_run(
        config={
            "command": "run_sensitivity_sweep",
            "seed": DEFAULT_SEED,
            "dataset_id": dataset_id,
            "db_url": db_url,
            "max_scenarios": max_scenarios,
            "mode": mode,
        }
    ) as run:
        with open(MODEL_PARAMS_PATH, "r", encoding="utf-8") as f:
            base_cfg = json.load(f)

        store = MetadataStore(db_url)
        dataset_profile = _load_dataset_profile(store, dataset_id)
        all_scenarios = _build_scenarios(base_cfg)
        scenario_count_expected = len(all_scenarios)

        if mode == "smoke" and max_scenarios is None:
            max_scenarios = 1

        scenarios = all_scenarios
        if max_scenarios is not None:
            scenarios = all_scenarios[:max_scenarios]
        results: List[Dict[str, Any]] = []

        for scenario in scenarios:
            scenario_result = _run_model_evaluation_scenario(
                db_url,
                dataset_id,
                scenario["config"],
            )
            row = {
                "id": scenario["id"],
                "family": scenario["family"],
                **scenario_result["metrics"],
                "warnings": scenario_result["warnings"],
                "quality_flags": scenario_result["quality_flags"],
                "valid": scenario_result["valid"],
            }
            results.append(row)

            console.print(
                f"[green]done[/green] {row['id']} -> {row['top_model']} "
                f"(surviving={row['surviving_models']}, warnings={row['warnings']['total_warnings']})"
            )

        summary = _decide_robustness(results)
        summary["date"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        summary["dataset_id"] = dataset_id
        summary["dataset_pages"] = dataset_profile["pages"]
        summary["dataset_tokens"] = dataset_profile["tokens"]
        summary["execution_mode"] = mode
        summary["scenario_count_expected"] = scenario_count_expected
        summary["scenario_count_executed"] = len(scenarios)
        summary["release_evidence_ready"] = _is_release_evidence_ready(
            summary,
            mode=mode,
            max_scenarios=max_scenarios,
            scenario_count_expected=scenario_count_expected,
            scenario_count_executed=len(scenarios),
        )

        status_payload = {
            "summary": summary,
            "dataset_profile": dataset_profile,
            "results": results,
        }
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(status_payload, STATUS_PATH)
        _write_markdown_report(summary, dataset_profile, results)
        store.save_run(run)

        table = Table(title="Sensitivity Sweep Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Dataset", dataset_id)
        table.add_row("Mode", mode)
        table.add_row(
            "Scenario execution",
            f"{summary['scenario_count_executed']}/{summary['scenario_count_expected']}",
        )
        table.add_row("Release evidence ready", str(summary["release_evidence_ready"]))
        table.add_row("Total scenarios", str(summary["total_scenarios"]))
        table.add_row("Valid scenarios", f"{summary['valid_scenarios']} ({summary['valid_scenario_rate']:.2%})")
        table.add_row("Top-model match rate", f"{summary['top_model_match_rate']:.2%}")
        table.add_row("Anomaly match rate", f"{summary['anomaly_match_rate']:.2%}")
        table.add_row("Decision", summary["robustness_decision"])
        table.add_row("Robust gate", str(summary["robust"]))
        console.print(table)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sensitivity sweep with quality guardrails.")
    parser.add_argument(
        "--dataset-id",
        default=DEFAULT_DATASET_ID,
        help="Dataset ID to evaluate (default: voynich_real).",
    )
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DB_URL,
        help="SQLAlchemy URL for metadata database.",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Optional limit for executed scenarios (for constrained environments).",
    )
    parser.add_argument(
        "--mode",
        choices=["release", "smoke"],
        default=DEFAULT_SWEEP_MODE,
        help=(
            "Sweep mode: release requires full scenario execution; "
            "smoke defaults to one scenario unless --max-scenarios is provided."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(
        dataset_id=args.dataset_id,
        db_url=args.db_url,
        max_scenarios=args.max_scenarios,
        mode=args.mode,
    )
