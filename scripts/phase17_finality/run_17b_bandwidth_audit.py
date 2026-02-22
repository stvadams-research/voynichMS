#!/usr/bin/env python3
"""Phase 17B: Steganographic Bandwidth Audit.

Calculates the upper bound of information (meaning) that could be
encoded into the manuscript's choices, given lattice constraints.
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase17_finality.bandwidth import BandwidthAuditor  # noqa: E402

BIAS_PATH = project_root / "results/data/phase14_machine/selection_bias.json"
EFFORT_PATH = project_root / "results/data/phase16_physical_grounding/effort_correlation.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/bandwidth_audit.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 17B: Steganographic Bandwidth Audit[/bold magenta]")

    if not BIAS_PATH.exists():
        console.print(f"[red]Error: Selection bias data missing at {BIAS_PATH}.[/red]")
        return

    # 1. Load Data
    with open(BIAS_PATH) as f:
        bias_data = json.load(f)["results"]
    
    effort_data = None
    if EFFORT_PATH.exists():
        with open(EFFORT_PATH) as f:
            effort_data = json.load(f)["results"]

    # 2. Audit
    auditor = BandwidthAuditor(bias_data, effort_data)
    audit = auditor.audit(stego_threshold=3.0)

    # 3. Save and Report
    audit["bandwidth_judgment"] = (
        "SUBSTANTIAL: The choice-stream has enough entropy to encode "
        "meaningful hidden text within lattice constraints."
        if audit["has_sufficient_bandwidth"] else
        "CONSTRAINED: The choice-stream entropy is too low to encode "
        "meaningful natural language within lattice constraints."
    )
    
    ProvenanceWriter.save_results(audit, OUTPUT_PATH)

    console.print("\n[green]Success! Bandwidth audit complete.[/green]")

    table = Table(title="Steganographic Bandwidth Analysis")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")

    table.add_row("Total Scribal Decisions", f"{audit['num_decisions']:,}")
    table.add_row("Max Bandwidth (uniform)", f"{audit['max_bandwidth_bpw']:.2f} bits/word")
    table.add_row("Realized Bandwidth (observed)", f"{audit['realized_bandwidth_bpw']:.2f} bits/word")
    table.add_row("Ergonomic Overhead", f"{audit['ergonomic_overhead_bpw']:.2f} bits/word")
    table.add_row("Total Capacity", f"{audit['total_capacity_kb']:.1f} KB ({audit['total_capacity_bits']:,.0f} bits)")
    if audit.get('ergonomic_rho') is not None:
        table.add_row("Ergonomic Correlation (rho)", f"{audit['ergonomic_rho']:.4f}")
    console.print(table)

    console.print(f"\nStego Threshold: {audit['stego_threshold_bpw']} bits/word")
    if audit["has_sufficient_bandwidth"]:
        console.print(
            f"[bold yellow]SUBSTANTIAL:[/bold yellow] "
            f"At {audit['realized_bandwidth_bpw']:.2f} bits/word, "
            "the manuscript's choices carry enough entropy "
            "to potentially encode hidden content."
        )
    else:
        console.print(
            f"[bold green]CONSTRAINED:[/bold green] "
            f"At {audit['realized_bandwidth_bpw']:.2f} bits/word, "
            "the choice-stream lacks sufficient entropy "
            "for natural language encoding."
        )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17b_bandwidth_audit"}):
        main()
