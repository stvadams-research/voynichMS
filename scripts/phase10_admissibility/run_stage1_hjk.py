#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 1 (Methods H, J, K) with checkpointed resume support.
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

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase10_admissibility.stage1_pipeline import (  # noqa: E402
    Stage1Config,
    build_reference_generators,
    build_stage1_markdown,
    generate_bundle_from_generator,
    load_dataset_bundle,
    now_utc_iso,
    run_method_h,
    run_method_j,
    run_method_k,
    summarize_stage1,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 10 Stage 1 methods (H/J/K).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-tokens", type=int, default=120000)
    parser.add_argument("--method-j-null-runs", type=int, default=100)
    parser.add_argument("--method-k-runs", type=int, default=100)
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage1_execution_status.json",
    )
    parser.add_argument(
        "--methods",
        type=str,
        default="H,J,K",
        help="Comma-separated list of methods to run (e.g., 'J,K'). Default is all: 'H,J,K'.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run completed methods instead of resuming.",
    )
    return parser.parse_args()


def _default_status(config: Stage1Config) -> dict[str, Any]:
    now = now_utc_iso()
    return {
        "phase": "10.1",
        "stage": "Stage 1",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "seed": config.seed,
            "target_tokens": config.target_tokens,
            "method_j_null_runs": config.method_j_null_runs,
            "method_k_runs": config.method_k_runs,
        },
        "steps": {
            "method_h": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
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
            "stage1_summary": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
        },
    }


def _load_status(path: Path, config: Stage1Config, force: bool) -> dict[str, Any]:
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
    return payload.get("results")


