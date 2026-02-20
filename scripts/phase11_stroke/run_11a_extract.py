#!/usr/bin/env python3
"""Phase 11A: Corpus-wide stroke feature extraction."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.randomness import get_randomness_controller
from phase1_foundation.runs.manager import active_run
from phase1_foundation.transcription.parsers import EVAParser
from phase11_stroke.extractor import StrokeExtractor
from phase11_stroke.schema import StrokeSchema

DEFAULT_TRANSCRIPTION_PATH = Path("data/raw/transliterations/ivtff2.0/ZL3b-n.txt")
DEFAULT_OUTPUT_PATH = Path("results/data/phase11_stroke/stroke_features.json")
SEED = 42
console = Console()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 11A stroke feature extraction.")
    parser.add_argument(
        "--transcription-path",
        type=Path,
        default=DEFAULT_TRANSCRIPTION_PATH,
        help="Canonical EVA transcription path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transcription_path: Path = args.transcription_path
    output_path: Path = args.output
    if not transcription_path.exists():
        raise FileNotFoundError(f"Transcription file not found: {transcription_path}")

    schema = StrokeSchema()
    corpus_hash = _sha256_file(transcription_path)
    schema_version = schema.schema_version()

    console.print(
        Panel.fit(
            "[bold blue]Phase 11A: Stroke Feature Extraction[/bold blue]\n"
            f"Seed: {SEED} | Randomness: FORBIDDEN | {datetime.now().isoformat()}"
        )
    )

    t_start = time.time()
    with active_run(
        config={
            "command": "run_11a_extract",
            "seed": SEED,
            "corpus_hash": corpus_hash,
            "schema_version": schema_version,
            "randomness_mode": "forbidden",
            "transcription_path": str(transcription_path),
        }
    ):
        console.print("[cyan]Stage:[/cyan] Parsing canonical EVA transcription...")
        parser = EVAParser()
        parsed_lines = list(parser.parse(transcription_path))
        console.print(f"[cyan]Stage:[/cyan] Parsed lines: {len(parsed_lines)}")

        controller = get_randomness_controller()
        extractor = StrokeExtractor(schema=schema)
        console.print("[cyan]Stage:[/cyan] Extracting token, line, and page stroke profiles...")
        with controller.forbidden_context("phase11_stage1_extract"):
            extracted = extractor.extract_corpus(parsed_lines, console=console)

        extracted["input"] = {
            "transcription_path": str(transcription_path),
            "corpus_hash": corpus_hash,
            "schema_version": schema_version,
        }
        saved_paths = ProvenanceWriter.save_results(extracted, output_path)
        elapsed = time.time() - t_start
        stats: dict[str, Any] = extracted.get("corpus_stats", {})
        console.print(
            "[green]Stage 1 complete[/green] "
            f"tokens={stats.get('token_count', 0)} lines={stats.get('line_count', 0)} "
            f"duration={elapsed:.1f}s"
        )
        console.print(
            f"[green]Saved:[/green] {saved_paths['latest_path']} "
            f"(snapshot: {saved_paths['snapshot_path']})"
        )


if __name__ == "__main__":
    main()

