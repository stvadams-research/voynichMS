#!/usr/bin/env python3
"""Phase 15D: Within-Window Selection Driver Analysis.

Analyzes hypotheses for what drives scribal selection within windows.
"""

import json
import sys
from collections import Counter
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
from phase15_rule_extraction.drivers import SelectionDriverAnalyzer  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase15_rule_extraction/selection_drivers.json"
)
console = Console()


def main():
    console.print(
        "[bold blue]Phase 15D: Within-Window Selection Drivers[/bold blue]"
    )

    # 1. Load choice stream
    if not CHOICE_STREAM_PATH.exists():
        console.print(f"[red]Error: Choice stream not found at {CHOICE_STREAM_PATH}. Run 15A first.[/red]")
        return

    with open(CHOICE_STREAM_PATH) as f:
        trace_data = json.load(f)

    # Handle provenance-wrapped format
    if "results" in trace_data:
        choices = trace_data["results"].get("choices", [])
        if not choices:
            choices = trace_data["results"].get("choice_stream", [])
    else:
        choices = trace_data if isinstance(trace_data, list) else []

    if not choices:
        console.print("[red]No choice records found in trace file.[/red]")
        return

    console.print(f"Loaded {len(choices)} choice records.")

    # 2. Load corpus frequencies and lattice
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    all_tokens = [t for line in lines for t in line]
    corpus_freq = Counter(all_tokens)

    # Load window_contents
    palette_path = (
        project_root / "results/data/phase14_machine/full_palette_grid.json"
    )
    with open(palette_path) as f:
        palette = json.load(f)["results"]
    window_contents = palette["window_contents"]

    # 3. Run hypothesis tests
    analyzer = SelectionDriverAnalyzer(choices, window_contents, corpus_freq)
    
    results = {}
    results["positional_bias"] = analyzer.test_positional_bias()
    results["bigram_context"] = analyzer.test_bigram_context()
    results["suffix_affinity"] = analyzer.test_suffix_affinity()
    results["frequency_bias"] = analyzer.test_frequency_bias()
    results["recency_bias"] = analyzer.test_recency_bias()

    # 4. Rank by bits explained
    ranked = sorted(
        results.items(),
        key=lambda x: x[1].get("bits_explained", 0),
        reverse=True,
    )

    console.print("\n[bold]Ranked Selection Drivers[/bold]")
    table = Table()
    table.add_column("Hypothesis", style="cyan")
    table.add_column("Bits Explained", justify="right")
    table.add_column("Significant?", justify="center")
    table.add_column("Key Metric")

    for name, r in ranked:
        sig = "[green]YES[/green]" if r.get("is_significant") else "[red]no[/red]"
        if name == "positional_bias":
            key = f"mean_pos={r.get('mean_relative_position', 0):.3f}"
        elif name == "bigram_context":
            key = f"IG={r.get('information_gain_bits', 0):.3f} bits"
        elif name == "suffix_affinity":
            key = f"excess={r.get('excess_ratio', 0):.2f}x"
        elif name == "frequency_bias":
            key = f"rho={r.get('spearman_rho', 0):.4f}"
        elif name == "recency_bias":
            key = f"adv={r.get('recency_advantage', 0):.4f}"
        else:
            key = "—"

        table.add_row(
            name.replace("_", " ").title(),
            f"{r.get('bits_explained', 0):.3f}",
            sig,
            key,
        )

    console.print(table)

    # 5. Save results
    output = {
        "num_choices": len(choices),
        "hypotheses": results,
        "ranked_drivers": [
            {"hypothesis": name, "bits_explained": r.get("bits_explained", 0)}
            for name, r in ranked
        ],
        "top_driver": ranked[0][0] if ranked else None,
    }

    ProvenanceWriter.save_results(output, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_15d_selection_drivers"}
    ):
        main()
