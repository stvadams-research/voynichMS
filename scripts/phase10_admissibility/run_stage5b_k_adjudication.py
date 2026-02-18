#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 5b targeted Method K adjudication.

Purpose:
- Close the remaining Method K angle without rerunning full Stage 5.
- Focus on seed-threshold instability and direction consensus.
"""

from __future__ import annotations

import argparse
import json
import statistics
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
from phase10_admissibility.stage1_pipeline import load_dataset_bundle, now_utc_iso, run_method_k

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run targeted Method K adjudication with resume checkpoints."
    )
    parser.add_argument(
        "--gate-config",
        type=str,
        default="configs/phase10_admissibility/stage5b_k_adjudication_gate.json",
    )
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage5b_k_adjudication_status.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run all steps even if checkpoints exist.",
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
    return {
        "phase": "10.5b",
        "stage": "Stage 5b",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "gate_config_path": gate_config_path,
            "focal_seed": gate_config.get("focal_seed"),
            "focal_num_runs": gate_config.get("focal_num_runs", []),
            "seed_band": gate_config.get("seed_band", []),
            "seed_band_runs": gate_config.get("seed_band_runs"),
            "correlation_threshold": gate_config.get("correlation_threshold"),
            "required_direction": gate_config.get("required_direction"),
            "min_language_hard_features": gate_config.get("min_language_hard_features"),
            "min_seed_pass_rate_for_weakened": gate_config.get(
                "min_seed_pass_rate_for_weakened"
            ),
        },
        "steps": {
            "focal_depth": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "seed_band": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "summary": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "report": None,
                "error": None,
            },
        },
        "focal_runs": {},
        "seed_runs": {},
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
    if status.get("phase") != "10.5b":
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


def _count_language_hard_features(method_k_result: dict[str, Any]) -> int:
    outliers = list(method_k_result.get("outlier_features", []))
    direction = method_k_result.get("direction_to_language", {})
    difficulty = method_k_result.get("modification_difficulty", {})
    robust = [
        feature
        for feature in outliers
        if bool(direction.get(feature, {}).get("toward_language", False))
        and difficulty.get(feature, {}).get("difficulty") == "hard_framework_shift"
    ]
    return len(robust)


def _evaluate_single_run(method_k_result: dict[str, Any], gate_config: dict[str, Any]) -> dict[str, Any]:
    decision = str(method_k_result.get("decision", "unknown"))
    correlation = float(method_k_result.get("outlier_mean_abs_correlation", 0.0))
    correlation_threshold = float(gate_config.get("correlation_threshold", 0.4))
    required_direction = str(gate_config.get("required_direction", "closure_weakened"))
    min_language_hard = int(gate_config.get("min_language_hard_features", 3))
    language_hard = _count_language_hard_features(method_k_result)

    decision_pass = decision == required_direction
    correlation_pass = correlation >= correlation_threshold
    language_hard_pass = language_hard >= min_language_hard
    pass_single = decision_pass and correlation_pass and language_hard_pass

    return {
        "decision": decision,
        "correlation": correlation,
        "correlation_threshold": correlation_threshold,
        "correlation_pass": correlation_pass,
        "required_direction": required_direction,
        "decision_pass": decision_pass,
        "language_hard_count": language_hard,
        "min_language_hard_features": min_language_hard,
        "language_hard_pass": language_hard_pass,
        "pass": pass_single,
    }


def _load_reusable_high_roi_seed(seed: int, expected_runs: int, target_tokens: int) -> dict[str, Any] | None:
    candidate = Path(f"results/data/phase10_admissibility/method_k_high_roi_seed_{seed}.json")
    if not candidate.exists():
        return None
    payload = _artifact_results(str(candidate))
    if not isinstance(payload, dict):
        return None
    config = payload.get("config", {})
    if int(config.get("num_runs", -1)) != expected_runs:
        return None
    if int(config.get("target_tokens", -1)) != target_tokens:
        return None
    return payload


def _build_stage5b_markdown(summary: dict[str, Any], artifacts: dict[str, str], status_path: str) -> str:
    lines = [
        "# Phase 10 Stage 5b Method K Adjudication",
        "",
        f"Generated: {summary['generated_at']}",
        f"Run ID: {summary['run_id']}",
        "",
        "## Adjudication Outcome",
        "",
        f"- Final adjudication: `{summary['final_adjudication']}`",
        f"- Focal seed: `{summary['focal_seed']}`",
        f"- Focal depth passes: `{summary['focal_pass']}`",
        f"- Seed-band pass rate: `{summary['seed_band_pass_rate']:.3f}`",
        f"- Seed-band threshold: `{summary['min_seed_pass_rate_for_weakened']:.3f}`",
        "",
        "## Notes",
        "",
        f"- Decision rationale: {summary['decision_rationale']}",
        "",
        "## Artifacts",
        "",
        f"- Focal-depth artifact: `{artifacts.get('focal_depth', 'n/a')}`",
        f"- Seed-band artifact: `{artifacts.get('seed_band', 'n/a')}`",
        f"- Stage 5b summary artifact: `{artifacts.get('summary', 'n/a')}`",
        f"- Status tracker: `{status_path}`",
        "",
    ]
    return "\n".join(lines)


def run_stage5b(args: argparse.Namespace) -> None:
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
            "[bold blue]Phase 10 Stage 5b Runner[/bold blue]\n"
            "Targeted Method K adjudication with restart checkpoints",
            border_style="blue",
        )
    )
    _log(f"Using gate config: {gate_config_path} | force={args.force}")

    target_tokens = int(gate_config.get("target_tokens", 30000))
    focal_seed = int(gate_config.get("focal_seed", 77))
    focal_num_runs = [int(v) for v in gate_config.get("focal_num_runs", [300])]
    seed_band = [int(v) for v in gate_config.get("seed_band", [42, 77, 101])]
    seed_band_runs = int(gate_config.get("seed_band_runs", 150))

    with active_run(config={"command": "run_phase10_stage5b_k_adjudication", "seed": focal_seed}) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich (Real)")
        latin_bundle = load_dataset_bundle(store, "latin_classic", "Latin (Semantic)")
        _log(
            "Loaded bundles for K adjudication: "
            f"Voynich tokens={len(voynich_bundle.tokens)}, Latin tokens={len(latin_bundle.tokens)}"
        )

        artifacts: dict[str, str] = {}

        # Step 1: focal depth.
        existing_focal = _artifact_results(status["steps"]["focal_depth"].get("artifact"))
        if (
            status["steps"]["focal_depth"].get("status") == "completed"
            and existing_focal is not None
            and not args.force
        ):
            focal_results = existing_focal
            artifacts["focal_depth"] = status["steps"]["focal_depth"]["artifact"]
            _log("Focal-depth step reused from checkpoint")
        else:
            _set_step(
                status,
                "focal_depth",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Focal-depth step started for seed={focal_seed}, runs={focal_num_runs}")

            focal_runs: dict[str, dict[str, Any]] = {}
            focal_artifacts: dict[str, str] = {}
            for idx, num_runs in enumerate(focal_num_runs):
                run_key = f"seed{focal_seed}_runs{num_runs}"
                run_state = status["focal_runs"].setdefault(
                    run_key,
                    {
                        "status": "pending",
                        "started_at": None,
                        "completed_at": None,
                        "artifact": None,
                        "seed": focal_seed,
                        "num_runs": num_runs,
                        "error": None,
                    },
                )
                run_state["seed"] = focal_seed
                run_state["num_runs"] = num_runs

                existing = _artifact_results(run_state.get("artifact"))
                if (
                    run_state.get("status") == "completed"
                    and existing is not None
                    and not args.force
                ):
                    focal_runs[run_key] = existing
                    focal_artifacts[run_key] = str(run_state.get("artifact"))
                    _log(
                        f"Focal run reused ({idx + 1}/{len(focal_num_runs)}): "
                        f"{run_key}"
                    )
                    continue

                run_state.update(
                    {
                        "status": "running",
                        "started_at": now_utc_iso(),
                        "completed_at": None,
                        "error": None,
                    }
                )
                _save_status(status_path, status)
                _log(
                    f"Focal run started ({idx + 1}/{len(focal_num_runs)}): "
                    f"{run_key}"
                )

                try:
                    result = run_method_k(
                        voynich_bundle=voynich_bundle,
                        latin_bundle=latin_bundle,
                        target_tokens=target_tokens,
                        num_runs=num_runs,
                        seed=focal_seed,
                        progress=lambda msg, rk=run_key: _log(f"[k_focal:{rk}] {msg}"),
                    )
                    saved = ProvenanceWriter.save_results(
                        result,
                        Path(
                            "results/data/phase10_admissibility/"
                            f"method_k_adjudication_{run_key}.json"
                        ),
                    )
                    run_state.update(
                        {
                            "status": "completed",
                            "completed_at": now_utc_iso(),
                            "artifact": saved["latest_path"],
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)

                    focal_runs[run_key] = result
                    focal_artifacts[run_key] = saved["latest_path"]
                    _log(f"Focal run complete: {run_key} -> {result.get('decision')}")
                except Exception as exc:
                    run_state.update(
                        {
                            "status": "failed",
                            "completed_at": now_utc_iso(),
                            "error": str(exc),
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Focal run failed: {run_key} ({exc})")
                    raise

            focal_results = {
                "status": "ok",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "focal_seed": focal_seed,
                "focal_num_runs": focal_num_runs,
                "runs": focal_runs,
                "run_artifacts": focal_artifacts,
            }
            saved_focal = ProvenanceWriter.save_results(
                focal_results,
                Path("results/data/phase10_admissibility/stage5b_k_focal_depth.json"),
            )
            artifacts["focal_depth"] = saved_focal["latest_path"]
            _set_step(
                status,
                "focal_depth",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_focal["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log("Focal-depth step complete")

        # Step 2: seed-band.
        existing_seed_band = _artifact_results(status["steps"]["seed_band"].get("artifact"))
        if (
            status["steps"]["seed_band"].get("status") == "completed"
            and existing_seed_band is not None
            and not args.force
        ):
            seed_band_results = existing_seed_band
            artifacts["seed_band"] = status["steps"]["seed_band"]["artifact"]
            _log("Seed-band step reused from checkpoint")
        else:
            _set_step(
                status,
                "seed_band",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Seed-band step started: seeds={seed_band}, num_runs={seed_band_runs}")

            seed_runs: dict[str, dict[str, Any]] = {}
            seed_artifacts: dict[str, str] = {}

            for idx, seed in enumerate(seed_band):
                key = str(seed)
                seed_state = status["seed_runs"].setdefault(
                    key,
                    {
                        "status": "pending",
                        "started_at": None,
                        "completed_at": None,
                        "artifact": None,
                        "seed": seed,
                        "num_runs": seed_band_runs,
                        "source": "fresh",
                        "error": None,
                    },
                )
                seed_state["seed"] = seed
                seed_state["num_runs"] = seed_band_runs

                existing = _artifact_results(seed_state.get("artifact"))
                if (
                    seed_state.get("status") == "completed"
                    and existing is not None
                    and not args.force
                ):
                    seed_runs[key] = existing
                    seed_artifacts[key] = str(seed_state.get("artifact"))
                    _log(f"Seed-band run reused ({idx + 1}/{len(seed_band)}): seed={seed}")
                    continue

                reusable = _load_reusable_high_roi_seed(
                    seed=seed,
                    expected_runs=seed_band_runs,
                    target_tokens=target_tokens,
                )
                if reusable is not None and not args.force:
                    seed_runs[key] = reusable
                    reusable_path = (
                        f"results/data/phase10_admissibility/method_k_high_roi_seed_{seed}.json"
                    )
                    seed_artifacts[key] = reusable_path
                    seed_state.update(
                        {
                            "status": "completed",
                            "started_at": now_utc_iso(),
                            "completed_at": now_utc_iso(),
                            "artifact": reusable_path,
                            "source": "reused_stage5",
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)
                    _log(
                        f"Seed-band run reused from stage5 ({idx + 1}/{len(seed_band)}): "
                        f"seed={seed}"
                    )
                    continue

                seed_state.update(
                    {
                        "status": "running",
                        "started_at": now_utc_iso(),
                        "completed_at": None,
                        "source": "fresh",
                        "error": None,
                    }
                )
                _save_status(status_path, status)
                _log(f"Seed-band run started ({idx + 1}/{len(seed_band)}): seed={seed}")

                try:
                    result = run_method_k(
                        voynich_bundle=voynich_bundle,
                        latin_bundle=latin_bundle,
                        target_tokens=target_tokens,
                        num_runs=seed_band_runs,
                        seed=seed,
                        progress=lambda msg, s=seed: _log(f"[k_seed:{s}] {msg}"),
                    )
                    saved = ProvenanceWriter.save_results(
                        result,
                        Path(
                            "results/data/phase10_admissibility/"
                            f"method_k_adjudication_seed_{seed}_runs_{seed_band_runs}.json"
                        ),
                    )
                    seed_state.update(
                        {
                            "status": "completed",
                            "completed_at": now_utc_iso(),
                            "artifact": saved["latest_path"],
                            "source": "fresh",
                            "error": None,
                        }
                    )
                    _save_status(status_path, status)

                    seed_runs[key] = result
                    seed_artifacts[key] = saved["latest_path"]
                    _log(
                        f"Seed-band run complete ({idx + 1}/{len(seed_band)}): "
                        f"seed={seed} -> {result.get('decision')}"
                    )
                except Exception as exc:
                    seed_state.update(
                        {
                            "status": "failed",
                            "completed_at": now_utc_iso(),
                            "error": str(exc),
                        }
                    )
                    _save_status(status_path, status)
                    _log(f"Seed-band run failed: seed={seed} ({exc})")
                    raise

            seed_band_results = {
                "status": "ok",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "seed_band": seed_band,
                "seed_band_runs": seed_band_runs,
                "runs": seed_runs,
                "run_artifacts": seed_artifacts,
            }
            saved_seed_band = ProvenanceWriter.save_results(
                seed_band_results,
                Path("results/data/phase10_admissibility/stage5b_k_seed_band.json"),
            )
            artifacts["seed_band"] = saved_seed_band["latest_path"]
            _set_step(
                status,
                "seed_band",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_seed_band["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log("Seed-band step complete")

        # Step 3: summary.
        existing_summary = _artifact_results(status["steps"]["summary"].get("artifact"))
        if (
            status["steps"]["summary"].get("status") == "completed"
            and existing_summary is not None
            and not args.force
        ):
            summary = existing_summary
            artifacts["summary"] = status["steps"]["summary"]["artifact"]
            _log("Stage 5b summary reused from checkpoint")
        else:
            _set_step(
                status,
                "summary",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 5b summary step started")

            focal_eval = {}
            focal_passes = []
            focal_decisions = []
            focal_correlations = []
            focal_runs = focal_results.get("runs", {})
            for run_key, run_result in focal_runs.items():
                eval_row = _evaluate_single_run(run_result, gate_config)
                focal_eval[run_key] = eval_row
                focal_passes.append(bool(eval_row["pass"]))
                focal_decisions.append(str(eval_row["decision"]))
                focal_correlations.append(float(eval_row["correlation"]))

            focal_pass = all(focal_passes) if focal_passes else False
            focal_direction_stable = len(set(focal_decisions)) == 1 if focal_decisions else False

            seed_eval = {}
            seed_passes = []
            seed_decisions = []
            seed_correlations = []
            seed_runs = seed_band_results.get("runs", {})
            for seed in seed_band:
                row = seed_runs.get(str(seed), {})
                eval_row = _evaluate_single_run(row, gate_config)
                seed_eval[str(seed)] = eval_row
                seed_passes.append(bool(eval_row["pass"]))
                seed_decisions.append(str(eval_row["decision"]))
                seed_correlations.append(float(eval_row["correlation"]))

            pass_count = sum(1 for value in seed_passes if value)
            seed_count = len(seed_passes)
            pass_rate = float(pass_count / seed_count) if seed_count else 0.0
            min_pass_rate = float(gate_config.get("min_seed_pass_rate_for_weakened", 0.75))

            decision_counts: dict[str, int] = {}
            for decision in seed_decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1

            corr_mean = statistics.fmean(seed_correlations) if seed_correlations else 0.0
            corr_min = min(seed_correlations) if seed_correlations else 0.0
            corr_max = max(seed_correlations) if seed_correlations else 0.0

            if focal_pass and focal_direction_stable and pass_rate >= min_pass_rate:
                final_adjudication = "closure_weakened_supported"
                decision_rationale = (
                    "Focal depth run(s) passed and seed-band pass rate met the registered threshold."
                )
            else:
                final_adjudication = "indeterminate_confirmed"
                decision_rationale = (
                    "At least one registered criterion failed (focal pass/direction stability/"
                    "seed pass-rate), so K is not stable enough for closure-weakened status."
                )

            summary = {
                "status": "ok",
                "stage": "10.5b",
                "generated_at": now_utc_iso(),
                "run_id": str(run.run_id),
                "elapsed_seconds": time.perf_counter() - run_start,
                "gate_config_path": str(gate_config_path),
                "focal_seed": focal_seed,
                "focal_num_runs": focal_num_runs,
                "focal_eval": focal_eval,
                "focal_pass": focal_pass,
                "focal_direction_stable": focal_direction_stable,
                "seed_band": seed_band,
                "seed_band_runs": seed_band_runs,
                "seed_eval": seed_eval,
                "seed_band_pass_count": pass_count,
                "seed_band_count": seed_count,
                "seed_band_pass_rate": pass_rate,
                "min_seed_pass_rate_for_weakened": min_pass_rate,
                "seed_decision_counts": decision_counts,
                "seed_correlation_summary": {
                    "mean": corr_mean,
                    "min": corr_min,
                    "max": corr_max,
                },
                "final_adjudication": final_adjudication,
                "decision_rationale": decision_rationale,
            }

            saved_summary = ProvenanceWriter.save_results(
                summary,
                Path("results/data/phase10_admissibility/stage5b_k_adjudication_summary.json"),
            )
            artifacts["summary"] = saved_summary["latest_path"]

            report_path = Path(
                "results/reports/phase10_admissibility/PHASE_10_STAGE5B_K_ADJUDICATION.md"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                _build_stage5b_markdown(summary, artifacts, str(status_path)),
                encoding="utf-8",
            )

            _set_step(
                status,
                "summary",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved_summary["latest_path"],
                report=str(report_path),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 5b summary step complete")

        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)
        _log("Stage 5b run completed")

        summary_table = Table(title="Phase 10 Stage 5b K Adjudication Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Final adjudication", str(summary["final_adjudication"]))
        summary_table.add_row("Focal pass", str(summary["focal_pass"]))
        summary_table.add_row(
            "Focal direction stable", str(summary["focal_direction_stable"])
        )
        summary_table.add_row("Seed-band pass rate", f"{summary['seed_band_pass_rate']:.3f}")
        summary_table.add_row(
            "Seed-band threshold", f"{summary['min_seed_pass_rate_for_weakened']:.3f}"
        )
        summary_table.add_row(
            "Elapsed (s)", f"{float(summary.get('elapsed_seconds', 0.0)):.1f}"
        )
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(
            f"[green]Focal-depth artifact:[/green] {artifacts.get('focal_depth', 'n/a')}"
        )
        console.print(
            f"[green]Seed-band artifact:[/green] {artifacts.get('seed_band', 'n/a')}"
        )
        console.print(
            f"[green]Summary artifact:[/green] {artifacts.get('summary', 'n/a')}"
        )

        store.save_run(run)


if __name__ == "__main__":
    run_stage5b(parse_args())
