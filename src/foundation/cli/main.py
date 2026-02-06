import typer
import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
import uuid

from foundation.configs.logging import setup_logging
from foundation.runs.manager import active_run
from foundation.core.ids import RunID, PageID, FolioID
from foundation.storage.metadata import MetadataStore, PageRecord, StructureRecord, DecisionRecord, HypothesisRecord
from foundation.core.dataset import DatasetManager
from foundation.transcription.parsers import EVAParser
from foundation.core.queries import QueryEngine
from foundation.segmentation.dummy import DummyLineSegmenter, DummyWordSegmenter, DummyGlyphSegmenter
from foundation.alignment.engine import AlignmentEngine
from foundation.regions.dummy import GridProposer, RandomBlobProposer
from foundation.regions.graph import GraphBuilder
from foundation.controls.scramblers import ScrambledControlGenerator
from foundation.controls.synthetic import SyntheticNullGenerator
from foundation.metrics.library import RepetitionRate, ClusterTightness
from foundation.analysis.comparator import Comparator
from foundation.anchors.engine import AnchorEngine
from foundation.analysis.stability import AnchorStabilityAnalyzer
from foundation.decisions.registry import StructureRegistry
from foundation.analysis.sensitivity import SensitivityAnalyzer
from foundation.hypotheses.manager import HypothesisManager
from foundation.hypotheses.library import GlyphPositionHypothesis

app = typer.Typer()
data_app = typer.Typer()
transcription_app = typer.Typer()
query_app = typer.Typer()
segmentation_app = typer.Typer()
alignment_app = typer.Typer()
regions_app = typer.Typer()
controls_app = typer.Typer()
metrics_app = typer.Typer()
analysis_app = typer.Typer()
anchors_app = typer.Typer()
decisions_app = typer.Typer()
sensitivity_app = typer.Typer()
hypotheses_app = typer.Typer()

app.add_typer(data_app, name="data", help="Data management commands")
app.add_typer(transcription_app, name="transcription", help="Transcription management commands")
app.add_typer(query_app, name="query", help="Query the ledger")
app.add_typer(segmentation_app, name="segmentation", help="Segmentation commands")
app.add_typer(alignment_app, name="alignment", help="Alignment commands")
app.add_typer(regions_app, name="regions", help="Region commands")
app.add_typer(controls_app, name="controls", help="Control dataset commands")
app.add_typer(metrics_app, name="metrics", help="Metric calculation commands")
app.add_typer(analysis_app, name="analysis", help="Analysis and comparison commands")
app.add_typer(anchors_app, name="anchors", help="Anchor management commands")
app.add_typer(decisions_app, name="decisions", help="Decision management commands")
app.add_typer(sensitivity_app, name="sensitivity", help="Sensitivity analysis commands")
app.add_typer(hypotheses_app, name="hypotheses", help="Hypothesis testing commands")

console = Console()

DB_PATH = "sqlite:///data/voynich.db"

def get_metadata_store():
    return MetadataStore(DB_PATH)

@app.callback()
def main(verbose: bool = False):
    """
    Voynich Foundation Project CLI.
    """
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level)

@app.command()
def init(
    path: Path = typer.Option(
        Path("."), 
        help="Path to initialize the project structure in."
    )
):
    """
    Initialize local data directories.
    """
    with active_run(config={"command": "init", "path": str(path)}) as run:
        console.print(f"[bold green]Initializing Voynich data structure in {path}[/bold green]")
        
        dirs = [
            "data/raw",
            "data/derived",
            "data/qc",
            "runs"
        ]
        
        for d in dirs:
            target = path / d
            target.mkdir(parents=True, exist_ok=True)
            console.print(f"Created: {target}")
        
        # Initialize DB
        get_metadata_store()
        console.print(f"Initialized Database at {DB_PATH}")
            
        console.print(f"[bold blue]Run ID:[/bold blue] {run.run_id}")

@app.command()
def status():
    """
    Show current environment status.
    """
    with active_run(config={"command": "status"}) as run:
        table = Table(title="Voynich Foundation Status")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Run ID", str(run.run_id))
        table.add_row("Git Commit", run.git_commit)
        table.add_row("Git Dirty", str(run.git_dirty))
        table.add_row("User", run.user)
        table.add_row("Timestamp", str(run.timestamp_start))
        
        console.print(table)

