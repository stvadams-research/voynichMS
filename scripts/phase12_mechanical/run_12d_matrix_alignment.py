#!/usr/bin/env python3
"""Phase 12D: Matrix Alignment (Section Comparison)."""

import json
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase12_mechanical.matrix_alignment import MatrixAlignmentAnalyzer  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
ILLUS_PATH = project_root / "data" / "illustration_features.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/matrix_alignment.json"
console = Console()

def get_lines_by_section(store: MetadataStore, folio_to_section: dict) -> dict:
    """Group lines by their thematic section."""
    session = store.Session()
    try:
        rows = (
            session.query(TranscriptionTokenRecord.content, TranscriptionLineRecord.id, PageRecord.id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )

        sections = defaultdict(list)
        current_line = []
        last_line_id = None
        last_folio_id = None

        for content, line_id, folio_id in rows:
            if last_line_id is not None and line_id != last_line_id:
                section = folio_to_section.get(last_folio_id, "unknown")
                sections[section].append(current_line)
                current_line = []

            current_line.append(content)
            last_line_id = line_id
            last_folio_id = folio_id

        if current_line:
            section = folio_to_section.get(last_folio_id, "unknown")
            sections[section].append(current_line)

        return sections
    finally:
        session.close()

def main():
    console.print("[bold blue]Phase 12D: Cross-Sectional Matrix Alignment[/bold blue]")

    if not ILLUS_PATH.exists():
        console.print("[red]Error: illustration_features.json not found.[/red]")
        return

    with open(ILLUS_PATH) as f:
        illus_data = json.load(f)

    folio_to_section = {fid: fdata.get("section", "unknown") for fid, fdata in illus_data.get("folios", {}).items()}

    store = MetadataStore(DB_PATH)
    section_lines = get_lines_by_section(store, folio_to_section)

    analyzer = MatrixAlignmentAnalyzer()

    # We focus on the most data-rich comparison: Herbal vs Biological
    herbal_lines = section_lines.get("herbal", [])
    bio_lines = section_lines.get("biological", [])

    if not herbal_lines or not bio_lines:
        console.print("[yellow]Warning: Insufficient data for comparison.[/yellow]")
        return

    matrix_herbal = analyzer.build_section_matrix(herbal_lines)
    matrix_bio = analyzer.build_section_matrix(bio_lines)

    overlap = analyzer.calculate_overlap(matrix_herbal, matrix_bio)
    structural = analyzer.test_permutation_alignment(matrix_herbal, matrix_bio)

    results = {
        "comparison": "herbal_vs_biological",
        "overlap": overlap,
        "structural_similarity": structural
    }

    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Alignment saved to:[/green] {saved['latest_path']}")

    # Display Summary
    table = Table(title="Mechanical Alignment: Herbal vs Biological")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold green")

    table.add_row("Shared Contexts", str(overlap['shared_contexts']))
    table.add_row("Exact Match Rate", f"{overlap['overlap_score']*100:.1f}%")
    table.add_row("Structural Correlation", f"{structural['structural_correlation']:.3f}")
    table.add_row("Mechanically Equivalent?", "YES" if structural['is_mechanically_equivalent'] else "NO")

    console.print(table)

    if not structural['is_mechanically_equivalent']:
        console.print("\n[yellow]Interpretation:[/yellow] Low overlap and correlation suggest the Biological section uses a significantly different 'Engine state' or a different physical tool entirely.")

if __name__ == "__main__":
    main()
