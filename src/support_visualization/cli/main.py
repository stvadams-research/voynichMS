import typer
from pathlib import Path
from rich.console import Console
import os
from typing import Optional

from phase1_foundation.configs.logging import setup_logging
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from support_visualization.layers.layer_1_foundation import FoundationVisualizer
from support_visualization.layers.layer_2_analysis import AnalysisVisualizer
from support_visualization.layers.layer_3_synthesis import SynthesisVisualizer
from support_visualization.layers.layer_4_inference import InferenceVisualizer

app = typer.Typer()
foundation_app = typer.Typer()
analysis_app = typer.Typer()
synthesis_app = typer.Typer()
inference_app = typer.Typer()

app.add_typer(foundation_app, name="phase1_foundation", help="Foundation layer (L1) visualizations")
app.add_typer(analysis_app, name="phase2_analysis", help="Analysis layer (L2) visualizations")
app.add_typer(synthesis_app, name="phase3_synthesis", help="Synthesis layer (L3) visualizations")
app.add_typer(inference_app, name="phase4_inference", help="Inference layer (L4) visualizations")

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_metadata_store():
    db_file = DB_PATH.replace("sqlite:///", "")
    if not os.path.exists(db_file):
        console.print(f"[bold red]Error:[/bold red] Database not found at {db_file}")
        raise typer.Exit(code=1)
    return MetadataStore(DB_PATH)

@app.callback()
def main(verbose: bool = False):
    """
    Voynich Manuscript Visualization CLI.
    """
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level)

# --- Foundation Layer (L1) ---

@foundation_app.command("token-frequency")
def plot_token_frequency(
    dataset: str = typer.Argument(..., help="Dataset ID (e.g., 'voynich_real')"),
    top_n: int = typer.Option(50, help="Number of top tokens to display"),
    output_dir: Optional[Path] = typer.Option(None, help="Custom output directory")
):
    """
    Generate Token Frequency Distribution (Zipfian) plot.
    """
    with active_run(config={"command": "viz phase1_foundation token-frequency", "dataset": dataset}) as run:
        store = get_metadata_store()
        viz = FoundationVisualizer(store, output_dir=output_dir)
        
        console.print(f"Generating token frequency plot for {dataset}...")
        path = viz.plot_token_frequency(dataset, top_n=top_n)
        
        if path:
            console.print(f"[bold green]Successfully generated:[/bold green] {path}")
            store.save_run(run)
        else:
            console.print("[bold red]Failed to generate plot.[/bold red]")
            raise typer.Exit(code=1)

@foundation_app.command("repetition-rate")
def plot_repetition_rate(
    dataset: str = typer.Argument(..., help="Dataset ID (e.g., 'voynich_real')"),
    output_dir: Optional[Path] = typer.Option(None, help="Custom output directory")
):
    """
    Generate Page-level Repetition Rate Distribution plot.
    """
    with active_run(config={"command": "viz phase1_foundation repetition-rate", "dataset": dataset}) as run:
        store = get_metadata_store()
        viz = FoundationVisualizer(store, output_dir=output_dir)
        
        console.print(f"Generating repetition rate plot for {dataset}...")
        path = viz.plot_repetition_rate(dataset)
        
        if path:
            console.print(f"[bold green]Successfully generated:[/bold green] {path}")
            store.save_run(run)
        else:
            console.print("[bold red]Failed to generate plot.[/bold red]")
            raise typer.Exit(code=1)

# --- Analysis Layer (L2) ---

@analysis_app.command("sensitivity-sweep")
def plot_sensitivity_sweep(
    path: Path = typer.Argument(Path("core_status/core_audit/sensitivity_sweep.json"), help="Path to sensitivity sweep JSON"),
    output_dir: Optional[Path] = typer.Option(None, help="Custom output directory")
):
    """
    Generate sensitivity sweep summary plots.
    """
    with active_run(config={"command": "viz phase2_analysis sensitivity-sweep", "path": str(path)}) as run:
        store = get_metadata_store()
        viz = AnalysisVisualizer(store, output_dir=output_dir)
        
        console.print(f"Generating sensitivity sweep plots from {path}...")
        result_path = viz.plot_sensitivity_sweep(path)
        
        if result_path:
            console.print(f"[bold green]Successfully generated plots.[/bold green]")
            store.save_run(run)
        else:
            console.print("[bold red]Failed to generate plots.[/bold red]")
            raise typer.Exit(code=1)

# --- Synthesis Layer (L3) ---

@synthesis_app.command("gap-phase2_analysis")
def plot_gap_analysis(
    path: Path = typer.Argument(Path("core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json"), help="Path to gap phase2_analysis JSON"),
    output_dir: Optional[Path] = typer.Option(None, help="Custom output directory")
):
    """
    Generate phase3_synthesis gap phase2_analysis plots (Real vs Synthetic metrics).
    """
    with active_run(config={"command": "viz phase3_synthesis gap-phase2_analysis", "path": str(path)}) as run:
        store = get_metadata_store()
        viz = SynthesisVisualizer(store, output_dir=output_dir)
        
        console.print(f"Generating gap phase2_analysis plots from {path}...")
        result_path = viz.plot_gap_analysis(path)
        
        if result_path:
            console.print(f"[bold green]Successfully generated plots.[/bold green]")
            store.save_run(run)
        else:
            console.print("[bold red]Failed to generate plots (check if file exists and has valid data).[/bold red]")
            raise typer.Exit(code=1)

# --- Inference Layer (L4) ---

@inference_app.command("lang-id")
def plot_lang_id(
    path: Path = typer.Argument(Path("results/data/phase4_inference/lang_id_results.json"), help="Path to lang-id results JSON"),
    output_dir: Optional[Path] = typer.Option(None, help="Custom output directory")
):
    """
    Generate Language ID false-positive evaluation plots.
    """
    with active_run(config={"command": "viz phase4_inference lang-id", "path": str(path)}) as run:
        store = get_metadata_store()
        viz = InferenceVisualizer(store, output_dir=output_dir)
        
        console.print(f"Generating lang-id comparison plots from {path}...")
        result_path = viz.plot_lang_id_comparison(path)
        
        if result_path:
            console.print(f"[bold green]Successfully generated plots.[/bold green]")
            store.save_run(run)
        else:
            console.print("[bold red]Failed to generate plots.[/bold red]")
            raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