@data_app.command("register")
def register_dataset(
    path: Path = typer.Argument(..., help="Path to the dataset directory"),
    name: str = typer.Option(..., help="Unique name for the dataset")
):
    """
    Register a dataset by scanning a directory for images.
    """
    with active_run(config={"command": "data register", "path": str(path), "name": name}) as run:
        store = get_metadata_store()
        manager = DatasetManager(store)
        
        console.print(f"Scanning {path} for dataset '{name}'...")
        try:
            pages = manager.register_dataset(name, path)
            console.print(f"[bold green]Successfully registered {len(pages)} pages.[/bold green]")
            store.save_run(run)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

@transcription_app.command("ingest")
def ingest_transcription(
    path: Path = typer.Argument(..., help="Path to transcription file"),
    source: str = typer.Option(..., help="Source name (e.g. eva_v1)"),
    format: str = typer.Option("eva", help="Format (currently only eva)")
):
    """
    Ingest a transcription file into the database.
    """
    with active_run(config={"command": "transcription ingest", "path": str(path), "source": source}) as run:
        store = get_metadata_store()
        
        # Register source
        store.add_transcription_source(id=source, name=source)
        
        if format != "eva":
            console.print(f"[bold red]Error:[/bold red] Only 'eva' format is supported currently.")
            raise typer.Exit(code=1)
            
        parser = EVAParser()
        count_lines = 0
        count_tokens = 0
        
        try:
            for line in parser.parse(path):
                # Ensure page exists or just log it?
                # For now, we assume page IDs in transcript match our canonical IDs.
                # But we should probably check or just insert.
                # To be safe, we'll try to convert folio string to PageID
                try:
                    # Handle potential mismatches or formatting in folio string
                    # EVAParser returns generic string. We need to normalize to PageID if possible.
                    # Assuming parser returns "f1r" style.
                    page_id = str(PageID(folio=FolioID(line.folio)))
                except ValueError:
                    console.print(f"Skipping line for invalid folio: {line.folio}")
                    continue

                line_id = str(uuid.uuid4())
                store.add_transcription_line(
                    id=line_id,
                    source_id=source,
                    page_id=page_id,
                    line_index=line.line_index,
                    content=line.content
                )
                count_lines += 1
                
                for token in line.tokens:
                    token_id = str(uuid.uuid4())
                    store.add_transcription_token(
                        id=token_id,
                        line_id=line_id,
                        token_index=token.token_index,
                        content=token.content
                    )
                    count_tokens += 1
            
            store.save_run(run)
            console.print(f"[bold green]Ingested {count_lines} lines and {count_tokens} tokens from {source}.[/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

@query_app.command("token")
def query_token(token: str):
    """
    Find all word images aligned to a specific transcription token.
    """
    store = get_metadata_store()
    engine = QueryEngine(store)
    results = engine.get_words_for_token(token)
    
    table = Table(title=f"Occurrences of '{token}'")
    table.add_column("Word ID", style="cyan")
    table.add_column("Page", style="magenta")
    table.add_column("BBox", style="green")
    
    for r in results:
        table.add_row(r['word_id'], r['page_id'], str(r['bbox']))
    console.print(table)

@query_app.command("word")
def query_word(word_id: str):
    """
    Show glyph candidates for a specific word.
    """
    store = get_metadata_store()
    engine = QueryEngine(store)
    results = engine.get_glyphs_for_word(word_id)
    
    table = Table(title=f"Glyphs in Word {word_id}")
    table.add_column("Glyph ID", style="cyan")
    table.add_column("Index", style="magenta")
    table.add_column("BBox", style="green")
    
    for r in results:
        table.add_row(r['glyph_id'], str(r['index']), str(r['bbox']))
    console.print(table)

@query_app.command("region")
def query_region(region_id: str):
    """
    Show details and relationships for a region.
    """
    store = get_metadata_store()
    engine = QueryEngine(store)
    related = engine.get_related_regions(region_id)
    
    table = Table(title=f"Relationships for Region {region_id}")
    table.add_column("Related Region ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Weight", style="green")
    
    for r in related:
        table.add_row(r['region_id'], r['type'], str(r['weight']))
    console.print(table)

@segmentation_app.command("run-dummy")
def run_dummy_segmentation(page_id: str):
    """
    Run dummy segmentation on a page.
    """
    with active_run(config={"command": "segmentation run-dummy", "page_id": page_id}) as run:
        store = get_metadata_store()
        
        # Check if page exists
        # In real app, verify page_id in DB.
        
        line_seg = DummyLineSegmenter()
        word_seg = DummyWordSegmenter()
        glyph_seg = DummyGlyphSegmenter()
        
        # Segment Lines
        lines = line_seg.segment_page(page_id, "dummy_path")
        console.print(f"Generated {len(lines)} dummy lines for {page_id}")
        
        for line in lines:
            line_id = str(uuid.uuid4())
            store.add_line(
                id=line_id,
                page_id=page_id,
                line_index=line.line_index,
                bbox=line.bbox.model_dump(),
                confidence=line.confidence
            )
            
            # Segment Words
            words = word_seg.segment_line(line.bbox, "dummy_path")
            for word in words:
                word_id = str(uuid.uuid4())
                store.add_word(
                    id=word_id,
                    line_id=line_id,
                    word_index=word.word_index,
                    bbox=word.bbox.model_dump(),
                    confidence=word.confidence
                )
                
                # Segment Glyphs
                glyphs = glyph_seg.segment_word(word.bbox, "dummy_path")
                for glyph in glyphs:
                    glyph_id = str(uuid.uuid4())
                    store.add_glyph_candidate(
                        id=glyph_id,
                        word_id=word_id,
                        glyph_index=glyph.glyph_index,
                        bbox=glyph.bbox.model_dump(),
                        confidence=glyph.confidence
                    )
        
        store.save_run(run)
        console.print(f"[bold green]Dummy segmentation complete for {page_id}[/bold green]")

@alignment_app.command("run")
def run_alignment(page_id: str, source_id: str):
    """
    Run alignment for a page and source.
    """
    with active_run(config={"command": "alignment run", "page_id": page_id, "source_id": source_id}) as run:
        store = get_metadata_store()
        engine = AlignmentEngine(store)
        
        console.print(f"Aligning {page_id} with source {source_id}...")
        engine.align_page_lines(page_id, source_id)
        
        store.save_run(run)
        console.print(f"[bold green]Alignment complete.[/bold green]")

@regions_app.command("propose-dummy")
def propose_dummy_regions(page_id: str):
    """
    Run dummy region proposals (multi-scale).
    """
    with active_run(config={"command": "regions propose-dummy", "page_id": page_id}) as run:
        store = get_metadata_store()
        
        # 1. Grid (Large/Mid)
        grid_proposer = GridProposer(rows=3, cols=3, scale="large")
        regions = grid_proposer.propose_regions(page_id, "dummy_path")
        
        for r in regions:
            store.add_region(
                id=str(uuid.uuid4()),
                page_id=page_id,
                scale=r.scale,
                method=r.method,
                bbox=r.bbox.model_dump(),
                confidence=r.confidence
            )
            
        # 2. Random Blobs (Primitive)
        blob_proposer = RandomBlobProposer(count=10, scale="primitive")
        regions = blob_proposer.propose_regions(page_id, "dummy_path")
        
        for r in regions:
            store.add_region(
                id=str(uuid.uuid4()),
                page_id=page_id,
                scale=r.scale,
                method=r.method,
                bbox=r.bbox.model_dump(),
                confidence=r.confidence
            )
            
        store.save_run(run)
        console.print(f"[bold green]Generated dummy regions for {page_id}.[/bold green]")

@regions_app.command("build-graph")
def build_region_graph(page_id: str):
    """
    Build relationship graph for regions on a page.
    """
    with active_run(config={"command": "regions build-graph", "page_id": page_id}) as run:
        store = get_metadata_store()
        builder = GraphBuilder(store)
        
        console.print(f"Building region graph for {page_id}...")
        builder.build_graph(page_id)
        
        store.save_run(run)
        console.print(f"[bold green]Graph build complete.[/bold green]")

# --- Level 3 Commands ---

@controls_app.command("generate-scrambled")
def generate_scrambled(
    source: str = typer.Option(..., help="Source dataset ID"),
    name: str = typer.Option(..., help="Name for the control dataset"),
    seed: int = typer.Option(42, help="Random seed")
):
    """
    Generate a scrambled control dataset.
    """
    with active_run(config={"command": "controls generate-scrambled", "source": source, "name": name}) as run:
        store = get_metadata_store()
        generator = ScrambledControlGenerator(store)
        
        console.print(f"Generating scrambled control dataset '{name}' from '{source}'...")
        generator.generate(source, name, seed=seed)
        
        store.save_run(run)
        console.print(f"[bold green]Generated scrambled dataset: {name}[/bold green]")

@controls_app.command("generate-synthetic")
def generate_synthetic(
    source: str = typer.Option(..., help="Source dataset ID (for reference)"),
    name: str = typer.Option(..., help="Name for the control dataset"),
    pages: int = typer.Option(5, help="Number of pages to generate"),
    seed: int = typer.Option(42, help="Random seed")
):
    """
    Generate a synthetic null dataset.
    """
    with active_run(config={"command": "controls generate-synthetic", "name": name}) as run:
        store = get_metadata_store()
        generator = SyntheticNullGenerator(store)
        
        console.print(f"Generating synthetic null dataset '{name}'...")
        generator.generate(source, name, seed=seed, params={"num_pages": pages})
        
        store.save_run(run)
        console.print(f"[bold green]Generated synthetic dataset: {name}[/bold green]")

@metrics_app.command("run")
def run_metric(
    dataset: str = typer.Option(..., help="Dataset ID"),
    metric: str = typer.Option(..., help="Metric name (RepetitionRate, ClusterTightness)")
):
    """
    Run a metric on a dataset.
    """
    with active_run(config={"command": "metrics run", "dataset": dataset, "metric": metric}) as run:
        store = get_metadata_store()
        
        metric_cls = None
        if metric == "RepetitionRate":
            metric_cls = RepetitionRate(store)
        elif metric == "ClusterTightness":
            metric_cls = ClusterTightness(store)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown metric '{metric}'")
            raise typer.Exit(code=1)
            
        console.print(f"Calculating {metric} for {dataset}...")
        results = metric_cls.calculate(dataset)
        
        for r in results:
            store.add_metric_result(
                run_id=run.run_id,
                dataset_id=dataset,
                metric_name=metric,
                scope=r.scope,
                value=r.value,
                details=r.details
            )
            console.print(f"Result: {r.value:.4f} ({r.scope})")
            
        store.save_run(run)

@analysis_app.command("compare")
def compare_datasets(
    real: str = typer.Option(..., help="Real dataset ID"),
    control: str = typer.Option(..., help="Control dataset ID"),
    metric: str = typer.Option(..., help="Metric to compare")
):
    """
    Compare a real dataset against a control dataset for a specific metric.
    """
    with active_run(config={"command": "analysis compare", "real": real, "control": control}) as run:
        store = get_metadata_store()
        
        # Fetch results from DB (simulated here by re-running or assuming they exist)
        # For CLI simplicity, we'll re-calculate or fetch.
        # Let's assume we re-calculate for the demo flow to ensure values exist.
        
        metric_cls = None
        if metric == "RepetitionRate":
            metric_cls = RepetitionRate(store)
        elif metric == "ClusterTightness":
            metric_cls = ClusterTightness(store)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown metric '{metric}'")
            raise typer.Exit(code=1)
            
        real_results = metric_cls.calculate(real)
        control_results = metric_cls.calculate(control)
        
        all_results = real_results + control_results
        
        comparator = Comparator(store)
        comparison = comparator.compare_datasets(real, control, all_results)
        
        table = Table(title=f"Comparison: {real} vs {control}")
        table.add_column("Metric", style="cyan")
        table.add_column("Real Value", style="green")
        table.add_column("Control Value", style="yellow")
        table.add_column("Diff", style="white")
        table.add_column("Classification", style="bold magenta")
        
        for m, data in comparison.items():
            table.add_row(
                m,
                f"{data['real']:.4f}",
                f"{data['control']:.4f}",
                f"{data['diff']:.4f}",
                data['classification']
            )
            
        console.print(table)
        store.save_run(run)

# --- Level 4 Commands ---

@anchors_app.command("generate")
def generate_anchors(
    dataset: str = typer.Option(..., help="Dataset ID"),
    method: str = typer.Option("geometric_v1", help="Method name"),
    dist_threshold: float = typer.Option(0.1, help="Distance threshold for 'near' anchors")
):
    """
    Compute anchors for all pages in a dataset.
    """
    with active_run(config={"command": "anchors generate", "dataset": dataset, "method": method}) as run:
        store = get_metadata_store()
        engine = AnchorEngine(store)
        
        # Register method
        method_id = engine.register_method(name=method, parameters={"distance_threshold": dist_threshold})
        
        session = store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=dataset).all()
            total_anchors = 0
            
            for page in pages:
                count = engine.compute_page_anchors(page.id, method_id, run.run_id)
                total_anchors += count
                console.print(f"Page {page.id}: Generated {count} anchors")
            
            console.print(f"[bold green]Total anchors generated: {total_anchors}[/bold green]")
            store.save_run(run)
        finally:
            session.close()

