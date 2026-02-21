#!/usr/bin/env python3
"""
Phase 6A: Formal-System Exhaustion and Completeness Runner
"""

import argparse
import sys
import os
import json
from pathlib import Path
import numpy as np

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord, PageRecord
from phase1_foundation.core.provenance import ProvenanceWriter
from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
from phase6_functional.formal_system.simulators import LatticeTraversalSimulator

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_real_lines(store, dataset_id="voynich_real"):
    session = store.Session()
    try:
        tokens_recs = (
            session.query(TranscriptionTokenRecord.content, TranscriptionTokenRecord.line_id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )
        
        lines = []
        current_line = []
        last_line_id = None
        
        for content, line_id in tokens_recs:
            if last_line_id and line_id != last_line_id:
                lines.append(current_line)
                current_line = []
            current_line.append(content)
            last_line_id = line_id
        if current_line:
            lines.append(current_line)
            
        return lines
    finally:
        session.close()

def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 6A: Formal-System Exhaustion and Completeness")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_phase_6a(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold green]Phase 6A: Formal-System Exhaustion and Completeness[/bold green]\n"
        "Testing structural signatures of formal execution.",
        border_style="green"
    ))

    with active_run(config={"command": "run_6a_exhaustion", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = FormalSystemAnalyzer()

        # 1. Prepare Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_real_lines(store)
        console.print(f"Loaded {len(real_lines)} real lines.")

        # Synthetic Formal System (Lattice Traversal)
        # We use a larger vocab and longer lines to match Voynich better
        sim = LatticeTraversalSimulator(vocab_size=5000, seed=seed)
        syn_lines = sim.generate_corpus(num_lines=len(real_lines), line_len=8)
        console.print(f"Generated {len(syn_lines)} synthetic lines.")
        
        datasets = {
            "Voynich (Real)": real_lines,
            "Lattice Simulator (Syn)": syn_lines
        }
        
        # 2. Run Analysis
        results = {}
        for label, lines in datasets.items():
            console.print(f"\n[bold blue]Analyzing {label}...[/bold blue]")
            results[label] = analyzer.run_full_analysis(lines)
            
        # 3. Display Results
        table = Table(title="Phase 6A: Formal System Signatures")
        table.add_column("Metric", style="cyan")
        table.add_column("Voynich (Real)", justify="right")
        table.add_column("Lattice Sim (Syn)", justify="right")
        
        # Coverage
        table.add_row("Coverage Ratio", 
                      f"{results['Voynich (Real)']['coverage']['coverage_ratio']:.4f}",
                      f"{results['Lattice Simulator (Syn)']['coverage']['coverage_ratio']:.4f}")
        table.add_row("Hapax Ratio", 
                      f"{results['Voynich (Real)']['coverage']['hapax_ratio']:.4f}",
                      f"{results['Lattice Simulator (Syn)']['coverage']['hapax_ratio']:.4f}")
        
        # Redundancy
        table.add_row("Overlap Rate (N=3)", 
                      f"{results['Voynich (Real)']['redundancy']['path_overlap_rate_n3']:.4f}",
                      f"{results['Lattice Simulator (Syn)']['redundancy']['path_overlap_rate_n3']:.4f}")
        table.add_row("Mean Repet. Dist.", 
                      f"{results['Voynich (Real)']['redundancy']['mean_repetition_distance']:.1f}",
                      f"{results['Lattice Simulator (Syn)']['redundancy']['mean_repetition_distance']:.1f}")
        
        # Errors
        table.add_row("Deviation Rate", 
                      f"{results['Voynich (Real)']['errors']['deviation_rate']:.5f}",
                      f"{results['Lattice Simulator (Syn)']['errors']['deviation_rate']:.5f}")
        
        # Exhaustion
        table.add_row("Final Novelty Rate", 
                      f"{results['Voynich (Real)']['exhaustion']['final_novelty_rate']:.4f}",
                      f"{results['Lattice Simulator (Syn)']['exhaustion']['final_novelty_rate']:.4f}")
        table.add_row("Converging?", 
                      str(results['Voynich (Real)']['exhaustion']['is_converging']),
                      str(results['Lattice Simulator (Syn)']['exhaustion']['is_converging']))
        
        console.print(table)
        
        # 4. Save Artifacts
        out = Path(output_dir) if output_dir else Path("results/data/phase6_functional/phase_6a")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "phase_6a_results.json")
            
        # CSV Artifacts
        import csv
        with open(out / "coverage_tables.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Dataset", "Total Visits", "Unique States", "Coverage Ratio", "Hapax Ratio"])
            for label, res in results.items():
                writer.writerow([
                    label, 
                    res['coverage']['total_visits'], 
                    res['coverage']['unique_states'], 
                    res['coverage']['coverage_ratio'], 
                    res['coverage']['hapax_ratio']
                ])
                
        with open(out / "error_typology.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Dataset", "Context", "Expected", "Actual"])
            for label, res in results.items():
                for dev in res['errors']['sample_deviations']:
                    writer.writerow([label, str(dev['context']), dev['expected'], dev['actual']])
            
        # Generate Interpretation Report
        report_path = Path("results/reports/phase6_functional/PHASE_6A_RESULTS.md")
        with open(report_path, "w") as f:
            f.write("# PHASE 6A RESULTS\n\n")
            f.write("## Quantitative Analysis\n\n")
            f.write("| Metric | Voynich (Real) | Lattice Sim (Syn) |\n")
            f.write("|--------|----------------|-------------------|\n")
            f.write(f"| Coverage Ratio | {results['Voynich (Real)']['coverage']['coverage_ratio']:.4f} | {results['Lattice Simulator (Syn)']['coverage']['coverage_ratio']:.4f} |\n")
            f.write(f"| Hapax Ratio | {results['Voynich (Real)']['coverage']['hapax_ratio']:.4f} | {results['Lattice Simulator (Syn)']['coverage']['hapax_ratio']:.4f} |\n")
            f.write(f"| Overlap Rate (N=3) | {results['Voynich (Real)']['redundancy']['path_overlap_rate_n3']:.4f} | {results['Lattice Simulator (Syn)']['redundancy']['path_overlap_rate_n3']:.4f} |\n")
            f.write(f"| Deviation Rate | {results['Voynich (Real)']['errors']['deviation_rate']:.5f} | {results['Lattice Simulator (Syn)']['errors']['deviation_rate']:.5f} |\n")
            f.write(f"| Convergence | {results['Voynich (Real)']['exhaustion']['is_converging']} | {results['Lattice Simulator (Syn)']['exhaustion']['is_converging']} |\n\n")
            
            f.write("## Interpretation\n\n")
            if results['Voynich (Real)']['exhaustion']['is_converging']:
                f.write("- **Novelty Decay:** The manuscript shows a declining novelty rate, supporting H6A.1 (Formal-System Execution).\n")
            else:
                f.write("- **Persistent Novelty:** The novelty rate does not show clear convergence, weakening H6A.1.\n")
                
            if results['Voynich (Real)']['errors']['deviation_rate'] < 0.01:
                f.write("- **Rigid Execution:** The very low deviation rate supports a highly disciplined formal system.\n")
            else:
                f.write("- **High Variance:** The deviation rate suggests a more stochastic or noisy process.\n")

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {out}[/bold green]")

if __name__ == "__main__":
    args = _parse_args()
    run_phase_6a(seed=args.seed, output_dir=args.output_dir)
