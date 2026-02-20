#!/usr/bin/env python3
"""Phase 11B: Test A stroke-feature clustering."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TimeRemainingColumn

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.randomness import get_randomness_controller
from phase1_foundation.runs.manager import active_run
from phase11_stroke.clustering import ClusteringAnalyzer
from phase11_stroke.schema import StrokeSchema

DEFAULT_INPUT_PATH = Path("results/data/phase11_stroke/stroke_features.json")
DEFAULT_OUTPUT_PATH = Path("results/data/phase11_stroke/test_a_clustering.json")
DEFAULT_SEED = 42
DEFAULT_PERMUTATIONS = 10_000
console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 11 Test A (clustering).")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Stage 1 input JSON path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Permutation seed.")
    parser.add_argument(
        "--permutations",
        type=int,
        default=DEFAULT_PERMUTATIONS,
        help="Number of null permutations.",
    )
    parser.add_argument(
        "--min-occurrence",
        type=int,
        default=5,
        help="Minimum token occurrence threshold for pair analysis.",
    )
    return parser.parse_args()


def _load_results_payload(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "results" in raw and isinstance(raw["results"], dict):
        return raw["results"]
    return raw


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input extraction file not found: {args.input}")

    extracted_data = _load_results_payload(args.input)
    schema = StrokeSchema()

    console.print(
        Panel.fit(
            "[bold blue]Phase 11B: Test A Stroke Clustering[/bold blue]\n"
            f"Seed: {args.seed} | Permutations: {args.permutations:,} | {datetime.now().isoformat()}"
        )
    )

    t_start = time.time()
    with active_run(
        config={
            "command": "run_11b_cluster",
            "seed": int(args.seed),
            "permutations": int(args.permutations),
            "min_occurrence": int(args.min_occurrence),
            "randomness_mode": "seeded",
            "schema_version": schema.schema_version(),
            "input_path": str(args.input),
        }
    ):
        controller = get_randomness_controller()
        analyzer = ClusteringAnalyzer(schema=schema, min_occurrence=args.min_occurrence)
        console.print("[cyan]Stage:[/cyan] Computing observed statistic and permutation null...")
        with controller.seeded_context(
            "phase11_stage2_test_a",
            seed=int(args.seed),
            purpose=f"test_a_permutations_{args.permutations}",
        ):
            rng = np.random.default_rng(int(args.seed))
            use_live_progress = console.is_terminal and sys.stdout.isatty()
            if use_live_progress:
                with Progress(
                    SpinnerColumn(),
                    "[progress.description]{task.description}",
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    console=console,
                ) as progress:
                    task_id = progress.add_task("Test A permutation null", total=args.permutations)
                    results = analyzer.run(
                        extracted_data=extracted_data,
                        n_permutations=int(args.permutations),
                        rng=rng,
                        console=console,
                        progress=progress,
                        task_id=task_id,
                    )
            else:
                console.print("[cyan]Heartbeat mode:[/cyan] non-interactive output; using console heartbeats.")
                results = analyzer.run(
                    extracted_data=extracted_data,
                    n_permutations=int(args.permutations),
                    rng=rng,
                    console=console,
                )

        payload: dict[str, Any] = {
            **results,
            "input_metadata": extracted_data.get("input", {}),
        }
        saved_paths = ProvenanceWriter.save_results(payload, args.output)
        elapsed = time.time() - t_start
        console.print(
            "[green]Test A complete[/green] "
            f"| rho_partial={results['observed_partial_rho']:.4f} "
            f"| p={results['p_value']:.4f} "
            f"| {results['determination']} "
            f"| {elapsed:.1f}s"
        )
        console.print(
            f"[green]Saved:[/green] {saved_paths['latest_path']} "
            f"(snapshot: {saved_paths['snapshot_path']})"
        )


if __name__ == "__main__":
    main()