@anchors_app.command("query")
def query_anchors(
    region: str = typer.Option(..., help="Region ID to query anchors for")
):
    """
    Show all text objects anchored to a specific region.
    """
    store = get_metadata_store()
    engine = QueryEngine(store)
    anchors = engine.get_anchors_for_region(region)
    
    table = Table(title=f"Anchors for Region {region}")
    table.add_column("Anchor ID", style="cyan")
    table.add_column("Source Type", style="magenta")
    table.add_column("Source ID", style="blue")
    table.add_column("Relation", style="yellow")
    table.add_column("Score", style="green")
    
    for a in anchors:
        table.add_row(
            a['anchor_id'],
            a['source_type'],
            a['source_id'],
            a['relation'],
            f"{a['score']:.4f}"
        )
    console.print(table)

@anchors_app.command("analyze")
def analyze_anchors(
    real: str = typer.Option(..., help="Real dataset ID"),
    control: str = typer.Option(..., help="Control dataset ID")
):
    """
    Compare anchor stability between real and control datasets.
    """
    with active_run(config={"command": "anchors analyze", "real": real, "control": control}) as run:
        store = get_metadata_store()
        analyzer = AnchorStabilityAnalyzer(store)
        
        comparison = analyzer.compare_anchor_counts(real, control, run.run_id)
        
        table = Table(title=f"Anchor Stability: {real} vs {control}")
        table.add_column("Relation Type", style="cyan")
        table.add_column("Real Count", style="green")
        table.add_column("Control Count", style="yellow")
        table.add_column("Degradation", style="red")
        
        degradation = comparison["degradation"]
        real_counts = comparison["real"]
        control_counts = comparison["control"]
        
        all_types = set(real_counts.keys()) | set(control_counts.keys())
        
        for t in all_types:
            r = real_counts.get(t, 0)
            c = control_counts.get(t, 0)
            deg = degradation.get(t, 0.0)
            
            table.add_row(
                t,
                str(r),
                str(c),
                f"{deg:.2%}"
            )
            
        console.print(table)
        store.save_run(run)

