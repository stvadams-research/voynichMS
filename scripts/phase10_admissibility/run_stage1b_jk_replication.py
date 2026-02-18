#!/usr/bin/env python3
# ruff: noqa: E402
"""
Phase 10 Stage 1b: Multi-seed replication and gate evaluation for Methods J/K.
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

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 10 Stage 1b J/K multi-seed replication and gates."
    )
    parser.add_argument("--seeds", type=str, default="42,77,101")
    parser.add_argument("--target-tokens", type=int, default=30000)
    parser.add_argument("--method-j-null-runs", type=int, default=100)
    parser.add_argument("--method-k-runs", type=int, default=100)
    parser.add_argument(
        "--gate-config",
        type=str,
        default="configs/phase10_admissibility/stage1b_upgrade_gate.json",
    )
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage1b_jk_replication_status.json",
    )
    return parser.parse_args()


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def _parse_seeds(raw: str) -> list[int]:
    seeds = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not seeds:
        raise ValueError("At least one seed is required")
    return seeds


def _load_gate_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _default_status(
    seeds: list[int],
    target_tokens: int,
    method_j_null_runs: int,
    method_k_runs: int,
    gate_config_path: str,
) -> dict[str, Any]:
    now = now_utc_iso()
    return {
        "phase": "10.1b",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "seeds": seeds,
            "target_tokens": target_tokens,
            "method_j_null_runs": method_j_null_runs,
            "method_k_runs": method_k_runs,
            "gate_config_path": gate_config_path,
        },
        "seeds": {
            str(seed): {
                "method_j": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "artifact": None,
                    "decision": None,
                    "error": None,
                },
                "method_k": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "artifact": None,
                    "decision": None,
                    "error": None,
                },
            }
            for seed in seeds
        },
        "aggregate": {
            "status": "pending",
            "artifact": None,
            "report": None,
        },
    }


def _save_status(path: Path, status: dict[str, Any]) -> None:
    status["updated_at"] = now_utc_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _unwrap_results(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _pending_method_state() -> dict[str, Any]:
    return {
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "artifact": None,
        "decision": None,
        "error": None,
    }


def _load_or_initialize_status(path: Path, default_status: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default_status
    try:
        status = _load_json(path)
    except Exception:
        return default_status
    if status.get("phase") != "10.1b":
        return default_status
    return status


def _status_config_matches(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return expected.get("config") == observed.get("config")


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
    required_direction: str,
    correlation_threshold: float,
    min_consistent_outliers: int,
) -> dict[str, Any]:
    seeds = sorted(by_seed.keys())
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
    pass_gate = (
        required_direction_met
        and correlation_all_pass
        and len(hard_to_close_consistent) >= min_consistent_outliers
    )

    return {
        "per_seed": {str(seed): seed_eval[seed] for seed in seeds},
        "direction_consensus": direction_consensus,
        "consensus_direction": consensus_direction,
        "required_direction": required_direction,
        "required_direction_met": required_direction_met,
        "same_outlier_set": same_outlier_set,
        "common_outlier_features": sorted(common_features),
        "consistent_sign_features": consistent_sign_features,
        "languageward_consistent_features": languageward_consistent,
        "hard_to_close_consistent_features": hard_to_close_consistent,
        "correlation_threshold": correlation_threshold,
        "correlation_all_pass": correlation_all_pass,
        "min_consistent_outliers": min_consistent_outliers,
        "pass": pass_gate,
    }


def _evaluate_method_j_multiseed(
    by_seed: dict[int, dict[str, Any]],
    required_direction: str,
    z_threshold: float,
    min_stable_non_edge_anomalies: int,
    edge_rules: set[str],
) -> dict[str, Any]:
    seeds = sorted(by_seed.keys())

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


def _build_markdown_report(results: dict[str, Any], status_path: str) -> str:
    summary = results["summary"]
    method_j = results["method_j"]
    method_k = results["method_k"]

    lines = [
        "# Phase 10 Stage 1b Replication (Methods J/K)",
        "",
        f"Generated: {summary['generated_at']}",
        f"Run ID: {summary['run_id']}",
        f"Seeds: {summary['seeds']}",
        "",
        "## Multi-Seed Direction Consensus",
        "",
        f"- Method J consensus direction: `{method_j['consensus_direction']}`",
        f"- Method K consensus direction: `{method_k['consensus_direction']}`",
        f"- Method J gate pass: `{method_j['pass']}`",
        f"- Method K gate pass: `{method_k['pass']}`",
        "",
        "## Method J Ablation Outcome",
        "",
        "- Edge rules removed for ablation: "
        f"`{', '.join(method_j['edge_rules'])}`",
        "- Gate definition: stable |z| > threshold non-edge anomalies must remain "
        "under folio-order permutation stability",
        "",
        "## Method K Robustness Outcome",
        "",
        "- Requires consistent outlier sign across seeds, correlated residuals, and "
        "persistent hard-to-close language-ward residual features",
        f"- Correlation all-pass: `{method_k['correlation_all_pass']}`",
        "",
        "## Upgrade Gate Summary",
        "",
        f"- Method J stays weakened: `{method_j['pass']}`",
        f"- Method K stays weakened: `{method_k['pass']}`",
        f"- Priority recommendation: `{summary['next_stage_priority']}`",
        "",
        "## Artifacts",
        "",
        f"- Canonical replication artifact: `{summary.get('artifact_path', 'n/a')}`",
        f"- Status tracker: `{status_path}`",
        "",
    ]
    return "\n".join(lines)


def run_replication(args: argparse.Namespace) -> None:
    seeds = _parse_seeds(args.seeds)
    gate_config_path = Path(args.gate_config)
    gate_config = _load_gate_config(gate_config_path)

    status_path = Path(args.status_path)
    default_status = _default_status(
        seeds=seeds,
        target_tokens=args.target_tokens,
        method_j_null_runs=args.method_j_null_runs,
        method_k_runs=args.method_k_runs,
        gate_config_path=str(gate_config_path),
    )
    status = _load_or_initialize_status(status_path, default_status)
    if not _status_config_matches(default_status, status):
        _log("Existing status config mismatch; starting a fresh status checkpoint.")
        status = default_status
    elif status_path.exists():
        _log(f"Loaded existing status checkpoint: {status_path}")

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 1b J/K Replication[/bold blue]\n"
            "Multi-seed replication with pre-registered upgrade gates",
            border_style="blue",
        )
    )
    _log(
        "Requested config: "
        f"seeds={seeds}, target_tokens={args.target_tokens}, "
        f"method_j_null_runs={args.method_j_null_runs}, method_k_runs={args.method_k_runs}"
    )

    with active_run(
        config={"command": "run_phase10_stage1b_jk_replication", "seed": seeds[0]}
    ) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich (Real)")
        latin_bundle = load_dataset_bundle(store, "latin_classic", "Latin (Semantic)")
        _log(
            "Loaded bundles: "
            f"Voynich tokens={len(voynich_bundle.tokens)}, Latin tokens={len(latin_bundle.tokens)}"
        )

        method_j_by_seed: dict[int, dict[str, Any]] = {}
        method_k_by_seed: dict[int, dict[str, Any]] = {}
        method_artifacts: dict[str, Any] = {"method_j": {}, "method_k": {}}

        for seed in seeds:
            seed_key = str(seed)
            seed_status = status["seeds"].setdefault(
                seed_key,
                {
                    "method_j": _pending_method_state(),
                    "method_k": _pending_method_state(),
                },
            )
            seed_status.setdefault("method_j", _pending_method_state())
            seed_status.setdefault("method_k", _pending_method_state())

            method_j_state = seed_status["method_j"]
            method_j_artifact = method_j_state.get("artifact")
            if (
                method_j_state.get("status") == "completed"
                and isinstance(method_j_artifact, str)
                and Path(method_j_artifact).exists()
            ):
                _log(f"Seed {seed}: Method J already completed; reusing {method_j_artifact}")
                j_result = _unwrap_results(_load_json(Path(method_j_artifact)))
                method_j_by_seed[seed] = j_result
                method_artifacts["method_j"][seed_key] = method_j_artifact
            else:
                _log(f"Seed {seed}: starting Method J")
                method_j_state["status"] = "running"
                method_j_state["started_at"] = now_utc_iso()
                _save_status(status_path, status)

                try:
                    generators_j = build_reference_generators(voynich_bundle.lines, seed)
                    j_result = run_method_j(
                        voynich_bundle=voynich_bundle,
                        generators=generators_j,
                        target_tokens=args.target_tokens,
                        null_runs=args.method_j_null_runs,
                        seed=seed,
                        progress=lambda m, s=seed: _log(f"[seed {s}] {m}"),
                    )
                    method_j_by_seed[seed] = j_result
                    save_j = ProvenanceWriter.save_results(
                        j_result,
                        Path(f"results/data/phase10_admissibility/method_j_seed_{seed}.json"),
                    )
                    method_artifacts["method_j"][seed_key] = save_j["latest_path"]
                    seed_status["method_j"].update(
                        {
                            "status": "completed",
                            "completed_at": now_utc_iso(),
                            "artifact": save_j["latest_path"],
                            "decision": j_result.get("decision"),
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method J complete ({j_result.get('decision')})")
                except Exception as exc:
                    seed_status["method_j"].update(
                        {
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                    status["status"] = "failed"
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method J failed ({exc})")
                    raise

            method_k_state = seed_status["method_k"]
            method_k_artifact = method_k_state.get("artifact")
            if (
                method_k_state.get("status") == "completed"
                and isinstance(method_k_artifact, str)
                and Path(method_k_artifact).exists()
            ):
                _log(f"Seed {seed}: Method K already completed; reusing {method_k_artifact}")
                k_result = _unwrap_results(_load_json(Path(method_k_artifact)))
                method_k_by_seed[seed] = k_result
                method_artifacts["method_k"][seed_key] = method_k_artifact
            else:
                _log(f"Seed {seed}: starting Method K")
                method_k_state["status"] = "running"
                method_k_state["started_at"] = now_utc_iso()
                _save_status(status_path, status)

                try:
                    k_result = run_method_k(
                        voynich_bundle=voynich_bundle,
                        latin_bundle=latin_bundle,
                        target_tokens=args.target_tokens,
                        num_runs=args.method_k_runs,
                        seed=seed,
                        progress=lambda m, s=seed: _log(f"[seed {s}] {m}"),
                    )
                    method_k_by_seed[seed] = k_result
                    save_k = ProvenanceWriter.save_results(
                        k_result,
                        Path(f"results/data/phase10_admissibility/method_k_seed_{seed}.json"),
                    )
                    method_artifacts["method_k"][seed_key] = save_k["latest_path"]
                    seed_status["method_k"].update(
                        {
                            "status": "completed",
                            "completed_at": now_utc_iso(),
                            "artifact": save_k["latest_path"],
                            "decision": k_result.get("decision"),
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method K complete ({k_result.get('decision')})")
                except Exception as exc:
                    seed_status["method_k"].update(
                        {
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                    status["status"] = "failed"
                    _save_status(status_path, status)
                    _log(f"Seed {seed}: Method K failed ({exc})")
                    raise

        j_cfg = gate_config["method_j"]
        k_cfg = gate_config["method_k"]
        j_multi = _evaluate_method_j_multiseed(
            by_seed=method_j_by_seed,
            required_direction=str(j_cfg["required_direction"]),
            z_threshold=float(j_cfg["z_threshold"]),
            min_stable_non_edge_anomalies=int(j_cfg["min_stable_non_edge_anomalies"]),
            edge_rules=set(j_cfg.get("edge_rules", sorted(METHOD_J_EDGE_RULES))),
        )
        k_multi = _evaluate_method_k_multiseed(
            by_seed=method_k_by_seed,
            required_direction=str(k_cfg["required_direction"]),
            correlation_threshold=float(k_cfg["correlation_threshold"]),
            min_consistent_outliers=int(k_cfg["min_consistent_outliers"]),
        )

        j_status_after_gate = "closure_weakened" if j_multi["pass"] else "indeterminate"
        k_status_after_gate = "closure_weakened" if k_multi["pass"] else "indeterminate"

        if j_status_after_gate == "closure_weakened" and k_status_after_gate == "closure_weakened":
            next_stage_priority = "10.2_then_10.3"
        else:
            next_stage_priority = "resolve_stage1b_inconclusive"

        aggregate = {
            "status": "ok",
            "generated_at": now_utc_iso(),
            "run_id": str(run.run_id),
            "seeds": seeds,
            "target_tokens": args.target_tokens,
            "method_j_null_runs": args.method_j_null_runs,
            "method_k_runs": args.method_k_runs,
            "gate_config_path": str(gate_config_path),
            "method_j_status_after_gate": j_status_after_gate,
            "method_k_status_after_gate": k_status_after_gate,
            "next_stage_priority": next_stage_priority,
            "elapsed_seconds": time.perf_counter() - run_start,
            "artifact_path": (
                "results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json"
            ),
            "method_j_directions": {
                str(seed): method_j_by_seed[seed].get("decision") for seed in seeds
            },
            "method_k_directions": {
                str(seed): method_k_by_seed[seed].get("decision") for seed in seeds
            },
        }

        replication_results = {
            "summary": aggregate,
            "gate_config": gate_config,
            "method_j": j_multi,
            "method_k": k_multi,
            "seed_artifacts": method_artifacts,
        }

        save_replication = ProvenanceWriter.save_results(
            replication_results,
            Path("results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json"),
        )
        aggregate["artifact_path"] = save_replication["latest_path"]
        report_text = _build_markdown_report(
            replication_results,
            status_path=str(status_path),
        )
        report_path = Path(
            "results/reports/phase10_admissibility/PHASE_10_STAGE1B_JK_REPLICATION.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")

        status["aggregate"] = {
            "status": "completed",
            "artifact": save_replication["latest_path"],
            "report": str(report_path),
        }
        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)

        _log(
            "Stage 1b complete: "
            f"method_j_status_after_gate={j_status_after_gate}, "
            f"method_k_status_after_gate={k_status_after_gate}, "
            f"next={next_stage_priority}, "
            f"elapsed={aggregate['elapsed_seconds']:.1f}s"
        )

        summary_table = Table(title="Phase 10 Stage 1b Gate Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Method J status after gate", j_status_after_gate)
        summary_table.add_row("Method K status after gate", k_status_after_gate)
        summary_table.add_row("Next priority", next_stage_priority)
        summary_table.add_row("Seeds", ", ".join(str(s) for s in seeds))
        summary_table.add_row("Target tokens", str(args.target_tokens))
        summary_table.add_row("J null runs", str(args.method_j_null_runs))
        summary_table.add_row("K runs", str(args.method_k_runs))
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(f"[green]Replication artifact:[/green] {save_replication['latest_path']}")
        console.print(f"[green]Replication report:[/green] {report_path}")

        store.save_run(run)


if __name__ == "__main__":
    run_replication(parse_args())