def _load_optional_bundle(
    store: MetadataStore, dataset_id: str, label: str
) -> tuple[bool, Any]:
    try:
        bundle = load_dataset_bundle(store, dataset_id, label)
        if not bundle.tokens:
            return False, f"{dataset_id}: no tokens"
        return True, bundle
    except Exception as exc:  # pragma: no cover - defensive loader path
        return False, f"{dataset_id}: {exc}"


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def run_stage1(args: argparse.Namespace) -> None:
    config = Stage1Config(
        seed=args.seed,
        target_tokens=args.target_tokens,
        method_j_null_runs=args.method_j_null_runs,
        method_k_runs=args.method_k_runs,
    )
    status_path = Path(args.status_path)
    status = _load_status(status_path, config, args.force)
    status["config"] = {
        "seed": config.seed,
        "target_tokens": config.target_tokens,
        "method_j_null_runs": config.method_j_null_runs,
        "method_k_runs": config.method_k_runs,
    }

    requested_methods = {m.strip().upper() for m in args.methods.split(",")}
    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 1 Runner[/bold blue]\n"
            f"Executing Methods: {sorted(requested_methods)} with restart checkpoints",
            border_style="blue",
        )
    )
    _log(
        "Requested config: "
        f"seed={config.seed}, target_tokens={config.target_tokens}, "
        f"method_j_null_runs={config.method_j_null_runs}, method_k_runs={config.method_k_runs}, "
        f"force={args.force}"
    )

    with active_run(config={"command": "run_phase10_stage1_hjk", "seed": config.seed}) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        _log("Loading required datasets (Voynich and Latin)")
        voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich (Real)")
        _log(
            "Loaded Voynich bundle: "
            f"{len(voynich_bundle.tokens)} tokens, {len(voynich_bundle.lines)} lines, "
            f"{len(voynich_bundle.pages)} pages"
        )

        latin_ok, latin_payload = _load_optional_bundle(store, "latin_classic", "Latin (Semantic)")
        if latin_ok:
            latin_bundle = latin_payload
            _log(
                "Loaded Latin bundle: "
                f"{len(latin_bundle.tokens)} tokens, {len(latin_bundle.lines)} lines"
            )
        else:
            raise RuntimeError(f"Required dataset missing for Method K: {latin_payload}")

        method_results: dict[str, dict[str, Any]] = {}
        method_artifacts: dict[str, str] = {}

        # Method H
        if "H" in requested_methods:
            h_status = status["steps"]["method_h"]["status"]
            existing_h = _artifact_results(status["steps"]["method_h"]["artifact"])
            if h_status == "completed" and existing_h is not None and not args.force:
                method_results["H"] = existing_h
                method_artifacts["H"] = status["steps"]["method_h"]["artifact"]
                console.print("[cyan]Method H already complete; reusing prior artifact.[/cyan]")
                _log("Method H reused from checkpoint")
            else:
                _set_step(status, "method_h", "running", started_at=now_utc_iso(), error=None)
                _save_status(status_path, status)
                _log("Method H started")
                try:
                    comparison_ids = [
                        ("latin_classic", "Latin (Semantic)"),
                        ("self_citation", "Self-Citation"),
                        ("table_grille", "Table-Grille"),
                        ("mechanical_reuse", "Mechanical Reuse"),
                        ("shuffled_global", "Shuffled (Global)"),
                    ]
                    comparison_bundles = []
                    skipped = []
                    for dataset_id, label in comparison_ids:
                        ok, payload = _load_optional_bundle(store, dataset_id, label)
                        if ok:
                            comparison_bundles.append(payload)
                        else:
                            skipped.append(str(payload))

                    generators_h = build_reference_generators(voynich_bundle.lines, config.seed)
                    lines_per_page = max(
                        1,
                        int(round(len(voynich_bundle.lines) / max(len(voynich_bundle.pages), 1))),
                    )
                    for family, generator in generators_h.items():
                        comparison_bundles.append(
                            generate_bundle_from_generator(
                                generator=generator,
                                dataset_id=f"{family}_h",
                                label=f"{family} (generated)",
                                target_tokens=config.target_tokens,
                                lines_per_page=lines_per_page,
                            )
                        )

                    h_result = run_method_h(voynich_bundle, comparison_bundles)
                    h_result["skipped_comparison_datasets"] = skipped
                    save_h = ProvenanceWriter.save_results(
                        h_result,
                        Path("results/data/phase10_admissibility/method_h_typology.json"),
                    )
                    method_results["H"] = h_result
                    method_artifacts["H"] = save_h["latest_path"]
                    _set_step(
                        status,
                        "method_h",
                        "completed",
                        completed_at=now_utc_iso(),
                        artifact=save_h["latest_path"],
                        error=None,
                    )
                    _save_status(status_path, status)
                    _log(f"Method H complete: decision={h_result.get('decision')}")
                except Exception as exc:
                    _set_step(status, "method_h", "failed", error=str(exc))
                    status["status"] = "failed"
                    _save_status(status_path, status)
                    _log(f"Method H failed: {exc}")
                    raise
        else:
            # Use prior result if available
            existing_h = _artifact_results(status["steps"]["method_h"]["artifact"])
            if existing_h:
                method_results["H"] = existing_h
                method_artifacts["H"] = status["steps"]["method_h"]["artifact"]
                _log("Method H skipped (using prior artifact)")

        # Method J
        if "J" in requested_methods:
            j_status = status["steps"]["method_j"]["status"]
            existing_j = _artifact_results(status["steps"]["method_j"]["artifact"])
            if j_status == "completed" and existing_j is not None and not args.force:
                method_results["J"] = existing_j
                method_artifacts["J"] = status["steps"]["method_j"]["artifact"]
                console.print("[cyan]Method J already complete; reusing prior artifact.[/cyan]")
                _log("Method J reused from checkpoint")
            else:
                _set_step(status, "method_j", "running", started_at=now_utc_iso(), error=None)
                _save_status(status_path, status)
                _log("Method J started")
                try:
                    generators_j = build_reference_generators(voynich_bundle.lines, config.seed)
                    j_result = run_method_j(
                        voynich_bundle=voynich_bundle,
                        generators=generators_j,
                        target_tokens=config.target_tokens,
                        null_runs=config.method_j_null_runs,
                        seed=config.seed,
                        progress=_log,
                    )
                    save_j = ProvenanceWriter.save_results(
                        j_result,
                        Path("results/data/phase10_admissibility/method_j_steganographic.json"),
                    )
                    method_results["J"] = j_result
                    method_artifacts["J"] = save_j["latest_path"]
                    _set_step(
                        status,
                        "method_j",
                        "completed",
                        completed_at=now_utc_iso(),
                        artifact=save_j["latest_path"],
                        error=None,
                    )
                    _save_status(status_path, status)
                    _log(f"Method J complete: decision={j_result.get('decision')}")
                except Exception as exc:
                    _set_step(status, "method_j", "failed", error=str(exc))
                    status["status"] = "failed"
                    _save_status(status_path, status)
                    _log(f"Method J failed: {exc}")
                    raise
        else:
            existing_j = _artifact_results(status["steps"]["method_j"]["artifact"])
            if existing_j:
                method_results["J"] = existing_j
                method_artifacts["J"] = status["steps"]["method_j"]["artifact"]
                _log("Method J skipped (using prior artifact)")

        # Method K
        if "K" in requested_methods:
            k_status = status["steps"]["method_k"]["status"]
            existing_k = _artifact_results(status["steps"]["method_k"]["artifact"])
            if k_status == "completed" and existing_k is not None and not args.force:
                method_results["K"] = existing_k
                method_artifacts["K"] = status["steps"]["method_k"]["artifact"]
                console.print("[cyan]Method K already complete; reusing prior artifact.[/cyan]")
                _log("Method K reused from checkpoint")
            else:
                _set_step(status, "method_k", "running", started_at=now_utc_iso(), error=None)
                _save_status(status_path, status)
                _log("Method K started")
                try:
                    k_result = run_method_k(
                        voynich_bundle=voynich_bundle,
                        latin_bundle=latin_bundle,
                        target_tokens=config.target_tokens,
                        num_runs=config.method_k_runs,
                        seed=config.seed,
                        progress=_log,
                    )
                    save_k = ProvenanceWriter.save_results(
                        k_result,
                        Path("results/data/phase10_admissibility/method_k_residual_gap.json"),
                    )
                    method_results["K"] = k_result
                    method_artifacts["K"] = save_k["latest_path"]
                    _set_step(
                        status,
                        "method_k",
                        "completed",
                        completed_at=now_utc_iso(),
                        artifact=save_k["latest_path"],
                        error=None,
                    )
                    _save_status(status_path, status)
                    _log(f"Method K complete: decision={k_result.get('decision')}")
                except Exception as exc:
                    _set_step(status, "method_k", "failed", error=str(exc))
                    status["status"] = "failed"
                    _save_status(status_path, status)
                    _log(f"Method K failed: {exc}")
                    raise
        else:
            existing_k = _artifact_results(status["steps"]["method_k"]["artifact"])
            if existing_k:
                method_results["K"] = existing_k
                method_artifacts["K"] = status["steps"]["method_k"]["artifact"]
                _log("Method K skipped (using prior artifact)")

        # Stage summary
        _set_step(status, "stage1_summary", "running", started_at=now_utc_iso(), error=None)
        _save_status(status_path, status)
        _log("Building Stage 1 summary artifacts")
        summary = summarize_stage1(method_results)
        summary["run_id"] = str(run.run_id)
        save_stage = ProvenanceWriter.save_results(
            {
                "summary": summary,
                "method_artifacts": method_artifacts,
            },
            Path("results/data/phase10_admissibility/stage1_summary.json"),
        )
        method_artifacts["stage1"] = save_stage["latest_path"]

        report = build_stage1_markdown(summary, method_artifacts, str(status_path))
        report_path = Path("results/reports/phase10_admissibility/PHASE_10_STAGE1_RESULTS.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

        _set_step(
            status,
            "stage1_summary",
            "completed",
            completed_at=now_utc_iso(),
            artifact=save_stage["latest_path"],
            error=None,
        )
        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)
        _log(
            "Stage 1 complete: "
            f"decision={summary.get('stage_decision')} "
            f"elapsed={time.perf_counter() - run_start:.1f}s"
        )

        summary_table = Table(title="Phase 10 Stage 1 Decisions")
        summary_table.add_column("Method", style="cyan")
        summary_table.add_column("Decision", style="bold")
        summary_table.add_row("H", method_results.get("H", {}).get("decision", "skipped"))
        summary_table.add_row("J", method_results.get("J", {}).get("decision", "skipped"))
        summary_table.add_row("K", method_results.get("K", {}).get("decision", "skipped"))
        summary_table.add_row("Stage 1", summary.get("stage_decision", "n/a"))
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print(f"[green]Stage report:[/green] {report_path}")

        store.save_run(run)


if __name__ == "__main__":
    run_stage1(parse_args())
