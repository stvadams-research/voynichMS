#!/usr/bin/env python3
"""
Sensitivity sweep runner for parameter robustness checks.

Outputs:
- core_status/core_audit/sensitivity_sweep.json (latest local/iterative snapshot)
- core_status/core_audit/sensitivity_sweep_release.json (release-candidate snapshot)
- reports/core_audit/SENSITIVITY_RESULTS.md (latest local/iterative report)
- reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md (release-candidate report)
- core_status/core_audit/sensitivity_quality_diagnostics.json
- core_status/core_audit/sensitivity_quality_diagnostics_release.json
- core_status/core_audit/sensitivity_progress.json
- core_status/core_audit/sensitivity_release_preflight.json
- core_status/core_audit/sensitivity_checkpoint.json
- core_status/core_audit/sensitivity_release_run_status.json
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
import tempfile
import threading
from collections.abc import Callable
from contextlib import ExitStack, contextmanager
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from unittest.mock import patch

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.config import DEFAULT_SEED  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    DatasetRecord,
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase2_analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer  # noqa: E402
from phase2_analysis.models.constructed_system import (  # noqa: E402
    GlossalialSystemModel,
    MeaningfulConstructModel,
    ProceduralGenerationModel,
)
from phase2_analysis.models.disconfirmation import DisconfirmationEngine  # noqa: E402
from phase2_analysis.models.evaluation import CrossModelEvaluator  # noqa: E402
from phase2_analysis.models.visual_grammar import (  # noqa: E402
    AdjacencyGrammarModel,
    ContainmentGrammarModel,
    DiagramAnnotationModel,
)

console = Console()
MODEL_PARAMS_PATH = PROJECT_ROOT / "configs/phase6_functional/model_params.json"
STATUS_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_sweep.json"
RELEASE_STATUS_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_sweep_release.json"
REPORT_PATH = PROJECT_ROOT / "results/reports/core_audit/SENSITIVITY_RESULTS.md"
RELEASE_REPORT_PATH = PROJECT_ROOT / "results/reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md"
DIAGNOSTICS_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_quality_diagnostics.json"
RELEASE_DIAGNOSTICS_PATH = (
    PROJECT_ROOT / "core_status/core_audit/sensitivity_quality_diagnostics_release.json"
)
PROGRESS_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_progress.json"
RELEASE_PREFLIGHT_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_release_preflight.json"
CHECKPOINT_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_checkpoint.json"
RELEASE_RUN_STATUS_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_release_run_status.json"
POLICY_PATH = PROJECT_ROOT / "configs/core_audit/release_evidence_policy.json"
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
DEFAULT_DATASET_ID = "voynich_real"
ITERATIVE_DEFAULT_DATASET_ID = "voynich_synthetic_grammar"
DEFAULT_SWEEP_MODE = "release"
MIN_VALID_SCENARIO_RATE = 0.80
ITERATIVE_DEFAULT_MAX_SCENARIOS = 5
SENSITIVITY_SCHEMA_VERSION = "2026-02-10"
SENSITIVITY_GENERATED_BY = "scripts/phase2_analysis/run_sensitivity_sweep.py"
SENSITIVITY_PROGRESS_SCHEMA_VERSION = "2026-02-10"
SENSITIVITY_PREFLIGHT_SCHEMA_VERSION = "2026-02-10"
SENSITIVITY_CHECKPOINT_SCHEMA_VERSION = "2026-02-10"
SENSITIVITY_RELEASE_RUN_STATUS_SCHEMA_VERSION = "2026-02-10"
FULL_BATTERY_HEARTBEAT_SECONDS = 30
ITERATIVE_SCENARIO_IDS = {
    "baseline",
    "threshold_0.50",
    "threshold_0.70",
    "sensitivity_x1.20",
    "weights_focus_robustness",
}

DEFAULT_RELEASE_EVIDENCE_POLICY: dict[str, Any] = {
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
        self.messages: list[str] = []

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
def _scenario_model_params(model_params: dict[str, Any]):
    """Patch model-parameter lookups so scenario config is fully in-memory."""
    with ExitStack() as stack:
        stack.enter_context(
            patch("phase1_foundation.config.get_model_params", return_value=model_params)
        )
        stack.enter_context(
            patch("phase2_analysis.models.disconfirmation.get_model_params", return_value=model_params)
        )
        stack.enter_context(
            patch("phase2_analysis.models.evaluation.get_model_params", return_value=model_params)
        )
        yield


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return weights
    return {k: float(v) / total for k, v in weights.items()}


def _load_release_evidence_policy() -> dict[str, Any]:
    """Load release evidence policy with strict schema fallback defaults."""
    if not POLICY_PATH.exists():
        return copy.deepcopy(DEFAULT_RELEASE_EVIDENCE_POLICY)

    with open(POLICY_PATH, encoding="utf-8") as f:
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


def _render_path_for_summary(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
        prefix=f".{path.name}.tmp.",
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _atomic_write_json(path: Path, payload: Any, *, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=sort_keys) + "\n"
    _atomic_write_text(path, encoded)


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_results_atomic(results: Any, output_path: Path) -> dict[str, str]:
    try:
        json.dumps(results)
    except TypeError as exc:
        raise ValueError(f"Results must be JSON-serializable: {exc}") from exc

    provenance = ProvenanceWriter._get_provenance()
    data = {"provenance": provenance, "results": results}

    snapshot_id = str(provenance.get("run_id", "none"))
    if snapshot_id == "none":
        snapshot_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path = ProvenanceWriter._build_snapshot_path(output_path, snapshot_id)
    _atomic_write_json(snapshot_path, data)
    _atomic_write_json(output_path, data)
    return {
        "snapshot_path": str(snapshot_path),
        "latest_path": str(output_path),
    }


def _build_progress_timing(
    *, run_start: float, completed_scenarios: int, scenario_total: int
) -> dict[str, Any]:
    elapsed = perf_counter() - run_start
    eta: float | None = None
    remaining = max(scenario_total - completed_scenarios, 0)
    if completed_scenarios > 0 and scenario_total >= completed_scenarios:
        eta = (elapsed / completed_scenarios) * remaining
    return {
        "elapsed_sec": round(elapsed, 3),
        "completed_scenarios": int(completed_scenarios),
        "remaining_scenarios": int(remaining),
        "eta_sec": round(eta, 3) if eta is not None else None,
    }


def _build_release_preflight_payload(
    *,
    mode: str,
    dataset_profile: dict[str, Any],
    dataset_policy_eval: dict[str, Any],
    policy_version: str,
    max_scenarios: int | None,
    scenario_count_expected: int,
) -> dict[str, Any]:
    reason_codes: list[str] = []
    if mode != "release":
        reason_codes.append("MODE_NOT_RELEASE")
    if max_scenarios is not None:
        reason_codes.append("MAX_SCENARIOS_OVERRIDE_PRESENT")
    if dataset_policy_eval.get("dataset_policy_pass") is not True:
        reason_codes.append("DATASET_POLICY_FAILED")

    status = "PREFLIGHT_OK" if not reason_codes else "BLOCKED"
    return {
        "schema_version": SENSITIVITY_PREFLIGHT_SCHEMA_VERSION,
        "generated_utc": _utc_now_iso(),
        "generated_by": SENSITIVITY_GENERATED_BY,
        "status": status,
        "reason_codes": reason_codes,
        "mode": mode,
        "dataset_id": dataset_profile.get("dataset_id"),
        "dataset_profile": dataset_profile,
        "dataset_policy_pass": dataset_policy_eval.get("dataset_policy_pass"),
        "dataset_policy_reasons": dataset_policy_eval.get("dataset_policy_reasons", []),
        "dataset_policy_constraints": dataset_policy_eval.get(
            "dataset_policy_constraints", {}
        ),
        "policy_version": policy_version,
        "scenario_count_expected": scenario_count_expected,
        "max_scenarios": max_scenarios,
        "artifact_targets": {
            "release_status_path": _render_path_for_summary(RELEASE_STATUS_PATH),
            "release_report_path": _render_path_for_summary(RELEASE_REPORT_PATH),
        },
        "next_step_command": (
            "python3 scripts/phase2_analysis/run_sensitivity_sweep.py "
            "--mode release --dataset-id voynich_real"
        ),
    }


def _build_release_preflight_dataset_error_payload(
    *,
    mode: str,
    dataset_id: str,
    error_message: str,
    policy_version: str,
    max_scenarios: int | None,
) -> dict[str, Any]:
    return {
        "schema_version": SENSITIVITY_PREFLIGHT_SCHEMA_VERSION,
        "generated_utc": _utc_now_iso(),
        "generated_by": SENSITIVITY_GENERATED_BY,
        "status": "BLOCKED",
        "reason_codes": ["DATASET_PROFILE_UNAVAILABLE"],
        "mode": mode,
        "dataset_id": dataset_id,
        "dataset_profile": {"dataset_id": dataset_id},
        "dataset_policy_pass": False,
        "dataset_policy_reasons": [error_message],
        "dataset_policy_constraints": {},
        "policy_version": policy_version,
        "scenario_count_expected": 0,
        "max_scenarios": max_scenarios,
        "artifact_targets": {
            "release_status_path": _render_path_for_summary(RELEASE_STATUS_PATH),
            "release_report_path": _render_path_for_summary(RELEASE_REPORT_PATH),
        },
        "next_step_command": (
            "python3 scripts/phase2_analysis/run_sensitivity_sweep.py "
            "--mode release --dataset-id voynich_real"
        ),
    }


def _build_checkpoint_signature(
    *,
    dataset_id: str,
    mode: str,
    scenario_ids: list[str],
    policy_version: str,
) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "mode": mode,
        "scenario_ids": scenario_ids,
        "policy_version": policy_version,
    }


def _new_checkpoint_state(
    *, signature: dict[str, Any], scenario_total: int
) -> dict[str, Any]:
    return {
        "schema_version": SENSITIVITY_CHECKPOINT_SCHEMA_VERSION,
        "generated_utc": _utc_now_iso(),
        "generated_by": SENSITIVITY_GENERATED_BY,
        "status": "IN_PROGRESS",
        "signature": signature,
        "scenario_total": scenario_total,
        "completed_count": 0,
        "completed_scenario_ids": [],
        "completed_scenarios": [],
    }


def _checkpoint_rows_by_id(
    checkpoint_state: dict[str, Any], *, allowed_scenario_ids: list[str]
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    allowed = set(allowed_scenario_ids)
    for entry in checkpoint_state.get("completed_scenarios", []):
        if not isinstance(entry, dict):
            continue
        scenario_id = entry.get("id")
        result = entry.get("result")
        if (
            isinstance(scenario_id, str)
            and scenario_id in allowed
            and isinstance(result, dict)
        ):
            rows[scenario_id] = result
    return rows


def _write_checkpoint_state(checkpoint_state: dict[str, Any]) -> None:
    checkpoint_state["generated_utc"] = _utc_now_iso()
    _atomic_write_json(CHECKPOINT_PATH, checkpoint_state, sort_keys=True)


def _record_checkpoint_result(
    checkpoint_state: dict[str, Any],
    *,
    scenario_id: str,
    scenario_index: int,
    result_row: dict[str, Any],
) -> None:
    completed = checkpoint_state.setdefault("completed_scenarios", [])
    replaced = False
    for entry in completed:
        if entry.get("id") == scenario_id:
            entry.update(
                {
                    "id": scenario_id,
                    "scenario_index": scenario_index,
                    "result": result_row,
                }
            )
            replaced = True
            break
    if not replaced:
        completed.append(
            {
                "id": scenario_id,
                "scenario_index": scenario_index,
                "result": result_row,
            }
        )

    completed_ids = [
        entry.get("id")
        for entry in completed
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    checkpoint_state["completed_scenario_ids"] = completed_ids
    checkpoint_state["completed_count"] = len(completed_ids)
    checkpoint_state["last_completed_index"] = scenario_index


def _write_progress(payload: dict[str, Any]) -> None:
    envelope = {
        "schema_version": SENSITIVITY_PROGRESS_SCHEMA_VERSION,
        **payload,
    }
    _atomic_write_json(PROGRESS_PATH, envelope, sort_keys=True)


def _write_release_run_status(
    *,
    mode: str,
    run_id: str,
    run_started_utc: str,
    dataset_id: str,
    status: str,
    reason_codes: list[str],
    stage: str,
    max_scenarios: int | None,
    scenario_total: int | None,
    completed_scenarios: int | None,
    scenario_id: str | None = None,
    preflight_status: str | None = None,
    elapsed_sec: float | None = None,
    eta_sec: float | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    if mode != "release":
        return

    heartbeat_utc = _utc_now_iso()
    payload: dict[str, Any] = {
        "schema_version": SENSITIVITY_RELEASE_RUN_STATUS_SCHEMA_VERSION,
        "generated_utc": heartbeat_utc,
        "generated_by": SENSITIVITY_GENERATED_BY,
        "run_id": run_id,
        "run_started_utc": run_started_utc,
        "status": status,
        "reason_codes": sorted(set(reason_codes)),
        "mode": mode,
        "dataset_id": dataset_id,
        "stage": stage,
        "max_scenarios": max_scenarios,
        "scenario_total": scenario_total,
        "completed_scenarios": completed_scenarios,
        "last_scenario_id": scenario_id,
        "preflight_status": preflight_status,
        "elapsed_sec": elapsed_sec,
        "eta_sec": eta_sec,
        "artifact_targets": {
            "release_status_path": _render_path_for_summary(RELEASE_STATUS_PATH),
            "release_report_path": _render_path_for_summary(RELEASE_REPORT_PATH),
        },
        "runtime_paths": {
            "progress_path": _render_path_for_summary(PROGRESS_PATH),
            "checkpoint_path": _render_path_for_summary(CHECKPOINT_PATH),
        },
    }
    if details:
        payload["details"] = details
    _atomic_write_json(RELEASE_RUN_STATUS_PATH, payload, sort_keys=True)


def _summarize_warnings(messages: list[str]) -> dict[str, Any]:
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


def _load_dataset_profile(store: MetadataStore, dataset_id: str) -> dict[str, Any]:
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
            "Run corpus build scripts before sensitivity phase2_analysis."
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
    dataset_profile: dict[str, Any], dataset_policy: dict[str, Any]
) -> dict[str, Any]:
    allowed_dataset_ids = dataset_policy.get("allowed_dataset_ids", [])
    min_pages = int(dataset_policy.get("min_pages", 0))
    min_tokens = int(dataset_policy.get("min_tokens", 0))

    reasons: list[str] = []
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
    model_params: dict[str, Any],
    warning_policy: dict[str, Any],
    scenario_id: str = "",
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
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
        with _capture_logger_warnings("phase2_analysis.models.perturbation") as warning_capture:
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
                heartbeat_stop = threading.Event()

                def _emit_full_battery_heartbeat() -> None:
                    heartbeat_index = 0
                    while not heartbeat_stop.wait(FULL_BATTERY_HEARTBEAT_SECONDS):
                        heartbeat_index += 1
                        if progress_hook is not None:
                            progress_hook(
                                {
                                    "stage": "full_battery_heartbeat",
                                    "scenario_id": label,
                                    "model_index": model_idx,
                                    "model_total": len(models),
                                    "model_name": model_name,
                                    "heartbeat_index": heartbeat_index,
                                    "heartbeat_period_sec": FULL_BATTERY_HEARTBEAT_SECONDS,
                                }
                            )

                heartbeat_thread = threading.Thread(
                    target=_emit_full_battery_heartbeat,
                    daemon=True,
                )
                heartbeat_thread.start()
                try:
                    engine.run_full_battery(model, dataset_id)
                finally:
                    heartbeat_stop.set()
                    heartbeat_thread.join(timeout=0.5)
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

    quality_flags: list[str] = []
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


def _apply_threshold(cfg: dict[str, Any], threshold: float) -> dict[str, Any]:
    out = copy.deepcopy(cfg)
    battery = out.get("disconfirmation", {}).get("perturbation_battery", [])
    for item in battery:
        item["failure_threshold"] = float(threshold)
    return out


def _apply_sensitivity_scale(cfg: dict[str, Any], factor: float) -> dict[str, Any]:
    out = copy.deepcopy(cfg)
    models = out.get("models", {})
    for model_data in models.values():
        sensitivities = model_data.get("sensitivities", {})
        for key, value in sensitivities.items():
            sensitivities[key] = round(float(value) * factor, 6)
    return out


def _apply_weight_variant(cfg: dict[str, Any], focus_dimension: str, factor: float) -> dict[str, Any]:
    out = copy.deepcopy(cfg)
    weights = out.get("evaluation", {}).get("dimension_weights", {})
    adjusted = {}
    for dim, value in weights.items():
        base = float(value)
        adjusted[dim] = base * factor if dim == focus_dimension else base
    out["evaluation"]["dimension_weights"] = _normalize_weights(adjusted)
    return out


def _build_scenarios(base_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = [
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
    all_scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = [
        scenario for scenario in all_scenarios
        if scenario.get("id") in ITERATIVE_SCENARIO_IDS
    ]
    return selected if selected else all_scenarios[:]


def _decide_robustness(
    results: list[dict[str, Any]],
    warning_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
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

    def _warning_count(row: dict[str, Any], key: str) -> int:
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

    caveats: list[str] = []
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

    deduped_caveats: list[str] = []
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
    summary: dict[str, Any],
    *,
    mode: str,
    max_scenarios: int | None,
    scenario_count_expected: int,
    scenario_count_executed: int,
) -> list[str]:
    failures: list[str] = []
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
    summary: dict[str, Any],
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
    summary: dict[str, Any],
    dataset_profile: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    report_path: Path,
) -> None:
    lines: list[str] = []
    lines.append("# Sensitivity Results")
    lines.append("")
    lines.append(f"- Sweep date: {summary['date']}")
    lines.append(f"- Schema version: `{summary.get('schema_version')}`")
    lines.append(f"- Policy version: `{summary.get('policy_version')}`")
    lines.append(f"- Generated by: `{summary.get('generated_by')}`")
    lines.append(f"- Dataset: `{dataset_profile['dataset_id']}`")
    lines.append(f"- Dataset pages: `{dataset_profile['pages']}`")
    lines.append(f"- Dataset tokens: `{dataset_profile['tokens']}`")
    lines.append(f"- Dataset policy pass: `{summary.get('dataset_policy_pass')}`")
    if summary.get("dataset_policy_reasons"):
        for reason in summary["dataset_policy_reasons"]:
            lines.append(f"- Dataset policy note: {reason}")
    lines.append(f"- Execution mode: `{summary['execution_mode']}`")
    lines.append(
        f"- Scenario execution: `{summary['scenario_count_executed']}/{summary['scenario_count_expected']}`"
    )
    lines.append(
        "- Release evidence ready "
        "(full sweep + conclusive robustness + quality gate): "
        f"`{summary['release_evidence_ready']}`"
    )
    if summary.get("release_readiness_failures"):
        lines.append(
            "- Release readiness failures: "
            f"`{', '.join(summary['release_readiness_failures'])}`"
        )
    else:
        lines.append("- Release readiness failures: `none`")
    lines.append(f"- Total scenarios: {summary['total_scenarios']}")
    lines.append(
        f"- Valid scenarios: {summary['valid_scenarios']} ({summary['valid_scenario_rate']:.2%})"
    )
    lines.append(f"- Baseline top model: `{summary['baseline_top_model']}`")
    lines.append(
        f"- Baseline anomaly confirmed: `{summary['baseline_anomaly_confirmed']}`"
    )
    lines.append(
        f"- Top-model stability rate (valid scenarios): `{summary['top_model_match_rate']:.2%}`"
    )
    lines.append(
        f"- Anomaly-status stability rate (valid scenarios): `{summary['anomaly_match_rate']:.2%}`"
    )
    lines.append(f"- Robustness decision: `{summary['robustness_decision']}`")
    lines.append(
        "- Robustness conclusive "
        "(`PASS`/`FAIL`, excludes `INCONCLUSIVE`): "
        f"`{summary['robustness_conclusive']}`"
    )
    lines.append(f"- Warning policy pass: `{summary.get('warning_policy_pass')}`")
    lines.append(
        "- Quality gate passed "
        "(valid-scenario-rate threshold + non-collapse + warning policy): "
        f"`{summary['quality_gate_passed']}`"
    )
    lines.append(f"- Robustness gate passed (>90% both + quality gates): `{summary['robust']}`")
    lines.append("")
    lines.append("## Data Quality Caveats")
    lines.append("")
    lines.append(f"- Total warnings observed: `{summary['total_warning_count']}`")
    lines.append(
        f"- Warning density per scenario: `{summary.get('warning_density_per_scenario', 0.0):.2f}`"
    )
    lines.append(
        "- Scenarios with insufficient-data warnings: "
        f"`{summary['insufficient_data_scenarios']}/{summary['total_scenarios']}`"
    )
    lines.append(
        "- Scenarios with sparse-data warnings: "
        f"`{summary.get('sparse_data_scenarios', 0)}/{summary['total_scenarios']}`"
    )
    lines.append(
        "- Scenarios with NaN-sanitized warnings: "
        f"`{summary.get('nan_sanitized_scenarios', 0)}/{summary['total_scenarios']}`"
    )
    lines.append(
        "- Fallback-heavy scenarios: "
        f"`{summary.get('fallback_heavy_scenarios', 0)}/{summary['total_scenarios']}`"
    )
    lines.append(
        "- All scenarios zero-survivor: "
        f"`{summary['all_models_falsified_everywhere']}`"
    )
    if summary["caveats"]:
        for caveat in summary["caveats"]:
            lines.append(f"- Caveat: {caveat}")
    else:
        lines.append("- Caveat: none (no warnings observed)")

    lines.append("")
    lines.append("## Scenario Results")
    lines.append("")
    lines.append(
        "| Scenario | Family | Top Model | Top Score | Surviving | Falsified | Warnings | Quality Flags | Valid |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|")
    for row in results:
        flags = ", ".join(row["quality_flags"]) if row["quality_flags"] else "-"
        lines.append(
            f"| `{row['id']}` | {row['family']} | `{row['top_model']}` | "
            f"{row['top_score']:.3f} | {row['surviving_models']} | {row['falsified_models']} | "
            f"{row['warnings']['total_warnings']} | {flags} | {row['valid']} |"
        )

    _atomic_write_text(report_path, "\n".join(lines) + "\n")


def _write_quality_diagnostics(
    summary: dict[str, Any],
    dataset_profile: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    diagnostics_path: Path,
) -> None:
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
    _atomic_write_json(diagnostics_path, payload, sort_keys=True)


def main(
    dataset_id: str = DEFAULT_DATASET_ID,
    db_url: str = DEFAULT_DB_URL,
    max_scenarios: int | None = None,
    mode: str = DEFAULT_SWEEP_MODE,
    quick: bool = False,
    preflight_only: bool = False,
    resume_from_checkpoint: bool = True,
) -> None:
    if mode not in {"release", "smoke", "iterative"}:
        raise ValueError(f"Unsupported sensitivity sweep mode: {mode}")
    if preflight_only and mode != "release":
        raise ValueError("Preflight-only mode requires --mode release.")

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
            "preflight_only": preflight_only,
            "resume_from_checkpoint": resume_from_checkpoint,
        }
    ) as run:
        with open(MODEL_PARAMS_PATH, encoding="utf-8") as f:
            base_cfg = json.load(f)
        release_policy = _load_release_evidence_policy()
        dataset_policy = release_policy.get("dataset_policy", {})
        warning_policy = release_policy.get("warning_policy", {})

        store = MetadataStore(db_url)
        policy_version = str(release_policy.get("policy_version", "unknown"))
        try:
            dataset_profile = _load_dataset_profile(store, dataset_id)
        except Exception as exc:
            if preflight_only:
                preflight_payload = _build_release_preflight_dataset_error_payload(
                    mode=mode,
                    dataset_id=dataset_id,
                    error_message=str(exc),
                    policy_version=policy_version,
                    max_scenarios=max_scenarios,
                )
                _save_results_atomic(preflight_payload, RELEASE_PREFLIGHT_PATH)
                _write_progress(
                    {
                        "timestamp": _utc_now_iso(),
                        "stage": "preflight_blocked",
                        "dataset_id": dataset_id,
                        "mode": mode,
                        "preflight_status": preflight_payload.get("status"),
                        "reason_codes": preflight_payload.get("reason_codes", []),
                        "error_message": str(exc),
                    }
                )
                store.save_run(run)
                console.print(
                    f"[red]{_utc_now_iso()}[/red] release preflight blocked: {exc}"
                )
                raise SystemExit(1) from exc
            raise

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

        if preflight_only:
            preflight_payload = _build_release_preflight_payload(
                mode=mode,
                dataset_profile=dataset_profile,
                dataset_policy_eval=dataset_policy_eval,
                policy_version=policy_version,
                max_scenarios=max_scenarios,
                scenario_count_expected=scenario_count_expected,
            )
            _save_results_atomic(preflight_payload, RELEASE_PREFLIGHT_PATH)
            _write_progress(
                {
                    "timestamp": _utc_now_iso(),
                    "stage": "preflight_completed",
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "preflight_status": preflight_payload.get("status"),
                    "reason_codes": preflight_payload.get("reason_codes", []),
                    "scenario_total": len(scenarios),
                    "max_scenarios": max_scenarios,
                }
            )
            store.save_run(run)
            if preflight_payload.get("status") != "PREFLIGHT_OK":
                console.print(
                    "[red]Release preflight blocked.[/red] "
                    f"reason_codes={preflight_payload.get('reason_codes', [])}"
                )
                raise SystemExit(1)
            console.print(
                f"[green]{_utc_now_iso()}[/green] release preflight passed "
                f"(dataset=`{dataset_id}`, scenarios={scenario_count_expected})"
            )
            return

        run_start = perf_counter()
        run_started_utc = _utc_now_iso()
        run_id = str(run.run_id)
        scenario_ids = [str(s.get("id", "")) for s in scenarios]
        checkpoint_signature = _build_checkpoint_signature(
            dataset_id=dataset_id,
            mode=mode,
            scenario_ids=scenario_ids,
            policy_version=policy_version,
        )
        checkpoint_state = _new_checkpoint_state(
            signature=checkpoint_signature,
            scenario_total=len(scenarios),
        )
        resumed_rows: dict[str, dict[str, Any]] = {}
        if resume_from_checkpoint:
            existing_checkpoint = _safe_load_json(CHECKPOINT_PATH)
            if existing_checkpoint.get("signature") == checkpoint_signature:
                resumed_rows = _checkpoint_rows_by_id(
                    existing_checkpoint,
                    allowed_scenario_ids=scenario_ids,
                )
                if resumed_rows:
                    checkpoint_state = existing_checkpoint
                    checkpoint_state["status"] = "IN_PROGRESS"
                    console.print(
                        f"[cyan]{_utc_now_iso()}[/cyan] resuming sensitivity sweep from checkpoint "
                        f"({len(resumed_rows)}/{len(scenarios)} scenarios)."
                    )
            elif existing_checkpoint:
                console.print(
                    f"[yellow]{_utc_now_iso()}[/yellow] existing checkpoint signature mismatch; "
                    "starting a fresh checkpoint."
                )

        _write_checkpoint_state(checkpoint_state)

        results: list[dict[str, Any]] = []
        resumed_count = 0
        _write_progress(
            {
                "timestamp": run_started_utc,
                "stage": "run_started",
                "dataset_id": dataset_id,
                "mode": mode,
                "scenario_total": len(scenarios),
                "max_scenarios": max_scenarios,
                "quick": quick,
                "resume_from_checkpoint": resume_from_checkpoint,
                "resumed_scenarios": len(resumed_rows),
                "checkpoint_path": _render_path_for_summary(CHECKPOINT_PATH),
                **_build_progress_timing(
                    run_start=run_start,
                    completed_scenarios=0,
                    scenario_total=len(scenarios),
                ),
            }
        )
        _write_release_run_status(
            mode=mode,
            run_id=run_id,
            run_started_utc=run_started_utc,
            dataset_id=dataset_id,
            status="STARTED",
            reason_codes=["RELEASE_RUN_STARTED"],
            stage="run_started",
            max_scenarios=max_scenarios,
            scenario_total=len(scenarios),
            completed_scenarios=0,
            preflight_status="PREFLIGHT_OK",
            elapsed_sec=0.0,
            eta_sec=None,
            details={
                "resume_from_checkpoint": resume_from_checkpoint,
                "resumed_scenarios": len(resumed_rows),
            },
        )

        for scenario_idx, scenario in enumerate(scenarios, start=1):
            scenario_id = str(scenario["id"])
            if scenario_id in resumed_rows:
                row = resumed_rows[scenario_id]
                results.append(row)
                resumed_count += 1
                timing = _build_progress_timing(
                    run_start=run_start,
                    completed_scenarios=len(results),
                    scenario_total=len(scenarios),
                )
                _write_progress(
                    {
                        "timestamp": _utc_now_iso(),
                        "stage": "scenario_resumed",
                        "dataset_id": dataset_id,
                        "mode": mode,
                        "scenario_id": scenario_id,
                        "scenario_index": scenario_idx,
                        "scenario_total": len(scenarios),
                        **timing,
                    }
                )
                _write_release_run_status(
                    mode=mode,
                    run_id=run_id,
                    run_started_utc=run_started_utc,
                    dataset_id=dataset_id,
                    status="RUNNING",
                    reason_codes=["RELEASE_RUN_RESUMED"],
                    stage="scenario_resumed",
                    max_scenarios=max_scenarios,
                    scenario_total=len(scenarios),
                    completed_scenarios=len(results),
                    scenario_id=scenario_id,
                    preflight_status="PREFLIGHT_OK",
                    elapsed_sec=timing.get("elapsed_sec"),
                    eta_sec=timing.get("eta_sec"),
                )
                continue

            dispatch_timing = _build_progress_timing(
                run_start=run_start,
                completed_scenarios=len(results),
                scenario_total=len(scenarios),
            )
            _write_progress(
                {
                    "timestamp": _utc_now_iso(),
                    "stage": "scenario_dispatch",
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "scenario_id": scenario_id,
                    "scenario_index": scenario_idx,
                    "scenario_total": len(scenarios),
                    **dispatch_timing,
                }
            )
            _write_release_run_status(
                mode=mode,
                run_id=run_id,
                run_started_utc=run_started_utc,
                dataset_id=dataset_id,
                status="RUNNING",
                reason_codes=["RELEASE_RUN_SCENARIO_DISPATCHED"],
                stage="scenario_dispatch",
                max_scenarios=max_scenarios,
                scenario_total=len(scenarios),
                completed_scenarios=len(results),
                scenario_id=scenario_id,
                preflight_status="PREFLIGHT_OK",
                elapsed_sec=dispatch_timing.get("elapsed_sec"),
                eta_sec=dispatch_timing.get("eta_sec"),
            )

            def _scenario_progress(event: dict[str, Any]) -> None:
                timing = _build_progress_timing(
                    run_start=run_start,
                    completed_scenarios=len(results),
                    scenario_total=len(scenarios),
                )
                payload = {
                    "timestamp": _utc_now_iso(),
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "scenario_id": scenario_id,
                    "scenario_index": scenario_idx,
                    "scenario_total": len(scenarios),
                    **timing,
                }
                payload.update(event)
                _write_progress(payload)
                _write_release_run_status(
                    mode=mode,
                    run_id=run_id,
                    run_started_utc=run_started_utc,
                    dataset_id=dataset_id,
                    status="RUNNING",
                    reason_codes=["RELEASE_RUN_SCENARIO_IN_PROGRESS"],
                    stage=str(event.get("stage", "scenario_in_progress")),
                    max_scenarios=max_scenarios,
                    scenario_total=len(scenarios),
                    completed_scenarios=len(results),
                    scenario_id=scenario_id,
                    preflight_status="PREFLIGHT_OK",
                    elapsed_sec=timing.get("elapsed_sec"),
                    eta_sec=timing.get("eta_sec"),
                )

            scenario_wall_start = perf_counter()
            console.print(
                f"[bold cyan]{_utc_now_iso()}[/bold cyan] "
                f"scenario {scenario_idx}/{len(scenarios)} `{scenario['id']}` started"
            )
            try:
                scenario_result = _run_model_evaluation_scenario(
                    db_url,
                    dataset_id,
                    scenario["config"],
                    warning_policy,
                    scenario_id=scenario_id,
                    progress_hook=_scenario_progress,
                )
            except BaseException as exc:
                failure_timestamp = _utc_now_iso()
                failure_timing = _build_progress_timing(
                    run_start=run_start,
                    completed_scenarios=len(results),
                    scenario_total=len(scenarios),
                )
                checkpoint_state["status"] = "FAILED"
                checkpoint_state["failure"] = {
                    "timestamp": failure_timestamp,
                    "scenario_id": scenario_id,
                    "scenario_index": scenario_idx,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                _write_checkpoint_state(checkpoint_state)
                _write_progress(
                    {
                        "timestamp": failure_timestamp,
                        "stage": "run_failed",
                        "dataset_id": dataset_id,
                        "mode": mode,
                        "scenario_id": scenario_id,
                        "scenario_index": scenario_idx,
                        "scenario_total": len(scenarios),
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        **failure_timing,
                    }
                )
                _write_release_run_status(
                    mode=mode,
                    run_id=run_id,
                    run_started_utc=run_started_utc,
                    dataset_id=dataset_id,
                    status="FAILED",
                    reason_codes=["RELEASE_RUN_FAILED"],
                    stage="run_failed",
                    max_scenarios=max_scenarios,
                    scenario_total=len(scenarios),
                    completed_scenarios=len(results),
                    scenario_id=scenario_id,
                    preflight_status="PREFLIGHT_OK",
                    elapsed_sec=failure_timing.get("elapsed_sec"),
                    eta_sec=failure_timing.get("eta_sec"),
                    details={
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )
                raise
            row = {
                "id": scenario_id,
                "family": scenario["family"],
                **scenario_result["metrics"],
                "warnings": scenario_result["warnings"],
                "quality_flags": scenario_result["quality_flags"],
                "valid": scenario_result["valid"],
            }
            results.append(row)
            _record_checkpoint_result(
                checkpoint_state,
                scenario_id=scenario_id,
                scenario_index=scenario_idx,
                result_row=row,
            )
            _write_checkpoint_state(checkpoint_state)

            scenario_wall_elapsed = perf_counter() - scenario_wall_start
            timing = _build_progress_timing(
                run_start=run_start,
                completed_scenarios=len(results),
                scenario_total=len(scenarios),
            )
            eta_sec = timing.get("eta_sec")
            eta_text = f"{eta_sec:.1f}s" if isinstance(eta_sec, float) else "n/a"
            console.print(
                f"[green]{_utc_now_iso()}[/green] scenario {scenario_idx}/{len(scenarios)} "
                f"`{row['id']}` done -> {row['top_model']} "
                f"(surviving={row['surviving_models']}, warnings={row['warnings']['total_warnings']}, "
                f"elapsed={scenario_wall_elapsed:.1f}s, eta={eta_text})"
            )
            _write_progress(
                {
                    "timestamp": _utc_now_iso(),
                    "stage": "scenario_completed",
                    "dataset_id": dataset_id,
                    "mode": mode,
                    "scenario_id": scenario_id,
                    "scenario_index": scenario_idx,
                    "scenario_total": len(scenarios),
                    "warning_total": row["warnings"]["total_warnings"],
                    "quality_flags": row["quality_flags"],
                    **timing,
                }
            )
            _write_release_run_status(
                mode=mode,
                run_id=run_id,
                run_started_utc=run_started_utc,
                dataset_id=dataset_id,
                status="RUNNING",
                reason_codes=["RELEASE_RUN_SCENARIO_COMPLETED"],
                stage="scenario_completed",
                max_scenarios=max_scenarios,
                scenario_total=len(scenarios),
                completed_scenarios=len(results),
                scenario_id=scenario_id,
                preflight_status="PREFLIGHT_OK",
                elapsed_sec=timing.get("elapsed_sec"),
                eta_sec=timing.get("eta_sec"),
            )

        if resumed_count:
            console.print(
                f"[cyan]{_utc_now_iso()}[/cyan] resumed {resumed_count} scenario(s) from checkpoint."
            )

        summary = _decide_robustness(results, warning_policy)
        generated_utc = _utc_now_iso()
        summary["date"] = generated_utc
        summary["generated_utc"] = generated_utc
        summary["generated_by"] = SENSITIVITY_GENERATED_BY
        summary["schema_version"] = SENSITIVITY_SCHEMA_VERSION
        summary["policy_version"] = policy_version
        summary["dataset_id"] = dataset_id
        summary["dataset_pages"] = dataset_profile["pages"]
        summary["dataset_tokens"] = dataset_profile["tokens"]
        summary["dataset_policy_pass"] = dataset_policy_eval["dataset_policy_pass"]
        summary["dataset_policy_reasons"] = dataset_policy_eval["dataset_policy_reasons"]
        summary["dataset_policy_constraints"] = dataset_policy_eval[
            "dataset_policy_constraints"
        ]
        summary["execution_mode"] = mode
        summary["artifact_class"] = (
            "release_candidate" if mode == "release" else "latest_snapshot"
        )
        summary["scenario_count_expected"] = scenario_count_expected
        summary["scenario_count_executed"] = len(results)
        summary["release_readiness_failures"] = _collect_release_readiness_failures(
            summary,
            mode=mode,
            max_scenarios=max_scenarios,
            scenario_count_expected=scenario_count_expected,
            scenario_count_executed=len(results),
        )
        summary["release_evidence_ready"] = len(summary["release_readiness_failures"]) == 0

        status_payload = {
            "summary": summary,
            "dataset_profile": dataset_profile,
            "results": results,
        }

        if mode == "release":
            status_path = RELEASE_STATUS_PATH
            report_path = RELEASE_REPORT_PATH
            diagnostics_path = RELEASE_DIAGNOSTICS_PATH
            summary["release_run_status_path"] = _render_path_for_summary(
                RELEASE_RUN_STATUS_PATH
            )
        else:
            status_path = STATUS_PATH
            report_path = REPORT_PATH
            diagnostics_path = DIAGNOSTICS_PATH

        status_path.parent.mkdir(parents=True, exist_ok=True)
        summary["artifact_path"] = _render_path_for_summary(status_path)
        summary["report_path"] = _render_path_for_summary(report_path)
        summary["diagnostics_path"] = _render_path_for_summary(diagnostics_path)

        _save_results_atomic(status_payload, status_path)
        _write_markdown_report(
            summary,
            dataset_profile,
            results,
            report_path=report_path,
        )
        _write_quality_diagnostics(
            summary,
            dataset_profile,
            results,
            diagnostics_path=diagnostics_path,
        )
        completion_timing = _build_progress_timing(
            run_start=run_start,
            completed_scenarios=len(results),
            scenario_total=len(scenarios),
        )
        _write_progress(
            {
                "timestamp": _utc_now_iso(),
                "stage": "run_completed",
                "dataset_id": dataset_id,
                "mode": mode,
                "scenario_total": len(scenarios),
                "resumed_scenarios": resumed_count,
                **completion_timing,
                "summary": {
                    "release_evidence_ready": summary.get("release_evidence_ready"),
                    "robustness_decision": summary.get("robustness_decision"),
                    "quality_gate_passed": summary.get("quality_gate_passed"),
                    "dataset_policy_pass": summary.get("dataset_policy_pass"),
                    "warning_policy_pass": summary.get("warning_policy_pass"),
                },
            }
        )
        _write_release_run_status(
            mode=mode,
            run_id=run_id,
            run_started_utc=run_started_utc,
            dataset_id=dataset_id,
            status="COMPLETED",
            reason_codes=["RELEASE_RUN_COMPLETED"],
            stage="run_completed",
            max_scenarios=max_scenarios,
            scenario_total=len(scenarios),
            completed_scenarios=len(results),
            preflight_status="PREFLIGHT_OK",
            elapsed_sec=completion_timing.get("elapsed_sec"),
            eta_sec=completion_timing.get("eta_sec"),
            details={
                "release_evidence_ready": summary.get("release_evidence_ready"),
                "robustness_decision": summary.get("robustness_decision"),
                "quality_gate_passed": summary.get("quality_gate_passed"),
            },
        )
        checkpoint_state["status"] = "COMPLETED"
        checkpoint_state["summary"] = {
            "release_evidence_ready": summary.get("release_evidence_ready"),
            "robustness_decision": summary.get("robustness_decision"),
            "quality_gate_passed": summary.get("quality_gate_passed"),
        }
        _write_checkpoint_state(checkpoint_state)
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
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Release-mode preflight only: validate release prerequisites and write "
            "`core_status/core_audit/sensitivity_release_preflight.json` without running scenarios."
        ),
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help=(
            "Disable scenario-level checkpoint resume behavior from "
            "`core_status/core_audit/sensitivity_checkpoint.json`."
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
        preflight_only=args.preflight_only,
        resume_from_checkpoint=not args.no_resume,
    )
