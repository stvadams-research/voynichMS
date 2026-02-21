#!/usr/bin/env python3
"""Phase 16B: Effort Correlation.

Tests if scribal selection bias is correlated with physical word effort.
Correlates effort (stroke cost) with selection FREQUENCY within each window,
not with arbitrary list position.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from scipy.stats import spearmanr

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.runs.manager import active_run  # noqa: E402

TRACE_PATH = project_root / "results/data/phase15_selection/choice_stream_trace.json"
COST_PATH = project_root / "results/data/phase16_physical/word_ergonomic_costs.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical/effort_correlation.json"
console = Console()

def main():
    console.print(
        "[bold magenta]Phase 16B: Effort Correlation"
        " (Physical Preference)[/bold magenta]"
    )

    if not TRACE_PATH.exists() or not COST_PATH.exists():
        console.print("[red]Error: Trace or Cost data missing.[/red]")
        return

    # 1. Load Data
    with open(TRACE_PATH) as f:
        choices = json.load(f)["results"]["choices"]
    with open(COST_PATH) as f:
        costs = json.load(f)["results"]["word_costs"]

    # 2. Compute per-window selection frequency for each word
    # For each window, count how many times each word was chosen
    win_word_counts = defaultdict(Counter)
    win_totals = defaultdict(int)
    for c in choices:
        wid = c['window_id']
        word = c['chosen_word']
        win_word_counts[wid][word] += 1
        win_totals[wid] += 1

    # 3. Build (effort, relative_frequency) pairs per word-in-window
    # Relative frequency = times_chosen / total_choices_in_window
    efforts = []
    frequencies = []
    word_labels = []

    for wid, word_counts in win_word_counts.items():
        total = win_totals[wid]
        if total < 20:
            continue  # Skip windows with too few observations
        for word, count in word_counts.items():
            if word in costs:
                efforts.append(costs[word])
                frequencies.append(count / total)
                word_labels.append(word)

    if len(efforts) < 10:
        console.print("[red]Insufficient data for correlation.[/red]")
        return

    # 4. Compute Correlation: effort vs selection frequency
    # Hypothesis: lower effort → higher frequency (negative rho)
    rho, p_value = spearmanr(efforts, frequencies)

    # 5. Effort Stability (Gradient between consecutive selections)
    effort_seq = []
    for c in choices[:10000]:
        word = c['chosen_word']
        if word in costs:
            effort_seq.append(costs[word])
    gradients = [abs(effort_seq[i] - effort_seq[i-1]) for i in range(1, len(effort_seq))]
    avg_gradient = float(np.mean(gradients)) if gradients else 0.0

    # 6. Save and Report
    results = {
        "num_word_window_pairs": len(efforts),
        "correlation_rho": float(rho),
        "p_value": float(p_value),
        "avg_effort_gradient": avg_gradient,
        "is_ergonomically_coupled": bool(p_value < 0.01 and abs(rho) > 0.1),
        "interpretation": (
            "Negative rho: lower-effort words selected more often. "
            "Positive rho: higher-effort words selected more often. "
            f"rho^2 = {rho**2:.4f} "
            f"({rho**2*100:.1f}% variance explained)."
        )
    }

    from phase1_foundation.core.provenance import ProvenanceWriter
    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print("\n[green]Success! Effort correlation complete.[/green]")
    console.print(f"Word-Window Pairs Analyzed: [bold]{len(efforts)}[/bold]")
    console.print(
        f"Spearman Rho: [bold cyan]{rho:.4f}[/bold cyan] "
        f"(p={p_value:.4e})"
    )
    console.print(
        f"Variance Explained (rho^2): "
        f"[bold]{rho**2*100:.1f}%[/bold]"
    )
    console.print(
        f"Effort Gradient: "
        f"[bold]{avg_gradient:.2f} strokes/word[/bold]"
    )

    if results['is_ergonomically_coupled'] and rho < 0:
        console.print(
            "\n[bold green]VERIFIED:[/bold green] "
            "Lower-effort words are preferred."
        )
    elif results['is_ergonomically_coupled'] and rho > 0:
        console.print(
            "\n[bold yellow]UNEXPECTED:[/bold yellow] "
            "Higher-effort words preferred. "
            "Ergonomic hypothesis rejected."
        )
    else:
        console.print(
            "\n[bold yellow]WEAK:[/bold yellow] "
            "Effort correlation not strong enough "
            "(need |rho|>0.1, p<0.01)."
        )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_16b_effort_correlation"}):
        main()