# --- Level 5 Commands ---

@decisions_app.command("register")
def register_structure(
    id: str = typer.Option(..., help="Structure ID"),
    name: str = typer.Option(..., help="Human readable name"),
    description: str = typer.Option(..., help="Description"),
    origin: str = typer.Option(..., help="Origin Level (2A, 2B, 4)")
):
    """
    Register a new candidate structure.
    """
    with active_run(config={"command": "decisions register", "id": id}) as run:
        store = get_metadata_store()
        registry = StructureRegistry(store)
        
        registry.register_structure(id, name, description, origin)
        console.print(f"[bold green]Registered structure: {name} ({id})[/bold green]")
        store.save_run(run)

@decisions_app.command("decide")
def record_decision(
    id: str = typer.Option(..., help="Structure ID"),
    outcome: str = typer.Option(..., help="ACCEPT, REJECT, or HOLD"),
    reason: str = typer.Option(..., help="Reasoning for decision")
):
    """
    Record a decision for a structure.
    """
    with active_run(config={"command": "decisions decide", "id": id, "outcome": outcome}) as run:
        store = get_metadata_store()
        registry = StructureRegistry(store)
        
        registry.record_decision(id, outcome, reason, run.run_id)
        console.print(f"[bold green]Recorded decision for {id}: {outcome}[/bold green]")
        store.save_run(run)

