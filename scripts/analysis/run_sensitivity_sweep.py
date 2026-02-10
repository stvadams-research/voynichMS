#!/usr/bin/env python3
"""
Sensitivity sweep runner for parameter robustness checks.

Outputs:
- status/audit/sensitivity_sweep.json (with provenance envelope)
- reports/audit/SENSITIVITY_RESULTS.md
- status/audit/sensitivity_quality_diagnostics.json
- status/audit/sensitivity_progress.json
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
from time import perf_counter
from typing import Any, Callable, Dict, List
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
DIAGNOSTICS_PATH = PROJECT_ROOT / "status/audit/sensitivity_quality_diagnostics.json"
PROGRESS_PATH = PROJECT_ROOT / "status/audit/sensitivity_progress.json"
POLICY_PATH = PROJECT_ROOT / "configs/audit/release_evidence_policy.json"
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
DEFAULT_DATASET_ID = "voynich_real"
ITERATIVE_DEFAULT_DATASET_ID = "voynich_synthetic_grammar"
DEFAULT_SWEEP_MODE = "release"
MIN_VALID_SCENARIO_RATE = 0.80
ITERATIVE_DEFAULT_MAX_SCENARIOS = 5
SENSITIVITY_SCHEMA_VERSION = "2026-02-10"
SENSITIVITY_GENERATED_BY = "scripts/analysis/run_sensitivity_sweep.py"
ITERATIVE_SCENARIO_IDS = {
    "baseline",
    "threshold_0.50",
    "threshold_0.70",
    "sensitivity_x1.20",
    "weights_focus_robustness",
}

DEFAULT_RELEASE_EVIDENCE_POLICY: Dict[str, Any] = {
    "policy_version": "2026-02-10",
    "dataset_policy": {
        "allowed_dataset_ids": ["voynich_real"],
        "min_pages": 200,
        "min_tokens": 200000,
    },
    "warning_policy": {
        "max_total_warning_count": 400,
        "max_warning_density_per_scenario": 20.0,
        "max_insufficient_data_scenarios": 0,
        "max_sparse_data_scenarios": 0,
        "max_nan_sanitized_scenarios": 0,
        "max_fallback_heavy_scenarios": 0,
        "fallback_heavy_threshold_per_scenario": 3,
        "max_fallback_warning_ratio_per_scenario": 0.25,
    },
}


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


def _load_release_evidence_policy() -> Dict[str, Any]:
    """Load release evidence policy with strict schema fallback defaults."""
    if not POLICY_PATH.exists():
        return copy.deepcopy(DEFAULT_RELEASE_EVIDENCE_POLICY)

    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    policy = copy.deepcopy(DEFAULT_RELEASE_EVIDENCE_POLICY)
    if isinstance(loaded.get("policy_version"), str):
        policy["policy_version"] = loaded["policy_version"]
    for section in ("dataset_policy", "warning_policy"):
        if isinstance(loaded.get(section), dict):
            policy[section].update(loaded[section])
    return policy


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _write_progress(payload: Dict[str, Any]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _summarize_warnings(messages: List[str]) -> Dict[str, Any]:
    insufficient_data = sum("Insufficient data for" in m for m in messages)
    sparse_data = sum("Sparse data for" in m for m in messages)
    nan_sanitized = sum("NaN degradation detected" in m for m in messages)
    fallback_estimate = sum("fallback estimated degradation" in m for m in messages)
    fallback_related = insufficient_data + sparse_data + nan_sanitized + fallback_estimate
    total = len(messages)
    return {
        "total_warnings": total,
        "insufficient_data_warnings": insufficient_data,
        "sparse_data_warnings": sparse_data,
        "nan_sanitized_warnings": nan_sanitized,
        "fallback_estimate_warnings": fallback_estimate,
        "fallback_related_warnings": fallback_related,
        "fallback_warning_ratio": (fallback_related / total) if total > 0 else 0.0,
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


def _evaluate_dataset_policy(
    dataset_profile: Dict[str, Any], dataset_policy: Dict[str, Any]
) -> Dict[str, Any]:
    allowed_dataset_ids = dataset_policy.get("allowed_dataset_ids", [])
    min_pages = int(dataset_policy.get("min_pages", 0))
    min_tokens = int(dataset_policy.get("min_tokens", 0))

    reasons: List[str] = []
    dataset_id = str(dataset_profile.get("dataset_id", ""))
    pages = int(dataset_profile.get("pages", 0))
    tokens = int(dataset_profile.get("tokens", 0))

    if allowed_dataset_ids and dataset_id not in allowed_dataset_ids:
        reasons.append(
            f"dataset_id={dataset_id!r} is not in allowed release datasets: {allowed_dataset_ids}"
        )
    if pages < min_pages:
        reasons.append(f"dataset_pages={pages} below minimum {min_pages}")
    if tokens < min_tokens:
        reasons.append(f"dataset_tokens={tokens} below minimum {min_tokens}")

    return {
        "dataset_policy_pass": len(reasons) == 0,
        "dataset_policy_reasons": reasons,
        "dataset_policy_constraints": {
            "allowed_dataset_ids": allowed_dataset_ids,
            "min_pages": min_pages,
            "min_tokens": min_tokens,
        },
    }


def _run_model_evaluation_scenario(
    db_url: str,
    dataset_id: str,
    model_params: Dict[str, Any],
    warning_policy: Dict[str, Any],
    scenario_id: str = "",
    progress_hook: Callable[[Dict[str, Any]], None] | None = None,
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

    label = scenario_id or "scenario"
    scenario_start = perf_counter()
    if progress_hook is not None:
        progress_hook(
            {
                "stage": "scenario_started",
                "scenario_id": label,
                "model_total": len(models),
            }
        )

    console.print(
        f"[cyan]{_utc_now_iso()}[/cyan] starting scenario `{label}` "
        f"on dataset `{dataset_id}` ({len(models)} models)"
    )

    with _scenario_model_params(model_params):
        with _capture_logger_warnings("analysis.models.perturbation") as warning_capture:
            engine = DisconfirmationEngine(store)
            for model_idx, model in enumerate(models, start=1):
                model_name = model.__class__.__name__
                model_start = perf_counter()
                if progress_hook is not None:
                    progress_hook(
                        {
                            "stage": "model_started",
                            "scenario_id": label,
                            "model_index": model_idx,
                            "model_total": len(models),
                            "model_name": model_name,
                        }
                    )
                console.print(
                    f"[dim]{_utc_now_iso()}[/dim] [{label}] "
                    f"model {model_idx}/{len(models)} `{model_name}`: prediction tests"
                )
                engine.run_prediction_tests(model, dataset_id)
                if progress_hook is not None:
                    progress_hook(
                        {
                            "stage": "prediction_tests_completed",
                            "scenario_id": label,
                            "model_index": model_idx,
                            "model_total": len(models),
                            "model_name": model_name,
                        }
                    )
                console.print(
                    f"[dim]{_utc_now_iso()}[/dim] [{label}] "
                    f"model {model_idx}/{len(models)} `{model_name}`: full battery"
                )
                engine.run_full_battery(model, dataset_id)
                model_elapsed = perf_counter() - model_start
                if progress_hook is not None:
                    progress_hook(
                        {
                            "stage": "model_completed",
                            "scenario_id": label,
                            "model_index": model_idx,
                            "model_total": len(models),
                            "model_name": model_name,
                            "model_elapsed_sec": round(model_elapsed, 3),
                        }
                    )
                console.print(
                    f"[green]{_utc_now_iso()}[/green] [{label}] "
                    f"model {model_idx}/{len(models)} `{model_name}` done "
                    f"({model_elapsed:.1f}s)"
                )

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
    if warning_summary["sparse_data_warnings"] > 0:
        quality_flags.append("sparse_data")
    if warning_summary["nan_sanitized_warnings"] > 0:
        quality_flags.append("nan_sanitized")

    fallback_heavy_threshold = int(
        warning_policy.get("fallback_heavy_threshold_per_scenario", 3)
    )
    if warning_summary["fallback_estimate_warnings"] >= fallback_heavy_threshold:
        quality_flags.append("fallback_heavy")

    fallback_ratio_limit = float(
        warning_policy.get("max_fallback_warning_ratio_per_scenario", 1.0)
    )
    if warning_summary["fallback_warning_ratio"] > fallback_ratio_limit:
        quality_flags.append("fallback_ratio_exceeded")

    max_warning_density_per_scenario = float(
        warning_policy.get("max_warning_density_per_scenario", float("inf"))
    )
    if warning_summary["total_warnings"] > max_warning_density_per_scenario:
        quality_flags.append("warning_density_exceeded")

    if metrics["surviving_models"] == 0:
        quality_flags.append("all_models_falsified")

    scenario_elapsed = perf_counter() - scenario_start
    if progress_hook is not None:
        progress_hook(
            {
                "stage": "scenario_completed",
                "scenario_id": label,
                "scenario_elapsed_sec": round(scenario_elapsed, 3),
            }
        )
    console.print(
        f"[bold green]{_utc_now_iso()}[/bold green] scenario `{label}` complete "
        f"({scenario_elapsed:.1f}s)"
    )

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


def _build_iterative_scenarios(
    all_scenarios: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    selected = [
        scenario for scenario in all_scenarios
        if scenario.get("id") in ITERATIVE_SCENARIO_IDS
    ]
    return selected if selected else all_scenarios[:]


def _decide_robustness(
    results: List[Dict[str, Any]],
    warning_policy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if warning_policy is None:
        warning_policy = copy.deepcopy(
            DEFAULT_RELEASE_EVIDENCE_POLICY["warning_policy"]
        )

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
            "sparse_data_scenarios": 0,
            "nan_sanitized_scenarios": 0,
            "fallback_heavy_scenarios": 0,
            "fallback_ratio_exceeded_scenarios": 0,
            "total_warning_count": 0,
            "warning_density_per_scenario": 0.0,
            "warning_policy_pass": False,
            "warning_policy_limits": warning_policy,
        }

    def _warning_count(row: Dict[str, Any], key: str) -> int:
        return int(row.get("warnings", {}).get(key, 0) or 0)

    valid = [r for r in results if r["valid"]]
    valid_rate = len(valid) / total
    all_models_falsified_everywhere = all(r["surviving_models"] == 0 for r in results)
    insufficient_data_scenarios = sum(
        1 for r in results if "insufficient_data" in r["quality_flags"]
    )
    sparse_data_scenarios = sum(
        1 for r in results if "sparse_data" in r["quality_flags"]
    )
    nan_sanitized_scenarios = sum(
        1 for r in results if "nan_sanitized" in r["quality_flags"]
    )
    fallback_heavy_scenarios = sum(
        1 for r in results if "fallback_heavy" in r["quality_flags"]
    )
    fallback_ratio_exceeded_scenarios = sum(
        1 for r in results if "fallback_ratio_exceeded" in r["quality_flags"]
    )
    total_warning_count = sum(_warning_count(r, "total_warnings") for r in results)
    warning_density_per_scenario = total_warning_count / total if total > 0 else 0.0

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
    if total_warning_count > 0 and not caveats:
        caveats.append(
            "Warnings were emitted across scenarios; treat robustness as qualified evidence."
        )

    max_total_warning_count = int(
        warning_policy.get("max_total_warning_count", 10**9)
    )
    max_warning_density_per_scenario = float(
        warning_policy.get("max_warning_density_per_scenario", float("inf"))
    )
    max_insufficient_data_scenarios = int(
        warning_policy.get("max_insufficient_data_scenarios", 10**9)
    )
    max_sparse_data_scenarios = int(
        warning_policy.get("max_sparse_data_scenarios", 10**9)
    )
    max_nan_sanitized_scenarios = int(
        warning_policy.get("max_nan_sanitized_scenarios", 10**9)
    )
    max_fallback_heavy_scenarios = int(
        warning_policy.get("max_fallback_heavy_scenarios", 10**9)
    )

    warning_policy_pass = True
    if total_warning_count > max_total_warning_count:
        warning_policy_pass = False
        caveats.append(
            f"Total warnings {total_warning_count} exceed policy max {max_total_warning_count}."
        )
    if warning_density_per_scenario > max_warning_density_per_scenario:
        warning_policy_pass = False
        caveats.append(
            "Warning density per scenario "
            f"{warning_density_per_scenario:.2f} exceeds policy max "
            f"{max_warning_density_per_scenario:.2f}."
        )
    if insufficient_data_scenarios > max_insufficient_data_scenarios:
        warning_policy_pass = False
        caveats.append(
            "Insufficient-data scenario count "
            f"{insufficient_data_scenarios} exceeds policy max "
            f"{max_insufficient_data_scenarios}."
        )
    if sparse_data_scenarios > max_sparse_data_scenarios:
        warning_policy_pass = False
        caveats.append(
            "Sparse-data scenario count "
            f"{sparse_data_scenarios} exceeds policy max "
            f"{max_sparse_data_scenarios}."
        )
    if nan_sanitized_scenarios > max_nan_sanitized_scenarios:
        warning_policy_pass = False
        caveats.append(
            "NaN-sanitized scenario count "
            f"{nan_sanitized_scenarios} exceeds policy max "
            f"{max_nan_sanitized_scenarios}."
        )
    if fallback_heavy_scenarios > max_fallback_heavy_scenarios:
        warning_policy_pass = False
        caveats.append(
            "Fallback-heavy scenario count "
            f"{fallback_heavy_scenarios} exceeds policy max "
            f"{max_fallback_heavy_scenarios}."
        )

    deduped_caveats: List[str] = []
    for caveat in caveats:
        if caveat not in deduped_caveats:
            deduped_caveats.append(caveat)

    robust = (
        not all_models_falsified_everywhere
        and valid_rate >= MIN_VALID_SCENARIO_RATE
        and top_model_match_rate >= 0.9
        and anomaly_match_rate >= 0.9
        and warning_policy_pass
    )

    if all_models_falsified_everywhere or not valid:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if robust else "FAIL"

    quality_gate_passed = (
        not all_models_falsified_everywhere
        and valid_rate >= MIN_VALID_SCENARIO_RATE
        and warning_policy_pass
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
        "sparse_data_scenarios": sparse_data_scenarios,
        "nan_sanitized_scenarios": nan_sanitized_scenarios,
        "fallback_heavy_scenarios": fallback_heavy_scenarios,
        "fallback_ratio_exceeded_scenarios": fallback_ratio_exceeded_scenarios,
        "total_warning_count": total_warning_count,
        "warning_density_per_scenario": warning_density_per_scenario,
        "warning_policy_pass": warning_policy_pass,
        "warning_policy_limits": warning_policy,
        "robust": robust,
        "robustness_decision": decision,
        "caveats": deduped_caveats,
    }


def _collect_release_readiness_failures(
    summary: Dict[str, Any],
    *,
    mode: str,
    max_scenarios: int | None,
    scenario_count_expected: int,
    scenario_count_executed: int,
) -> List[str]:
    failures: List[str] = []
    if mode != "release":
        failures.append("execution_mode_not_release")
    if max_scenarios is not None:
        failures.append("max_scenarios_override_present")
    if scenario_count_executed != scenario_count_expected:
        failures.append("incomplete_scenario_execution")
    if bool(summary.get("quality_gate_passed")) is not True:
        failures.append("quality_gate_failed")
    if bool(summary.get("robustness_conclusive")) is not True:
        failures.append("robustness_not_conclusive")
    if bool(summary.get("dataset_policy_pass")) is not True:
        failures.append("dataset_policy_failed")
    if bool(summary.get("warning_policy_pass")) is not True:
        failures.append("warning_policy_failed")
    return failures


def _is_release_evidence_ready(
    summary: Dict[str, Any],
    *,
    mode: str,
    max_scenarios: int | None,
    scenario_count_expected: int,
    scenario_count_executed: int,
) -> bool:
    return len(
        _collect_release_readiness_failures(
            summary,
            mode=mode,
            max_scenarios=max_scenarios,
            scenario_count_expected=scenario_count_expected,
            scenario_count_executed=scenario_count_executed,
        )
    ) == 0


def _write_markdown_report(
    summary: Dict[str, Any],
    dataset_profile: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Sensitivity Results\n\n")
        f.write(f"- Sweep date: {summary['date']}\n")
        f.write(f"- Schema version: `{summary.get('schema_version')}`\n")
        f.write(f"- Policy version: `{summary.get('policy_version')}`\n")
        f.write(f"- Generated by: `{summary.get('generated_by')}`\n")
        f.write(f"- Dataset: `{dataset_profile['dataset_id']}`\n")
        f.write(f"- Dataset pages: `{dataset_profile['pages']}`\n")
        f.write(f"- Dataset tokens: `{dataset_profile['tokens']}`\n")
        f.write(f"- Dataset policy pass: `{summary.get('dataset_policy_pass')}`\n")
        if summary.get("dataset_policy_reasons"):
            for reason in summary["dataset_policy_reasons"]:
                f.write(f"- Dataset policy note: {reason}\n")
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
        if summary.get("release_readiness_failures"):
            f.write(
                "- Release readiness failures: "
                f"`{', '.join(summary['release_readiness_failures'])}`\n"
            )
        else:
            f.write("- Release readiness failures: `none`\n")
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
        f.write(f"- Warning policy pass: `{summary.get('warning_policy_pass')}`\n")
        f.write(
            "- Quality gate passed "
            "(valid-scenario-rate threshold + non-collapse + warning policy): "
            f"`{summary['quality_gate_passed']}`\n"
        )
        f.write(f"- Robustness gate passed (>90% both + quality gates): `{summary['robust']}`\n\n")

        f.write("## Data Quality Caveats\n\n")
        f.write(f"- Total warnings observed: `{summary['total_warning_count']}`\n")
        f.write(
            f"- Warning density per scenario: `{summary.get('warning_density_per_scenario', 0.0):.2f}`\n"
        )
        f.write(
            f"- Scenarios with insufficient-data warnings: "
            f"`{summary['insufficient_data_scenarios']}/{summary['total_scenarios']}`\n"
        )
        f.write(
            f"- Scenarios with sparse-data warnings: "
            f"`{summary.get('sparse_data_scenarios', 0)}/{summary['total_scenarios']}`\n"
        )
        f.write(
            f"- Scenarios with NaN-sanitized warnings: "
            f"`{summary.get('nan_sanitized_scenarios', 0)}/{summary['total_scenarios']}`\n"
        )
        f.write(
            f"- Fallback-heavy scenarios: "
            f"`{summary.get('fallback_heavy_scenarios', 0)}/{summary['total_scenarios']}`\n"
        )
        f.write(
            "- All scenarios zero-survivor: "
            f"`{summary['all_models_falsified_everywhere']}`\n"
        )
        if summary["caveats"]:
            for caveat in summary["caveats"]:
                f.write(f"- Caveat: {caveat}\n")
        else:
            f.write("- Caveat: none (no warnings observed)\n")

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


def _write_quality_diagnostics(
    summary: Dict[str, Any],
    dataset_profile: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> None:
    DIAGNOSTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": summary.get("date"),
        "dataset_profile": dataset_profile,
        "summary": {
            "schema_version": summary.get("schema_version"),
            "policy_version": summary.get("policy_version"),
            "generated_utc": summary.get("generated_utc"),
            "generated_by": summary.get("generated_by"),
            "release_readiness_failures": summary.get("release_readiness_failures", []),
            "release_evidence_ready": summary.get("release_evidence_ready"),
            "warning_policy_pass": summary.get("warning_policy_pass"),
            "warning_density_per_scenario": summary.get("warning_density_per_scenario"),
            "total_warning_count": summary.get("total_warning_count"),
            "insufficient_data_scenarios": summary.get("insufficient_data_scenarios"),
            "sparse_data_scenarios": summary.get("sparse_data_scenarios"),
            "nan_sanitized_scenarios": summary.get("nan_sanitized_scenarios"),
            "fallback_heavy_scenarios": summary.get("fallback_heavy_scenarios"),
            "fallback_ratio_exceeded_scenarios": summary.get(
                "fallback_ratio_exceeded_scenarios"
            ),
            "caveats": summary.get("caveats", []),
        },
        "scenarios": [
            {
                "id": row.get("id"),
                "family": row.get("family"),
                "valid": row.get("valid"),
                "quality_flags": row.get("quality_flags", []),
                "warnings": row.get("warnings", {}),
            }
            for row in results
        ],
    }
    with open(DIAGNOSTICS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def main(
    dataset_id: str = DEFAULT_DATASET_ID,
    db_url: str = DEFAULT_DB_URL,
    max_scenarios: int | None = None,
    mode: str = DEFAULT_SWEEP_MODE,
    quick: bool = False,
) -> None:
    if mode not in {"release", "smoke", "iterative"}:
        raise ValueError(f"Unsupported sensitivity sweep mode: {mode}")

    if quick:
        if mode == "release":
            raise ValueError("Quick mode cannot be combined with release mode.")
        mode = "iterative"
        if dataset_id == DEFAULT_DATASET_ID:
            dataset_id = ITERATIVE_DEFAULT_DATASET_ID
        if max_scenarios is None:
            max_scenarios = ITERATIVE_DEFAULT_MAX_SCENARIOS

    if mode == "iterative" and dataset_id == DEFAULT_DATASET_ID:
        dataset_id = ITERATIVE_DEFAULT_DATASET_ID
    if mode == "iterative" and max_scenarios is None:
        max_scenarios = ITERATIVE_DEFAULT_MAX_SCENARIOS

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
            "quick": quick,
        }
    ) as run:
        with open(MODEL_PARAMS_PATH, "r", encoding="utf-8") as f:
            base_cfg = json.load(f)
        release_policy = _load_release_evidence_policy()
        dataset_policy = release_policy.get("dataset_policy", {})
        warning_policy = release_policy.get("warning_policy", {})

        store = MetadataStore(db_url)
        dataset_profile = _load_dataset_profile(store, dataset_id)
        dataset_policy_eval = _evaluate_dataset_policy(dataset_profile, dataset_policy)
        all_scenarios = _build_scenarios(base_cfg)
        if mode == "iterative":
            all_scenarios = _build_iterative_scenarios(all_scenarios)
        scenario_count_expected = len(all_scenarios)

        if mode == "smoke" and max_scenarios is None:
            max_scenarios = 1

        scenarios = all_scenarios
        if max_scenarios is not None:
            scenarios = all_scenarios[:max_scenarios]
        results: List[Dict[str, Any]] = []
        _write_progress(
            {
                "timestamp": _utc_now_iso(),
                "stage": "run_started",
                "dataset_id": dataset_id,
                "mode": mode,
                "scenario_total": len(scenarios),
                "max_scenarios": max_scenarios,
                "quick": quick,
            }
        )

        for scenario_idx, scenario in enumerate(scenarios, start=1):
            _write_progress(
                {
                    "timestamp": _utc_now_iso(),
                    "stage": "scenario_dispatch",
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "scenario_id": scenario["id"],
                    "scenario_index": scenario_idx,
                    "scenario_total": len(scenarios),
                }
            )

            def _scenario_progress(event: Dict[str, Any]) -> None:
                payload = {
                    "timestamp": _utc_now_iso(),
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "scenario_id": scenario["id"],
                    "scenario_index": scenario_idx,
                    "scenario_total": len(scenarios),
                }
                payload.update(event)
                _write_progress(payload)

            scenario_wall_start = perf_counter()
            console.print(
                f"[bold cyan]{_utc_now_iso()}[/bold cyan] "
                f"scenario {scenario_idx}/{len(scenarios)} `{scenario['id']}` started"
            )
            scenario_result = _run_model_evaluation_scenario(
                db_url,
                dataset_id,
                scenario["config"],
                warning_policy,
                scenario_id=scenario["id"],
                progress_hook=_scenario_progress,
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
            scenario_wall_elapsed = perf_counter() - scenario_wall_start
            console.print(
                f"[green]{_utc_now_iso()}[/green] scenario {scenario_idx}/{len(scenarios)} "
                f"`{row['id']}` done -> {row['top_model']} "
                f"(surviving={row['surviving_models']}, warnings={row['warnings']['total_warnings']}, "
                f"elapsed={scenario_wall_elapsed:.1f}s)"
            )

        summary = _decide_robustness(results, warning_policy)
        generated_utc = _utc_now_iso()
        summary["date"] = generated_utc
        summary["generated_utc"] = generated_utc
        summary["generated_by"] = SENSITIVITY_GENERATED_BY
        summary["schema_version"] = SENSITIVITY_SCHEMA_VERSION
        summary["policy_version"] = release_policy.get("policy_version", "unknown")
        summary["dataset_id"] = dataset_id
        summary["dataset_pages"] = dataset_profile["pages"]
        summary["dataset_tokens"] = dataset_profile["tokens"]
        summary["dataset_policy_pass"] = dataset_policy_eval["dataset_policy_pass"]
        summary["dataset_policy_reasons"] = dataset_policy_eval["dataset_policy_reasons"]
        summary["dataset_policy_constraints"] = dataset_policy_eval[
            "dataset_policy_constraints"
        ]
        summary["execution_mode"] = mode
        summary["scenario_count_expected"] = scenario_count_expected
        summary["scenario_count_executed"] = len(scenarios)
        summary["release_readiness_failures"] = _collect_release_readiness_failures(
            summary,
            mode=mode,
            max_scenarios=max_scenarios,
            scenario_count_expected=scenario_count_expected,
            scenario_count_executed=len(scenarios),
        )
        summary["release_evidence_ready"] = len(summary["release_readiness_failures"]) == 0

        status_payload = {
            "summary": summary,
            "dataset_profile": dataset_profile,
            "results": results,
        }
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(status_payload, STATUS_PATH)
        _write_markdown_report(summary, dataset_profile, results)
        _write_quality_diagnostics(summary, dataset_profile, results)
        _write_progress(
            {
                "timestamp": _utc_now_iso(),
                "stage": "run_completed",
                "dataset_id": dataset_id,
                "mode": mode,
                "scenario_total": len(scenarios),
                "summary": {
                    "release_evidence_ready": summary.get("release_evidence_ready"),
                    "robustness_decision": summary.get("robustness_decision"),
                    "quality_gate_passed": summary.get("quality_gate_passed"),
                    "dataset_policy_pass": summary.get("dataset_policy_pass"),
                    "warning_policy_pass": summary.get("warning_policy_pass"),
                },
            }
        )
        store.save_run(run)

        table = Table(title="Sensitivity Sweep Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Dataset", dataset_id)
        table.add_row("Mode", mode)
        table.add_row("Dataset policy pass", str(summary["dataset_policy_pass"]))
        table.add_row("Warning policy pass", str(summary["warning_policy_pass"]))
        table.add_row(
            "Scenario execution",
            f"{summary['scenario_count_executed']}/{summary['scenario_count_expected']}",
        )
        table.add_row("Release evidence ready", str(summary["release_evidence_ready"]))
        table.add_row("Total scenarios", str(summary["total_scenarios"]))
        table.add_row("Valid scenarios", f"{summary['valid_scenarios']} ({summary['valid_scenario_rate']:.2%})")
        table.add_row("Top-model match rate", f"{summary['top_model_match_rate']:.2%}")
        table.add_row("Anomaly match rate", f"{summary['anomaly_match_rate']:.2%}")
        table.add_row("Warning density/scenario", f"{summary['warning_density_per_scenario']:.2f}")
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
        choices=["release", "smoke", "iterative"],
        default=DEFAULT_SWEEP_MODE,
        help=(
            "Sweep mode: release requires full scenario execution; "
            "smoke defaults to one scenario unless --max-scenarios is provided; "
            "iterative uses a reduced scenario profile for faster local runs."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Convenience shortcut for iterative local runs. "
            "Forces iterative mode, defaults dataset to "
            f"`{ITERATIVE_DEFAULT_DATASET_ID}`, and limits scenarios."
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
        quick=args.quick,
    )
