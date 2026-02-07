#!/usr/bin/env python3
"""
Phase 2.3: Explicit Model Instantiation and Disconfirmation

Executes all four tracks of Phase 2.3:
- C1: Visual Grammar models
- C2: Constructed System models
- C3: Disconfirmation testing
- C4: Cross-model evaluation

Produces:
- Model Registry with all models
- Disconfirmation Log per model
- Comparative Evaluation Matrix
- Phase 2.3 Findings Summary
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

from foundation.storage.metadata import MetadataStore
from analysis.models.interface import ModelStatus
from analysis.models.registry import ModelRegistry
from analysis.models.disconfirmation import DisconfirmationEngine
from analysis.models.evaluation import CrossModelEvaluator
from analysis.models.visual_grammar import (
    AdjacencyGrammarModel,
    ContainmentGrammarModel,
    DiagramAnnotationModel,
)
from analysis.models.constructed_system import (
    ProceduralGenerationModel,
    GlossalialSystemModel,
    MeaningfulConstructModel,
)

app = typer.Typer()
console = Console()


def display_model_info(model, include_details: bool = False):
    """Display information about a model."""
    status_color = {
        ModelStatus.UNTESTED: "white",
        ModelStatus.SURVIVING: "green",
        ModelStatus.FRAGILE: "yellow",
        ModelStatus.FALSIFIED: "red",
        ModelStatus.DISCONTINUED: "dim",
    }.get(model.status, "white")

    console.print(f"\n[bold]{model.model_name}[/bold] [{status_color}][{model.status.value}][/{status_color}]")
    console.print(f"  ID: {model.model_id}")
    console.print(f"  Class: {model.explanation_class}")

    if include_details:
        console.print(f"\n  [dim]Description:[/dim] {model.description[:100]}...")
        console.print(f"\n  [dim]Rules:[/dim]")
        for rule in model.rules:
            console.print(f"    - {rule}")


def display_prediction_results(results: Dict[str, Any]):
    """Display prediction test results."""
    table = Table(title="Prediction Tests", show_header=True)
    table.add_column("Prediction", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Confidence", justify="right")
    table.add_column("Result")

    for pred in results["predictions"]:
        status = "[green]PASS[/green]" if pred["passed"] else "[red]FAIL[/red]"
        conf = f"{pred['confidence']:.0%}"
        result = pred["actual_result"][:50] + "..." if len(pred["actual_result"]) > 50 else pred["actual_result"]
        table.add_row(pred["prediction_id"], status, conf, result)

    console.print(table)


def display_disconfirmation_log(log: Dict[str, Any]):
    """Display disconfirmation test log."""
    if log["total_tests"] == 0:
        console.print("[dim]No disconfirmation tests run[/dim]")
        return

    table = Table(title="Disconfirmation Tests", show_header=True)
    table.add_column("Perturbation", style="cyan")
    table.add_column("Tests", justify="center")
    table.add_column("Survived", justify="center")
    table.add_column("Failed", justify="center")

    for ptype, stats in log["by_perturbation_type"].items():
        survived = f"[green]{stats['survived']}[/green]"
        failed = f"[red]{stats['failed']}[/red]" if stats["failed"] > 0 else "0"
        table.add_row(ptype, str(stats["tests"]), survived, failed)

    console.print(table)

    if log["failures"]:
        console.print("\n[red bold]Failures:[/red bold]")
        for f in log["failures"]:
            console.print(f"  - {f['test_id']}: {f['failure_mode']}")


def display_evaluation_matrix(report: Dict[str, Any]):
    """Display the cross-model evaluation matrix."""
    # Overall ranking
    console.print(Panel("[bold]Overall Model Ranking[/bold]", style="blue"))

    table = Table(show_header=True)
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Model", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for i, (model_id, score) in enumerate(report["overall_ranking"], 1):
        status = report["all_scores"].get(model_id, {})
        table.add_row(
            str(i),
            model_id,
            f"{score:.3f}",
            ""  # Could add status here
        )

    console.print(table)

    # Dimension breakdown
    console.print("\n[bold]Scores by Dimension[/bold]")
    dim_table = Table(show_header=True)
    dim_table.add_column("Model", style="cyan")
    for dim in ["prediction_accuracy", "robustness", "explanatory_scope", "parsimony", "falsifiability"]:
        dim_table.add_column(dim[:10], justify="right")

    for model_id in report["all_scores"]:
        scores = report["all_scores"][model_id]
        dim_table.add_row(
            model_id[:25],
            f"{scores['prediction_accuracy']:.2f}",
            f"{scores['robustness']:.2f}",
            f"{scores['explanatory_scope']:.2f}",
            f"{scores['parsimony']:.2f}",
            f"{scores['falsifiability']:.2f}",
        )

    console.print(dim_table)


def display_class_summary(report: Dict[str, Any]):
    """Display summary by explanation class."""
    console.print(Panel("[bold]Summary by Explanation Class[/bold]", style="green"))

    table = Table(show_header=True)
    table.add_column("Class", style="cyan")
    table.add_column("Models", justify="center")
    table.add_column("Surviving", justify="center")
    table.add_column("Falsified", justify="center")
    table.add_column("Best Model")
    table.add_column("Best Score", justify="right")

    for exp_class, data in report["by_class"].items():
        table.add_row(
            exp_class,
            str(len(data["models"])),
            f"[green]{data['surviving']}[/green]",
            f"[red]{data['falsified']}[/red]" if data["falsified"] > 0 else "0",
            data["best_model"] or "N/A",
            f"{data['best_score']:.3f}",
        )

    console.print(table)


@app.command()
def main(
    db_path: str = typer.Option(
        "sqlite:///voynich_foundation.db",
        help="SQLAlchemy database URL"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output"
    ),
):
    """Execute Phase 2.3: Explicit Model Instantiation and Disconfirmation."""

    console.print(Panel.fit(
        "[bold blue]Phase 2.3: Explicit Model Instantiation[/bold blue]\n"
        "[dim]Testing falsifiable models within admissible classes[/dim]",
        border_style="blue"
    ))

    # Initialize storage
    store = MetadataStore(db_path)

    # ============================================================
    # TRACK C1 & C2: Register Models
    # ============================================================
    console.print("\n[bold yellow]Track C1 & C2: Registering Models[/bold yellow]")

    registry = ModelRegistry(store)

    # Visual Grammar models (C1)
    vg_models = [
        AdjacencyGrammarModel,
        ContainmentGrammarModel,
        DiagramAnnotationModel,
    ]

    # Constructed System models (C2)
    cs_models = [
        ProceduralGenerationModel,
        GlossalialSystemModel,
        MeaningfulConstructModel,
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Registering models...", total=len(vg_models) + len(cs_models))

        for model_class in vg_models + cs_models:
            model = registry.register(model_class)
            if verbose:
                display_model_info(model, include_details=True)
            progress.advance(task)

    console.print(f"[green]✓[/green] Registered {len(registry.get_all())} models")

    # Display registered models
    table = Table(title="Registered Models", show_header=True)
    table.add_column("Model ID", style="cyan")
    table.add_column("Name")
    table.add_column("Class")
    table.add_column("Rules", justify="center")
    table.add_column("Predictions", justify="center")

    for model in registry.get_all():
        table.add_row(
            model.model_id,
            model.model_name,
            model.explanation_class,
            str(len(model.rules)),
            str(len(model.get_predictions())),
        )
    console.print(table)

    # ============================================================
    # TRACK C3: Disconfirmation Testing
    # ============================================================
    console.print("\n[bold yellow]Track C3: Disconfirmation Testing[/bold yellow]")

    engine = DisconfirmationEngine(store)

    for model in registry.get_all():
        console.print(f"\n[cyan]Testing: {model.model_name}[/cyan]")

        # Run prediction tests
        pred_results = engine.run_prediction_tests(model, "real")
        if verbose:
            display_prediction_results(pred_results)

        console.print(f"  Predictions: {pred_results['passed']}/{pred_results['total']} passed")

        # Run disconfirmation battery
        disconf_results = engine.run_full_battery(model, "real")

        # Generate disconfirmation log
        disconf_log = engine.generate_disconfirmation_log(model)
        if verbose:
            display_disconfirmation_log(disconf_log)

        console.print(f"  Disconfirmation: {disconf_log['total_survived']}/{disconf_log['total_tests']} survived")

        # Display final status
        status_color = {
            ModelStatus.UNTESTED: "white",
            ModelStatus.SURVIVING: "green",
            ModelStatus.FRAGILE: "yellow",
            ModelStatus.FALSIFIED: "red",
            ModelStatus.DISCONTINUED: "dim",
        }.get(model.status, "white")
        console.print(f"  Status: [{status_color}]{model.status.value.upper()}[/{status_color}]")

    # ============================================================
    # TRACK C4: Cross-Model Evaluation
    # ============================================================
    console.print("\n[bold yellow]Track C4: Cross-Model Evaluation[/bold yellow]")

    evaluator = CrossModelEvaluator(registry.get_all())
    eval_report = evaluator.generate_report()

    display_evaluation_matrix(eval_report)
    display_class_summary(eval_report)

    # ============================================================
    # FINDINGS SUMMARY
    # ============================================================
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Phase 2.3 Findings Summary[/bold green]",
        border_style="green"
    ))

    # Overall statistics
    console.print(f"\n[bold]Overall Results:[/bold]")
    console.print(f"  Total Models Tested: {eval_report['total_models']}")
    console.print(f"  Surviving Models: [green]{eval_report['surviving_models']}[/green]")
    console.print(f"  Falsified Models: [red]{eval_report['falsified_models']}[/red]")

    # Top models
    console.print(f"\n[bold]Top Performing Models:[/bold]")
    for i, (model_id, score) in enumerate(eval_report["overall_ranking"][:3], 1):
        model = registry.get(model_id)
        console.print(f"  {i}. {model.model_name} ({score:.3f})")

    # Key findings
    console.print(f"\n[bold]Key Findings:[/bold]")

    # Find best class
    best_class = max(
        eval_report["by_class"].items(),
        key=lambda x: x[1]["best_score"]
    )
    console.print(f"  - Leading explanation class: [cyan]{best_class[0]}[/cyan]")
    console.print(f"    Best model: {best_class[1]['best_model']} (score: {best_class[1]['best_score']:.3f})")

    # Check for falsified models
    falsified = registry.get_falsified()
    if falsified:
        console.print(f"\n  - [red]Falsified models:[/red]")
        for m in falsified:
            console.print(f"    - {m.model_name}")
    else:
        console.print(f"\n  - [green]No models fully falsified[/green]")

    # Weaknesses
    console.print(f"\n  - [yellow]Model Weaknesses:[/yellow]")
    for model in registry.get_all():
        if model.status == ModelStatus.FRAGILE:
            console.print(f"    - {model.model_name}: FRAGILE (degradation concerns)")

    # Generate registry report
    reg_report = registry.generate_report()

    console.print("\n[dim]Phase 2.3 Complete[/dim]")

    return {
        "registry_report": reg_report,
        "evaluation_report": eval_report,
    }


if __name__ == "__main__":
    app()
