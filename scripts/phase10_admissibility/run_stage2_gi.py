#!/usr/bin/env python3
# ruff: noqa: E402
"""
Execute Phase 10 Stage 2 (Methods G, I) with resume checkpoints.
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
from phase10_admissibility.stage2_pipeline import (  # noqa: E402
    Stage2Config,
    build_cross_linguistic_manifest,
    build_illustration_features,
    build_stage2_markdown,
    now_utc_iso,
    run_method_g,
    run_method_i,
    scan_data_resource_inventory,
    summarize_stage2,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 10 Stage 2 methods (G/I).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scan-resolution", type=str, default="folios_2000")
    parser.add_argument(
        "--scan-fallbacks",
        type=str,
        default="folios_full,tiff,folios_1000",
    )
    parser.add_argument("--image-max-side", type=int, default=1400)
    parser.add_argument("--method-g-permutations", type=int, default=1000)
    parser.add_argument("--method-i-bootstrap", type=int, default=500)
    parser.add_argument("--method-i-min-languages", type=int, default=12)
    parser.add_argument("--language-token-cap", type=int, default=50000)
    parser.add_argument(
        "--status-path",
        type=str,
        default="results/data/phase10_admissibility/stage2_execution_status.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run completed steps instead of resuming.",
    )
    return parser.parse_args()


def _parse_fallbacks(raw: str) -> tuple[str, ...]:
    out = tuple(part.strip() for part in raw.split(",") if part.strip())
    return out if out else ("folios_full", "tiff", "folios_1000")


def _default_status(config: Stage2Config) -> dict[str, Any]:
    now = now_utc_iso()
    return {
        "phase": "10.2",
        "stage": "Stage 2",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "config": {
            "seed": config.seed,
            "scan_resolution": config.scan_resolution,
            "scan_fallbacks": list(config.scan_fallbacks),
            "image_max_side": config.image_max_side,
            "method_g_permutations": config.method_g_permutations,
            "method_i_bootstrap": config.method_i_bootstrap,
            "method_i_min_languages": config.method_i_min_languages,
            "language_token_cap": config.language_token_cap,
        },
        "steps": {
            "data_inventory": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "illustration_features": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "deliverable_path": "data/illustration_features.json",
                "error": None,
            },
            "cross_linguistic_manifest": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "deliverable_path": "data/corpora/cross_linguistic_manifest.json",
                "error": None,
            },
            "method_g": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "method_i": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "error": None,
            },
            "stage2_summary": {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact": None,
                "report": None,
                "error": None,
            },
        },
    }


def _load_status(path: Path, config: Stage2Config, force: bool) -> dict[str, Any]:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _log(message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def run_stage2(args: argparse.Namespace) -> None:
    config = Stage2Config(
        seed=args.seed,
        scan_resolution=args.scan_resolution,
        scan_fallbacks=_parse_fallbacks(args.scan_fallbacks),
        image_max_side=args.image_max_side,
        method_g_permutations=args.method_g_permutations,
        method_i_bootstrap=args.method_i_bootstrap,
        method_i_min_languages=args.method_i_min_languages,
        language_token_cap=args.language_token_cap,
    )
    status_path = Path(args.status_path)
    status = _load_status(status_path, config, args.force)
    status["config"] = {
        "seed": config.seed,
        "scan_resolution": config.scan_resolution,
        "scan_fallbacks": list(config.scan_fallbacks),
        "image_max_side": config.image_max_side,
        "method_g_permutations": config.method_g_permutations,
        "method_i_bootstrap": config.method_i_bootstrap,
        "method_i_min_languages": config.method_i_min_languages,
        "language_token_cap": config.language_token_cap,
    }

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Stage 2 Runner[/bold blue]\n"
            "Executing Method G and Method I with machine-extracted inputs",
            border_style="blue",
        )
    )
    _log(
        "Requested config: "
        f"seed={config.seed}, resolution={config.scan_resolution}, "
        f"fallbacks={list(config.scan_fallbacks)}, image_max_side={config.image_max_side}, "
        f"method_g_permutations={config.method_g_permutations}, "
        f"method_i_bootstrap={config.method_i_bootstrap}, "
        f"method_i_min_languages={config.method_i_min_languages}, "
        f"language_token_cap={config.language_token_cap}, force={args.force}"
    )

    with active_run(config={"command": "run_phase10_stage2_gi", "seed": config.seed}) as run:
        run_start = time.perf_counter()
        status["status"] = "in_progress"
        status["run_id"] = str(run.run_id)
        _save_status(status_path, status)
        _log(f"Run started with run_id={run.run_id}")

        store = MetadataStore(DB_PATH)
        scans_root = Path("data/raw/scans")
        external_corpora_dir = Path("data/external_corpora")

        method_results: dict[str, dict[str, Any]] = {}
        artifacts: dict[str, str] = {}

        # Step: data inventory
        existing_inventory = _artifact_results(status["steps"]["data_inventory"]["artifact"])
        if (
            status["steps"]["data_inventory"]["status"] == "completed"
            and existing_inventory is not None
            and not args.force
        ):
            inventory = existing_inventory
            artifacts["inventory"] = status["steps"]["data_inventory"]["artifact"]
            _log("Data inventory reused from checkpoint")
        else:
            _set_step(status, "data_inventory", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Data inventory started")
            inventory = scan_data_resource_inventory(
                store=store,
                scans_root=scans_root,
                external_corpora_dir=external_corpora_dir,
            )
            saved = ProvenanceWriter.save_results(
                inventory,
                Path("results/data/phase10_admissibility/stage2_data_inventory.json"),
            )
            artifacts["inventory"] = saved["latest_path"]
            _set_step(
                status,
                "data_inventory",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log("Data inventory complete")

        # Step: illustration features
        illustration_step = status["steps"]["illustration_features"]
        existing_illustration = _artifact_results(illustration_step["artifact"])
        illustration_deliverable = Path(illustration_step["deliverable_path"])
        if (
            status["steps"]["illustration_features"]["status"] == "completed"
            and existing_illustration is not None
            and not args.force
        ):
            illustration_features = existing_illustration
            artifacts["illustration"] = status["steps"]["illustration_features"]["artifact"]
            if not illustration_deliverable.exists():
                _write_json(illustration_deliverable, illustration_features)
            _log("Illustration features reused from checkpoint")
        else:
            _set_step(
                status,
                "illustration_features",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("Illustration feature extraction started")
            illustration_features = build_illustration_features(
                store=store,
                scans_root=scans_root,
                resolution=config.scan_resolution,
                fallback_resolutions=config.scan_fallbacks,
                max_side=config.image_max_side,
                progress=lambda msg: _log(f"[illustration] {msg}"),
            )
            saved = ProvenanceWriter.save_results(
                illustration_features,
                Path("results/data/phase10_admissibility/illustration_features_machine.json"),
            )
            _write_json(illustration_deliverable, illustration_features)
            artifacts["illustration"] = saved["latest_path"]
            _set_step(
                status,
                "illustration_features",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log("Illustration feature extraction complete")

        # Step: cross-linguistic manifest
        manifest_step = status["steps"]["cross_linguistic_manifest"]
        existing_manifest = _artifact_results(manifest_step["artifact"])
        manifest_deliverable = Path(manifest_step["deliverable_path"])
        if (
            status["steps"]["cross_linguistic_manifest"]["status"] == "completed"
            and existing_manifest is not None
            and not args.force
        ):
            cross_manifest = existing_manifest
            artifacts["manifest"] = status["steps"]["cross_linguistic_manifest"]["artifact"]
            if not manifest_deliverable.exists():
                _write_json(manifest_deliverable, cross_manifest)
            _log("Cross-linguistic manifest reused from checkpoint")
        else:
            _set_step(
                status,
                "cross_linguistic_manifest",
                "running",
                started_at=now_utc_iso(),
                error=None,
            )
            _save_status(status_path, status)
            _log("Cross-linguistic manifest construction started")
            cross_manifest = build_cross_linguistic_manifest(
                store=store,
                external_corpora_dir=external_corpora_dir,
                token_cap=config.language_token_cap,
                progress=lambda msg: _log(f"[manifest] {msg}"),
            )
            saved = ProvenanceWriter.save_results(
                cross_manifest,
                Path("results/data/phase10_admissibility/cross_linguistic_manifest_machine.json"),
            )
            _write_json(manifest_deliverable, cross_manifest)
            artifacts["manifest"] = saved["latest_path"]
            _set_step(
                status,
                "cross_linguistic_manifest",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log("Cross-linguistic manifest complete")

        # Step: Method G
        existing_g = _artifact_results(status["steps"]["method_g"]["artifact"])
        if (
            status["steps"]["method_g"]["status"] == "completed"
            and existing_g is not None
            and not args.force
        ):
            method_results["G"] = existing_g
            artifacts["G"] = status["steps"]["method_g"]["artifact"]
            _log("Method G reused from checkpoint")
        else:
            _set_step(status, "method_g", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Method G started")
            method_g_result = run_method_g(
                store=store,
                illustration_features=illustration_features,
                permutations=config.method_g_permutations,
                seed=config.seed,
                progress=lambda msg: _log(f"[method_g] {msg}"),
            )
            method_results["G"] = method_g_result
            saved = ProvenanceWriter.save_results(
                method_g_result,
                Path("results/data/phase10_admissibility/method_g_text_illustration.json"),
            )
            artifacts["G"] = saved["latest_path"]
            _set_step(
                status,
                "method_g",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Method G complete ({method_g_result.get('decision')})")

        # Step: Method I
        existing_i = _artifact_results(status["steps"]["method_i"]["artifact"])
        if (
            status["steps"]["method_i"]["status"] == "completed"
            and existing_i is not None
            and not args.force
        ):
            method_results["I"] = existing_i
            artifacts["I"] = status["steps"]["method_i"]["artifact"]
            _log("Method I reused from checkpoint")
        else:
            _set_step(status, "method_i", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Method I started")
            method_i_result = run_method_i(
                store=store,
                cross_linguistic_manifest=cross_manifest,
                external_corpora_dir=external_corpora_dir,
                bootstrap_iterations=config.method_i_bootstrap,
                min_languages=config.method_i_min_languages,
                seed=config.seed,
                progress=lambda msg: _log(f"[method_i] {msg}"),
            )
            method_results["I"] = method_i_result
            saved = ProvenanceWriter.save_results(
                method_i_result,
                Path("results/data/phase10_admissibility/method_i_cross_linguistic.json"),
            )
            artifacts["I"] = saved["latest_path"]
            _set_step(
                status,
                "method_i",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                error=None,
            )
            _save_status(status_path, status)
            _log(f"Method I complete ({method_i_result.get('decision')})")

        # Stage summary
        existing_stage2 = _artifact_results(status["steps"]["stage2_summary"]["artifact"])
        if (
            status["steps"]["stage2_summary"]["status"] == "completed"
            and existing_stage2 is not None
            and not args.force
        ):
            summary = existing_stage2
            artifacts["stage2"] = status["steps"]["stage2_summary"]["artifact"]
            _log("Stage 2 summary reused from checkpoint")
        else:
            _set_step(status, "stage2_summary", "running", started_at=now_utc_iso(), error=None)
            _save_status(status_path, status)
            _log("Stage 2 summary started")
            summary = summarize_stage2(method_results)
            summary["elapsed_seconds"] = time.perf_counter() - run_start
            saved = ProvenanceWriter.save_results(
                summary,
                Path("results/data/phase10_admissibility/stage2_summary.json"),
            )
            artifacts["stage2"] = saved["latest_path"]
            report_text = build_stage2_markdown(
                summary=summary,
                method_artifacts=artifacts,
                status_path=str(status_path),
            )
            report_path = Path("results/reports/phase10_admissibility/PHASE_10_STAGE2_RESULTS.md")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
            _set_step(
                status,
                "stage2_summary",
                "completed",
                completed_at=now_utc_iso(),
                artifact=saved["latest_path"],
                report=str(report_path),
                error=None,
            )
            _save_status(status_path, status)
            _log("Stage 2 summary complete")

        status["status"] = "completed"
        status["completed_at"] = now_utc_iso()
        _save_status(status_path, status)

        summary_table = Table(title="Phase 10 Stage 2 Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="bold")
        summary_table.add_row("Method G", str(method_results["G"].get("decision")))
        summary_table.add_row("Method I", str(method_results["I"].get("decision")))
        summary_table.add_row("Stage decision", str(summary.get("stage_decision")))
        summary_table.add_row("Scan resolution", config.scan_resolution)
        summary_table.add_row("Fallbacks", ", ".join(config.scan_fallbacks))
        summary_table.add_row("Method G permutations", str(config.method_g_permutations))
        summary_table.add_row("Method I bootstrap", str(config.method_i_bootstrap))
        summary_table.add_row("Elapsed (s)", f"{float(summary.get('elapsed_seconds', 0.0)):.1f}")
        console.print(summary_table)
        console.print(f"[green]Status tracker:[/green] {status_path}")
        console.print("[green]Data deliverable:[/green] data/illustration_features.json")
        console.print(
            "[green]Data deliverable:[/green] data/corpora/cross_linguistic_manifest.json"
        )
        console.print(f"[green]Method G artifact:[/green] {artifacts.get('G', 'n/a')}")
        console.print(f"[green]Method I artifact:[/green] {artifacts.get('I', 'n/a')}")
        console.print(f"[green]Stage 2 summary artifact:[/green] {artifacts.get('stage2', 'n/a')}")
        store.save_run(run)


if __name__ == "__main__":
    run_stage2(parse_args())