@decisions_app.command("list")
def list_decisions():
    """
    Show the Structure Ledger.
    """
    store = get_metadata_store()
    session = store.Session()
    try:
        structures = session.query(StructureRecord).all()
        
        table = Table(title="Structure Ledger")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Origin", style="blue")
        table.add_column("Status", style="bold yellow")
        table.add_column("Last Decision", style="white")
        
        for s in structures:
            last_decision = ""
            if s.decisions:
                last_decision = s.decisions[-1].decision
            
            table.add_row(s.id, s.name, s.origin_level, s.status, last_decision)
            
        console.print(table)
    finally:
        session.close()

@sensitivity_app.command("run")
def run_sensitivity(
    structure: str = typer.Option(..., help="Structure ID"),
    param: str = typer.Option(..., help="Parameter name"),
    start: float = typer.Option(..., help="Start value"),
    end: float = typer.Option(..., help="End value"),
    step: float = typer.Option(..., help="Step size")
):
    """
    Run a sensitivity analysis sweep.
    """
    with active_run(config={"command": "sensitivity run", "structure": structure}) as run:
        store = get_metadata_store()
        analyzer = SensitivityAnalyzer(store)
        
        # Generate range
        import numpy as np
        value_range = np.arange(start, end, step).tolist()
        
        # Mock metric function for demo purposes
        # In real usage, this would map structure ID to a specific metric calculation
        def mock_metric(val):
            # Simulate a metric that degrades as parameter increases (e.g. strictness)
            import math
            return 1.0 / (1.0 + math.exp(val - 0.5))
            
        console.print(f"Running sensitivity sweep for {structure} on {param}...")
        results = analyzer.run_parameter_sweep(structure, mock_metric, param, value_range, run.run_id)
        
        table = Table(title=f"Sensitivity Analysis: {structure}")
        table.add_column("Parameter", style="cyan")
        table.add_column("Metric Score", style="green")
        
        for r in results:
            table.add_row(str(r['param']), f"{r['score']:.4f}")
            
        console.print(table)
        store.save_run(run)

