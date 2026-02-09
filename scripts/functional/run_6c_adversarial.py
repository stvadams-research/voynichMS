#!/usr/bin/env python3
"""
Phase 6C: Adversarial vs Indifferent Structure Test Runner
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

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord, PageRecord
from functional.adversarial.metrics import AdversarialAnalyzer
from functional.formal_system.simulators import LatticeTraversalSimulator
from functional.adversarial.simulators import AdversarialLatticeSimulator

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

def run_phase_6c():
    console.print(Panel.fit(
        "[bold red]Phase 6C: Adversarial vs Indifferent Structure Test[/bold red]\n"
        "Testing for evidence of active resistance to inference and learnability.",
        border_style="red"
    ))

    with active_run(config={"command": "run_6c_adversarial", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = AdversarialAnalyzer()
        
        # 1. Prepare Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_real_lines(store)
        num_lines = len(real_lines)
        console.print(f"Loaded {num_lines} real lines.")
        
        # H6C.1: Indifferent (Formal system from 6A)
        indifferent_sim = LatticeTraversalSimulator(vocab_size=5000, seed=42)
        indifferent_lines = indifferent_sim.generate_corpus(num_lines=num_lines, line_len=8)
        
        # H6C.2: Adversarial (Section-variant rules, decoys)
        adversarial_sim = AdversarialLatticeSimulator(vocab_size=5000, seed=42)
        adversarial_lines = adversarial_sim.generate_corpus_adversarial(num_lines=num_lines, line_len=8, sections=10)
        
        datasets = {
            "Voynich (Real)": real_lines,
            "Indifferent (H6C.1)": indifferent_lines,
            "Adversarial (H6C.2)": adversarial_lines
        }
        
        # 2. Run Audit
        results = {}
        for label, lines in datasets.items():
            console.print(f"\n[bold blue]Auditing {label}...[/bold blue]")
            results[label] = analyzer.run_adversarial_audit(lines)
            
        # 3. Display Results
        table = Table(title="Phase 6C: Adversarial Signature Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Voynich (Real)", justify="right")
        table.add_column("Indifferent (H6C.1)", justify="right")
        table.add_column("Adversarial (H6C.2)", justify="right")
        
        table.add_row("Final Predict. Acc.", 
                      f"{results['Voynich (Real)']['learnability']['final_accuracy']:.4f}",
                      f"{results['Indifferent (H6C.1)']['learnability']['final_accuracy']:.4f}",
                      f"{results['Adversarial (H6C.2)']['learnability']['final_accuracy']:.4f}")
        
        table.add_row("Monotonic Learn.?", 
                      str(results['Voynich (Real)']['learnability']['is_monotonic']),
                      str(results['Indifferent (H6C.1)']['learnability']['is_monotonic']),
                      str(results['Adversarial (H6C.2)']['learnability']['is_monotonic']))
        
        table.add_row("Decoy Rule Rate", 
                      f"{results['Voynich (Real)']['decoy_regularity']['decoy_rate']:.4f}",
                      f"{results['Indifferent (H6C.1)']['decoy_regularity']['decoy_rate']:.4f}",
                      f"{results['Adversarial (H6C.2)']['decoy_regularity']['decoy_rate']:.4f}")
        
        table.add_row("Ent. Reduction (bits)", 
                      f"{results['Voynich (Real)']['conditioning_sensitivity']['entropy_reduction']:.4f}",
                      f"{results['Indifferent (H6C.1)']['conditioning_sensitivity']['entropy_reduction']:.4f}",
                      f"{results['Adversarial (H6C.2)']['conditioning_sensitivity']['entropy_reduction']:.4f}")
        
        table.add_row("Conditioning Paradox?", 
                      str(results['Voynich (Real)']['conditioning_sensitivity']['is_paradoxical']),
                      str(results['Indifferent (H6C.1)']['conditioning_sensitivity']['is_paradoxical']),
                      str(results['Adversarial (H6C.2)']['conditioning_sensitivity']['is_paradoxical']))
        
        console.print(table)
        
        # 4. Save Artifacts
        output_dir = Path("results/functional/phase_6c")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "phase_6c_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        # Generate Report
        report_path = Path("reports/functional/PHASE_6C_RESULTS.md")
        with open(report_path, "w") as f:
            f.write("# PHASE 6C RESULTS: ADVERSARIAL VS INDIFFERENT\n\n")
            f.write("## Quantitative Results\n\n")
            f.write("| Metric | Voynich (Real) | Indifferent (H6C.1) | Adversarial (H6C.2) |\n")
            f.write("|--------|----------------|----------------------|-------------------|\n")
            f.write(f"| Predict. Acc. | {results['Voynich (Real)']['learnability']['final_accuracy']:.4f} | {results['Indifferent (H6C.1)']['learnability']['final_accuracy']:.4f} | {results['Adversarial (H6C.2)']['learnability']['final_accuracy']:.4f} |\n")
            f.write(f"| Decoy Rate | {results['Voynich (Real)']['decoy_regularity']['decoy_rate']:.4f} | {results['Indifferent (H6C.1)']['decoy_regularity']['decoy_rate']:.4f} | {results['Adversarial (H6C.2)']['decoy_regularity']['decoy_rate']:.4f} |\n")
            f.write(f"| Ent. Reduction | {results['Voynich (Real)']['conditioning_sensitivity']['entropy_reduction']:.4f} | {results['Indifferent (H6C.1)']['conditioning_sensitivity']['entropy_reduction']:.4f} | {results['Adversarial (H6C.2)']['conditioning_sensitivity']['entropy_reduction']:.4f} |\n\n")
            
            f.write("## Analysis\n\n")
            if not results['Voynich (Real)']['learnability']['is_monotonic']:
                f.write("- **Non-Monotonic Learnability:** Predictability does not increase smoothly with data, suggesting potential adversarial state-switching or high noise.\n")
            else:
                f.write("- **Monotonic Learnability:** Predictability increases smoothly, supporting H6C.1 (Formal Indifference).\n")
                
            if results['Voynich (Real)']['conditioning_sensitivity']['is_paradoxical']:
                f.write("- **Conditioning Paradox Detected:** Adding context increases ambiguity, a signature of adversarial misdirection (H6C.2).\n")
            else:
                f.write("- **Normal Conditioning:** Adding context reduces entropy, consistent with indifferent formal structure.\n")

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {output_dir}[/bold green]")

if __name__ == "__main__":
    run_phase_6c()