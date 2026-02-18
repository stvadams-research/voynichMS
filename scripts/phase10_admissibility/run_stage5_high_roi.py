#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 5 high-ROI confirmatory reruns.

Scope:
- Method F robustness matrix (multi-seed, multi-window, multi-null-profile)
- Method J/K strict recalibration gates
- Pre-registered tension-resolution gate evaluation
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase10_admissibility.stage1_pipeline import (
    METHOD_J_EDGE_RULES,
    analyze_method_j_line_reset_effects,
    build_reference_generators,
    evaluate_method_j_upgrade_gate,
    load_dataset_bundle,
    now_utc_iso,
    run_method_j,
    run_method_k,
)
from phase10_admissibility.stage3_pipeline import Stage3Config, run_method_f

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 10 Stage 5 high-ROI confirmatory reruns."
    )
    parser.add_argument(
        "--gate-config",
        type=str,
        default="configs/phase10_admissibility/stage5_high_roi_gate.json",
    )
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage5_high_roi_status.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset checkpoints and re-run all Stage 5 steps.",
    )
    return parser.parse_args()


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _unwrap_results(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _artifact_results(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    artifact = Path(path)
    if not artifact.exists():
        return None
    return _unwrap_results(_load_json(artifact))


def _default_status(gate_config_path: str, gate_config: dict[str, Any]) -> dict[str, Any]:
    now = now_utc_iso()
    method_f = gate_config.get("method_f", {})
    method_j = gate_config.get("method_j", {})
    method_k = gate_config.get("method_k", {})
    return {
        "phase": "10.5",
        "stage": "Stage 5",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "gate_config_path": gate_config_path,
            "method_f": {
                "seeds": method_f.get("seeds", []),
                "token_windows": method_f.get("token_windows", []),
                "token_offsets": method_f.get("token_offsets", []),
                "null_profiles": [
                    str(profile.get("name", "profile"))
                    for profile in method_f.get("null_profiles", [])
                    if isinstance(profile, dict)
                ],
            },
            "method_j": {
                "seeds": method_j.get("seeds", []),
                "target_tokens": method_j.get("target_tokens"),
                "null_runs": method_j.get("null_runs"),
            },
            "method_k": {
                "seeds": method_k.get("seeds", []),
                "target_tokens": method_k.get("target_tokens"),
                "num_runs": method_k.get("num_runs"),
            },
        },
        "steps": {
            "method_f_matrix": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "jk_recalibration": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "stage5_summary": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "report": None,
                "error": None,
            },
        },
        "method_f_runs": {},
        "jk_runs": {},
    }


def _load_or_init_status(
    path: Path,
    gate_config_path: str,
    gate_config: dict[str, Any],
    force: bool,
) -> dict[str, Any]:
    if force or not path.exists():
        return _default_status(gate_config_path, gate_config)
    try:
        status = _load_json(path)
    except Exception:
        return _default_status(gate_config_path, gate_config)
    if status.get("phase") != "10.5":
        return _default_status(gate_config_path, gate_config)
    return status


def _save_status(path: Path, status: dict[str, Any]) -> None:
    status["updated_at"] = now_utc_iso()
    _save_json(path, status)


def _set_step(status: dict[str, Any], step: str, step_status: str, **fields: Any) -> None:
    entry = status["steps"][step]
    entry["status"] = step_status
    for key, value in fields.items():
        entry[key] = value


def _method_f_specs(gate_config: dict[str, Any]) -> list[dict[str, Any]]:
    method_f = gate_config["method_f"]
    specs: list[dict[str, Any]] = []
    for seed in method_f.get("seeds", []):
        for token_window in method_f.get("token_windows", []):
            for token_offset in method_f.get("token_offsets", [0]):
                for profile in method_f.get("null_profiles", []):
                    profile_name = str(profile.get("name", "profile"))
                    specs.append(
                        {
                            "seed": int(seed),
                            "token_window": int(token_window),
                            "token_offset": int(token_offset),
                            "profile_name": profile_name,
                            "null_block_min": int(profile.get("null_block_min", 2)),
                            "null_block_max": int(profile.get("null_block_max", 12)),
                            "param_samples_per_family": int(
                                method_f.get("param_samples_per_family", 10000)
                            ),
                            "null_sequences": int(method_f.get("null_sequences", 1000)),
                            "perturbations_per_candidate": int(
                                method_f.get("perturbations_per_candidate", 12)
                            ),
                            "max_outlier_probes": int(
                                method_f.get("max_outlier_probes", 12)
                            ),
                            "symbol_alphabet_size": int(
                                method_f.get("symbol_alphabet_size", 64)
                            ),
                        }
                    )
    return specs


