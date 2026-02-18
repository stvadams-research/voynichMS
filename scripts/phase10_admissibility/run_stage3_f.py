#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 3 (Method F) with resume checkpoints.
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
from phase10_admissibility.stage3_pipeline import (
    Stage3Config,
    build_stage3_markdown,
    evaluate_stage3_priority_gate,
    now_utc_iso,
    run_method_f,
    summarize_stage3,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 10 Stage 3 Method F.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--token-start", type=int, default=0)
    parser.add_argument("--target-tokens", type=int, default=30000)
    parser.add_argument("--param-samples-per-family", type=int, default=10000)
    parser.add_argument("--null-sequences", type=int, default=1000)
    parser.add_argument("--perturbations-per-candidate", type=int, default=12)
    parser.add_argument("--max-outlier-probes", type=int, default=12)
    parser.add_argument("--null-block-min", type=int, default=2)
    parser.add_argument("--null-block-max", type=int, default=12)
    parser.add_argument("--symbol-alphabet-size", type=int, default=64)
    parser.add_argument(
        "--stage1-summary-path",
        type=str,
        default="results/data/phase10_admissibility/stage1_summary.json",
    )
    parser.add_argument(
        "--stage2-summary-path",
        type=str,
        default="results/data/phase10_admissibility/stage2_summary.json",
    )
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage3_execution_status.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run completed Stage 3 steps instead of resuming.",
    )
    return parser.parse_args()


def _default_status(config: Stage3Config) -> dict[str, Any]:
    now = now_utc_iso()
    return {
        "phase": "10.3",
        "stage": "Stage 3",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "seed": config.seed,
            "token_start": config.token_start,
            "target_tokens": config.target_tokens,
            "param_samples_per_family": config.param_samples_per_family,
            "null_sequences": config.null_sequences,
            "perturbations_per_candidate": config.perturbations_per_candidate,
            "max_outlier_probes": config.max_outlier_probes,
            "null_block_min": config.null_block_min,
            "null_block_max": config.null_block_max,
            "symbol_alphabet_size": config.symbol_alphabet_size,
        },
        "steps": {
            "priority_gate": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "method_f": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "stage3_summary": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "report": None,
                "error": None,
            },
        },
    }


def _load_status(path: Path, config: Stage3Config, force: bool) -> dict[str, Any]:
    if not path.exists() or force:
        return _default_status(config)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_status(path: Path, status: dict[str, Any]) -> None:
    status["updated_at"] = now_utc_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2)


def _set_step(status: dict[str, Any], step: str, step_status: str, **fields: Any) -> None:
    entry = status["steps"][step]
    entry["status"] = step_status
    for key, value in fields.items():
        entry[key] = value


