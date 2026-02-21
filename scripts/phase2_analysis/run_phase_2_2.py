#!/usr/bin/env python3
"""
Phase 2.2 Execution Script: Constraint Tightening

This script executes the three stress test tracks to tighten constraints
on admissible explanation classes:

- Track B1: Mapping Stability Tests
- Track B2: Information Preservation Tests
- Track B3: Locality and Compositionality Tests

Per Phase 2.2 Execution Plan:
- Only tests ADMISSIBLE and UNDERCONSTRAINED classes from Phase 2.1
- Does not attempt translation or interpretation
- Produces Mapping Stress Test Report for each class
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from phase1_foundation.core.provenance import ProvenanceWriter

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, ExplanationClassRecord
from phase2_analysis.stress_tests.interface import StressTestOutcome
from phase2_analysis.stress_tests.mapping_stability import MappingStabilityTest
from phase2_analysis.stress_tests.information_preservation import InformationPreservationTest
from phase2_analysis.stress_tests.locality import LocalityTest

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

# Classes eligible for Phase 2.2 testing
ELIGIBLE_CLASSES = ["constructed_system", "visual_grammar", "hybrid_system"]


def get_admissible_classes(store: MetadataStore) -> List[str]:
    """Get explanation classes eligible for Phase 2.2 testing."""
    session = store.Session()
    try:
        classes = session.query(ExplanationClassRecord).filter(
            ExplanationClassRecord.status.in_(["admissible", "underconstrained"])
        ).all()
        return [c.id for c in classes if c.id in ELIGIBLE_CLASSES]
    finally:
        session.close()


def run_track_b1(store: MetadataStore, classes: List[str],
                 dataset_id: str, control_ids: List[str]) -> Dict[str, Any]:
    """Execute Track B1: Mapping Stability Tests."""
    console.print("\n[bold cyan]Track B1: Mapping Stability Tests[/bold cyan]")

    test = MappingStabilityTest(store)
    results = {}

    for class_id in classes:
        if not test.applies_to(class_id):
            continue

        console.print(f"  Testing: [yellow]{class_id}[/yellow]")
        result = test.run(class_id, dataset_id, control_ids)
        results[class_id] = result

        # Display outcome
        color = {
            StressTestOutcome.STABLE: "green",
            StressTestOutcome.FRAGILE: "yellow",
            StressTestOutcome.COLLAPSED: "red",
            StressTestOutcome.INDISTINGUISHABLE: "red",
            StressTestOutcome.INCONCLUSIVE: "dim",
        }.get(result.outcome, "white")

        console.print(f"    Outcome: [{color}]{result.outcome.value.upper()}[/{color}]")
        console.print(f"    Stability: {result.stability_score:.2f}")
        console.print(f"    [dim]{result.summary}[/dim]")

    return results


def run_track_b2(store: MetadataStore, classes: List[str],
                 dataset_id: str, control_ids: List[str]) -> Dict[str, Any]:
    """Execute Track B2: Information Preservation Tests."""
    console.print("\n[bold cyan]Track B2: Information Preservation Tests[/bold cyan]")

    test = InformationPreservationTest(store)
    results = {}

    for class_id in classes:
        if not test.applies_to(class_id):
            continue

        console.print(f"  Testing: [yellow]{class_id}[/yellow]")
        result = test.run(class_id, dataset_id, control_ids)
        results[class_id] = result

        color = {
            StressTestOutcome.STABLE: "green",
            StressTestOutcome.FRAGILE: "yellow",
            StressTestOutcome.COLLAPSED: "red",
            StressTestOutcome.INDISTINGUISHABLE: "red",
            StressTestOutcome.INCONCLUSIVE: "dim",
        }.get(result.outcome, "white")

        console.print(f"    Outcome: [{color}]{result.outcome.value.upper()}[/{color}]")
        console.print(f"    Control Differential: {result.control_differential:.2f}")
        console.print(f"    [dim]{result.summary}[/dim]")

    return results


def run_track_b3(store: MetadataStore, classes: List[str],
                 dataset_id: str, control_ids: List[str]) -> Dict[str, Any]:
    """Execute Track B3: Locality and Compositionality Tests."""
    console.print("\n[bold cyan]Track B3: Locality & Compositionality Tests[/bold cyan]")

    test = LocalityTest(store)
    results = {}

    for class_id in classes:
        if not test.applies_to(class_id):
            continue

        console.print(f"  Testing: [yellow]{class_id}[/yellow]")
        result = test.run(class_id, dataset_id, control_ids)
        results[class_id] = result

        color = {
            StressTestOutcome.STABLE: "green",
            StressTestOutcome.FRAGILE: "yellow",
            StressTestOutcome.COLLAPSED: "red",
            StressTestOutcome.INDISTINGUISHABLE: "red",
            StressTestOutcome.INCONCLUSIVE: "dim",
        }.get(result.outcome, "white")

        pattern = result.metrics.get("pattern_type", "unknown")
        console.print(f"    Outcome: [{color}]{result.outcome.value.upper()}[/{color}]")
        console.print(f"    Pattern Type: {pattern}")
        console.print(f"    [dim]{result.summary}[/dim]")

    return results


def generate_stress_test_report(b1_results: Dict, b2_results: Dict,
                                b3_results: Dict) -> Dict[str, Any]:
    """Generate the Mapping Stress Test Report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "classes_tested": list(set(b1_results.keys()) | set(b2_results.keys()) | set(b3_results.keys())),
        "track_results": {},
        "class_summaries": {},
        "constraint_implications": [],
        "forbidden_operations": [],
    }

    # Aggregate by class
    all_classes = report["classes_tested"]

    for class_id in all_classes:
        b1 = b1_results.get(class_id)
        b2 = b2_results.get(class_id)
        b3 = b3_results.get(class_id)

        # Overall status for class
        outcomes = []
        if b1:
            outcomes.append(b1.outcome)
        if b2:
            outcomes.append(b2.outcome)
        if b3:
            outcomes.append(b3.outcome)

        # Worst outcome determines overall
        if StressTestOutcome.COLLAPSED in outcomes:
            overall = "COLLAPSED"
            should_rule_out = True
        elif StressTestOutcome.INDISTINGUISHABLE in outcomes:
            overall = "WEAKENED"
            should_rule_out = False
        elif StressTestOutcome.FRAGILE in outcomes:
            overall = "FRAGILE"
            should_rule_out = False
        elif StressTestOutcome.STABLE in outcomes:
            overall = "STABLE"
            should_rule_out = False
        else:
            overall = "INCONCLUSIVE"
            should_rule_out = False

        report["class_summaries"][class_id] = {
            "overall_status": overall,
            "should_rule_out": should_rule_out,
            "b1_outcome": b1.outcome.value if b1 else None,
            "b2_outcome": b2.outcome.value if b2 else None,
            "b3_outcome": b3.outcome.value if b3 else None,
            "stability_score": b1.stability_score if b1 else None,
            "control_differential": b2.control_differential if b2 else None,
            "pattern_type": b3.metrics.get("pattern_type") if b3 else None,
        }

        # Collect constraint implications
        if b1 and b1.constraint_implications:
            report["constraint_implications"].extend(b1.constraint_implications)
        if b2 and b2.constraint_implications:
            report["constraint_implications"].extend(b2.constraint_implications)
        if b3 and b3.constraint_implications:
            report["constraint_implications"].extend(b3.constraint_implications)

        # Identify forbidden operations
        if b1 and b1.outcome == StressTestOutcome.COLLAPSED:
            report["forbidden_operations"].append(
                f"{class_id}: Segmentation-dependent mappings forbidden"
            )
        if b2 and b2.outcome == StressTestOutcome.INDISTINGUISHABLE:
            report["forbidden_operations"].append(
                f"{class_id}: Information-preserving interpretations not supported"
            )

    # Deduplicate implications
    report["constraint_implications"] = list(set(report["constraint_implications"]))

    return report


