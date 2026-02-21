#!/usr/bin/env python3
"""
Phase 3.2.1: Synthesis Baseline Assessment (The Gap Analysis)

Benchmarks the current Constrained Markov Generator against the 
real Voynich Manuscript metrics (Z-score 5.68, Locality 2-4).

Objectives:
1. Generate 50 synthetic pages using current logic.
2. Register them as 'synthesis_baseline' dataset.
3. Compute RepetitionRate, InformationDensity, and Locality.
4. Compare with 'voynich_real' metrics.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.id_factory import DeterministicIDFactory  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402

# Phase 2 metrics library
from phase1_foundation.metrics.library import RepetitionRate  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import DatasetRecord, MetadataStore  # noqa: E402
from phase2_analysis.stress_tests.information_preservation import (
    InformationPreservationTest,  # noqa: E402
)
from phase2_analysis.stress_tests.locality import LocalityTest  # noqa: E402
from phase3_synthesis.interface import GapDefinition, GapStrength  # noqa: E402
from phase3_synthesis.profile_extractor import PharmaceuticalProfileExtractor  # noqa: E402
from phase3_synthesis.text_generator import TextContinuationGenerator  # noqa: E402

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 3.2.1: Synthesis Baseline Assessment")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def _dataset_exists(store: MetadataStore, dataset_id: str) -> bool:
    session = store.Session()
    try:
        return session.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first() is not None
    finally:
        session.close()

def main(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 3.2.1: Baseline Gap Analysis[/bold blue]\n"
        "Benchmarking current generator against real metrics",
        border_style="blue"
    ))

    # Force real computation
    # (In a real scenario, we might set an env var, but here we assume config defaults or env is set)

    with active_run(config={"command": "baseline_assessment", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        id_factory = DeterministicIDFactory(seed=seed)

        # 1. Setup Generator
        console.print("\n[bold yellow]Step 1: initializing Generator[/bold yellow]")
        extractor = PharmaceuticalProfileExtractor(store)
        profile = extractor.extract_section_profile()

        # Define a test gap (Gap A)
        gap_a = GapDefinition(
            gap_id="gap_a",
            strength=GapStrength.STRONG,
            preceding_page="f88v",
            following_page="f89r"
        )

        generator = TextContinuationGenerator(profile)

        # 2. Generate Pages
        console.print("\n[bold yellow]Step 2: Generating 5 Synthetic Pages[/bold yellow]")
        synthetic_pages = generator.generate_multiple(gap_id="gap_a", count=5)
        console.print(f"Generated {len(synthetic_pages)} pages.")

        # 3. Register as Dataset 'synthesis_baseline'
        console.print("\n[bold yellow]Step 3: Registering Dataset[/bold yellow]")
        dataset_id = "synthesis_baseline"

        # Clean up previous run if exists
        session = store.Session()
        try:
            # Delete existing pages for this dataset to avoid conflicts
            # (Simplified support_cleanup)
            pass
        finally:
            session.close()

        store.add_dataset(dataset_id, "generated")

        # Ingest pages into DB
        session = store.Session()
        try:
            for i, page in enumerate(synthetic_pages):
                page_id = f"syn_base_{i}"
                store.add_page(
                    page_id=page_id,
                    dataset_id=dataset_id,
                    image_path="placeholder.jpg",
                    checksum=f"hash_{i}",
                    width=1000,
                    height=1500
                )

                # Ingest text structure
                for jar_idx, text_block in enumerate(page.text_blocks):
                    # Create a dummy line for this block
                    line_id = id_factory.next_uuid(f"line:{page_id}:{jar_idx}")
                    store.add_line(
                        id=line_id,
                        page_id=page_id,
                        line_index=jar_idx,
                        bbox={"x":0, "y":0, "w":0, "h":0},
                        confidence=1.0
                    )

                    # Add words
                    for w_idx, token in enumerate(text_block):
                        word_id = id_factory.next_uuid(f"word:{line_id}:{w_idx}")
                        store.add_word(
                            id=word_id,
                            line_id=line_id,
                            word_index=w_idx,
                            bbox={"x":0, "y":0, "w":0, "h":0},
                            confidence=1.0
                        )
                    # Repetition and stress tests read transcription tokens.
                    trans_line_id = id_factory.next_uuid(f"trans_line:{page_id}:{jar_idx}")
                    store.add_transcription_line(
                        id=trans_line_id,
                        source_id="synthetic",
                        page_id=page_id,
                        line_index=jar_idx,
                        content=" ".join(text_block)
                    )

                    for w_idx, token in enumerate(text_block):
                        token_id = id_factory.next_uuid(f"trans_token:{trans_line_id}:{w_idx}")
                        store.add_transcription_token(
                            id=token_id,
                            line_id=trans_line_id,
                            token_index=w_idx,
                            content=token
                        )

            session.commit()
        finally:
            session.close()

        console.print(f"Registered {len(synthetic_pages)} pages to {dataset_id}")

        # 4. Run Metrics
        console.print("\n[bold yellow]Step 4: Benchmarking[/bold yellow]")

        rep_metric = RepetitionRate(store)

        # Compute targets from actual voynich_real dataset (not hardcoded)
        real_rep_results = rep_metric.calculate("voynich_real")
        target_rep = real_rep_results[0].value if real_rep_results else None

        # Synthetic repetition rate
        syn_rep_results = rep_metric.calculate(dataset_id)
        syn_rep = syn_rep_results[0].value if syn_rep_results else None

        # Compute information density and locality using stress-test implementations.
        controls = ["shuffled_global"]
        missing_controls = [cid for cid in controls if not _dataset_exists(store, cid)]
        if missing_controls:
            raise RuntimeError(
                "Missing required control dataset(s) for baseline assessment: "
                + ", ".join(missing_controls)
                + ". Run scripts/phase4_inference/build_corpora.py first."
            )

        info_test = InformationPreservationTest(store)
        real_info = info_test.run("constructed_system", "voynich_real", controls)
        syn_info = info_test.run("constructed_system", dataset_id, controls)
        target_z = real_info.metrics.get("z_score")
        syn_z = syn_info.metrics.get("z_score")

        locality_test = LocalityTest(store)
        real_loc = locality_test.run("constructed_system", "voynich_real", controls)
        syn_loc_res = locality_test.run("constructed_system", dataset_id, controls)
        target_loc = real_loc.metrics.get("locality_radius")
        syn_loc = syn_loc_res.metrics.get("locality_radius")

        # 5. Display Results
        table = Table(title="Baseline Gap Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Real (Computed)", style="green")
        table.add_column("Baseline Synthetic", style="yellow")
        table.add_column("Gap", style="red")

        def fmt(val):
            return f"{val:.4f}" if val is not None else "UNAVAILABLE"

        def gap(a, b):
            if a is not None and b is not None:
                return f"{a - b:.4f}"
            return "N/A"

        table.add_row("Repetition Rate", fmt(target_rep), fmt(syn_rep), gap(target_rep, syn_rep))
        table.add_row("Info Density (Z)", fmt(target_z), fmt(syn_z), gap(target_z, syn_z))
        table.add_row("Locality Radius", fmt(target_loc), fmt(syn_loc), gap(target_loc, syn_loc))

        console.print(table)

        # Save Gap Analysis
        findings = {
            "repetition_rate": {
                "target": target_rep,
                "synthetic": syn_rep,
                "gap": (target_rep - syn_rep) if target_rep is not None and syn_rep is not None else None,
            },
            "info_density_z": {
                "target": target_z,
                "synthetic": syn_z,
                "gap": (target_z - syn_z) if target_z is not None and syn_z is not None else None,
                "control_datasets": controls,
            },
            "locality": {
                "target": target_loc,
                "synthetic": syn_loc,
                "gap": (target_loc - syn_loc) if target_loc is not None and syn_loc is not None else None,
                "control_datasets": controls,
            }
        }

        # Save results with provenance
        out = Path(output_dir) if output_dir else Path("core_status/phase3_synthesis")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(findings, out / "BASELINE_GAP_ANALYSIS.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    main(seed=args.seed, output_dir=args.output_dir)
    sys.exit(0)
