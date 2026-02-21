#!/usr/bin/env python3
"""Phase 11D: Stroke Topology (Fractal Lattice Test)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.transcription.parsers import EVAParser  # noqa: E402
from phase11_stroke.analysis.topology import StrokeTopologyAnalyzer  # noqa: E402
from phase11_stroke.schema import StrokeSchema  # noqa: E402

DEFAULT_TRANSCRIPTION_PATH = Path("data/raw/transliterations/ivtff2.0/ZL3b-n.txt")
PHASE5_RESULTS_PATH = Path("results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json")
DEFAULT_OUTPUT_PATH = Path("results/data/phase11_stroke/topology_results.json")
SEED = 42
console = Console()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 11D stroke topology analysis.")
    parser.add_argument(
        "--transcription-path",
        type=Path,
        default=DEFAULT_TRANSCRIPTION_PATH,
        help="Canonical EVA transcription path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output JSON path.",
    )
    return parser.parse_args()

def run_correlation(word_scale: dict[str, Any], stroke_scale: dict[str, Any]) -> dict[str, Any]:
    """Task 4.2: Measure hierarchical transition correlation."""
    metrics = ["collision_rate", "gini_coefficient", "avg_successor_convergence"]
    correlations = {}

    # We compare the 'Real' word-scale metrics with the 'Real' stroke-scale metrics
    # A small delta (high similarity) suggests fractal/recursive production.
    for m in metrics:
        w_val = word_scale.get(m)
        if w_val is None: # Handle nested keys in word_scale
            # word_scale is nested (overlap.collision_rate, coverage.gini_coefficient, convergence.avg_successor_convergence)
            if m == "collision_rate": w_val = word_scale.get("overlap", {}).get(m)
            if m == "gini_coefficient": w_val = word_scale.get("coverage", {}).get(m)
            if m == "avg_successor_convergence": w_val = word_scale.get("convergence", {}).get(m)

        s_val = stroke_scale.get(m)
        if s_val is None: # Handle nested keys in stroke_scale
             if m == "collision_rate": s_val = stroke_scale.get("overlap", {}).get(m)
             if m == "gini_coefficient": s_val = stroke_scale.get("coverage", {}).get(m)
             if m == "avg_successor_convergence": s_val = stroke_scale.get("convergence", {}).get(m)

        if w_val is not None and s_val is not None:
            delta = abs(w_val - s_val)
            similarity = 1.0 - (delta / max(w_val, s_val)) if max(w_val, s_val) > 0 else 1.0
            correlations[m] = {
                "word_scale": float(w_val),
                "stroke_scale": float(s_val),
                "similarity": float(similarity)
            }

    avg_sim = sum(c["similarity"] for c in correlations.values()) / len(correlations) if correlations else 0.0
    return {
        "metrics": correlations,
        "average_similarity": float(avg_sim),
        "is_recursive_machine": bool(avg_sim > 0.8)
    }

def main() -> None:
    args = parse_args()
    transcription_path: Path = args.transcription_path
    output_path: Path = args.output
    if not transcription_path.exists():
        raise FileNotFoundError(f"Transcription file not found: {transcription_path}")

    console.print(
        Panel.fit(
            "[bold blue]Phase 11D: Stroke Topology (Fractal Lattice Test)[/bold blue]\n"
            f"Analyzing sub-glyph vs word-level recursion | {datetime.now().isoformat()}"
        )
    )

    t_start = time.time()
    with active_run(config={"command": "run_11d_topology", "seed": SEED}):
        # 1. Load Data
        parser = EVAParser()
        parsed_lines = list(parser.parse(transcription_path))
        all_words = []
        for line in parsed_lines:
            all_words.extend([t.content for t in line.tokens])

        # 2. Run Stroke Topology Test (Task 4.1)
        schema = StrokeSchema()
        analyzer = StrokeTopologyAnalyzer(schema=schema)
        stroke_results = analyzer.run_fractal_lattice_test(all_words)

        # 3. Hierarchical Correlation (Task 4.2)
        correlation_results = {}
        if PHASE5_RESULTS_PATH.exists():
            with PHASE5_RESULTS_PATH.open("r", encoding="utf-8") as f:
                phase5_data = json.load(f)
            voynich_word_scale = phase5_data.get("Voynich (Real)")
            if voynich_word_scale:
                correlation_results = run_correlation(voynich_word_scale, stroke_results)

        final_results = {
            "stroke_topology": stroke_results,
            "hierarchical_correlation": correlation_results,
            "metadata": {
                "word_count": len(all_words),
                "transcription": str(transcription_path),
                "timestamp": datetime.now().isoformat()
            }
        }

        saved_paths = ProvenanceWriter.save_results(final_results, output_path)

        # Display Results
        table = Table(title="Fractal Lattice Test (Sub-Glyph vs Word)")
        table.add_column("Metric", style="cyan")
        table.add_column("Word Scale (P5)", justify="right")
        table.add_column("Stroke Scale (P11)", justify="right")
        table.add_column("Similarity", justify="right", style="bold green")

        for m, data in correlation_results.get("metrics", {}).items():
            sim = data["similarity"]
            color = "green" if sim > 0.8 else "yellow" if sim > 0.6 else "red"
            table.add_row(
                m,
                f"{data['word_scale']:.4f}",
                f"{data['stroke_scale']:.4f}",
                f"[{color}]{sim*100:.1f}%[/{color}]"
            )

        console.print(table)
        console.print(f"Recursive Machine Detection: [bold]{'POSITIVE' if correlation_results.get('is_recursive_machine') else 'NEGATIVE'}[/bold]")
        console.print(f"\n[green]Saved:[/green] {saved_paths['latest_path']}")

if __name__ == "__main__":
    main()
