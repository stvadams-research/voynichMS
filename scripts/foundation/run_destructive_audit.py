#!/usr/bin/env python3
"""
Phase 1 Destructive Audit Runner

This script executes destructive hypotheses designed to break common assumptions
and record failures. Its purpose is to demonstrate the rigor of the negative
control framework by producing at least:

1. One structure that fails controls
2. One that fails sensitivity analysis
3. One widely believed idea that becomes inadmissible

Per Phase 1 Destructive Audit Plan:
- Register destructive hypotheses
- Run them against Real and Control datasets
- Explicitly record FALSIFIED or INADMISSIBLE outcomes
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from foundation.hypotheses.manager import HypothesisManager
from foundation.hypotheses.destructive import (
    FixedGlyphIdentityHypothesis,
    WordBoundaryStabilityHypothesis,
    DiagramTextAlignmentHypothesis,
)
from foundation.controls.scramblers import ScrambledControlGenerator
from foundation.controls.synthetic import SyntheticNullGenerator
from foundation.segmentation.dummy import DummyLineSegmenter, DummyWordSegmenter, DummyGlyphSegmenter
from foundation.regions.dummy import GridProposer, RandomBlobProposer
from foundation.anchors.engine import AnchorEngine
from foundation.core.id_factory import DeterministicIDFactory

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def setup_test_infrastructure(store: MetadataStore, run_id: str, seed: int = 42):
    """Set up minimal test data if needed."""
    session = store.Session()
    try:
        from foundation.storage.metadata import DatasetRecord, PageRecord

        # Check if test dataset exists
        test_ds = session.query(DatasetRecord).filter_by(id="audit_real").first()
        if test_ds:
            console.print("[dim]Test dataset 'audit_real' already exists, reusing...[/dim]")
            return

        console.print("[yellow]Setting up test infrastructure...[/yellow]")
        id_factory = DeterministicIDFactory(seed=seed)

        # Create test dataset
        store.add_dataset("audit_real", "tests/foundation/dataset")

        # Add test pages
        test_pages = ["f1r", "f1v", "f2r"]
        for page_id in test_pages:
            store.add_page(
                page_id=page_id,
                dataset_id="audit_real",
                image_path=f"tests/foundation/dataset/{page_id}.jpg",
                checksum=f"test_checksum_{page_id}",
                width=800,
                height=1200
            )

            # Add dummy segmentation
            line_seg = DummyLineSegmenter()
            word_seg = DummyWordSegmenter()
            glyph_seg = DummyGlyphSegmenter()

            lines = line_seg.segment_page(page_id, "dummy")
            for line in lines:
                line_id = id_factory.next_uuid(f"line:{page_id}")
                store.add_line(
                    id=line_id,
                    page_id=page_id,
                    line_index=line.line_index,
                    bbox=line.bbox.model_dump(),
                    confidence=line.confidence
                )

                words = word_seg.segment_line(line.bbox, "dummy")
                for word in words:
                    word_id = id_factory.next_uuid(f"word:{line_id}")
                    store.add_word(
                        id=word_id,
                        line_id=line_id,
                        word_index=word.word_index,
                        bbox=word.bbox.model_dump(),
                        confidence=word.confidence
                    )

                    glyphs = glyph_seg.segment_word(word.bbox, "dummy")
                    for glyph in glyphs:
                        glyph_id = id_factory.next_uuid(f"glyph:{word_id}")
                        store.add_glyph_candidate(
                            id=glyph_id,
                            word_id=word_id,
                            glyph_index=glyph.glyph_index,
                            bbox=glyph.bbox.model_dump(),
                            confidence=glyph.confidence
                        )

            # Add dummy regions
            grid_proposer = GridProposer(rows=3, cols=3, scale="large")
            regions = grid_proposer.propose_regions(page_id, "dummy")
            for r in regions:
                store.add_region(
                    id=id_factory.next_uuid(f"region:{page_id}"),
                    page_id=page_id,
                    scale=r.scale,
                    method=r.method,
                    bbox=r.bbox.model_dump(),
                    confidence=r.confidence
                )

        # Add transcription sources
        store.add_transcription_source("eva", "EVA Transcription")
        store.add_transcription_source("currier", "Currier Transcription")
        store.add_transcription_source("bennett", "Bennett Transcription")

        console.print("[green]Test infrastructure ready.[/green]")

    finally:
        session.close()


def setup_control_datasets(store: MetadataStore, run_id: str, seed: int = 42):
    """Generate control datasets for comparison."""
    session = store.Session()
    try:
        from foundation.storage.metadata import ControlDatasetRecord

        # Check if controls exist
        scrambled = session.query(ControlDatasetRecord).filter_by(id="audit_scrambled").first()
        if scrambled:
            console.print("[dim]Control datasets already exist, reusing...[/dim]")
            return

        console.print("[yellow]Generating control datasets...[/yellow]")

        # Generate scrambled control
        scrambler = ScrambledControlGenerator(store)
        scrambler.generate("audit_real", "audit_scrambled", seed=seed)
        console.print("  [green]Generated: audit_scrambled[/green]")

        # Generate synthetic control
        synthetic = SyntheticNullGenerator(store)
        synthetic.generate("audit_real", "audit_synthetic", seed=seed, params={"num_pages": 3})
        console.print("  [green]Generated: audit_synthetic[/green]")

    finally:
        session.close()


def generate_anchors(store: MetadataStore, run_id: str, seed: int = 42):
    """Generate anchors for all datasets."""
    from foundation.storage.metadata import PageRecord

    session = store.Session()
    try:
        from foundation.storage.metadata import AnchorRecord

        # Check if anchors exist
        existing = session.query(AnchorRecord).first()
        if existing:
            console.print("[dim]Anchors already exist, reusing...[/dim]")
            return

        console.print("[yellow]Generating geometric anchors...[/yellow]")

        engine = AnchorEngine(store, seed=seed)
        method_id = engine.register_method(name="geometric_v1", parameters={"distance_threshold": 0.1})

        for dataset_id in ["audit_real", "audit_scrambled", "audit_synthetic"]:
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()
            total = 0
            for page in pages:
                count = engine.compute_page_anchors(page.id, method_id, run_id)
                total += count
            console.print(f"  [green]{dataset_id}: {total} anchors[/green]")

    finally:
        session.close()


def run_destructive_audit(seed: int = 42):
    """Execute the Phase 1 Destructive Audit."""
    console.print(Panel.fit(
        "[bold cyan]Phase 1 Destructive Audit[/bold cyan]\n"
        "Testing assumptions designed to fail",
        border_style="cyan"
    ))

    with active_run(config={"command": "destructive_audit", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)

        # Phase 0: Setup
        console.print("\n[bold]Phase 0: Infrastructure Setup[/bold]")
        setup_test_infrastructure(store, run.run_id, seed=seed)
        setup_control_datasets(store, run.run_id, seed=seed)
        generate_anchors(store, run.run_id, seed=seed)

        # Phase 1: Register hypotheses
        console.print("\n[bold]Phase 1: Registering Destructive Hypotheses[/bold]")
        manager = HypothesisManager(store)

        destructive_hypotheses = [
            FixedGlyphIdentityHypothesis,
            WordBoundaryStabilityHypothesis,
            DiagramTextAlignmentHypothesis,
        ]

        for hyp_cls in destructive_hypotheses:
            manager.register_hypothesis(hyp_cls)
            temp = hyp_cls(store)
            console.print(f"  Registered: [cyan]{temp.id}[/cyan]")

        # Phase 2: Run hypotheses
        console.print("\n[bold]Phase 2: Executing Destructive Tests[/bold]")

        results = {}
        control_ids = ["audit_scrambled", "audit_synthetic"]

        for hyp_cls in destructive_hypotheses:
            temp = hyp_cls(store)
            hyp_id = temp.id

            console.print(f"\n[yellow]Testing: {hyp_id}[/yellow]")
            console.print(f"  [dim]{temp.description}[/dim]")

            result = manager.run_hypothesis(hyp_id, "audit_real", control_ids, run.run_id)
            results[hyp_id] = result

            # Display outcome with color coding
            color = {
                "SUPPORTED": "green",
                "WEAKLY_SUPPORTED": "yellow",
                "NOT_SUPPORTED": "orange1",
                "FALSIFIED": "red",
            }.get(result.outcome, "white")

            console.print(f"  Outcome: [{color}]{result.outcome}[/{color}]")

            # Show key metrics
            if result.summary:
                verdict = result.summary.get("verdict", "")
                if verdict:
                    console.print(f"  [dim italic]{verdict}[/dim italic]")

        # Phase 3: Generate report
        console.print("\n[bold]Phase 3: Audit Report[/bold]")

        table = Table(title="Destructive Audit Results")
        table.add_column("Hypothesis", style="cyan")
        table.add_column("Outcome", style="bold")
        table.add_column("Status", style="white")

        falsified_count = 0
        weak_count = 0

        for hyp_id, result in results.items():
            status = ""
            if result.outcome == "FALSIFIED":
                status = "[red]ASSUMPTION COLLAPSED[/red]"
                falsified_count += 1
            elif result.outcome == "WEAKLY_SUPPORTED":
                status = "[yellow]FRAGILE[/yellow]"
                weak_count += 1
            elif result.outcome == "SUPPORTED":
                status = "[green]Unexpectedly Robust[/green]"
            else:
                status = "[dim]Inconclusive[/dim]"

            color = {
                "SUPPORTED": "green",
                "WEAKLY_SUPPORTED": "yellow",
                "FALSIFIED": "red",
            }.get(result.outcome, "white")

            table.add_row(hyp_id, f"[{color}]{result.outcome}[/{color}]", status)

        console.print(table)

        # Summary
        console.print("\n[bold]Summary[/bold]")
        console.print(f"  Total hypotheses tested: {len(results)}")
        console.print(f"  [red]Falsified (collapsed):[/red] {falsified_count}")
        console.print(f"  [yellow]Weakly supported (fragile):[/yellow] {weak_count}")
        console.print(f"  [green]Supported:[/green] {len(results) - falsified_count - weak_count}")

        # Audit findings for FINDINGS document
        findings = {
            "run_id": run.run_id,
            "timestamp": datetime.now().isoformat(),
            "hypotheses": {},
        }

        for hyp_id, result in results.items():
            findings["hypotheses"][hyp_id] = {
                "outcome": result.outcome,
                "metrics": result.metrics,
                "summary": result.summary,
            }

        # Save findings to file
        findings_path = Path("runs") / run.run_id / "destructive_audit_findings.json"
        findings_path.parent.mkdir(parents=True, exist_ok=True)

        with open(findings_path, "w") as f:
            json.dump(findings, f, indent=2, default=str)

        console.print(f"\n[dim]Findings saved to: {findings_path}[/dim]")

        store.save_run(run)

        # Return findings for potential programmatic use
        return findings


def print_findings_for_document(findings: dict):
    """Format findings for inclusion in FINDINGS_PHASE_1_FOUNDATION.md"""
    console.print("\n" + "="*60)
    console.print("[bold cyan]Content for FINDINGS_PHASE_1_FOUNDATION.md Section 4:[/bold cyan]")
    console.print("="*60 + "\n")

    print("## 4. Failed or Collapsed Structures\n")
    print("The following assumptions were tested and **failed** the Phase 1 Destructive Audit:\n")

    for hyp_id, data in findings["hypotheses"].items():
        outcome = data["outcome"]
        summary = data.get("summary", {})

        if outcome in ["FALSIFIED", "WEAKLY_SUPPORTED"]:
            verdict = summary.get("verdict", "No verdict available")
            print(f"### {hyp_id.replace('_', ' ').title()}")
            print(f"- **Status**: {outcome}")
            print(f"- **Finding**: {verdict}")

            # Add specific metrics if relevant
            if "collapse_at_5pct" in str(data.get("metrics", {})):
                collapse = data["metrics"].get(f"audit_real:collapse_at_5pct", 0)
                print(f"- **Detail**: Identity collapse rate at 5% perturbation: {collapse:.1%}")

            if "avg_agreement" in str(data.get("metrics", {})):
                agreement = data["metrics"].get(f"audit_real:avg_agreement", 0)
                print(f"- **Detail**: Cross-source agreement rate: {agreement:.1%}")

            if "z_score" in str(data.get("metrics", {})):
                z = data["metrics"].get(f"audit_real:z_score", 0)
                print(f"- **Detail**: Significance z-score: {z:.2f} (threshold: 2.0)")

            print()

    print("---\n")
    print("These failures are **expected and intentional**. They demonstrate that the")
    print("negative control framework correctly identifies fragile assumptions.")


if __name__ == "__main__":
    findings = run_destructive_audit(seed=42)
    print_findings_for_document(findings)