#!/usr/bin/env python3
"""
Phase 3.1: Residual Structural Constraint Extraction

Closes the synthetic-real gap by:
- Track A: Discriminative Feature Discovery
- Track B: Structural Hypothesis Formalization
- Track C: Constraint Integration and Re-Synthesis
- Track D: Equivalence Re-Testing and Termination

Goal: Exhaust reasonable structural explanations before any interpretive escalation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Dict, List, Any

from synthesis.interface import Phase3Findings
from synthesis.profile_extractor import PharmaceuticalProfileExtractor
from synthesis.text_generator import TextContinuationGenerator
from synthesis.gap_continuation import MultiGapContinuation
from synthesis.refinement.interface import Phase31Findings, EquivalenceOutcome
from synthesis.refinement.feature_discovery import DiscriminativeFeatureDiscovery
from synthesis.refinement.constraint_formalization import ConstraintFormalization
from synthesis.refinement.resynthesis import RefinedSynthesis
from synthesis.refinement.equivalence_testing import EquivalenceReTest, TerminationDecision

app = typer.Typer()
console = Console()


def display_feature_discovery(results: Dict[str, Any]):
    """Display Track A results."""
    console.print("\n[bold cyan]Track A: Discriminative Feature Discovery[/bold cyan]")

    table = Table(title="Top Discriminative Features", show_header=True)
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Feature", style="cyan")
    table.add_column("Importance", justify="right")
    table.add_column("Stable?", justify="center")

    for imp in results["importances"][:8]:
        stable = "[green]YES[/green]" if imp["stable"] else "[yellow]NO[/yellow]"
        table.add_row(
            str(imp["rank"]),
            imp["feature"],
            f"{imp['importance']:.3f}",
            stable,
        )

    console.print(table)

    console.print(f"\nFeatures tested: {results['features_tested']}")
    console.print(f"Top discriminative (importance > 0.3): {results['top_discriminative']}")
    console.print(f"Formalizable features: {len(results['formalizable_features'])}")


def display_constraint_formalization(results: Dict[str, Any]):
    """Display Track B results."""
    console.print("\n[bold cyan]Track B: Structural Hypothesis Formalization[/bold cyan]")

    console.print(f"\nFeatures attempted: {results['features_attempted']}")
    console.print(f"Successfully formalized: [green]{results['successful']}[/green]")
    console.print(f"Rejected: [red]{results['rejected']}[/red]")

    if results["validated_constraints"]:
        table = Table(title="Validated Constraints", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Bounds")

        for c in results["validated_constraints"]:
            bounds = f"{c['bounds'][0] or '-'} to {c['bounds'][1] or '-'}"
            table.add_row(c["id"], c["name"][:30], c["type"], bounds)

        console.print(table)

    if results["rejected_constraints"]:
        console.print("\n[dim]Rejected constraints:[/dim]")
        for c in results["rejected_constraints"][:3]:
            console.print(f"  - {c['id']}: {c['reason']}")


def display_resynthesis_results(results: Dict[str, Any]):
    """Display Track C results."""
    console.print("\n[bold cyan]Track C: Constraint Integration and Re-Synthesis[/bold cyan]")

    table = Table(title="Re-Synthesis Results", show_header=True)
    table.add_column("Gap ID", style="cyan")
    table.add_column("Pages Generated", justify="right")
    table.add_column("Unique", justify="right")
    table.add_column("Non-Unique?", justify="center")

    for gap_id, data in results.items():
        non_unique = "[green]YES[/green]" if data["non_uniqueness_preserved"] else "[red]NO[/red]"
        table.add_row(
            gap_id,
            str(data["pages_count"]),
            str(data["unique_pages"]),
            non_unique,
        )

    console.print(table)


def display_equivalence_results(test: Any, comparison: Dict[str, Any]):
    """Display Track D results."""
    console.print("\n[bold cyan]Track D: Equivalence Re-Testing[/bold cyan]")

    # Overall comparison
    table = Table(title="Separation Comparison", show_header=True)
    table.add_column("Comparison", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    # Real vs Scrambled
    rs_status = "[green]GOOD[/green]" if test.real_vs_scrambled > 0.7 else "[red]WEAK[/red]"
    table.add_row("Real vs Scrambled", f"{test.real_vs_scrambled:.3f}", rs_status)

    # Real vs Phase 3
    table.add_row("Real vs Phase 3 Synthetic", f"{test.real_vs_synthetic_phase3:.3f}", "[dim]baseline[/dim]")

    # Real vs Phase 3.1
    p31_status = "[green]GOOD[/green]" if test.real_vs_synthetic_phase31 < 0.3 else "[yellow]GAP[/yellow]"
    table.add_row("Real vs Phase 3.1 Synthetic", f"{test.real_vs_synthetic_phase31:.3f}", p31_status)

    # Improvement
    delta = test.phase3_to_phase31_delta
    delta_color = "green" if delta > 0.1 else ("yellow" if delta > 0 else "red")
    table.add_row("Improvement", f"[{delta_color}]{delta:+.3f}[/{delta_color}]", "")

    console.print(table)

    # Per-gap comparison
    if comparison:
        console.print("\n[bold]Per-Gap Improvement:[/bold]")
        for gap_id, data in comparison.items():
            imp = data["improvement"]
            imp_color = "green" if imp > 0.05 else ("yellow" if imp > 0 else "red")
            console.print(
                f"  {gap_id}: P3={data['phase3_separation']:.3f} → "
                f"P3.1={data['phase31_separation']:.3f} "
                f"([{imp_color}]{imp:+.3f}[/{imp_color}])"
            )


def display_outcome(findings: Phase31Findings, termination: TerminationDecision):
    """Display the final outcome."""
    outcome = findings.equivalence_test.outcome

    color_map = {
        EquivalenceOutcome.STRUCTURAL_EQUIVALENCE: "green",
        EquivalenceOutcome.SEPARATION_REDUCED: "yellow",
        EquivalenceOutcome.NO_CHANGE: "red",
        EquivalenceOutcome.DIVERGENCE: "red",
    }
    color = color_map.get(outcome, "white")

    should_term, reason = termination.should_terminate()

    console.print(Panel(
        f"[bold {color}]Outcome: {outcome.value.upper()}[/bold {color}]\n\n"
        f"{reason}\n\n"
        f"[dim]{termination.get_final_statement()}[/dim]",
        title="Phase 3.1 Determination",
        border_style=color,
    ))


@app.command()
def main(
    pages_per_gap: int = typer.Option(
        15, "--pages", "-p",
        help="Number of synthetic pages to generate per gap"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output"
    ),
):
    """Execute Phase 3.1: Residual Structural Constraint Extraction."""

    console.print(Panel.fit(
        "[bold blue]Phase 3.1: Residual Structural Constraint Extraction[/bold blue]\n"
        "[dim]Closing the Synthetic-Real Gap[/dim]",
        border_style="blue"
    ))

    findings = Phase31Findings()

    # ============================================================
    # SETUP: Extract profile and generate Phase 3 baseline
    # ============================================================
    console.print("\n[bold yellow]Setup: Extracting Section Profile[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up...", total=None)

        extractor = PharmaceuticalProfileExtractor()
        section_profile = extractor.extract_section_profile()
        gaps = extractor.define_gaps()

        # Generate Phase 3 baseline pages
        multi_gap = MultiGapContinuation(section_profile, gaps)
        phase3_results = multi_gap.run_all(pages_per_gap=pages_per_gap)

        phase3_pages = {
            gap_id: result.pages
            for gap_id, result in phase3_results.items()
        }

        progress.update(task, completed=True)

    console.print(f"[green]✓[/green] Section profile extracted, {len(gaps)} gaps defined")
    console.print(f"[green]✓[/green] Phase 3 baseline: {sum(len(p) for p in phase3_pages.values())} pages generated")

    # ============================================================
    # TRACK A: Discriminative Feature Discovery
    # ============================================================
    console.print("\n[bold yellow]Track A: Discriminative Feature Discovery[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Discovering discriminative features...", total=None)

        # Flatten Phase 3 pages
        all_phase3_pages = []
        for pages in phase3_pages.values():
            all_phase3_pages.extend(pages)

        feature_discovery = DiscriminativeFeatureDiscovery(section_profile)
        discovery_results = feature_discovery.analyze(all_phase3_pages)

        findings.features_discovered = feature_discovery.discovered_features
        findings.feature_importances = []

        progress.update(task, completed=True)

    display_feature_discovery(discovery_results)

    # ============================================================
    # TRACK B: Structural Hypothesis Formalization
    # ============================================================
    console.print("\n[bold yellow]Track B: Structural Hypothesis Formalization[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Formalizing constraints...", total=None)

        formalization = ConstraintFormalization(feature_discovery.discovered_features)
        formalization_results = formalization.formalize_all()

        findings.constraints_proposed = formalization.proposed
        findings.constraints_validated = formalization.validated
        findings.constraints_rejected = formalization.rejected

        progress.update(task, completed=True)

    display_constraint_formalization(formalization_results)

    # ============================================================
    # TRACK C: Constraint Integration and Re-Synthesis
    # ============================================================
    console.print("\n[bold yellow]Track C: Constraint Integration and Re-Synthesis[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Re-synthesizing with new constraints...", total=None)

        refined_synthesis = RefinedSynthesis(
            section_profile,
            gaps,
            formalization.get_enforceable_constraints(),
        )
        refinement_results = refined_synthesis.run_all(pages_per_gap=pages_per_gap)

        findings.refinement_results = refinement_results

        # Get Phase 3.1 pages
        phase31_pages = refined_synthesis.get_all_pages()

        progress.update(task, completed=True)

    resynthesis_display = {
        gap_id: {
            "pages_count": result.phase31_pages_count,
            "unique_pages": result.unique_pages,
            "non_uniqueness_preserved": result.non_uniqueness_preserved,
        }
        for gap_id, result in refinement_results.items()
    }
    display_resynthesis_results(resynthesis_display)

    # ============================================================
    # TRACK D: Equivalence Re-Testing
    # ============================================================
    console.print("\n[bold yellow]Track D: Equivalence Re-Testing[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running equivalence tests...", total=None)

        equiv_test = EquivalenceReTest(section_profile)
        equivalence_result = equiv_test.run_comparison(phase3_pages, phase31_pages)
        detailed_comparison = equiv_test.get_detailed_comparison(phase3_pages, phase31_pages)

        findings.equivalence_test = equivalence_result

        progress.update(task, completed=True)

    display_equivalence_results(equivalence_result, detailed_comparison)

    # ============================================================
    # TERMINATION DECISION
    # ============================================================
    console.print("\n[bold yellow]Termination Decision[/bold yellow]")

    termination = TerminationDecision(
        equivalence_result,
        len(findings.constraints_validated),
        len(findings.constraints_rejected),
    )

    should_term, reason = termination.should_terminate()
    findings.structural_refinement_exhausted = should_term
    findings.termination_reason = reason

    # Evaluate success
    findings.evaluate_success()

    display_outcome(findings, termination)

    # ============================================================
    # SUMMARY
    # ============================================================
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Phase 3.1 Summary[/bold green]",
        border_style="green"
    ))

    summary = findings.generate_summary()

    console.print(f"\n[bold]Features Discovered:[/bold] {summary['features_discovered']}")
    console.print(f"[bold]Top Features:[/bold]")
    for f in summary["top_features"][:3]:
        console.print(f"  - {f['id']}: {f['importance']:.3f}")

    console.print(f"\n[bold]Constraints:[/bold]")
    console.print(f"  Proposed: {summary['constraints_proposed']}")
    console.print(f"  Validated: {summary['constraints_validated']}")
    console.print(f"  Rejected: {summary['constraints_rejected']}")

    console.print(f"\n[bold]Equivalence:[/bold]")
    console.print(f"  Phase 3 Separation: {summary['phase3_separation']:.3f}")
    console.print(f"  Phase 3.1 Separation: {summary['phase31_separation']:.3f}")
    console.print(f"  Improvement: {summary['improvement']:+.3f}")
    console.print(f"  Outcome: {summary['equivalence_outcome']}")

    console.print(f"\n[bold]Termination:[/bold] {summary['termination_reason'][:100]}...")

    console.print("\n[dim]Phase 3.1 Complete[/dim]")

    return summary


if __name__ == "__main__":
    app()
