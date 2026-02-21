#!/usr/bin/env python3
"""
Phase 2.4: Anomaly Characterization and Constraint Closure

Executes all four tracks of Phase 2.4:
- D1: Constraint Intersection Analysis
- D2: Anomaly Stability Analysis
- D3: Structural Capacity Bounding
- D4: Semantic Necessity Test

Produces:
- Anomaly Characterization Report
- Constraint Closure Summary
- Semantic Necessity Decision Record
- Phase 2.4 Findings Document
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

from phase2_analysis.anomaly.interface import (
    AnomalyDefinition,
    Phase24Findings,
    SemanticNecessity,
)
from phase2_analysis.anomaly.constraint_analysis import ConstraintIntersectionAnalyzer
from phase2_analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer
from phase2_analysis.anomaly.capacity_bounding import CapacityBoundingAnalyzer
from phase2_analysis.anomaly.semantic_necessity import SemanticNecessityAnalyzer

app = typer.Typer()
console = Console()


def display_anomaly_definition(anomaly: AnomalyDefinition):
    """Display the anomaly definition."""
    console.print(Panel(
        f"[bold]Information Density:[/bold] z = {anomaly.information_density_z}\n"
        f"[bold]Locality Radius:[/bold] {anomaly.locality_radius[0]}-{anomaly.locality_radius[1]} units\n"
        f"[bold]Robust Under Perturbation:[/bold] {anomaly.robustness_under_perturbation}\n\n"
        f"[dim]{anomaly.description}[/dim]",
        title="Anomaly Definition (Fixed for Phase 2.4)",
        border_style="yellow",
    ))


def display_constraint_results(results: Dict[str, Any]):
    """Display Track D1 results."""
    console.print(f"\n[bold cyan]Track D1: Constraint Intersection Analysis[/bold cyan]")

    table = Table(title="Constraints by Source", show_header=True)
    table.add_column("Source", style="cyan")
    table.add_column("Count", justify="right")

    for source, count in results["constraints_by_source"].items():
        table.add_row(source, str(count))

    console.print(table)

    console.print(f"\nTotal Constraints: {results['total_constraints']}")
    console.print(f"Total Models: {results['total_models']}")
    console.print(f"Minimal Impossibility Sets: {results['minimal_impossibility_sets']}")

    if results["exclusion_summary"]:
        console.print("\n[bold]Constraint Exclusions:[/bold]")
        for cid, models in list(results["exclusion_summary"].items())[:5]:
            console.print(f"  {cid}: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")


def display_stability_results(results: Dict[str, Any]):
    """Display Track D2 results."""
    console.print(f"\n[bold cyan]Track D2: Anomaly Stability Analysis[/bold cyan]")

    table = Table(title="Stability Envelopes", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Separation Z", justify="right")
    table.add_column("Stable?", justify="center")

    for env in results["envelopes"]:
        stable = "[green]YES[/green]" if env["is_stable"] else "[red]NO[/red]"
        table.add_row(
            env["metric"],
            f"{env['baseline']:.2f}",
            f"{env['mean']:.2f}",
            f"{env['std_dev']:.2f}",
            f"{env['separation_z']:.1f}",
            stable,
        )

    console.print(table)

    status = "[green]CONFIRMED[/green]" if results["anomaly_confirmed"] else "[yellow]UNCERTAIN[/yellow]"
    console.print(f"\nAnomaly Status: {status}")

    console.print(f"\n[bold]Sensitivity Report:[/bold]")
    sr = results["sensitivity_report"]
    console.print(f"  Segmentation sensitivity: {sr['segmentation_sensitivity']}")
    console.print(f"  Unit sensitivity: {sr['unit_sensitivity']}")
    console.print(f"  Metric sensitivity: {sr['metric_sensitivity']}")
    console.print(f"  Overall: {sr['overall_sensitivity']}")


def display_capacity_results(results: Dict[str, Any]):
    """Display Track D3 results."""
    console.print(f"\n[bold cyan]Track D3: Structural Capacity Bounding[/bold cyan]")

    table = Table(title="Capacity Bounds", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Bound Type")
    table.add_column("Value", justify="right")
    table.add_column("Derived From")

    for b in results["bounds_detail"]:
        table.add_row(
            b["property"],
            b["type"],
            f"{b['value']:.1f}",
            ", ".join(b["derived_from"][:2]),
        )

    console.print(table)

    console.print(f"\n[bold]System Class Evaluation:[/bold]")
    console.print(f"  Consistent classes: {', '.join(results['consistent_classes'])}")
    console.print(f"  Excluded classes: {len(results['excluded_classes'])}")

    if results["excluded_classes"]:
        console.print("\n  [dim]Exclusion reasons:[/dim]")
        for exc in results["excluded_classes"][:3]:
            console.print(f"    - {exc['name']}: {exc['reason'][:60]}...")

    console.print(f"\n[bold]Feasibility Region:[/bold]")
    fr = results["feasibility_region"]
    feasible = "[green]FEASIBLE[/green]" if fr["is_feasible"] else "[red]NOT FEASIBLE[/red]"
    console.print(f"  Status: {feasible}")
    console.print(f"  Required Properties:")
    for prop in fr["required_properties"][:4]:
        console.print(f"    - {prop}")


def display_semantic_results(results: Dict[str, Any]):
    """Display Track D4 results."""
    console.print(f"\n[bold cyan]Track D4: Semantic Necessity Test[/bold cyan]")

    table = Table(title="Non-Semantic System Tests", show_header=True)
    table.add_column("System", style="cyan")
    table.add_column("Info Density", justify="right")
    table.add_column("Locality", justify="right")
    table.add_column("Robustness", justify="right")
    table.add_column("Passes?", justify="center")

    for s in results["system_details"]:
        passes = "[green]YES[/green]" if s["passes"] else "[red]NO[/red]"
        # Use measured values if available, otherwise use theoretical bounds
        measured = s.get("measured_values", {})
        bounds = s.get("theoretical_bounds", {})
        info_density = measured.get("info_density") or bounds.get("max_info_density", 0)
        locality = measured.get("locality") or bounds.get("min_locality", 0)
        robustness = measured.get("robustness") or bounds.get("max_robustness", 0)

        info_str = f"{info_density:.1f}" if info_density else "-"
        loc_str = f"{locality:.1f}" if locality else "-"
        rob_str = f"{robustness:.2f}" if robustness else "-"

        table.add_row(
            s["name"][:25],
            info_str,
            loc_str,
            rob_str,
            passes,
        )

    console.print(table)

    console.print(f"\nSystems Tested: {results['systems_tested']}")
    console.print(f"Systems Passed: [green]{results['systems_passed']}[/green]")
    console.print(f"Systems Failed: [red]{results['systems_failed']}[/red]")

    # Assessment with color
    assessment = results["assessment"]
    color_map = {
        "definitely_necessary": "red",
        "likely_necessary": "yellow",
        "possibly_necessary": "cyan",
        "not_necessary": "green",
    }
    color = color_map.get(assessment, "white")
    console.print(f"\n[bold]Assessment:[/bold] [{color}]{assessment.upper()}[/{color}]")
    console.print(f"Confidence: {results['confidence']:.0%}")

    console.print(f"\n[bold]Evidence FOR Semantics:[/bold]")
    for e in results["evidence_for_semantics"][:3]:
        console.print(f"  - {e}")

    console.print(f"\n[bold]Evidence AGAINST Semantics:[/bold]")
    for e in results["evidence_against_semantics"][:3]:
        console.print(f"  - {e}")


def display_phase3_decision(results: Dict[str, Any]):
    """Display the Phase 3 decision."""
    justified = results["phase_3_justified"]

    if justified:
        console.print(Panel(
            f"[bold green]Phase 3 is JUSTIFIED[/bold green]\n\n"
            f"{results['justification']}\n\n"
            f"[dim]Semantic investigation may proceed.[/dim]",
            title="Phase 3 Decision",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold yellow]Phase 3 is NOT JUSTIFIED[/bold yellow]\n\n"
            f"{results['justification']}\n\n"
            f"[dim]Additional structural phase2_analysis recommended.[/dim]",
            title="Phase 3 Decision",
            border_style="yellow",
        ))


@app.command()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output"
    ),
    seed: int = typer.Option(
        42, "--seed",
        help="Random seed (default: 42)"
    ),
    output_dir: str = typer.Option(
        None, "--output-dir",
        help="Override output directory"
    ),
):
    """Execute Phase 2.4: Anomaly Characterization and Constraint Closure."""

    console.print(Panel.fit(
        "[bold blue]Phase 2.4: Anomaly Characterization[/bold blue]\n"
        "[dim]Characterizing the unresolved anomaly from Phase 2.3[/dim]",
        border_style="blue"
    ))

    # Define the anomaly
    anomaly = AnomalyDefinition()
    display_anomaly_definition(anomaly)

    findings = Phase24Findings(anomaly=anomaly)

    # ============================================================
    # TRACK D1: Constraint Intersection Analysis
    # ============================================================
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running Track D1: Constraint Analysis...", total=None)

        analyzer_d1 = ConstraintIntersectionAnalyzer()
        results_d1 = analyzer_d1.analyze()

        findings.constraints = analyzer_d1.constraints
        findings.intersections = analyzer_d1.all_intersections
        findings.minimal_impossibility_sets = analyzer_d1.minimal_sets

        progress.update(task, completed=True)

    display_constraint_results(results_d1)

    # ============================================================
    # TRACK D2: Anomaly Stability Analysis
    # ============================================================
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running Track D2: Stability Analysis...", total=None)

        analyzer_d2 = AnomalyStabilityAnalyzer()
        results_d2 = analyzer_d2.analyze()

        findings.stability_envelopes = analyzer_d2.envelopes
        findings.anomaly_confirmed = results_d2["anomaly_confirmed"]

        progress.update(task, completed=True)

    display_stability_results(results_d2)

    # ============================================================
    # TRACK D3: Structural Capacity Bounding
    # ============================================================
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running Track D3: Capacity Bounding...", total=None)

        analyzer_d3 = CapacityBoundingAnalyzer()
        results_d3 = analyzer_d3.analyze()

        findings.feasibility_region = analyzer_d3.feasibility_region

        progress.update(task, completed=True)

    display_capacity_results(results_d3)

    # ============================================================
    # TRACK D4: Semantic Necessity Test
    # ============================================================
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running Track D4: Semantic Necessity...", total=None)

        analyzer_d4 = SemanticNecessityAnalyzer()
        results_d4 = analyzer_d4.analyze()

        findings.semantic_necessity = analyzer_d4.result

        progress.update(task, completed=True)

    display_semantic_results(results_d4)

    # ============================================================
    # PHASE 3 DECISION
    # ============================================================
    console.print("\n")
    display_phase3_decision(results_d4)

    # Update findings
    findings.phase_3_decision = results_d4["phase_3_justified"]

    # ============================================================
    # FINDINGS SUMMARY
    # ============================================================
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Phase 2.4 Findings Summary[/bold green]",
        border_style="green"
    ))

    summary = findings.generate_summary()

    console.print(f"\n[bold]Anomaly Characterization:[/bold]")
    console.print(f"  Information Density: z = {summary['anomaly']['information_density_z']}")
    console.print(f"  Locality: {summary['anomaly']['locality_radius']} units")
    console.print(f"  Confirmed: {'YES' if summary['anomaly_confirmed'] else 'NO'}")

    console.print(f"\n[bold]Constraint Analysis:[/bold]")
    console.print(f"  Constraints Analyzed: {summary['constraints_analyzed']}")
    console.print(f"  Minimal Impossibility Sets: {summary['minimal_impossibility_sets']}")

    console.print(f"\n[bold]Feasibility Region:[/bold]")
    console.print(f"  Is Feasible: {summary['feasibility_region']['is_feasible']}")
    console.print(f"  Excluded Classes: {len(summary['feasibility_region']['excluded_classes'])}")

    console.print(f"\n[bold]Semantic Necessity:[/bold]")
    console.print(f"  Assessment: {summary['semantic_necessity']['assessment']}")
    console.print(f"  Confidence: {summary['semantic_necessity']['confidence']:.0%}")
    console.print(f"  Phase 3 Justified: {summary['semantic_necessity']['phase_3_justified']}")

    # Final determination
    if findings.phase_3_decision:
        console.print(f"\n[bold green]DETERMINATION: Proceed to Phase 3[/bold green]")
        findings.termination_reason = "Semantic necessity established"
    else:
        console.print(f"\n[bold yellow]DETERMINATION: Phase 2 terminates with integrity[/bold yellow]")
        findings.termination_reason = "Structural explanation sufficient or inconclusive"

    console.print("\n[dim]Phase 2.4 Complete[/dim]")

    return {
        "findings": summary,
        "constraint_results": results_d1,
        "stability_results": results_d2,
        "capacity_results": results_d3,
        "semantic_results": results_d4,
    }


if __name__ == "__main__":
    app()