def _artifact_results(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    artifact = Path(path)
    if not artifact.exists():
        return None
    with artifact.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    if isinstance(payload, dict):
        return payload
    return None


def _load_stage_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    # Stage 1 summary artifact nests under "summary"; Stage 2 is direct.
    nested = results.get("summary")
    if isinstance(nested, dict):
        return nested
    return results


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def run_stage3(args: argparse.Namespace) -> None:
    config = Stage3Config(
        seed=args.seed,
        token_start=args.token_start,
        target_tokens=args.target_tokens,
        param_samples_per_family=args.param_samples_per_family,
        null_sequences=args.null_sequences,
        perturbations_per_candidate=args.perturbations_per_candidate,
        max_outlier_probes=args.max_outlier_probes,
        null_block_min=args.null_block_min,
        null_block_max=args.null_block_max,
        symbol_alphabet_size=args.symbol_alphabet_size,
    )
    status_path = Path(args.status_path)
    status = _load_status(status_path, config, args.force)
    status["config"] = {
        "seed": config.seed,
        "token_start": config.token_start,
        "target_tokens": config.target_tokens,
        "param_samples_per_family": config.param_samples_per_family,
        "null_sequences": config.null_sequences,
        "perturbations_per_candidate": config.perturbations_per_candidate,
        "max_outlier_probes": config.max_outlier_probes,
        "null_block_min": config.null_block_min,
        "null_block_max": config.null_block_max,
        "symbol_alphabet_size": config.symbol_alphabet_size,
    }

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 3 Runner[/bold blue]\n"
            "Executing Method F (Reverse Mechanism Test) with restart checkpoints",
            border_style="blue",
        )
    )
    _log(
        "Requested config: "
        f"seed={config.seed}, token_start={config.token_start}, "
        f"target_tokens={config.target_tokens}, "
        f"param_samples_per_family={config.param_samples_per_family}, "
        f"null_sequences={config.null_sequences}, "
        f"perturbations_per_candidate={config.perturbations_per_candidate}, "
        f"max_outlier_probes={config.max_outlier_probes}, "
        f"null_block=({config.null_block_min},{config.null_block_max}), "
        f"symbol_alphabet_size={config.symbol_alphabet_size}, force={args.force}"
    )

    with active_run(config={"command": "run_phase10_stage3_f", "seed": config.seed}) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        method_artifacts: dict[str, str] = {}
        method_result: dict[str, Any] | None = None
        priority_gate_result: dict[str, Any] | None = None

        # Priority gate
        existing_priority = _artifact_results(status["steps"]["priority_gate"]["artifact"])
        if (
            status["steps"]["priority_gate"]["status"] == "completed"
            and existing_priority is not None
            and not args.force
        ):
            priority_gate_result = existing_priority
            method_artifacts["priority_gate"] = status["steps"]["priority_gate"]["artifact"]
            _log("Priority gate reused from checkpoint")
        else:
            _set_step(status, "priority_gate", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Priority gate started")
            stage1_summary = _load_stage_summary(Path(args.stage1_summary_path))
            stage2_summary = _load_stage_summary(Path(args.stage2_summary_path))
            priority_gate_result = evaluate_stage3_priority_gate(stage1_summary, stage2_summary)
            saved = ProvenanceWriter.save_results(
                priority_gate_result,
                Path("results/data/phase10_admissibility/stage3_priority_gate.json"),
            )
            method_artifacts["priority_gate"] = saved["latest_path"]
            _set_step(
                status,
                "priority_gate",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Priority gate complete ({priority_gate_result.get('priority')})")

        # Method F
        existing_f = _artifact_results(status["steps"]["method_f"]["artifact"])
        if (
            status["steps"]["method_f"]["status"] == "completed"
            and existing_f is not None
            and not args.force
        ):
            method_result = existing_f
            method_artifacts["F"] = status["steps"]["method_f"]["artifact"]
            _log("Method F reused from checkpoint")
        else:
            _set_step(status, "method_f", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Method F started")
            method_result = run_method_f(
                store=store,
                config=config,
                progress=lambda msg: _log(f"[method_f] {msg}"),
            )
            saved = ProvenanceWriter.save_results(
                method_result,
                Path("results/data/phase10_admissibility/method_f_reverse_mechanism.json"),
            )
            method_artifacts["F"] = saved["latest_path"]
            _set_step(
                status,
                "method_f",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Method F complete ({method_result.get('decision')})")

        # Stage summary
        existing_stage = _artifact_results(status["steps"]["stage3_summary"]["artifact"])
        if (
            status["steps"]["stage3_summary"]["status"] == "completed"
            and existing_stage is not None
            and not args.force
        ):
            summary = existing_stage
            method_artifacts["stage3"] = status["steps"]["stage3_summary"]["artifact"]
            _log("Stage 3 summary reused from checkpoint")
        else:
            _set_step(status, "stage3_summary", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Stage 3 summary started")
            summary = summarize_stage3(
                priority_gate=priority_gate_result or {},
                method_f_result=method_result or {},
            )
            summary["elapsed_seconds"] = time.perf_counter() - run_start
            saved = ProvenanceWriter.save_results(
                summary,
                Path("results/data/phase10_admissibility/stage3_summary.json"),
            )
            method_artifacts["stage3"] = saved["latest_path"]
            report_text = build_stage3_markdown(
                summary=summary,
                method_artifacts=method_artifacts,
                status_path=str(status_path),
            )
            report_path = Path("results/reports/phase10_admissibility/PHASE_10_STAGE3_RESULTS.md")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
            _set_step(
                status,
                "stage3_summary",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                report=str(report_path),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 3 summary complete")

        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)

        summary_table = Table(title="Phase 10 Stage 3 Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Priority gate", str(priority_gate_result.get("priority")))
        summary_table.add_row("Method F", str(method_result.get("decision")))
        summary_table.add_row("Stage decision", str(summary.get("stage_decision")))
        summary_table.add_row("Param samples / family", str(config.param_samples_per_family))
        summary_table.add_row("Null sequences", str(config.null_sequences))
        summary_table.add_row("Elapsed (s)", f"{float(summary.get('elapsed_seconds', 0.0)):.1f}")
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(
            f"[green]Priority gate artifact:[/green] {method_artifacts.get('priority_gate', 'n/a')}"
        )
        console.print(f"[green]Method F artifact:[/green] {method_artifacts.get('F', 'n/a')}")
        console.print(
            f"[green]Stage 3 summary artifact:[/green] {method_artifacts.get('stage3', 'n/a')}"
        )
        store.save_run(run)


if __name__ == "__main__":
    run_stage3(parse_args())