def display_report(report: Dict[str, Any]):
    """Display the stress test report."""
    console.print("\n" + "="*60)
    console.print("[bold cyan]Phase 2.2 Stress Test Report[/bold cyan]")
    console.print("="*60)

    # Summary table
    table = Table(title="Class Status Summary")
    table.add_column("Class", style="cyan")
    table.add_column("Overall", style="bold")
    table.add_column("B1: Mapping", style="white")
    table.add_column("B2: Info", style="white")
    table.add_column("B3: Locality", style="white")
    table.add_column("Pattern", style="dim")

    for class_id, summary in report["class_summaries"].items():
        overall = summary["overall_status"]
        color = {
            "STABLE": "green",
            "FRAGILE": "yellow",
            "WEAKENED": "orange1",
            "COLLAPSED": "red",
        }.get(overall, "white")

        table.add_row(
            class_id,
            f"[{color}]{overall}[/{color}]",
            summary["b1_outcome"] or "-",
            summary["b2_outcome"] or "-",
            summary["b3_outcome"] or "-",
            summary.get("pattern_type", "-") or "-"
        )

    console.print(table)

    # Constraint implications
    if report["constraint_implications"]:
        console.print("\n[bold]Constraint Implications:[/bold]")
        for imp in report["constraint_implications"][:10]:  # Limit display
            console.print(f"  - {imp}")

    # Forbidden operations
    if report["forbidden_operations"]:
        console.print("\n[bold red]Forbidden Operations:[/bold red]")
        for op in report["forbidden_operations"]:
            console.print(f"  - {op}")


