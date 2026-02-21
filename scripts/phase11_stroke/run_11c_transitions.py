#!/usr/bin/env python3
"""Phase 11C: Test B stroke-feature transitions."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import numpy as np  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.progress import (  # noqa: E402
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.randomness import get_randomness_controller  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.transcription.parsers import EVAParser  # noqa: E402
from phase11_stroke.schema import StrokeSchema  # noqa: E402
from phase11_stroke.transitions import TransitionAnalyzer  # noqa: E402

DEFAULT_TRANSCRIPTION_PATH = Path("data/raw/transliterations/ivtff2.0/ZL3b-n.txt")
DEFAULT_OUTPUT_PATH = Path("results/data/phase11_stroke/test_b_transitions.json")
DEFAULT_SEED = 42
DEFAULT_PERMUTATIONS = 10_000
console = Console()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 11 Test B (transitions).")
    parser.add_argument(
        "--transcription-path",
        type=Path,
        default=DEFAULT_TRANSCRIPTION_PATH,
        help="Canonical EVA transcription path.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Permutation seed.")
    parser.add_argument(
        "--permutations",
        type=int,
        default=DEFAULT_PERMUTATIONS,
        help="Number of null permutations.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.transcription_path.exists():
        raise FileNotFoundError(f"Transcription file not found: {args.transcription_path}")

    schema = StrokeSchema()
    corpus_hash = _sha256_file(args.transcription_path)
    parser = EVAParser()

    console.print(
        Panel.fit(
            "[bold blue]Phase 11C: Test B Stroke Transitions[/bold blue]\n"
            f"Seed: {args.seed} | Permutations: {args.permutations:,} | {datetime.now().isoformat()}"
        )
    )

    t_start = time.time()
    with active_run(
        config={
            "command": "run_11c_transitions",
            "seed": int(args.seed),
            "permutations": int(args.permutations),
            "randomness_mode": "seeded",
            "schema_version": schema.schema_version(),
            "corpus_hash": corpus_hash,
            "transcription_path": str(args.transcription_path),
        }
    ):
        console.print("[cyan]Stage:[/cyan] Parsing canonical EVA transcription...")
        parsed_lines = list(parser.parse(args.transcription_path))
        console.print(f"[cyan]Stage:[/cyan] Parsed lines: {len(parsed_lines)}")

        controller = get_randomness_controller()
        analyzer = TransitionAnalyzer(schema=schema)
        console.print("[cyan]Stage:[/cyan] Computing transition mutual information and permutation nulls...")
        with controller.seeded_context(
            "phase11_stage2_test_b",
            seed=int(args.seed),
            purpose=f"test_b_permutations_{args.permutations}",
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
                    task_id = progress.add_task("Test B permutation null", total=args.permutations)
                    results = analyzer.run(
                        parsed_lines=parsed_lines,
                        schema=schema,
                        n_permutations=int(args.permutations),
                        rng=rng,
                        console=console,
                        progress=progress,
                        task_id=task_id,
                    )
            else:
                console.print("[cyan]Heartbeat mode:[/cyan] non-interactive output; using console heartbeats.")
                results = analyzer.run(
                    parsed_lines=parsed_lines,
                    schema=schema,
                    n_permutations=int(args.permutations),
                    rng=rng,
                    console=console,
                )

        results["input_metadata"] = {
            "transcription_path": str(args.transcription_path),
            "corpus_hash": corpus_hash,
            "schema_version": schema.schema_version(),
        }
        saved_paths = ProvenanceWriter.save_results(results, args.output)
        elapsed = time.time() - t_start
        console.print(
            "[green]Test B complete[/green] "
            f"| MI_boundary={results['B1_boundary_mi']:.4f} "
            f"| p={results['B1_p_value']:.4f} "
            f"| {results['B1_determination']} "
            f"| {elapsed:.1f}s"
        )
        console.print(
            f"[green]Saved:[/green] {saved_paths['latest_path']} "
            f"(snapshot: {saved_paths['snapshot_path']})"
        )


if __name__ == "__main__":
    main()
