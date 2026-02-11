#!/usr/bin/env python3
"""
Phase 7A: Human Factors and Production Ergonomics Runner
"""

import sys
import json
from pathlib import Path
import numpy as np
from collections import defaultdict

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
from phase7_human.ergonomics import ErgonomicsAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_grouped_data(store, dataset_id="voynich_real"):
    session = store.Session()
    try:
        # Get lines grouped by page
        recs = (
            session.query(
                PageRecord.id, 
                TranscriptionLineRecord.line_index, 
                TranscriptionLineRecord.content,
                TranscriptionLineRecord.id.label("line_id")
            )
            .join(TranscriptionLineRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index)
            .all()
        )
        
        # Also get tokens for cost phase2_analysis
        token_recs = (
            session.query(TranscriptionTokenRecord.content, TranscriptionTokenRecord.line_id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .all()
        )
        
        tokens_by_line = defaultdict(list)
        for content, line_id in token_recs:
            tokens_by_line[line_id].append(content)
            
        pages = defaultdict(list)
        raw_lines = []
        for page_id, line_idx, content, line_id in recs:
            pages[page_id].append(tokens_by_line[line_id])
            raw_lines.append(content)
            
        return pages, raw_lines
    finally:
        session.close()

def run_phase_7a():
    console.print(Panel.fit(
        "[bold yellow]Phase 7A: Human Factors and Production Ergonomics[/bold yellow]\n"
        "Testing production constraints, fatigue, and effort proxies.",
        border_style="yellow"
    ))

    with active_run(config={"command": "run_7a_human_factors", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = ErgonomicsAnalyzer()
        
        # 1. Prepare Data
        console.print("\n[bold cyan]Step 1: Preparing Data[/bold cyan]")
        pages, raw_lines = get_grouped_data(store)
        console.print(f"Loaded {len(pages)} pages and {len(raw_lines)} lines.")
        
        # 2. Correction Analysis
        console.print("\n[bold cyan]Step 2: Analyzing Correction Density[/bold cyan]")
        corr_results = analyzer.calculate_correction_density(raw_lines)
        
        # 3. Fatigue Analysis
        console.print("\n[bold cyan]Step 3: Analyzing Fatigue Gradients[/bold cyan]")
        page_fatigue = []
        for page_id, lines in pages.items():
            fatigue = analyzer.analyze_page_fatigue(lines)
            if fatigue:
                page_fatigue.append(fatigue)
                
        avg_line_corr = np.nanmean([f['line_length_correlation'] for f in page_fatigue])
        avg_word_corr = np.nanmean([f['word_length_correlation'] for f in page_fatigue])
        
        # 4. Production Cost
        console.print("\n[bold cyan]Step 4: Estimating Production Cost[/bold cyan]")
        all_tokens = [t for p in pages.values() for l in p for t in l]
        cost_results = analyzer.estimate_production_cost(all_tokens)
        
        # 5. Display Results
        table = Table(title="Phase 7A: Human Factors Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Correction Count", str(corr_results['correction_count']))
        table.add_row("Uncertainty Count", str(corr_results['uncertainty_count']))
        table.add_row("Corrections per 100 lines", f"{corr_results['corrections_per_100_lines']:.2f}")
        table.add_row("Avg Line Length Corr (Fatigue)", f"{avg_line_corr:.4f}")
        table.add_row("Avg Word Length Corr (Fatigue)", f"{avg_word_corr:.4f}")
        table.add_row("Mean Strokes per Char", f"{cost_results['mean_strokes_per_char']:.2f}")
        table.add_row("Estimated Total Strokes", f"{cost_results['total_strokes']:,}")
        
        console.print(table)
        
        # 6. Save Artifacts
        output_dir = Path("results/phase7_human")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "corrections": corr_results,
            "fatigue": {
                "avg_line_length_correlation": float(avg_line_corr),
                "avg_word_length_correlation": float(avg_word_corr)
            },
            "cost": cost_results
        }
        
        ProvenanceWriter.save_results(results, output_dir / "phase_7a_results.json")
            
        # Generate Report
        report_path = Path("results/reports/phase7_human/PHASE_7A_RESULTS.md")
        with open(report_path, "w") as f:
            f.write("# PHASE 7A RESULTS: HUMAN FACTORS AND ERGONOMICS\n\n")
            f.write("## Correction and Uncertainty Density\n\n")
            f.write(f"- **Correction Count:** {corr_results['correction_count']}\n")
            f.write(f"- **Uncertainty Count:** {corr_results['uncertainty_count']}\n")
            f.write(f"- **Density:** {corr_results['corrections_per_100_lines']:.2f} corrections per 100 lines.\n\n")
            
            f.write("## Fatigue and Drift Analysis\n\n")
            f.write(f"- **Line Length Correlation:** {avg_line_corr:.4f}\n")
            f.write(f"- **Word Length Correlation:** {avg_word_corr:.4f}\n")
            f.write("  - *Interpretation:* A negative correlation would suggest fatigue (shorter lines/words as the page progresses).\n\n")
            
            f.write("## Production Effort Proxies\n\n")
            f.write(f"- **Mean Strokes per Character:** {cost_results['mean_strokes_per_char']:.2f}\n")
            f.write(f"- **Total Estimated Strokes:** {cost_results['total_strokes']:,}\n")
            f.write(f"- **Sustained Effort:** The manuscript represents approximately {cost_results['total_strokes']/1000000:.2f} million distinct mechanical pen strokes.\n\n")

            f.write("## Final Determination\n\n")
            if abs(avg_line_corr) < 0.1:
                f.write("- **High Execution Discipline:** No significant fatigue drift detected at the page level. This supports a highly disciplined, possibly ritualized or mastery-focused production mode (H7A).\n")
            else:
                f.write("- **Visible Fatigue:** Measurable drift detected, suggesting a more standard or episodic production mode.\n")

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {output_dir}[/bold green]")

if __name__ == "__main__":
    run_phase_7a()
