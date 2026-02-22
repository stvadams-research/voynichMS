#!/usr/bin/env python3
"""Phase 16B: Effort Correlation.

Tests if scribal selection bias is correlated with physical word effort.
Correlates effort (stroke cost) with selection FREQUENCY within each window,
not with arbitrary list position.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase16_physical_grounding.correlation import EffortCorrelationAnalyzer  # noqa: E402

TRACE_PATH = project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
COST_PATH = project_root / "results/data/phase16_physical_grounding/word_ergonomic_costs.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical_grounding/effort_correlation.json"
console = Console()

def main():
    console.print(
        "[bold magenta]Phase 16B: Effort Correlation"
        " (Physical Preference)[/bold magenta]"
    )

    if not TRACE_PATH.exists() or not COST_PATH.exists():
        console.print(f"[red]Error: Trace or Cost data missing at {TRACE_PATH} or {COST_PATH}[/red]")
        return

    # 1. Load Data
    with open(TRACE_PATH) as f:
        choices = json.load(f)["results"]["choices"]
    with open(COST_PATH) as f:
        costs = json.load(f)["results"]["word_costs"]

    # 2. Analyze
    analyzer = EffortCorrelationAnalyzer(choices, costs)
    corr = analyzer.analyze_selection_correlation(min_window_samples=20)
    rho = corr['correlation_rho']
    p_value = corr['p_value']
    num_pairs = corr['num_pairs']
    
    avg_gradient = analyzer.analyze_effort_gradient(limit=10000)

    # 6. Save and Report
    results = {
        "num_word_window_pairs": num_pairs,
        "correlation_rho": float(rho),
        "p_value": float(p_value),
        "avg_effort_gradient": avg_gradient,
        "is_ergonomically_coupled": corr['is_significant'],
        "interpretation": (
            "Negative rho: lower-effort words selected more often. "
            "Positive rho: higher-effort words selected more often. "
            f"rho^2 = {rho**2:.4f} "
            f"({rho**2*100:.1f}% variance explained)."
        )
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print("\n[green]Success! Effort correlation complete.[/green]")
    console.print(f"Word-Window Pairs Analyzed: [bold]{num_pairs}[/bold]")
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
