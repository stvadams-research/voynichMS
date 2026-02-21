#!/usr/bin/env python3
"""Phase 12G: Slip Permutation Test.

Formal statistical validation of the mechanical slip detection signal.
Compares the observed slip count against a null distribution generated
by shuffling line-row indices 10,000 times.

Reports empirical p-value and 95% CI to confirm the vertical-offset
signal is not an artifact of chance.
"""

import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase12_mechanical.slip_detection import MechanicalSlipDetector  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = (
    project_root / "results/data/phase12_mechanical/slip_permutation_test.json"
)
console = Console()

NUM_PERMUTATIONS = 10_000
SEED = 42


def count_slips(detector, lines):
    """Count slips using an already-built detector model."""
    slips = detector.detect_slips(lines)
    return len(slips)


def main():
    console.print(
        "[bold blue]Phase 12G: Slip Permutation Test "
        "(Statistical Validation)[/bold blue]"
    )

    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    console.print(f"Loaded {len(lines)} canonical lines.")

    # 1. Build model and get observed slip count
    console.print("Building empirical model...")
    detector = MechanicalSlipDetector(min_transition_count=2)
    detector.build_model(lines)

    observed_slips = count_slips(detector, lines)
    console.print(f"Observed slip count: [bold]{observed_slips}[/bold]")

    # 2. Permutation test: shuffle line order, re-detect slips
    console.print(f"Running {NUM_PERMUTATIONS:,} permutations...")
    rng = np.random.default_rng(SEED)
    null_counts = np.zeros(NUM_PERMUTATIONS, dtype=int)

    for i in range(NUM_PERMUTATIONS):
        # Shuffle line order (preserves within-line structure)
        perm_indices = rng.permutation(len(lines))
        perm_lines = [lines[idx] for idx in perm_indices]

        # Re-detect slips with the same model (transitions unchanged)
        # but shuffled line adjacency
        perm_slips = detector.detect_slips(perm_lines)
        null_counts[i] = len(perm_slips)

        if (i + 1) % 2000 == 0:
            console.print(f"  ... {i + 1:,} / {NUM_PERMUTATIONS:,}")

    # 3. Compute statistics
    null_mean = float(null_counts.mean())
    null_std = float(null_counts.std())
    null_p5 = float(np.percentile(null_counts, 5))
    null_p95 = float(np.percentile(null_counts, 95))
    null_max = int(null_counts.max())
    null_min = int(null_counts.min())

    # Empirical p-value: fraction of permutations with >= observed slips
    p_value = float(np.mean(null_counts >= observed_slips))

    # Z-score relative to null
    z_score = (
        (observed_slips - null_mean) / null_std if null_std > 0 else 0.0
    )

    # 4. Save and Report
    results = {
        "observed_slips": observed_slips,
        "num_permutations": NUM_PERMUTATIONS,
        "null_mean": null_mean,
        "null_std": null_std,
        "null_ci_5": null_p5,
        "null_ci_95": null_p95,
        "null_min": null_min,
        "null_max": null_max,
        "empirical_p_value": p_value,
        "z_score": z_score,
        "total_lines": len(lines),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Permutation test complete.[/green]")

    table = Table(title="Slip Permutation Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Observed Slips", str(observed_slips))
    table.add_row("Null Mean", f"{null_mean:.1f}")
    table.add_row("Null Std", f"{null_std:.1f}")
    table.add_row("Null 90% CI", f"[{null_p5:.0f}, {null_p95:.0f}]")
    table.add_row("Null Range", f"[{null_min}, {null_max}]")
    table.add_row("Empirical p-value", f"{p_value:.6f}")
    table.add_row("Z-Score", f"{z_score:.2f} σ")
    table.add_row("Permutations", f"{NUM_PERMUTATIONS:,}")
    console.print(table)

    if p_value < 0.001:
        console.print(
            f"\n[bold green]PASS:[/bold green] Observed slips "
            f"({observed_slips}) are {z_score:.1f}σ above null "
            f"(p < 0.001). Vertical-offset signal is real."
        )
    elif p_value < 0.05:
        console.print(
            f"\n[bold yellow]MARGINAL:[/bold yellow] p = {p_value:.4f}. "
            f"Signal is significant at 5% but not at 0.1%."
        )
    else:
        console.print(
            f"\n[bold red]FAIL:[/bold red] p = {p_value:.4f}. "
            f"Cannot reject null hypothesis. Observed slip count "
            f"is consistent with chance."
        )


if __name__ == "__main__":
    with active_run(config={"seed": SEED, "command": "run_12g_slip_permutation"}):
        main()