# --- Level 6 Commands ---

@hypotheses_app.command("register")
def register_hypothesis(
    id: str = typer.Option(..., help="Hypothesis ID"),
    desc: str = typer.Option(..., help="Description"),
    assumptions: str = typer.Option(..., help="Assumptions"),
    falsification: str = typer.Option(..., help="Falsification criteria")
):
    """
    Register a new hypothesis.
    """
    with active_run(config={"command": "hypotheses register", "id": id}) as run:
        store = get_metadata_store()
        store.add_hypothesis(id, desc, assumptions, falsification)
        console.print(f"[bold green]Registered hypothesis: {id}[/bold green]")
        store.save_run(run)

@hypotheses_app.command("run")
def run_hypothesis(
    id: str = typer.Option(..., help="Hypothesis ID"),
    real: str = typer.Option(..., help="Real dataset ID"),
    controls: str = typer.Option(..., help="Comma-separated control dataset IDs")
):
    """
    Run a hypothesis against real and control datasets.
    """
    control_list = controls.split(",")
    with active_run(config={"command": "hypotheses run", "id": id, "real": real}) as run:
        store = get_metadata_store()
        manager = HypothesisManager(store)
        
        # Register known hypotheses (manual step in code for now, dynamic loading later)
        manager.register_hypothesis(GlyphPositionHypothesis)
        
        console.print(f"Running hypothesis {id}...")
        result = manager.run_hypothesis(id, real, control_list, run.run_id)
        
        console.print(f"[bold]Outcome:[/bold] {result.outcome}")
        
        table = Table(title="Hypothesis Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for k, v in result.metrics.items():
            table.add_row(k, f"{v:.4f}")
            
        console.print(table)
        store.save_run(run)

@hypotheses_app.command("list")
def list_hypotheses():
    """
    List all hypotheses and their status.
    """
    store = get_metadata_store()
    session = store.Session()
    try:
        hypotheses = session.query(HypothesisRecord).all()
        
        table = Table(title="Hypothesis Ledger")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="bold yellow")
        table.add_column("Description", style="white")
        
        for h in hypotheses:
            table.add_row(h.id, h.status, h.description)
            
        console.print(table)
    finally:
        session.close()

if __name__ == "__main__":
    app()
