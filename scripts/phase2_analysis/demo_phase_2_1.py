#!/usr/bin/env python3
"""
Phase 2.1 Acceptance Demo

This script verifies the admissibility mapping process against acceptance criteria:

1. Query the final state of all explanation classes
2. For each INADMISSIBLE class, show the violating constraint and evidence
3. For each ADMISSIBLE class, show the reversal conditions
4. Verify the system produces meaningful discrimination

Per the Execution Plan: "Simple Acceptance Demo" criteria.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from phase1_foundation.storage.metadata import MetadataStore, ExplanationClassRecord
from phase2_analysis.admissibility.manager import AdmissibilityManager, AdmissibilityStatus

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def demo_acceptance():
    """Run the acceptance demonstration."""
    console.print(Panel.fit(
        "[bold magenta]Phase 2.1 Acceptance Demo[/bold magenta]\n"
        "Verifying admissibility mapping against acceptance criteria",
        border_style="magenta"
    ))

    store = MetadataStore(DB_PATH)
    manager = AdmissibilityManager(store)

    # 1. Query all classes
    console.print("\n[bold]1. Querying All Explanation Classes[/bold]")

    session = store.Session()
    try:
        classes = session.query(ExplanationClassRecord).all()

        if not classes:
            console.print("[red]ERROR: No explanation classes found. Run run_phase_2_1.py first.[/red]")
            return False

        table = Table(title="Registered Explanation Classes")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Status", style="bold")

        for c in classes:
            color = {
                "admissible": "green",
                "inadmissible": "red",
                "underconstrained": "yellow",
            }.get(c.status, "white")
            table.add_row(c.id, c.name, f"[{color}]{c.status.upper()}[/{color}]")

        console.print(table)

    finally:
        session.close()

    # 2. Detail INADMISSIBLE classes
    console.print("\n[bold]2. INADMISSIBLE Classes - Violation Details[/bold]")

    results = manager.evaluate_all()
    inadmissible_found = False

    for class_id, result in results.items():
        if result.status == AdmissibilityStatus.INADMISSIBLE:
            inadmissible_found = True
            tree = Tree(f"[red]{class_id}[/red] - INADMISSIBLE")

            for v in result.violations:
                violation_node = tree.add(f"[bold]Violated:[/bold] {v['constraint_type']}")
                violation_node.add(f"Constraint: {v['constraint_description']}")
                violation_node.add(f"[dim]Evidence: {v['evidence_reasoning'][:100]}...[/dim]")

                if v.get('structure_id'):
                    violation_node.add(f"Structure: {v['structure_id']}")
                if v.get('hypothesis_id'):
                    violation_node.add(f"Hypothesis: {v['hypothesis_id']}")

            console.print(tree)
            console.print()

    if not inadmissible_found:
        console.print("[yellow]No explanation classes are currently INADMISSIBLE.[/yellow]")

    # 3. Detail ADMISSIBLE classes with reversal conditions
    console.print("\n[bold]3. ADMISSIBLE Classes - Reversal Conditions[/bold]")

    admissible_found = False

    for class_id, result in results.items():
        if result.status == AdmissibilityStatus.ADMISSIBLE:
            admissible_found = True
            tree = Tree(f"[green]{class_id}[/green] - ADMISSIBLE")

            supporting_node = tree.add("[bold]Supporting Evidence:[/bold]")
            for s in result.supporting_evidence:
                supporting_node.add(f"{s['constraint_description']}")

            reversal_node = tree.add("[bold]Would Become Inadmissible If:[/bold]")
            for rc in result.reversal_conditions[:5]:
                reversal_node.add(f"[dim]{rc}[/dim]")

            console.print(tree)
            console.print()

    if not admissible_found:
        console.print("[yellow]No explanation classes are currently ADMISSIBLE.[/yellow]")

    # 4. Detail UNDERCONSTRAINED classes
    console.print("\n[bold]4. UNDERCONSTRAINED Classes - Missing Evidence[/bold]")

    underconstrained_found = False

    for class_id, result in results.items():
        if result.status == AdmissibilityStatus.UNDERCONSTRAINED:
            underconstrained_found = True
            tree = Tree(f"[yellow]{class_id}[/yellow] - UNDERCONSTRAINED")

            needs_node = tree.add("[bold]Needs Evidence For:[/bold]")
            for u in result.unmet_requirements:
                needs_node.add(f"{u['constraint_description']}")

            console.print(tree)
            console.print()

    if not underconstrained_found:
        console.print("[dim]No explanation classes are currently UNDERCONSTRAINED.[/dim]")

    # 5. Acceptance Verification
    console.print("\n[bold]5. Acceptance Criteria Verification[/bold]")

    checks = []

    # Check 1: At least one class evaluated
    total_classes = len(results)
    checks.append(("At least one explanation class evaluated", total_classes > 0))

    # Check 2: Multiple status types exist (system discriminates)
    status_types = set(r.status for r in results.values())
    checks.append(("Multiple status types present (discrimination)", len(status_types) > 1))

    # Check 3: Inadmissible classes have violations
    inadmissible_with_violations = all(
        len(r.violations) > 0
        for r in results.values()
        if r.status == AdmissibilityStatus.INADMISSIBLE
    )
    checks.append(("INADMISSIBLE classes have documented violations", inadmissible_with_violations))

    # Check 4: Admissible classes have reversal conditions
    admissible_with_reversals = all(
        len(r.reversal_conditions) > 0
        for r in results.values()
        if r.status == AdmissibilityStatus.ADMISSIBLE
    )
    checks.append(("ADMISSIBLE classes have reversal conditions", admissible_with_reversals))

    # Check 5: Evidence is linked to Phase 1
    has_linked_evidence = any(
        any(v.get('hypothesis_id') or v.get('structure_id') for v in r.violations)
        or any(s.get('hypothesis_id') or s.get('structure_id') for s in r.supporting_evidence)
        for r in results.values()
    )
    checks.append(("Evidence links to Phase 1 artifacts", has_linked_evidence))

    # Display checks
    table = Table(title="Acceptance Criteria")
    table.add_column("Criterion", style="white")
    table.add_column("Status", style="bold")

    all_passed = True
    for criterion, passed in checks:
        if passed:
            table.add_row(criterion, "[green]PASS[/green]")
        else:
            table.add_row(criterion, "[red]FAIL[/red]")
            all_passed = False

    console.print(table)

    # Final verdict
    if all_passed:
        console.print(Panel(
            "[bold green]ACCEPTANCE DEMO PASSED[/bold green]\n\n"
            "Phase 2.1 Admissibility Mapping is functioning correctly.\n"
            "The system successfully:\n"
            "- Registers and evaluates explanation classes\n"
            "- Maps Phase 1 evidence to constraints\n"
            "- Discriminates between admissible and inadmissible explanations\n"
            "- Documents violations and reversal conditions",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold red]ACCEPTANCE DEMO FAILED[/bold red]\n\n"
            "Some acceptance criteria were not met.\n"
            "Please review the failures above and ensure:\n"
            "1. run_phase_2_1.py has been executed\n"
            "2. Phase 1 foundations are properly set up\n"
            "3. Evidence mapping is complete",
            border_style="red"
        ))

    return all_passed


if __name__ == "__main__":
    success = demo_acceptance()
    sys.exit(0 if success else 1)
