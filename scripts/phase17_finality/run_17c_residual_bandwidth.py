#!/usr/bin/env python3
"""Sprint A1: Residual Bandwidth Decomposition.

The raw 7.53 bpw realized bandwidth includes entropy explained by known
mechanical drivers (bigram context, positional bias, recency, suffix
affinity, frequency bias).  This script computes the progressive
conditional entropy chain to determine the *residual steganographic
bandwidth* (RSB) — the bits per word that cannot be explained by any
known mechanical or structural driver.
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
from phase17_finality.residual import ResidualBandwidthAnalyzer  # noqa: E402

CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
)
OUTPUT_PATH = project_root / "results/data/phase17_finality/residual_bandwidth.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 17C: Residual Bandwidth Decomposition[/bold magenta]")

    # Load choice stream
    if not CHOICE_STREAM_PATH.exists():
        console.print(f"[red]Error: Choice stream trace missing at {CHOICE_STREAM_PATH}.[/red]")
        return
    with open(CHOICE_STREAM_PATH) as f:
        trace_data = json.load(f)
    choices = trace_data.get("results", trace_data).get("choices", [])
    if not choices:
        choices = trace_data.get("results", trace_data).get("choice_stream", [])
    console.print(f"Loaded {len(choices)} choice records.")

    # A1.1: Conditional entropy chain
    analyzer = ResidualBandwidthAnalyzer(choices)
    chain = analyzer.compute_entropy_chain()

    # Display chain
    table = Table(title="Conditional Entropy Chain")
    table.add_column("Conditioning", style="cyan")
    table.add_column("H (bits)", justify="right", style="bold")
    table.add_column("Reduction", justify="right")
    for i, entry in enumerate(chain):
        reduction = (
            f"-{chain[i - 1]['h'] - entry['h']:.4f}"
            if i > 0
            else "—"
        )
        table.add_row(entry["conditioning"], f"{entry['h']:.4f}", reduction)
    console.print(table)

    # A1.2: Independence check
    independence = analyzer.check_independence(chain)
    
    # Assemble results
    rsb = chain[-1]["h"]
    total_rsb_bits = rsb * len(choices)
    total_rsb_kb = total_rsb_bits / 8192

    results = {
        "num_choices": len(choices),
        "entropy_chain": chain,
        "rsb_bpw": round(rsb, 4),
        "rsb_total_bits": round(total_rsb_bits, 2),
        "rsb_total_kb": round(total_rsb_kb, 2),
        "rsb_latin_chars": round(total_rsb_bits / 4.1, 0),
        "independence_check": independence,
        "interpretation": (
            f"After conditioning on all 5 known drivers, "
            f"{rsb:.2f} bits/word remain unexplained. "
            f"Total residual capacity: {total_rsb_kb:.1f} KB."
        ),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17c_residual_bandwidth"}):
        main()