def check_success_criteria(report: Dict[str, Any]) -> Dict[str, bool]:
    """Check Phase 2.2 success criteria."""
    criteria = {
        "class_ruled_inadmissible": False,
        "hybrid_resolved": False,
        "operations_forbidden": False,
        "constraints_tightened": False,
    }

    # Check if any class should be ruled out
    for class_id, summary in report["class_summaries"].items():
        if summary.get("should_rule_out"):
            criteria["class_ruled_inadmissible"] = True
            break

    # Check if hybrid is resolved
    hybrid_summary = report["class_summaries"].get("hybrid_system", {})
    if hybrid_summary.get("overall_status") in ["STABLE", "COLLAPSED"]:
        criteria["hybrid_resolved"] = True

    # Check if operations are forbidden
    if report["forbidden_operations"]:
        criteria["operations_forbidden"] = True

    # Check if constraints are tightened
    if report["constraint_implications"]:
        criteria["constraints_tightened"] = True

    return criteria


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 2.2: Constraint Tightening")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_phase_2_2(seed: int = 42, output_dir: str | None = None):
    """Execute the full Phase 2.2 workflow."""
    console.print(Panel.fit(
        "[bold cyan]Phase 2.2: Constraint Tightening[/bold cyan]\n"
        "Stress testing translation-like operations",
        border_style="cyan"
    ))

    with active_run(config={"command": "phase_2_2_stress_tests", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)

        # Get eligible classes
        classes = get_admissible_classes(store)
        if not classes:
            console.print("[red]No admissible/underconstrained classes found. Run Phase 2.1 first.[/red]")
            return None

        console.print(f"\n[bold]Testing Classes:[/bold] {', '.join(classes)}")

        # Dataset configuration
        dataset_id = "audit_real"
        control_ids = ["audit_scrambled", "audit_synthetic"]

        console.print(f"[dim]Dataset: {dataset_id}[/dim]")
        console.print(f"[dim]Controls: {', '.join(control_ids)}[/dim]")

        # Execute tracks
        b1_results = run_track_b1(store, classes, dataset_id, control_ids)
        b2_results = run_track_b2(store, classes, dataset_id, control_ids)
        b3_results = run_track_b3(store, classes, dataset_id, control_ids)

        # Generate report
        report = generate_stress_test_report(b1_results, b2_results, b3_results)

        # Display report
        display_report(report)

        # Check success criteria
        console.print("\n[bold]Success Criteria:[/bold]")
        criteria = check_success_criteria(report)

        table = Table()
        table.add_column("Criterion", style="white")
        table.add_column("Status", style="bold")

        criteria_labels = {
            "class_ruled_inadmissible": "At least one class ruled inadmissible",
            "hybrid_resolved": "Hybrid system resolved (admissible or not)",
            "operations_forbidden": "Translation-like operations shown incoherent",
            "constraints_tightened": "Admissibility constraints tightened",
        }

        for key, label in criteria_labels.items():
            status = "[green]ACHIEVED[/green]" if criteria[key] else "[yellow]NOT YET[/yellow]"
            table.add_row(label, status)

        console.print(table)

        # Phase 2.2 success if any criterion met
        any_success = any(criteria.values())

        if any_success:
            console.print(Panel(
                "[green]Phase 2.2 SUCCESS[/green]\n"
                "Constraints have been tightened on admissible explanation classes.",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]Phase 2.2 INCONCLUSIVE[/yellow]\n"
                "No definitive constraint tightening achieved. "
                "Per principles: 'Producing no conclusion is acceptable if justified.'",
                border_style="yellow"
            ))

        # Save report
        if output_dir:
            report_path = Path(output_dir) / "phase_2_2_report.json"
        else:
            report_path = Path("runs") / run.run_id / "phase_2_2_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize results for JSON
        serializable_report = {
            **report,
            "success_criteria": criteria,
        }

        ProvenanceWriter.save_results(serializable_report, report_path)

        console.print(f"\n[dim]Report saved to: {report_path}[/dim]")

        store.save_run(run)
        return report


if __name__ == "__main__":
    args = _parse_args()
    run_phase_2_2(seed=args.seed, output_dir=args.output_dir)
    sys.exit(0)
