#!/usr/bin/env python3
"""Phase 15C: Bias and Compressibility Analysis.

Analyzes the instrumented choice stream for skew, predictive features,
and information-theoretic structure.
"""

import json
import math
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run

TRACE_PATH = project_root / "results/data/phase15_selection/choice_stream_trace.json"
OUTPUT_PATH = project_root / "results/data/phase15_selection/bias_modeling.json"
console = Console()

def calculate_entropy(data):
    if not data: return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

def main():
    console.print("[bold magenta]Phase 15C: Bias and Compressibility Analysis[/bold magenta]")

    if not TRACE_PATH.exists():
        console.print("[red]Error: Trace data not found. Run 15A first.[/red]")
        return

    # 1. Load Instrumented Trace
    with open(TRACE_PATH, "r") as f:
        trace_data = json.load(f)["results"]
    choices = trace_data["choices"]

    # 2. Within-Window Bias Profile
    # Build per-window candidate counts from the trace data itself
    win_choices = defaultdict(list)
    win_candidate_counts = {}
    for c in choices:
        wid = c['window_id']
        win_choices[wid].append(c['chosen_index'])
        # Track the actual window size from the trace
        if wid not in win_candidate_counts:
            win_candidate_counts[wid] = c['candidates_count']

    window_stats = []
    for wid, idxs in win_choices.items():
        if len(idxs) < 50: continue  # Need enough samples
        ent = calculate_entropy(idxs)
        # Use THIS window's actual candidate count for max entropy
        candidates = win_candidate_counts.get(wid, len(set(idxs)))
        max_ent = math.log2(candidates) if candidates > 1 else 1.0
        skew = max(0.0, (max_ent - ent) / max_ent) if max_ent > 0 else 0
        window_stats.append({
            "window_id": wid,
            "count": len(idxs),
            "candidates": candidates,
            "entropy": ent,
            "max_entropy": max_ent,
            "skew": skew
        })

    top_skewed = sorted(window_stats, key=lambda x: x['skew'], reverse=True)[:20]

    # 3. Choice-Stream Compressibility
    # Convert chosen indices to bytes (mod 256 for byte encoding)
    raw_indices = [c['chosen_index'] % 256 for c in choices]
    raw_bytes = bytes(raw_indices)

    compressed_size = len(zlib.compress(raw_bytes))
    uncompressed_size = len(raw_bytes)
    ratio = compressed_size / uncompressed_size

    # Simulated Uniform Baseline: for each decision, draw uniformly from
    # that decision's actual candidate count (seeded for reproducibility)
    rng = np.random.default_rng(seed=42)
    sim_indices = [
        rng.integers(0, max(c['candidates_count'], 1)) % 256
        for c in choices
    ]
    sim_bytes = bytes(sim_indices)
    sim_compressed_size = len(zlib.compress(sim_bytes))
    sim_ratio = sim_compressed_size / len(sim_bytes)

    improvement = (sim_ratio - ratio) / sim_ratio

    # 4. Save and Report
    results = {
        "num_decisions": len(choices),
        "avg_skew": float(np.mean([w['skew'] for w in window_stats])),
        "top_skewed_windows": top_skewed,
        "compression": {
            "real_ratio": ratio,
            "sim_ratio": sim_ratio,
            "improvement": improvement,
            "interpretation": "positive = real is MORE compressible than random (structured); "
                             "negative = real is LESS compressible (higher entropy)"
        }
    }

    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print(f"\n[green]Success! Analysis complete.[/green]")
    console.print(f"Average Selection Skew: [bold]{results['avg_skew']*100:.2f}%[/bold]")

    # Report compression honestly
    if improvement > 0:
        console.print(f"Compressibility: Real is [bold green]{improvement*100:.2f}% more compressible[/bold green] than uniform baseline")
    else:
        console.print(f"Compressibility: Real is [bold yellow]{abs(improvement)*100:.2f}% less compressible[/bold yellow] than uniform baseline")
        console.print("  (Higher entropy in real choice-stream than uniform — selection may be more dispersed)")

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
