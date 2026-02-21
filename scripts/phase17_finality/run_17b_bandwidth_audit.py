#!/usr/bin/env python3
"""Phase 17B: Steganographic Bandwidth Audit.

Calculates the upper bound of information (meaning) that could be
encoded into the manuscript's choices, given lattice constraints.

Information-theoretic framework:
- At each step, the scribe sees W candidates in the current window.
- The lattice dictates WHICH window, but the choice WITHIN the window is free.
- Maximum bandwidth = avg(log2(W)) per choice = "uniform random entropy"
- Observed bandwidth = actual entropy of the choice stream
- The difference (max - observed) is consumed by scribal ergonomic bias.
- The observed entropy IS the steganographic ceiling: the maximum bits
  that could be encoded per word while matching the observed selection pattern.
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run

BIAS_PATH = project_root / "results/data/phase14_machine/selection_bias.json"
EFFORT_PATH = project_root / "results/data/phase16_physical/effort_correlation.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/bandwidth_audit.json"
console = Console()

# Reference bandwidths for comparison (bits per symbol)
REFERENCE_BANDWIDTHS = {
    "English prose (Shannon)": 1.3,       # bits per character after redundancy
    "English words (semantic)": 8.0,       # bits per word (surprisal in LM)
    "Latin Vulgate (per char)": 4.1,       # bits per character
    "Random coin flip": 1.0,              # 1 bit
}


def main():
    console.print("[bold magenta]Phase 17B: Steganographic Bandwidth Audit[/bold magenta]")

    if not BIAS_PATH.exists():
        console.print("[red]Error: Selection bias data missing (run 14P first).[/red]")
        return

    # 1. Load selection entropy from Phase 14P
    with open(BIAS_PATH, "r") as f:
        bias_data = json.load(f)["results"]

    num_decisions = bias_data["admissible_choices"]
    observed_entropy = bias_data["real_choice_entropy"]
    uniform_entropy = bias_data["uniform_random_entropy"]
    entropy_reduction_pct = bias_data["entropy_reduction"]

    # 2. Load ergonomic correlation from Phase 16B (if available)
    ergonomic_rho = None
    if EFFORT_PATH.exists():
        with open(EFFORT_PATH, "r") as f:
            effort_data = json.load(f)["results"]
        ergonomic_rho = effort_data.get("correlation_rho")

    # 3. Steganographic Capacity Calculation
    #
    # The MAXIMUM steganographic bandwidth is the observed choice entropy:
    # this is how many bits of information the choice-stream actually carries.
    # Even if the scribe has ergonomic preferences, those preferences could
    # themselves encode information (steganography).
    #
    # The TRUE capacity ceiling is the uniform entropy (max possible per window).
    # The observed entropy is the REALIZED bandwidth given natural scribe behavior.

    max_capacity_bpw = uniform_entropy       # bits/word if selection were uniform
    realized_capacity_bpw = observed_entropy  # bits/word as actually observed
    ergonomic_overhead_bpw = uniform_entropy - observed_entropy  # bits lost to bias

    total_capacity_bits = num_decisions * realized_capacity_bpw
    total_capacity_kb = total_capacity_bits / 8192

    # 4. Comparative: how much text could be hidden?
    # Latin at ~4.1 bits/char, English at ~1.3 bits/char after redundancy
    latin_chars_equivalent = total_capacity_bits / 4.1
    english_chars_equivalent = total_capacity_bits / 1.3

    # 5. The key question: is there enough bandwidth for natural language?
    #
    # English words carry ~8-12 bits of information per word token.
    # If the steganographic bandwidth >= threshold, the manuscript COULD
    # encode meaningful text within the lattice constraints.
    #
    # Threshold: If observed entropy >= 3.0 bits/word, a skilled encoder
    # could embed a compressed natural language message.
    stego_threshold = 3.0  # bits/word — conservative lower bound for encoding text
    has_sufficient_bandwidth = realized_capacity_bpw >= stego_threshold

    # 6. Save and Report
    results = {
        "num_decisions": num_decisions,
        "max_bandwidth_bpw": max_capacity_bpw,
        "realized_bandwidth_bpw": realized_capacity_bpw,
        "ergonomic_overhead_bpw": ergonomic_overhead_bpw,
        "ergonomic_rho": ergonomic_rho,
        "total_capacity_bits": total_capacity_bits,
        "total_capacity_kb": total_capacity_kb,
        "latin_chars_equivalent": latin_chars_equivalent,
        "english_chars_equivalent": english_chars_equivalent,
        "stego_threshold_bpw": stego_threshold,
        "has_sufficient_bandwidth": has_sufficient_bandwidth,
        "bandwidth_judgment": (
            "SUBSTANTIAL: The choice-stream has enough entropy to encode "
            "meaningful hidden text within lattice constraints."
            if has_sufficient_bandwidth else
            "CONSTRAINED: The choice-stream entropy is too low to encode "
            "meaningful natural language within lattice constraints."
        )
    }

    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)

    # Report
    console.print(f"\n[green]Success! Bandwidth audit complete.[/green]")

    table = Table(title="Steganographic Bandwidth Analysis")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")

    table.add_row("Total Scribal Decisions", f"{num_decisions:,}")
    table.add_row("Max Bandwidth (uniform)", f"{max_capacity_bpw:.2f} bits/word")
    table.add_row("Realized Bandwidth (observed)", f"{realized_capacity_bpw:.2f} bits/word")
    table.add_row("Ergonomic Overhead", f"{ergonomic_overhead_bpw:.2f} bits/word")
    table.add_row("Entropy Reduction", f"{entropy_reduction_pct*100:.2f}%")
    table.add_row("Total Capacity", f"{total_capacity_kb:.1f} KB ({total_capacity_bits:,.0f} bits)")
    table.add_row("Equivalent Latin Text", f"~{latin_chars_equivalent:,.0f} characters")
    table.add_row("Equivalent English Text", f"~{english_chars_equivalent:,.0f} characters")
    if ergonomic_rho is not None:
        table.add_row("Ergonomic Correlation (rho)", f"{ergonomic_rho:.4f}")
    console.print(table)

    console.print(f"\nStego Threshold: {stego_threshold} bits/word")
    if has_sufficient_bandwidth:
        console.print(f"[bold yellow]SUBSTANTIAL:[/bold yellow] At {realized_capacity_bpw:.2f} bits/word, "
                      f"the manuscript's choices carry enough entropy to potentially encode hidden content.")
        console.print("This does NOT prove meaning exists — only that the mechanical model does not rule it out.")
    else:
        console.print(f"[bold green]CONSTRAINED:[/bold green] At {realized_capacity_bpw:.2f} bits/word, "
                      f"the choice-stream lacks sufficient entropy for natural language encoding.")

    # Comparison table
    console.print("")
    ref_table = Table(title="Reference Bandwidths")
    ref_table.add_column("System", style="cyan")
    ref_table.add_column("Bits/Symbol", justify="right")
    for name, bw in REFERENCE_BANDWIDTHS.items():
        ref_table.add_row(name, f"{bw:.1f}")
    ref_table.add_row("Voynich Choice-Stream", f"{realized_capacity_bpw:.1f}", style="bold green")
    console.print(ref_table)


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17b_bandwidth_audit"}):
        main()
