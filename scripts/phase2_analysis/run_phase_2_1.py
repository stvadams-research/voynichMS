#!/usr/bin/env python3
"""
Phase 2.1 Execution Script: Admissibility Mapping

This script performs the full admissibility mapping workflow:
1. Register core explanation classes
2. Define constraints for each class
3. Map Phase 1 findings to constraints
4. Evaluate status for all classes
5. Generate the Admissibility Matrix report

Per Phase 2 Principles:
- Admissibility Before Truth: We determine what's permitted, not what's correct
- Competing Explanations Are Required: All classes evaluated on equal footing
- Controls Are First-Class Citizens: Phase 1 controls inform all decisions
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase2_analysis.admissibility.manager import (  # noqa: E402
    AdmissibilityManager,
    AdmissibilityStatus,
    ConstraintType,
    SupportLevel,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
PHASE_2_1_CLAIMS_PATH = Path("results/data/phase2_analysis/phase_2_1_claims.json")


def _build_claim_traceability_payload() -> dict:
    """Structured claim payload for publication-tracked Phase 2.1 values."""
    glyph_collapse = 0.375
    word_boundary_agreement = 0.75
    return {
        "claim_2": {
            "description": "Glyph identity collapse at 5% perturbation",
            "glyph_identity_collapse_rate": glyph_collapse,
            "glyph_identity_collapse_percent": glyph_collapse * 100.0,
            "perturbation_strength": 0.05,
            "inadmissible_threshold": 0.20,
            "status": "FALSIFIED",
            "evidence_source": "phase1_destructive_audit",
        },
        "claim_3": {
            "description": "Word boundary cross-source agreement",
            "word_boundary_agreement_rate": word_boundary_agreement,
            "word_boundary_agreement_percent": word_boundary_agreement * 100.0,
            "minimum_support_threshold": 0.80,
            "status": "WEAKLY_SUPPORTED",
            "evidence_source": "phase1_destructive_audit",
        },
    }


def _write_phase_2_1_claim_artifacts(run_id: str, output_dir: str | None) -> list[str]:
    payload = {
        "phase": "2.1",
        "claim_traceability": _build_claim_traceability_payload(),
    }
    write_targets = [PHASE_2_1_CLAIMS_PATH]
    if output_dir:
        write_targets.append(Path(output_dir) / "phase_2_1_claims.json")
    else:
        write_targets.append(Path("runs") / run_id / "phase_2_1_claims.json")

    written: list[str] = []
    seen: set[Path] = set()
    for target in write_targets:
        normalized = target.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        out = ProvenanceWriter.save_results(payload, target)
        written.append(out["latest_path"])
    return written


def step_1_register_classes(manager: AdmissibilityManager):
    """Register the five core explanation classes."""
    console.print("\n[bold]Step 1: Registering Explanation Classes[/bold]")

    classes = [
        {
            "id": "natural_language",
            "name": "Natural Language",
            "description": (
                "The manuscript encodes a natural phase7_human language using a novel or "
                "adapted script. Words map to morphemes, phonemes, or syllables. "
                "The system exhibits properties of natural language such as Zipf's law, "
                "positional constraints, and bounded vocabulary growth."
            ),
        },
        {
            "id": "enciphered_language",
            "name": "Enciphered Language",
            "description": (
                "The manuscript is a cipher over a natural language plaintext. "
                "This includes simple substitution, polyalphabetic, or more complex "
                "historical cipher systems. The underlying plaintext would exhibit "
                "natural language statistics if deciphered."
            ),
        },
        {
            "id": "constructed_system",
            "name": "Constructed Symbolic System",
            "description": (
                "The manuscript is a deliberately constructed symbol system that is "
                "neither natural language nor cipher. This includes glossolalia, "
                "artistic gibberish, or structured nonsense designed to appear linguistic "
                "without carrying meaning."
            ),
        },
        {
            "id": "visual_grammar",
            "name": "Visual/Diagrammatic Grammar",
            "description": (
                "The manuscript is primarily a visual system where the text-like elements "
                "serve a diagrammatic rather than linguistic function. Text may annotate, "
                "label, or structure visual content without being independently readable. "
                "Meaning is derived from spatial relationships, not linear reading."
            ),
        },
        {
            "id": "hybrid_system",
            "name": "Hybrid/Layered System",
            "description": (
                "The manuscript combines multiple encoding systems: parts may be natural "
                "language, parts cipher, parts visual grammar. Different sections or "
                "even different components within a page may use different systems. "
                "No single explanation class fully describes the whole."
            ),
        },
    ]

    for cls in classes:
        manager.register_class(cls["id"], cls["name"], cls["description"])
        console.print(f"  [green]+[/green] {cls['name']} ({cls['id']})")


def step_2_define_constraints(manager: AdmissibilityManager) -> dict:
    """Define constraints for each explanation class. Returns constraint IDs."""
    console.print("\n[bold]Step 2: Defining Admissibility Constraints[/bold]")

    constraints = {}

    # Natural Language constraints
    constraints["natural_language"] = {
        "positional_constraints": manager.add_constraint(
            "natural_language",
            ConstraintType.REQUIRED,
            "Text must exhibit positional constraints (certain symbols prefer word-initial/final positions)"
        ),
        "bounded_vocabulary": manager.add_constraint(
            "natural_language",
            ConstraintType.REQUIRED,
            "Vocabulary growth must be bounded (not random symbol generation)"
        ),
        "stable_glyph_identity": manager.add_constraint(
            "natural_language",
            ConstraintType.REQUIRED,
            "Glyph identity must be stable enough to support consistent reading"
        ),
        "word_boundaries": manager.add_constraint(
            "natural_language",
            ConstraintType.REQUIRED,
            "Word boundaries must be objective and consistent"
        ),
        "random_statistics": manager.add_constraint(
            "natural_language",
            ConstraintType.FORBIDDEN,
            "Statistics indistinguishable from random generation"
        ),
    }
    console.print(f"  [cyan]natural_language:[/cyan] {len(constraints['natural_language'])} constraints")

    # Enciphered Language constraints
    constraints["enciphered_language"] = {
        "substitution_feasible": manager.add_constraint(
            "enciphered_language",
            ConstraintType.REQUIRED,
            "Substitution patterns must be recoverable (not one-way transformation)"
        ),
        "underlying_structure": manager.add_constraint(
            "enciphered_language",
            ConstraintType.REQUIRED,
            "Underlying plaintext structure must be detectable through cipher"
        ),
        "stable_glyph_identity": manager.add_constraint(
            "enciphered_language",
            ConstraintType.REQUIRED,
            "Glyph identity must be stable for consistent substitution"
        ),
        "no_visual_dependency": manager.add_constraint(
            "enciphered_language",
            ConstraintType.OPTIONAL,
            "Text meaning should not depend on visual/spatial context"
        ),
    }
    console.print(f"  [cyan]enciphered_language:[/cyan] {len(constraints['enciphered_language'])} constraints")

    # Constructed System constraints
    constraints["constructed_system"] = {
        "surface_regularity": manager.add_constraint(
            "constructed_system",
            ConstraintType.REQUIRED,
            "Must exhibit surface regularity (patterns that mimic language)"
        ),
        "generation_detectable": manager.add_constraint(
            "constructed_system",
            ConstraintType.OPTIONAL,
            "Generation algorithm may be detectable through statistical phase2_analysis"
        ),
        "semantic_content": manager.add_constraint(
            "constructed_system",
            ConstraintType.FORBIDDEN,
            "Must not exhibit genuine semantic content under any decoding"
        ),
    }
    console.print(f"  [cyan]constructed_system:[/cyan] {len(constraints['constructed_system'])} constraints")

    # Visual Grammar constraints
    constraints["visual_grammar"] = {
        "spatial_dependency": manager.add_constraint(
            "visual_grammar",
            ConstraintType.REQUIRED,
            "Meaning must depend on spatial relationships between elements"
        ),
        "text_diagram_linkage": manager.add_constraint(
            "visual_grammar",
            ConstraintType.REQUIRED,
            "Text and diagrams must be systematically linked (not independent)"
        ),
        "linear_independence": manager.add_constraint(
            "visual_grammar",
            ConstraintType.FORBIDDEN,
            "Text should not be fully interpretable independent of visual context"
        ),
    }
    console.print(f"  [cyan]visual_grammar:[/cyan] {len(constraints['visual_grammar'])} constraints")

    # Hybrid System constraints
    constraints["hybrid_system"] = {
        "multiple_patterns": manager.add_constraint(
            "hybrid_system",
            ConstraintType.REQUIRED,
            "Different sections/components must exhibit different statistical profiles"
        ),
        "section_boundaries": manager.add_constraint(
            "hybrid_system",
            ConstraintType.OPTIONAL,
            "Boundaries between systems may be detectable"
        ),
        "single_system_failure": manager.add_constraint(
            "hybrid_system",
            ConstraintType.REQUIRED,
            "Single-system explanations must fail to account for all phenomena"
        ),
    }
    console.print(f"  [cyan]hybrid_system:[/cyan] {len(constraints['hybrid_system'])} constraints")

    return constraints


def step_3_map_evidence(manager: AdmissibilityManager, constraints: dict):
    """Map Phase 1 findings to constraints."""
    console.print("\n[bold]Step 3: Mapping Phase 1 Evidence to Constraints[/bold]")

    evidence_count = 0

    # --- Natural Language Evidence ---

    # From Phase 1: glyph_position_entropy hypothesis was SUPPORTED
    # This supports positional constraints requirement
    manager.map_evidence(
        class_id="natural_language",
        constraint_id=constraints["natural_language"]["positional_constraints"],
        support_level=SupportLevel.SUPPORTS,
        reasoning=(
            "Phase 1 glyph_position_entropy hypothesis was SUPPORTED. "
            "Real data entropy (0.40) was significantly lower than scrambled (0.95), "
            "indicating genuine positional constraints exist."
        ),
        hypothesis_id="glyph_position_entropy"
    )
    evidence_count += 1

    # From Phase 1 Destructive Audit: fixed_glyph_identity was FALSIFIED
    # This CONTRADICTS stable glyph identity requirement
    manager.map_evidence(
        class_id="natural_language",
        constraint_id=constraints["natural_language"]["stable_glyph_identity"],
        support_level=SupportLevel.CONTRADICTS,
        reasoning=(
            "Phase 1 Destructive Audit: fixed_glyph_identity was FALSIFIED. "
            "Identity collapse rate at 5% boundary perturbation was 37.5% (threshold: 20%). "
            "Glyph identity is segmentation-dependent, undermining stable reading."
        ),
        hypothesis_id="fixed_glyph_identity"
    )
    evidence_count += 1

    # From Phase 1 Destructive Audit: word_boundary_stability was WEAKLY_SUPPORTED
    # This weakly contradicts word boundaries requirement
    manager.map_evidence(
        class_id="natural_language",
        constraint_id=constraints["natural_language"]["word_boundaries"],
        support_level=SupportLevel.CONTRADICTS,
        reasoning=(
            "Phase 1 Destructive Audit: word_boundary_stability was WEAKLY_SUPPORTED. "
            "Cross-source agreement was only 75% (threshold: 80%). "
            "Word boundaries are not sufficiently objective for confident phase2_analysis."
        ),
        hypothesis_id="word_boundary_stability"
    )
    evidence_count += 1

    # --- Enciphered Language Evidence ---

    # Same glyph identity issue applies
    manager.map_evidence(
        class_id="enciphered_language",
        constraint_id=constraints["enciphered_language"]["stable_glyph_identity"],
        support_level=SupportLevel.CONTRADICTS,
        reasoning=(
            "Phase 1 Destructive Audit: fixed_glyph_identity was FALSIFIED. "
            "If glyph identity is unstable, consistent substitution is undermined."
        ),
        hypothesis_id="fixed_glyph_identity"
    )
    evidence_count += 1

    # --- Constructed System Evidence ---

    # Positional constraints support surface regularity
    manager.map_evidence(
        class_id="constructed_system",
        constraint_id=constraints["constructed_system"]["surface_regularity"],
        support_level=SupportLevel.SUPPORTS,
        reasoning=(
            "Phase 1 glyph_position_entropy was SUPPORTED. "
            "The text exhibits surface regularity consistent with constructed mimicry of language."
        ),
        hypothesis_id="glyph_position_entropy"
    )
    evidence_count += 1

    # --- Visual Grammar Evidence ---

    # From Phase 1: geometric_anchors structure was ACCEPTED
    # This supports spatial dependency
    manager.map_evidence(
        class_id="visual_grammar",
        constraint_id=constraints["visual_grammar"]["spatial_dependency"],
        support_level=SupportLevel.SUPPORTS,
        reasoning=(
            "Phase 1 geometric_anchors structure was ACCEPTED. "
            "Anchors degrade >80% on scrambled data, indicating genuine spatial relationships."
        ),
        structure_id="geometric_anchors"
    )
    evidence_count += 1

    # From Phase 1 Destructive Audit: diagram_text_alignment
    # Result was context-dependent but shows some linkage
    manager.map_evidence(
        class_id="visual_grammar",
        constraint_id=constraints["visual_grammar"]["text_diagram_linkage"],
        support_level=SupportLevel.SUPPORTS,
        reasoning=(
            "Phase 1 Destructive Audit: diagram_text_alignment showed alignment. "
            "While z-score was modest, geometric anchors demonstrate systematic text-diagram relationships."
        ),
        hypothesis_id="diagram_text_alignment"
    )
    evidence_count += 1

    # --- Hybrid System Evidence ---

    # The fact that single systems have issues supports hybrid
    manager.map_evidence(
        class_id="hybrid_system",
        constraint_id=constraints["hybrid_system"]["single_system_failure"],
        support_level=SupportLevel.SUPPORTS,
        reasoning=(
            "Phase 1 findings show that pure linguistic models face glyph identity collapse, "
            "while pure visual models can't explain text-like regularities. "
            "This supports the need for hybrid explanation."
        ),
    )
    evidence_count += 1

    console.print(f"  [green]Mapped {evidence_count} evidence items[/green]")


def step_4_evaluate(manager: AdmissibilityManager):
    """Evaluate all classes and display results."""
    console.print("\n[bold]Step 4: Evaluating Admissibility Status[/bold]")

    results = manager.evaluate_all()

    for class_id, result in results.items():
        color = {
            AdmissibilityStatus.ADMISSIBLE: "green",
            AdmissibilityStatus.INADMISSIBLE: "red",
            AdmissibilityStatus.UNDERCONSTRAINED: "yellow",
        }.get(result.status, "white")

        console.print(f"  {class_id}: [{color}]{result.status.value.upper()}[/{color}]")

    return results


def step_5_report(manager: AdmissibilityManager):
    """Generate and display the full Admissibility Matrix."""
    console.print("\n[bold]Step 5: Generating Admissibility Matrix[/bold]")

    report = manager.generate_report()

    # Summary Panel
    summary = report["summary"]
    summary_text = (
        f"Total Classes: {summary['total_classes']}\n"
        f"[green]Admissible:[/green] {summary['admissible']}\n"
        f"[red]Inadmissible:[/red] {summary['inadmissible']}\n"
        f"[yellow]Underconstrained:[/yellow] {summary['underconstrained']}"
    )
    console.print(Panel(summary_text, title="Summary", border_style="cyan"))

    # Detailed Matrix
    table = Table(title="Admissibility Matrix")
    table.add_column("Class", style="cyan", width=20)
    table.add_column("Status", style="bold", width=15)
    table.add_column("Violations", style="red", width=25)
    table.add_column("Unmet Req.", style="yellow", width=25)
    table.add_column("Supporting", style="green", width=15)

    for class_id, data in report["classes"].items():
        status = data["status"]
        color = {
            "admissible": "green",
            "inadmissible": "red",
            "underconstrained": "yellow",
        }.get(status, "white")

        violations = len(data["violations"])
        unmet = len(data["unmet_requirements"])
        supporting = len(data["supporting_evidence"])

        violation_text = ""
        if data["violations"]:
            violation_text = data["violations"][0]["constraint_description"][:23] + "..."

        unmet_text = ""
        if data["unmet_requirements"]:
            unmet_text = data["unmet_requirements"][0]["constraint_description"][:23] + "..."

        table.add_row(
            class_id,
            f"[{color}]{status.upper()}[/{color}]",
            violation_text if violations else "-",
            unmet_text if unmet else "-",
            str(supporting) if supporting else "-"
        )

    console.print(table)

    # Key Insights
    console.print("\n[bold]Key Insights:[/bold]")

    for class_id, data in report["classes"].items():
        if data["status"] == "inadmissible":
            console.print(f"\n[red]{class_id}[/red] is INADMISSIBLE because:")
            for v in data["violations"]:
                console.print(f"  - {v['constraint_type']}: {v['constraint_description']}")
                console.print(f"    [dim]{v['evidence_reasoning'][:80]}...[/dim]")

        elif data["status"] == "underconstrained":
            console.print(f"\n[yellow]{class_id}[/yellow] is UNDERCONSTRAINED. Needs:")
            for u in data["unmet_requirements"]:
                console.print(f"  - {u['constraint_description']}")

        elif data["status"] == "admissible":
            console.print(f"\n[green]{class_id}[/green] is ADMISSIBLE. Would become inadmissible if:")
            for rc in data["reversal_conditions"][:2]:
                console.print(f"  - {rc}")

    return report


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 2.1: Admissibility Mapping")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_phase_2_1(seed: int = 42, output_dir: str | None = None):
    """Execute the full Phase 2.1 workflow."""
    console.print(Panel.fit(
        "[bold cyan]Phase 2.1: Admissibility Mapping[/bold cyan]\n"
        "Systematically mapping the space of allowed explanations",
        border_style="cyan"
    ))

    with active_run(config={"command": "phase_2_1_admissibility", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        manager = AdmissibilityManager(store)

        # Execute all steps
        step_1_register_classes(manager)
        constraints = step_2_define_constraints(manager)
        step_3_map_evidence(manager, constraints)
        results = step_4_evaluate(manager)
        report = step_5_report(manager)

        # Final summary
        console.print("\n" + "="*60)
        console.print("[bold]Phase 2.1 Complete[/bold]")
        console.print("="*60)

        inadmissible = [k for k, v in results.items() if v.status == AdmissibilityStatus.INADMISSIBLE]
        admissible = [k for k, v in results.items() if v.status == AdmissibilityStatus.ADMISSIBLE]
        underconstrained = [k for k, v in results.items() if v.status == AdmissibilityStatus.UNDERCONSTRAINED]

        if inadmissible:
            console.print(f"\n[red]Ruled Out:[/red] {', '.join(inadmissible)}")
        if admissible:
            console.print(f"[green]Admissible:[/green] {', '.join(admissible)}")
        if underconstrained:
            console.print(f"[yellow]Need More Evidence:[/yellow] {', '.join(underconstrained)}")

        written_artifacts = _write_phase_2_1_claim_artifacts(
            run_id=str(run.run_id),
            output_dir=output_dir,
        )
        console.print("\n[dim]Structured claim artifacts:[/dim]")
        for artifact in written_artifacts:
            console.print(f"[dim]  - {artifact}[/dim]")

        console.print("\n[dim]Per Phase 2 Principles: 'Nothing definitive' is an acceptable outcome.[/dim]")

        store.save_run(run)
        return report


if __name__ == "__main__":
    args = _parse_args()
    run_phase_2_1(seed=args.seed, output_dir=args.output_dir)
    sys.exit(0)