def _method_f_run_key(spec: dict[str, Any]) -> str:
    return (
        f"seed{spec['seed']}_w{spec['token_window']}_o{spec['token_offset']}_"
        f"{spec['profile_name']}"
    )


def _evaluate_method_f_matrix(
    run_results: dict[str, dict[str, Any]],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    method_f_cfg = gate_config["method_f"]
    allowed = set(str(v) for v in method_f_cfg.get("allowed_method_decisions", []))
    if not allowed:
        allowed = {"closure_strengthened", "indeterminate"}
    max_stable_natural = int(method_f_cfg.get("max_stable_natural_outliers_per_family", 0))

    per_run: dict[str, Any] = {}
    all_pass = True
    weakened_family_runs = 0
    stable_natural_violations = 0
    aggregate_family_decisions: dict[str, dict[str, int]] = {
        "table_grille": {"closure_weakened": 0, "indeterminate": 0, "closure_strengthened": 0},
        "slot_logic": {"closure_weakened": 0, "indeterminate": 0, "closure_strengthened": 0},
        "constrained_markov": {
            "closure_weakened": 0,
            "indeterminate": 0,
            "closure_strengthened": 0,
        },
    }

    for run_key in sorted(run_results):
        result = run_results[run_key]
        decision = str(result.get("decision", "unknown"))
        family_decisions = {
            name: str(value)
            for name, value in result.get("family_decisions", {}).items()
        }
        family_results = result.get("family_results", {})
        stable_natural_by_family = {
            name: int(data.get("stable_natural_outlier_count", 0))
            for name, data in family_results.items()
            if isinstance(data, dict)
        }

        for family, family_decision in family_decisions.items():
            aggregate_family_decisions.setdefault(family, {})
            aggregate_family_decisions[family].setdefault(family_decision, 0)
            aggregate_family_decisions[family][family_decision] += 1

        any_family_weakened = any(v == "closure_weakened" for v in family_decisions.values())
        stable_natural_pass = all(
            value <= max_stable_natural for value in stable_natural_by_family.values()
        )
        decision_pass = decision in allowed
        run_pass = decision_pass and (not any_family_weakened) and stable_natural_pass

        if any_family_weakened:
            weakened_family_runs += 1
        if not stable_natural_pass:
            stable_natural_violations += 1
        if not run_pass:
            all_pass = False

        per_run[run_key] = {
            "decision": decision,
            "decision_pass": decision_pass,
            "family_decisions": family_decisions,
            "any_family_weakened": any_family_weakened,
            "stable_natural_by_family": stable_natural_by_family,
            "max_stable_natural_allowed": max_stable_natural,
            "stable_natural_pass": stable_natural_pass,
            "pass": run_pass,
        }

    return {
        "pass": all_pass,
        "run_count": len(run_results),
        "allowed_method_decisions": sorted(allowed),
        "max_stable_natural_outliers_per_family": max_stable_natural,
        "weakened_family_runs": weakened_family_runs,
        "stable_natural_violations": stable_natural_violations,
        "aggregate_family_decisions": aggregate_family_decisions,
        "per_run": per_run,
    }


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _evaluate_method_k_seed(
    method_k_result: dict[str, Any],
    correlation_threshold: float,
) -> dict[str, Any]:
    outliers = list(method_k_result.get("outlier_features", []))
    direction = method_k_result.get("direction_to_language", {})
    difficulty = method_k_result.get("modification_difficulty", {})

    robust_language_hard = [
        feature
        for feature in outliers
        if bool(direction.get(feature, {}).get("toward_language", False))
        and difficulty.get(feature, {}).get("difficulty") == "hard_framework_shift"
    ]

    corr = float(method_k_result.get("outlier_mean_abs_correlation", 0.0))
    return {
        "decision": method_k_result.get("decision"),
        "outliers": outliers,
        "correlation": corr,
        "correlation_pass": corr >= correlation_threshold,
        "robust_language_hard_features": robust_language_hard,
    }


def _evaluate_method_k_multiseed(
    by_seed: dict[int, dict[str, Any]],
    method_k_cfg: dict[str, Any],
) -> dict[str, Any]:
    seeds = sorted(by_seed.keys())
    required_direction = str(method_k_cfg.get("required_direction", "closure_weakened"))
    correlation_threshold = float(method_k_cfg.get("correlation_threshold", 0.4))
    min_consistent_outliers = int(method_k_cfg.get("min_consistent_outliers", 2))
    require_same_outlier_set = bool(method_k_cfg.get("require_same_outlier_set", True))
    require_same_outlier_sign = bool(method_k_cfg.get("require_same_outlier_sign", True))
    require_language_ward = bool(method_k_cfg.get("require_language_ward", True))
    require_hard_to_close = bool(method_k_cfg.get("require_hard_to_close", True))

    seed_eval = {
        seed: _evaluate_method_k_seed(by_seed[seed], correlation_threshold) for seed in seeds
    }

    decisions = [str(seed_eval[seed]["decision"]) for seed in seeds]
    direction_consensus = len(set(decisions)) == 1
    consensus_direction = decisions[0] if direction_consensus else "mixed"
    required_direction_met = direction_consensus and consensus_direction == required_direction

    outlier_sets = {seed: set(seed_eval[seed]["outliers"]) for seed in seeds}
    if outlier_sets:
        first_set = next(iter(outlier_sets.values()))
        same_outlier_set = all(current == first_set for current in outlier_sets.values())
        common_features = set.intersection(*outlier_sets.values()) if outlier_sets else set()
    else:
        same_outlier_set = True
        common_features = set()

    consistent_sign_features: list[str] = []
    for feature in sorted(common_features):
        signs = []
        for seed in seeds:
            z = float(by_seed[seed].get("feature_stats", {}).get(feature, {}).get("z_score", 0.0))
            signs.append(_sign(z))
        if len(set(signs)) == 1 and signs[0] != 0:
            consistent_sign_features.append(feature)

    languageward_consistent = [
        feature
        for feature in consistent_sign_features
        if all(
            bool(
                by_seed[seed]
                .get("direction_to_language", {})
                .get(feature, {})
                .get("toward_language", False)
            )
            for seed in seeds
        )
    ]

    hard_to_close_consistent = [
        feature
        for feature in languageward_consistent
        if all(
            by_seed[seed].get("modification_difficulty", {}).get(feature, {}).get("difficulty")
            == "hard_framework_shift"
            for seed in seeds
        )
    ]

    correlation_all_pass = all(seed_eval[seed]["correlation_pass"] for seed in seeds)
    same_outlier_set_pass = (not require_same_outlier_set) or same_outlier_set
    same_sign_pass = (not require_same_outlier_sign) or (
        len(consistent_sign_features) >= min_consistent_outliers
    )
    languageward_pass = (not require_language_ward) or (
        len(languageward_consistent) >= min_consistent_outliers
    )
    hard_to_close_pass = (not require_hard_to_close) or (
        len(hard_to_close_consistent) >= min_consistent_outliers
    )

    pass_gate = (
        required_direction_met
        and correlation_all_pass
        and same_outlier_set_pass
        and same_sign_pass
        and languageward_pass
        and hard_to_close_pass
    )

    return {
        "per_seed": {str(seed): seed_eval[seed] for seed in seeds},
        "direction_consensus": direction_consensus,
        "consensus_direction": consensus_direction,
        "required_direction": required_direction,
        "required_direction_met": required_direction_met,
        "same_outlier_set": same_outlier_set,
        "same_outlier_set_pass": same_outlier_set_pass,
        "common_outlier_features": sorted(common_features),
        "consistent_sign_features": consistent_sign_features,
        "same_sign_pass": same_sign_pass,
        "languageward_consistent_features": languageward_consistent,
        "languageward_pass": languageward_pass,
        "hard_to_close_consistent_features": hard_to_close_consistent,
        "hard_to_close_pass": hard_to_close_pass,
        "correlation_threshold": correlation_threshold,
        "correlation_all_pass": correlation_all_pass,
        "min_consistent_outliers": min_consistent_outliers,
        "pass": pass_gate,
    }


def _evaluate_method_j_multiseed(
    by_seed: dict[int, dict[str, Any]],
    method_j_cfg: dict[str, Any],
) -> dict[str, Any]:
    seeds = sorted(by_seed.keys())
    required_direction = str(method_j_cfg.get("required_direction", "closure_weakened"))
    z_threshold = float(method_j_cfg.get("z_threshold", 3.0))
    min_stable_non_edge_anomalies = int(method_j_cfg.get("min_stable_non_edge_anomalies", 1))
    edge_rules = set(method_j_cfg.get("edge_rules", sorted(METHOD_J_EDGE_RULES)))

    per_seed = {}
    decisions = []
    for seed in seeds:
        result = by_seed[seed]
        gate = evaluate_method_j_upgrade_gate(
            method_j_result=result,
            z_threshold=z_threshold,
            min_stable_non_edge_anomalies=min_stable_non_edge_anomalies,
            edge_rules=edge_rules,
        )
        ablation = analyze_method_j_line_reset_effects(
            method_j_result=result,
            z_threshold=z_threshold,
            edge_rules=edge_rules,
        )
        decisions.append(str(result.get("decision")))
        per_seed[str(seed)] = {
            "decision": result.get("decision"),
            "gate": gate,
            "ablation": ablation,
        }

    direction_consensus = len(set(decisions)) == 1
    consensus_direction = decisions[0] if direction_consensus else "mixed"
    required_direction_met = direction_consensus and consensus_direction == required_direction
    seed_pass_all = all(per_seed[str(seed)]["gate"]["pass"] for seed in seeds)
    pass_gate = required_direction_met and seed_pass_all

    return {
        "per_seed": per_seed,
        "direction_consensus": direction_consensus,
        "consensus_direction": consensus_direction,
        "required_direction": required_direction,
        "required_direction_met": required_direction_met,
        "seed_gate_all_pass": seed_pass_all,
        "z_threshold": z_threshold,
        "min_stable_non_edge_anomalies": min_stable_non_edge_anomalies,
        "edge_rules": sorted(edge_rules),
        "pass": pass_gate,
    }


def _build_stage5_markdown(
    summary: dict[str, Any],
    artifacts: dict[str, str],
    status_path: str,
) -> str:
    method_f_gate = summary["method_f_gate"]
    method_j_gate = summary["method_j_gate"]
    method_k_gate = summary["method_k_gate"]
    lines = [
        "# Phase 10 Stage 5 High-ROI Confirmatory Results",
        "",
        f"Generated: {summary['generated_at']}",
        f"Run ID: {summary['run_id']}",
        "",
        "## Gate Outcomes",
        "",
        f"- Method F robustness gate pass: `{method_f_gate['pass']}`",
        f"- Method J strict gate pass (stays weakened): `{method_j_gate['pass']}`",
        f"- Method K strict gate pass (stays weakened): `{method_k_gate['pass']}`",
        f"- Resolution class: `{summary['resolution_class']}`",
        "",
        "## Method F Matrix",
        "",
        f"- Robustness runs completed: `{method_f_gate['run_count']}`",
        f"- Runs with weakened family decisions: `{method_f_gate['weakened_family_runs']}`",
        (
            "- Runs violating stable-natural cap: "
            f"`{method_f_gate['stable_natural_violations']}`"
        ),
        "",
        "## Resolution Rule",
        "",
        "- Pre-registered rule: closure upgrade is only eligible if Method F passes and "
        "both Method J and Method K fail strict weakened-status gates.",
        f"- Rule satisfied: `{summary['closure_upgrade_rule_satisfied']}`",
        f"- Recommendation: `{summary['recommendation']}`",
        "",
        "## Artifacts",
        "",
        f"- Method F matrix artifact: `{artifacts.get('method_f_matrix', 'n/a')}`",
        f"- J/K strict artifact: `{artifacts.get('jk_recalibration', 'n/a')}`",
        f"- Stage 5 summary artifact: `{artifacts.get('stage5_summary', 'n/a')}`",
        f"- Status tracker: `{status_path}`",
        "",
    ]
    return "\n".join(lines)


def run_stage5(args: argparse.Namespace) -> None:
    gate_config_path = Path(args.gate_config)
    gate_config = _load_json(gate_config_path)

    status_path = Path(args.status_path)
    status = _load_or_init_status(
        path=status_path,
        gate_config_path=str(gate_config_path),
        gate_config=gate_config,
        force=args.force,
    )

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 5 Runner[/bold blue]\n"
            "High-ROI confirmatory reruns with restart checkpoints",
            border_style="blue",
        )
    )
    _log(
        "Using gate config: "
        f"{gate_config_path} | force={args.force}"
    )

    with active_run(config={"command": "run_phase10_stage5_high_roi", "seed": 42}) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        artifacts: dict[str, str] = {}

        # Step 1: Method F matrix.
        existing_method_f = _artifact_results(status["steps"]["method_f_matrix"].get("artifact"))
        if (
            status["steps"]["method_f_matrix"].get("status") == "completed"
            and existing_method_f is not None
            and not args.force
        ):
            method_f_matrix_results = existing_method_f
            artifacts["method_f_matrix"] = status["steps"]["method_f_matrix"]["artifact"]
            _log("Method F matrix step reused from checkpoint")
        else:
            _set_step(
                status,
                "method_f_matrix",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("Method F matrix step started")

            method_f_specs = _method_f_specs(gate_config)
            _log(f"Method F matrix size: {len(method_f_specs)} runs")
            method_f_results_by_run: dict[str, dict[str, Any]] = {}
            run_artifacts: dict[str, str] = {}

            for idx, spec in enumerate(method_f_specs):
                run_key = _method_f_run_key(spec)
                run_state = status["method_f_runs"].setdefault(
                    run_key,
                    {
                        "status": "pending",
                        "started_at": None,
                        "completed_at": None,
                        "artifact": None,
                        "config": spec,
                        "error": None,
                    },
                )
                run_state["config"] = spec
                artifact_path = run_state.get("artifact")
                existing = _artifact_results(artifact_path)
                if (
                    run_state.get("status") == "completed"
                    and existing is not None
                    and not args.force
                ):
                    method_f_results_by_run[run_key] = existing
                    run_artifacts[run_key] = str(artifact_path)
                    _log(
                        "Method F matrix run reused "
                        f"({idx + 1}/{len(method_f_specs)}): {run_key}"
                    )
                    continue

                _log(
                    "Method F matrix run started "
                    f"({idx + 1}/{len(method_f_specs)}): {run_key}"
                )
                run_state.update(
                    {
                        "status": "running",
                        "started_at": now_utc_iso(),
                        "completed_at": None,
                        "error": None,
                    }
                )
                _save_status(status_path, status)

                config = Stage3Config(
                    seed=int(spec["seed"]),
                    token_start=int(spec["token_offset"]),
                    target_tokens=int(spec["token_window"]),
                    param_samples_per_family=int(spec["param_samples_per_family"]),
                    null_sequences=int(spec["null_sequences"]),
                    perturbations_per_candidate=int(spec["perturbations_per_candidate"]),
                    max_outlier_probes=int(spec["max_outlier_probes"]),
                    null_block_min=int(spec["null_block_min"]),
                    null_block_max=int(spec["null_block_max"]),
                    symbol_alphabet_size=int(spec["symbol_alphabet_size"]),
                )

                try:
                    result = run_method_f(
                        store=store,
                        config=config,
                        progress=lambda msg, rk=run_key: _log(f"[method_f:{rk}] {msg}"),
                    )
                    save_path = (
                        "results/data/phase10_admissibility/"
                        f"method_f_high_roi_{run_key}.json"
                    )
                    saved = ProvenanceWriter.save_results(result, Path(save_path))
                    run_state.update(
                        {
                            "status": "completed",
                            "completed_at": now_utc_iso(),
                            "artifact": saved["latest_path"],
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)

                    method_f_results_by_run[run_key] = result
                    run_artifacts[run_key] = saved["latest_path"]
                    _log(
                        "Method F matrix run complete "
                        f"({idx + 1}/{len(method_f_specs)}): {run_key} -> "
                        f"{result.get('decision')}"
                    )
                except Exception as exc:
                    run_state.update(
                        {
                            "status": "failed",
                            "completed_at": now_utc_iso(),
                            "error": str(exc),
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Method F matrix run failed ({run_key}): {exc}")
                    raise

            method_f_gate = _evaluate_method_f_matrix(
                run_results=method_f_results_by_run,
                gate_config=gate_config,
            )
            method_f_matrix_results = {
                "status": "ok",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "gate_config_path": str(gate_config_path),
                "method_f_gate": method_f_gate,
                "runs": method_f_results_by_run,
                "run_artifacts": run_artifacts,
            }
            saved_matrix = ProvenanceWriter.save_results(
                method_f_matrix_results,
                Path("results/data/phase10_admissibility/stage5_method_f_matrix.json"),
            )
            artifacts["method_f_matrix"] = saved_matrix["latest_path"]
            _set_step(
                status,
                "method_f_matrix",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_matrix["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(
                "Method F matrix step complete: "
                f"pass={method_f_gate['pass']}, runs={method_f_gate['run_count']}"
            )

        # Step 2: Method J/K strict recalibration.
        existing_jk = _artifact_results(status["steps"]["jk_recalibration"].get("artifact"))
        if (
            status["steps"]["jk_recalibration"].get("status") == "completed"
            and existing_jk is not None
            and not args.force
        ):
            jk_results = existing_jk
            artifacts["jk_recalibration"] = status["steps"]["jk_recalibration"]["artifact"]
            _log("J/K strict recalibration step reused from checkpoint")
        else:
            _set_step(
                status,
                "jk_recalibration",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("J/K strict recalibration step started")

            method_j_cfg = gate_config["method_j"]
            method_k_cfg = gate_config["method_k"]
            seeds_j = [int(v) for v in method_j_cfg.get("seeds", [])]
            seeds_k = [int(v) for v in method_k_cfg.get("seeds", [])]
            if seeds_j != seeds_k:
                raise RuntimeError(
                    "Method J/K strict recalibration requires identical seed lists in gate config."
                )
            seeds = seeds_j

            voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich (Real)")
            latin_bundle = load_dataset_bundle(store, "latin_classic", "Latin (Semantic)")
            _log(
                "Loaded bundles for J/K recalibration: "
                f"Voynich tokens={len(voynich_bundle.tokens)}, "
                f"Latin tokens={len(latin_bundle.tokens)}"
            )

            method_j_by_seed: dict[int, dict[str, Any]] = {}
            method_k_by_seed: dict[int, dict[str, Any]] = {}
            seed_artifacts: dict[str, dict[str, str]] = {"method_j": {}, "method_k": {}}

            for seed in seeds:
                seed_key = str(seed)
                seed_state = status["jk_runs"].setdefault(
                    seed_key,
                    {
                        "method_j": {
                            "status": "pending",
                            "started_at": None,
                            "completed_at": None,
                            "artifact": None,
                            "error": None,
                        },
                        "method_k": {
                            "status": "pending",
                            "started_at": None,
                            "completed_at": None,
                            "artifact": None,
                            "error": None,
                        },
                    },
                )

                # Method J
                method_j_state = seed_state["method_j"]
                existing_j_seed = _artifact_results(method_j_state.get("artifact"))
                if (
                    method_j_state.get("status") == "completed"
                    and existing_j_seed is not None
                    and not args.force
                ):
                    method_j_by_seed[seed] = existing_j_seed
                    seed_artifacts["method_j"][seed_key] = str(method_j_state.get("artifact"))
                    _log(f"Seed {seed}: Method J strict run reused")
                else:
                    method_j_state.update(
                        {
                            "status": "running",
                            "started_at": now_utc_iso(),
                            "completed_at": None,
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method J strict run started")

                    try:
                        generators = build_reference_generators(voynich_bundle.lines, seed)
                        method_j_result = run_method_j(
                            voynich_bundle=voynich_bundle,
                            generators=generators,
                            target_tokens=int(method_j_cfg.get("target_tokens", 30000)),
                            null_runs=int(method_j_cfg.get("null_runs", 150)),
                            seed=seed,
                            progress=lambda msg, s=seed: _log(f"[method_j:{s}] {msg}"),
                        )
                        saved_j = ProvenanceWriter.save_results(
                            method_j_result,
                            Path(
                                "results/data/phase10_admissibility/"
                                f"method_j_high_roi_seed_{seed}.json"
                            ),
                        )
                        method_j_state.update(
                            {
                                "status": "completed",
                                "completed_at": now_utc_iso(),
                                "artifact": saved_j["latest_path"],
                                "error": None,
                            }
                        )
                        _save_status(status_path, status)

                        method_j_by_seed[seed] = method_j_result
                        seed_artifacts["method_j"][seed_key] = saved_j["latest_path"]
                        _log(
                            f"Seed {seed}: Method J strict run complete "
                            f"({method_j_result.get('decision')})"
                        )
                    except Exception as exc:
                        method_j_state.update(
                            {
                                "status": "failed",
                                "completed_at": now_utc_iso(),
                                "error": str(exc),
                            }
                        )
                        _save_status(status_path, status)
                        _log(f"Seed {seed}: Method J strict run failed ({exc})")
                        raise

                # Method K
                method_k_state = seed_state["method_k"]
                existing_k_seed = _artifact_results(method_k_state.get("artifact"))
                if (
                    method_k_state.get("status") == "completed"
                    and existing_k_seed is not None
                    and not args.force
                ):
                    method_k_by_seed[seed] = existing_k_seed
                    seed_artifacts["method_k"][seed_key] = str(method_k_state.get("artifact"))
                    _log(f"Seed {seed}: Method K strict run reused")
                else:
                    method_k_state.update(
                        {
                            "status": "running",
                            "started_at": now_utc_iso(),
                            "completed_at": None,
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method K strict run started")

                    try:
                        method_k_result = run_method_k(
                            voynich_bundle=voynich_bundle,
                            latin_bundle=latin_bundle,
                            target_tokens=int(method_k_cfg.get("target_tokens", 30000)),
                            num_runs=int(method_k_cfg.get("num_runs", 150)),
                            seed=seed,
                            progress=lambda msg, s=seed: _log(f"[method_k:{s}] {msg}"),
                        )
                        saved_k = ProvenanceWriter.save_results(
                            method_k_result,
                            Path(
                                "results/data/phase10_admissibility/"
                                f"method_k_high_roi_seed_{seed}.json"
                            ),
                        )
                        method_k_state.update(
                            {
                                "status": "completed",
                                "completed_at": now_utc_iso(),
                                "artifact": saved_k["latest_path"],
                                "error": None,
                            }
                        )
                        _save_status(status_path, status)

                        method_k_by_seed[seed] = method_k_result
                        seed_artifacts["method_k"][seed_key] = saved_k["latest_path"]
                        _log(
                            f"Seed {seed}: Method K strict run complete "
                            f"({method_k_result.get('decision')})"
                        )
                    except Exception as exc:
                        method_k_state.update(
                            {
                                "status": "failed",
                                "completed_at": now_utc_iso(),
                                "error": str(exc),
                            }
                        )
                        _save_status(status_path, status)
                        _log(f"Seed {seed}: Method K strict run failed ({exc})")
                        raise

            method_j_gate = _evaluate_method_j_multiseed(method_j_by_seed, method_j_cfg)
            method_k_gate = _evaluate_method_k_multiseed(method_k_by_seed, method_k_cfg)

            jk_results = {
                "status": "ok",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "gate_config_path": str(gate_config_path),
                "method_j": method_j_gate,
                "method_k": method_k_gate,
                "seed_artifacts": seed_artifacts,
            }
            saved_jk = ProvenanceWriter.save_results(
                jk_results,
                Path("results/data/phase10_admissibility/stage5_jk_recalibration.json"),
            )
            artifacts["jk_recalibration"] = saved_jk["latest_path"]
            _set_step(
                status,
                "jk_recalibration",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_jk["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(
                "J/K strict recalibration step complete: "
                f"method_j_pass={method_j_gate['pass']}, method_k_pass={method_k_gate['pass']}"
            )

        # Step 3: Stage 5 summary and report.
        existing_summary = _artifact_results(status["steps"]["stage5_summary"].get("artifact"))
        if (
            status["steps"]["stage5_summary"].get("status") == "completed"
            and existing_summary is not None
            and not args.force
        ):
            summary = existing_summary
            artifacts["stage5_summary"] = status["steps"]["stage5_summary"]["artifact"]
            _log("Stage 5 summary reused from checkpoint")
        else:
            _set_step(
                status,
                "stage5_summary",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 5 summary step started")

            method_f_gate = method_f_matrix_results["method_f_gate"]
            method_j_gate = jk_results["method_j"]
            method_k_gate = jk_results["method_k"]
            resolution_rule = gate_config.get("resolution_gate", {}).get(
                "closure_upgrade_requires", {}
            )
            closure_upgrade_rule_satisfied = (
                bool(method_f_gate.get("pass", False))
                == bool(resolution_rule.get("method_f_pass", True))
                and bool(method_j_gate.get("pass", False))
                == bool(resolution_rule.get("method_j_pass", False))
                and bool(method_k_gate.get("pass", False))
                == bool(resolution_rule.get("method_k_pass", False))
            )

            if not method_f_gate.get("pass", False):
                resolution_class = "reverse_signal_reopen_candidate"
                recommendation = "Re-run Method F with expanded mechanism families before closure updates."
            elif method_j_gate.get("pass", False) and method_k_gate.get("pass", False):
                resolution_class = "weakened_signals_confirmed_keep_tension"
                recommendation = (
                    "Keep closure in tension; J/K weakening persists under strict controls."
                )
            elif (not method_j_gate.get("pass", False)) and (not method_k_gate.get("pass", False)):
                resolution_class = "closure_upgrade_candidate"
                recommendation = (
                    "Re-run Stage 4 synthesis with a closure-upgrade candidate posture."
                )
            else:
                resolution_class = "partial_resolution_inconclusive"
                recommendation = (
                    "One weakened method persists; collect an independent adjudicating test family."
                )

            summary = {
                "status": "ok",
                "stage": "10.5",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "elapsed_seconds": time.perf_counter() - run_start,
                "method_f_gate": method_f_gate,
                "method_j_gate": method_j_gate,
                "method_k_gate": method_k_gate,
                "closure_upgrade_rule_satisfied": closure_upgrade_rule_satisfied,
                "resolution_class": resolution_class,
                "recommendation": recommendation,
                "gate_config_path": str(gate_config_path),
            }

            saved_summary = ProvenanceWriter.save_results(
                summary,
                Path("results/data/phase10_admissibility/stage5_high_roi_summary.json"),
            )
            artifacts["stage5_summary"] = saved_summary["latest_path"]

            report_path = Path(
                "results/reports/phase10_admissibility/PHASE_10_STAGE5_HIGH_ROI.md"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                _build_stage5_markdown(
                    summary=summary,
                    artifacts=artifacts,
                    status_path=str(status_path),
                ),
                encoding="utf-8",
            )

            _set_step(
                status,
                "stage5_summary",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_summary["latest_path"],
                report=str(report_path),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 5 summary step complete")

        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)
        _log("Stage 5 run completed")

        summary_table = Table(title="Phase 10 Stage 5 High-ROI Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Method F gate", str(summary["method_f_gate"]["pass"]))
        summary_table.add_row("Method J strict gate", str(summary["method_j_gate"]["pass"]))
        summary_table.add_row("Method K strict gate", str(summary["method_k_gate"]["pass"]))
        summary_table.add_row("Resolution class", str(summary["resolution_class"]))
        summary_table.add_row(
            "Upgrade rule satisfied", str(summary["closure_upgrade_rule_satisfied"])
        )
        summary_table.add_row("Elapsed (s)", f"{float(summary.get('elapsed_seconds', 0.0)):.1f}")
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(
            f"[green]Method F matrix artifact:[/green] "
            f"{artifacts.get('method_f_matrix', 'n/a')}"
        )
        console.print(
            f"[green]J/K strict artifact:[/green] "
            f"{artifacts.get('jk_recalibration', 'n/a')}"
        )
        console.print(
            f"[green]Stage 5 summary artifact:[/green] "
            f"{artifacts.get('stage5_summary', 'n/a')}"
        )

        store.save_run(run)


if __name__ == "__main__":
    run_stage5(parse_args())
