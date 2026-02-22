#!/usr/bin/env python3
"""Phase 15C: Bias and Compressibility Analysis.

Analyzes the instrumented choice stream for skew, predictive features,
and information-theoretic structure.
"""

import json
import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase15_rule_extraction.bias import BiasAnalyzer  # noqa: E402

TRACE_PATH = project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
OUTPUT_PATH = project_root / "results/data/phase15_rule_extraction/bias_modeling.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 15C: Bias and Compressibility Analysis[/bold magenta]")

    if not TRACE_PATH.exists():
        console.print(f"[red]Error: Trace data not found at {TRACE_PATH}. Run 15A first.[/red]")
        return

    # 1. Load Instrumented Trace
    with open(TRACE_PATH) as f:
        trace_data = json.load(f)["results"]
    choices = trace_data["choices"]

    # 2. Analyze Bias & Compressibility
    analyzer = BiasAnalyzer(choices)
    
    # Within-Window Bias
    window_stats = analyzer.analyze_window_bias(min_samples=50)
    top_skewed = sorted(window_stats, key=lambda x: x['skew'], reverse=True)[:20]

    # Choice-Stream Compressibility
    compression_results = analyzer.analyze_compressibility(seed=42)
    improvement = compression_results['improvement']
    ratio = compression_results['real_ratio']
    sim_ratio = compression_results['sim_ratio']

    # 4. Save and Report
    results = {
        "num_decisions": len(choices),
        "avg_skew": float(np.mean([w['skew'] for w in window_stats])) if window_stats else 0.0,
        "top_skewed_windows": top_skewed,
        "compression": {
            "real_ratio": ratio,
            "sim_ratio": sim_ratio,
            "improvement": improvement,
            "interpretation": "positive = real is MORE compressible than random (structured); "
                             "negative = real is LESS compressible (higher entropy)"
        }
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print("\n[green]Success! Analysis complete.[/green]")
    console.print(f"Average Selection Skew: [bold]{results['avg_skew']*100:.2f}%[/bold]")

    # Report compression honestly
    if improvement > 0:
        console.print(
            f"Compressibility: Real is [bold green]"
            f"{improvement*100:.2f}% more compressible"
            f"[/bold green] than uniform baseline"
        )
    else:
        console.print(
            f"Compressibility: Real is [bold yellow]"
            f"{abs(improvement)*100:.2f}% less compressible"
            f"[/bold yellow] than uniform baseline"
        )
        console.print(
            "  (Higher entropy in choice-stream than uniform "
            "— selection may be more dispersed)"
        )

    table = Table(title="Top 10 Most Skewed Windows")
    table.add_column("Window", justify="right")
    table.add_column("Choices", justify="right")
    table.add_column("Win Size", justify="right")
    table.add_column("Entropy", justify="right")
    table.add_column("Max Ent", justify="right")
    table.add_column("Skew (%)", justify="right", style="bold yellow")

    for w in top_skewed[:10]:
        table.add_row(
            str(w['window_id']), str(w['count']), str(w['candidates']),
            f"{w['entropy']:.2f}", f"{w['max_entropy']:.2f}", f"{w['skew']*100:.2f}"
        )
    console.print(table)

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_15c_bias_and_compressibility"}):
        main()
