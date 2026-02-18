#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 4 synthesis and closure update outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
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
from phase10_admissibility.stage4_pipeline import (
    Stage4Config,
    build_phase10_closure_update_markdown,
    build_phase10_results_markdown,
    now_utc_iso,
    synthesize_stage4,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 10 Stage 4 synthesis.")
    parser.add_argument(
        "--stage1-summary-path",
        type=str,
        default="results/data/phase10_admissibility/stage1_summary.json",
    )
    parser.add_argument(
        "--stage1b-path",
        type=str,
        default="results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json",
    )
    parser.add_argument(
        "--stage2-summary-path",
        type=str,
        default="results/data/phase10_admissibility/stage2_summary.json",
    )
    parser.add_argument(
        "--stage3-summary-path",
        type=str,
        default="results/data/phase10_admissibility/stage3_summary.json",
    )
    parser.add_argument(
        "--stage3-priority-path",
        type=str,
        default="results/data/phase10_admissibility/stage3_priority_gate.json",
    )
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage4_execution_status.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run synthesis even when Stage 4 status is already completed.",
    )
    return parser.parse_args()


def _default_status() -> dict[str, Any]:
    now = now_utc_iso()
    return {
        "phase": "10.4",
        "stage": "Stage 4",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "steps": {
            "synthesis": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "results_report": None,
                "closure_report": None,
                "error": None,
            }
        },
    }


def _load_status(path: Path, force: bool) -> dict[str, Any]:
    if not path.exists() or force:
        return _default_status()
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


def _load_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    nested = results.get("summary")
    if isinstance(nested, dict):
        return nested
    return results


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def run_stage4(args: argparse.Namespace) -> None:
    status_path = Path(args.status_path)
    status = _load_status(status_path, args.force)

    if (
        status.get("status") == "completed"
        and not args.force
        and status["steps"]["synthesis"].get("artifact")
    ):
        console.print("[cyan]Stage 4 already completed; reuse existing synthesis artifacts.[/cyan]")
        console.print(f"[green]Status tracker:[/green] {status_path}")
        return

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 4 Runner[/bold blue]\n"
            "Compiling final synthesis and closure update reports",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_phase10_stage4_synthesis", "seed": 42}) as run:
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        _set_step(status, "synthesis", "running", started_at=now_utc_iso(), error=None)
        _save_status(status_path, status)
        _log("Loading stage summaries and priority gate artifacts")

        stage1_summary = _load_summary(Path(args.stage1_summary_path))
        stage1b = _load_summary(Path(args.stage1b_path))
        stage2_summary = _load_summary(Path(args.stage2_summary_path))
        stage3_summary = _load_summary(Path(args.stage3_summary_path))
        stage3_priority = _load_summary(Path(args.stage3_priority_path))

        synthesis = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary=stage1_summary,
            stage1b_replication=stage1b,
            stage2_summary=stage2_summary,
            stage3_summary=stage3_summary,
            stage3_priority_gate=stage3_priority,
        )
        _log(
            "Synthesis decision: "
            f"aggregate={synthesis.get('aggregate_class')}, "
            f"closure_status={synthesis.get('closure_status')}, "
            f"priority={synthesis.get('urgent_designation', {}).get('priority')}"
        )

        saved = ProvenanceWriter.save_results(
            synthesis,
            Path("results/data/phase10_admissibility/stage4_synthesis.json"),
        )

        report_dir = Path("results/reports/phase10_admissibility")
        report_dir.mkdir(parents=True, exist_ok=True)
        results_report = report_dir / "PHASE_10_RESULTS.md"
        closure_report = report_dir / "PHASE_10_CLOSURE_UPDATE.md"

        artifacts = {
            "stage4": saved["latest_path"],
            "stage1": args.stage1_summary_path,
            "stage1b": args.stage1b_path,
            "stage2": args.stage2_summary_path,
            "stage3": args.stage3_summary_path,
        }
        results_report.write_text(
            build_phase10_results_markdown(
                synthesis=synthesis,
                artifacts=artifacts,
                status_path=str(status_path),
            ),
            encoding="utf-8",
        )
        closure_report.write_text(
            build_phase10_closure_update_markdown(synthesis),
            encoding="utf-8",
        )
        _log("Stage 4 reports written")

        _set_step(
            status,
            "synthesis",
            "completed",
            completed_at=now_utc_iso(),
            artifact=saved["latest_path"],
            results_report=str(results_report),
            closure_report=str(closure_report),
            error=None,
        )
        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)
        _log("Stage 4 completed")

        summary_table = Table(title="Phase 10 Stage 4 Synthesis")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Aggregate class", str(synthesis.get("aggregate_class")))
        summary_table.add_row("Closure status", str(synthesis.get("closure_status")))
        summary_table.add_row(
            "Priority gate meaning",
            str(synthesis.get("urgent_designation", {}).get("priority")),
        )
        summary_table.add_row("Method H", str(synthesis.get("method_decisions", {}).get("H")))
        summary_table.add_row("Method J", str(synthesis.get("method_decisions", {}).get("J")))
        summary_table.add_row("Method K", str(synthesis.get("method_decisions", {}).get("K")))
        summary_table.add_row("Method G", str(synthesis.get("method_decisions", {}).get("G")))
        summary_table.add_row("Method I", str(synthesis.get("method_decisions", {}).get("I")))
        summary_table.add_row("Method F", str(synthesis.get("method_decisions", {}).get("F")))
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(f"[green]Synthesis artifact:[/green] {saved['latest_path']}")
        console.print(f"[green]Results report:[/green] {results_report}")
        console.print(f"[green]Closure update:[/green] {closure_report}")

        # Preserve run metadata in the same store used by prior stage runners.
        store = MetadataStore(DB_PATH)
        store.save_run(run)


if __name__ == "__main__":
    run_stage4(parse_args())

