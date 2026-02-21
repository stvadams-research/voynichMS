#!/usr/bin/env python3
"""
Phase 7C: Comparative Formal Artifact Analysis Runner
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from phase7_human.phase8_comparative import ComparativeAnalyzer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.queries import get_lines_from_store  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 7C: Comparative Formal Artifact Analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_phase_7c(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold cyan]Phase 7C: Comparative Formal Artifact Analysis[/bold cyan]\n"
        "Situating the Voynich Manuscript in the Morphospace of Rule-Based Systems.",
        border_style="cyan"
    ))

    with active_run(config={"command": "run_7c_comparative", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = ComparativeAnalyzer()

        # 1. Prepare Data
        datasets = [
            "voynich_real",
            "latin_classic",
            "table_grille",
            "self_citation"
        ]

        console.print("\n[bold yellow]Step 1: Extracting Structural Fingerprints[/bold yellow]")
        fingerprints = {}
        for ds_id in datasets:
            console.print(f"  Processing {ds_id}...")
            lines = get_lines_from_store(store, ds_id)
            if lines:
                fingerprints[ds_id] = analyzer.calculate_fingerprint(lines)
            else:
                console.print(f"  [red]Warning: No data for {ds_id}[/red]")

        # 2. Distance Matrix
        console.print("\n[bold yellow]Step 2: Computing Distances from Voynich[/bold yellow]")
        v_finger = fingerprints.get("voynich_real")
        distances = {}
        if v_finger:
            for ds_id, finger in fingerprints.items():
                if ds_id != "voynich_real":
                    distances[ds_id] = analyzer.compute_distance(v_finger, finger)

        # 3. Display Results
        table = Table(title="Phase 7C: Structural Fingerprint Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("TTR", justify="right")
        table.add_column("Determinism", justify="right")
        table.add_column("Sparsity", justify="right")
        table.add_column("Convergence", justify="right")
        table.add_column("Dist (to VM)", style="magenta")

        for ds_id, finger in fingerprints.items():
            dist_str = f"{distances.get(ds_id):.4f}" if ds_id in distances else "0.0000"
            table.add_row(
                ds_id,
                f"{finger['ttr']:.4f}",
                f"{finger['determinism']:.4f}",
                f"{finger['sparsity']:.4f}",
                f"{finger['convergence']:.4f}",
                dist_str
            )

        console.print(table)

        # 4. Save Artifacts
        out = Path(output_dir) if output_dir else Path("results/data/phase7_human")
        out.mkdir(parents=True, exist_ok=True)

        results = {
            "fingerprints": fingerprints,
            "distances_from_voynich": distances
        }

        ProvenanceWriter.save_results(results, out / "phase_7c_results.json")

        # Generate Report
        report_path = Path("results/reports/phase7_human/PHASE_7C_RESULTS.md")
        with open(report_path, "w") as report_file:
            report_file.write("# PHASE 7C RESULTS: COMPARATIVE FORMAL ARTIFACT ANALYSIS\n\n")
            report_file.write("## Quantitative Structural Fingerprints\n\n")
            report_file.write("| Dataset | TTR | Determinism | Sparsity | Convergence | Dist (to VM) |\n")
            report_file.write("|---------|-----|-------------|----------|-------------|--------------|\n")
            for ds_id, finger in fingerprints.items():
                dist_val = distances.get(ds_id, 0.0)
                report_file.write(f"| {ds_id} | {finger['ttr']:.4f} | {finger['determinism']:.4f} | {finger['sparsity']:.4f} | {finger['convergence']:.4f} | {dist_val:.4f} |\n")

            report_file.write("\n## Morphospace Analysis\n\n")
            if distances:
                closest = min(distances, key=distances.get)
                report_file.write(f"- **Nearest Artifact Class:** {closest} (Dist: {distances[closest]:.4f})\n")

            report_file.write("\n## Final Determination\n\n")
            v_sparsity = v_finger['sparsity'] if v_finger else 0
            if v_sparsity > 0.8:
                report_file.write("- **Unique Profile:** The Voynich Manuscript exhibits extreme sparsity and novelty convergence not fully matched by semantic or simple non-semantic baselines.\n")

            if "table_grille" in distances and distances["table_grille"] < 0.2:
                report_file.write("- **Mechanism Alignment:** The manuscript aligns closely with deterministic, non-semantic table-based systems.\n")
            else:
                report_file.write("- **Structural Isolation:** Voynich remains structurally isolated in the morphospace, suggesting a highly specialized or custom formal system.\n")

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {out}[/bold green]")

if __name__ == "__main__":
    args = _parse_args()
    run_phase_7c(seed=args.seed, output_dir=args.output_dir)
