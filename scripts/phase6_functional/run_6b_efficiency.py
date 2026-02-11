#!/usr/bin/env python3
"""
Phase 6B: Optimization Pressure and Efficiency Audit Runner
"""

import sys
import json
from pathlib import Path

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
from phase6_functional.efficiency.metrics import EfficiencyAnalyzer
from phase6_functional.formal_system.simulators import LatticeTraversalSimulator
from phase6_functional.efficiency.simulators import OptimizedLatticeSimulator

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

def run_phase_6b():
    console.print(Panel.fit(
        "[bold magenta]Phase 6B: Optimization Pressure and Efficiency Audit[/bold magenta]\n"
        "Testing for evidence of reuse minimization and cost-aware traversal.",
        border_style="magenta"
    ))

    with active_run(config={"command": "run_6b_efficiency", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = EfficiencyAnalyzer()
        
        # 1. Prepare Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_real_lines(store)
        num_lines = len(real_lines)
        console.print(f"Loaded {num_lines} real lines.")
        
        # H6B.2: Efficiency-Indifferent (Formal system from 6A)
        indifferent_sim = LatticeTraversalSimulator(vocab_size=5000, seed=42)
        indifferent_lines = indifferent_sim.generate_corpus(num_lines=num_lines, line_len=8)
        
        # H6B.1: Efficiency-Optimized (Small vocab, token reuse)
        optimized_sim = OptimizedLatticeSimulator(vocab_size=500, seed=42)
        optimized_lines = optimized_sim.generate_corpus(num_lines=num_lines, line_len=8)
        
        datasets = {
            "Voynich (Real)": real_lines,
            "Indifferent (H6B.2)": indifferent_lines,
            "Optimized (H6B.1)": optimized_lines
        }
        
        # 2. Run Audit
        results = {}
        for label, lines in datasets.items():
            console.print(f"\n[bold blue]Auditing {label}...[/bold blue]")
            results[label] = analyzer.run_efficiency_audit(lines)
            
        # 3. Display Results
        table = Table(title="Phase 6B: Efficiency Audit Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Voynich (Real)", justify="right")
        table.add_column("Indifferent (H6B.2)", justify="right")
        table.add_column("Optimized (H6B.1)", justify="right")
        
        table.add_row("Reuse Supp. Index", 
                      f"{results['Voynich (Real)']['reuse_suppression']['reuse_suppression_index']:.4f}",
                      f"{results['Indifferent (H6B.2)']['reuse_suppression']['reuse_suppression_index']:.4f}",
                      f"{results['Optimized (H6B.1)']['reuse_suppression']['reuse_suppression_index']:.4f}")
        
        table.add_row("Path Efficiency", 
                      f"{results['Voynich (Real)']['path_efficiency']['path_efficiency']:.4f}",
                      f"{results['Indifferent (H6B.2)']['path_efficiency']['path_efficiency']:.4f}",
                      f"{results['Optimized (H6B.1)']['path_efficiency']['path_efficiency']:.4f}")
        
        table.add_row("Redundancy Rate", 
                      f"{results['Voynich (Real)']['redundancy_cost']['redundancy_rate']:.4f}",
                      f"{results['Indifferent (H6B.2)']['redundancy_cost']['redundancy_rate']:.4f}",
                      f"{results['Optimized (H6B.1)']['redundancy_cost']['redundancy_rate']:.4f}")
        
        table.add_row("Compression Ratio", 
                      f"{results['Voynich (Real)']['compressibility']['compression_ratio']:.4f}",
                      f"{results['Indifferent (H6B.2)']['compressibility']['compression_ratio']:.4f}",
                      f"{results['Optimized (H6B.1)']['compressibility']['compression_ratio']:.4f}")
        
        console.print(table)
        
        # 4. Save Artifacts
        output_dir = Path("results/phase6_functional/phase_6b")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "phase_6b_results.json")
            
        # Generate Report
        report_path = Path("results/reports/phase6_functional/PHASE_6B_RESULTS.md")
        with open(report_path, "w") as f:
            f.write("# PHASE 6B RESULTS: EFFICIENCY AUDIT\n\n")
            f.write("## Quantitative Results\n\n")
            f.write("| Metric | Voynich (Real) | Indifferent (H6B.2) | Optimized (H6B.1) |\n")
            f.write("|--------|----------------|----------------------|-------------------|\n")
            f.write(f"| Reuse Supp. Index | {results['Voynich (Real)']['reuse_suppression']['reuse_suppression_index']:.4f} | {results['Indifferent (H6B.2)']['reuse_suppression']['reuse_suppression_index']:.4f} | {results['Optimized (H6B.1)']['reuse_suppression']['reuse_suppression_index']:.4f} |\n")
            f.write(f"| Path Efficiency | {results['Voynich (Real)']['path_efficiency']['path_efficiency']:.4f} | {results['Indifferent (H6B.2)']['path_efficiency']['path_efficiency']:.4f} | {results['Optimized (H6B.1)']['path_efficiency']['path_efficiency']:.4f} |\n")
            f.write(f"| Redundancy Rate | {results['Voynich (Real)']['redundancy_cost']['redundancy_rate']:.4f} | {results['Indifferent (H6B.2)']['redundancy_cost']['redundancy_rate']:.4f} | {results['Optimized (H6B.1)']['redundancy_cost']['redundancy_rate']:.4f} |\n")
            f.write(f"| Comp. Ratio | {results['Voynich (Real)']['compressibility']['compression_ratio']:.4f} | {results['Indifferent (H6B.2)']['compressibility']['compression_ratio']:.4f} | {results['Optimized (H6B.1)']['compressibility']['compression_ratio']:.4f} |\n\n")
            
            f.write("## Analysis\n\n")
            voynich_ratio = results['Voynich (Real)']['compressibility']['compression_ratio']
            opt_ratio = results['Optimized (H6B.1)']['compressibility']['compression_ratio']
            
            if voynich_ratio > opt_ratio + 0.05:
                f.write("- **Low Compressibility:** Voynich is significantly less compressible than an optimized system, supporting H6B.2.\n")
            elif voynich_ratio < opt_ratio:
                f.write("- **High Compressibility:** Voynich shows optimization levels consistent with or exceeding the optimized baseline, supporting H6B.1.\n")
            else:
                f.write("- **Moderate Efficiency:** Voynich shows baseline efficiency consistent with its formal structure.\n")
                
            if results['Voynich (Real)']['reuse_suppression']['reuse_suppression_index'] > 0.9:
                f.write("- **High Reuse Suppression:** The system actively avoids repeating states despite potential cost, suggesting efficiency is not a priority.\n")

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {output_dir}[/bold green]")

if __name__ == "__main__":
    run_phase_6b()
