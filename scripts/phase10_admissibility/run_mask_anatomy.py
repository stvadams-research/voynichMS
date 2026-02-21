#!/usr/bin/env python3
"""
Mask Anatomy Runner

Executes Change-Point Detection, Thematic Correlation, and Bottleneck Estimation.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase10_admissibility.mask_anatomy.correlator import ThematicMaskCorrelator  # noqa: E402
from phase10_admissibility.mask_anatomy.estimator import MaskStateEstimator  # noqa: E402
from phase10_admissibility.mask_anatomy.mapper import SlidingResidualMapper  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
ILLUS_PATH = project_root / "data" / "illustration_features.json"
OUTPUT_PATH = project_root / "results/data/phase10_admissibility/mask_anatomy_results.json"

console = Console()

def get_tokens_and_folios(store: MetadataStore, dataset_id: str) -> tuple[list[str], list[str]]:
    """Extract tokens and their folio IDs."""
    session = store.Session()
    try:
        rows = (
            session.query(TranscriptionTokenRecord.content, PageRecord.id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )
        tokens = [r[0] for r in rows]
        folios = [r[1] for r in rows]
        return tokens, folios
    finally:
        session.close()

def main():
    console.print("[bold blue]Voynich Mask Anatomy Analysis[/bold blue]")

    if not Path("data/voynich.db").exists():
        console.print("[red]Error: data/voynich.db not found.[/red]")
        return

    store = MetadataStore(DB_PATH)
    tokens, folios = get_tokens_and_folios(store, "voynich_real")

    # 1. Map Corpus (Change-Point Detection)
    mapper = SlidingResidualMapper(window_size=1000, step_size=200)
    map_results = mapper.map_corpus(tokens, folios)

    # 2. Thematic Correlation
    correlator_results = {}
    if ILLUS_PATH.exists():
        with ILLUS_PATH.open("r") as f:
            illus_data = json.load(f)
        correlator = ThematicMaskCorrelator(illus_data)
        correlator_results = correlator.correlate(map_results['series'])

    # 3. Hardware Bottleneck Estimation
    estimator = MaskStateEstimator()
    bottleneck_results = estimator.estimate_bottleneck(map_results['series'])

    final_output = {
        "mapping": map_results,
        "thematic_correlation": correlator_results,
        "bottleneck": bottleneck_results
    }

    saved = ProvenanceWriter.save_results(final_output, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Saved to:[/green] {saved['latest_path']}")

    # --- Summary Display ---

    # Table 1: Change Points
    cp_table = Table(title="Detected Mask Change-Points (Jumps)")
    cp_table.add_column("Token Index", justify="right")
    cp_table.add_column("Folio(s)", style="cyan")
    cp_table.add_column("Jump Magnitude", justify="right", style="bold red")
    for cp in map_results['change_points'][:10]: # Top 10
        cp_table.add_row(str(cp['token_index']), ", ".join(cp['folio_ids'][:3]), f"{cp['magnitude']:.2f}")
    console.print(cp_table)

    # Table 2: Thematic Profiles
    if correlator_results:
        th_table = Table(title="Mask Profiles by Illustration Section")
        th_table.add_column("Section", style="cyan")
        th_table.add_column("Mean Residual (z)", justify="right")
        th_table.add_column("Std Dev", justify="right")
        for section, s_data in correlator_results['stats_by_section'].items():
            th_table.add_row(section, f"{s_data['mean_z']:.3f}", f"{s_data['std_z']:.3f}")
        console.print(th_table)

        sig = correlator_results['anova']['is_significant']
        console.print(f"Thematic Significance (ANOVA): [bold]{'POSITIVE' if sig else 'NEGATIVE'}[/bold] (p={correlator_results['anova']['p_value']:.4e})")

    # Hardware Conjecture
    console.print(f"\n[bold green]Hardware Conjecture:[/bold green] {bottleneck_results['hardware_conjecture']}")
    console.print(f"Effective States: {bottleneck_results['effective_discrete_states']:.1f} (~{bottleneck_results['estimated_mask_bits']:.1f} bits)")

if __name__ == "__main__":
    main()
