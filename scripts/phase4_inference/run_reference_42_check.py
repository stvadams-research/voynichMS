#!/usr/bin/env python3
# ruff: noqa: E402
"""
Reference-42 relevance check (Phase 4).

Scores whether structural counts disproportionately reference the target value
across line/page/section levels.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase4_inference.projection_diagnostics.reference_number import (  # noqa: E402
    ReferenceNumberAnalyzer,
    ReferenceNumberConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
FOLIO_PATTERN = re.compile(r"^f(\d+)([rv])(\d*)$")
SECTION_RANGES = {
    "herbal": (1, 66),
    "astronomical": (67, 73),
    "biological": (75, 84),
    "cosmological": (85, 86),
    "pharmaceutical": (87, 102),
    "stars": (103, 116),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reference-number relevance diagnostics.")
    parser.add_argument("--dataset-id", type=str, default="voynich_real")
    parser.add_argument("--target", type=int, default=42)
    parser.add_argument("--window-radius", type=int, default=6)
    parser.add_argument(
        "--output-name",
        type=str,
        default="reference_42_check.json",
        help="Output filename written under results/data/phase4_inference/",
    )
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Reference-Number Relevance Check[/bold blue]\n"
            f"dataset={args.dataset_id} | target={args.target} | window=+/-{args.window_radius}",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_reference_42_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        metric_values = _load_structural_metric_values(store=store, dataset_id=args.dataset_id)

        analyzer = ReferenceNumberAnalyzer(
            ReferenceNumberConfig(
                target_value=int(args.target),
                local_window_radius=max(1, int(args.window_radius)),
            )
        )
        results = analyzer.analyze(metric_values)
        results["dataset_id"] = args.dataset_id
        results["metric_value_counts"] = {
            metric: len(values) for metric, values in metric_values.items()
        }

        _print_metric_table(results)
        _print_aggregate_table(results)

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)

        store.save_run(run)


def _load_structural_metric_values(store: MetadataStore, dataset_id: str) -> dict[str, list[int]]:
    session = store.Session()
    try:
        page_rows = (
            session.query(PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(PageRecord.id)
            .all()
        )
        line_rows = (
            session.query(PageRecord.id, TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index)
            .all()
        )
        token_rows = (
            session.query(
                PageRecord.id,
                TranscriptionTokenRecord.line_id,
                TranscriptionTokenRecord.content,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )
    finally:
        session.close()

    page_ids = [str(page_id) for (page_id,) in page_rows]

    line_token_counts: dict[str, int] = defaultdict(int)
    line_char_counts: dict[str, int] = defaultdict(int)
    page_token_counts: dict[str, int] = defaultdict(int)
    page_char_counts: dict[str, int] = defaultdict(int)
    for page_id, line_id, content in token_rows:
        page_id_s = str(page_id)
        line_id_s = str(line_id)
        token = str(content)
        line_token_counts[line_id_s] += 1
        line_char_counts[line_id_s] += len(token)
        page_token_counts[page_id_s] += 1
        page_char_counts[page_id_s] += len(token)

    line_token_count_values: list[int] = []
    line_char_count_values: list[int] = []
    page_line_counts: dict[str, int] = defaultdict(int)
    for page_id, line_id in line_rows:
        page_id_s = str(page_id)
        line_id_s = str(line_id)
        page_line_counts[page_id_s] += 1
        line_token_count_values.append(int(line_token_counts.get(line_id_s, 0)))
        line_char_count_values.append(int(line_char_counts.get(line_id_s, 0)))

    page_line_count_values = [int(page_line_counts.get(page_id, 0)) for page_id in page_ids]
    page_token_count_values = [int(page_token_counts.get(page_id, 0)) for page_id in page_ids]
    page_char_count_values = [int(page_char_counts.get(page_id, 0)) for page_id in page_ids]

    section_pages: dict[str, list[str]] = defaultdict(list)
    section_line_count: dict[str, int] = defaultdict(int)
    section_token_count: dict[str, int] = defaultdict(int)
    section_char_count: dict[str, int] = defaultdict(int)
    for page_id in page_ids:
        section = _section_for_folio(page_id)
        if section == "unknown":
            continue
        section_pages[section].append(page_id)
        section_line_count[section] += int(page_line_counts.get(page_id, 0))
        section_token_count[section] += int(page_token_counts.get(page_id, 0))
        section_char_count[section] += int(page_char_counts.get(page_id, 0))

    section_names = sorted(section_pages.keys())
    section_page_count_values = [len(section_pages[name]) for name in section_names]
    section_line_count_values = [int(section_line_count[name]) for name in section_names]
    section_token_count_values = [int(section_token_count[name]) for name in section_names]
    section_char_count_values = [int(section_char_count[name]) for name in section_names]

    return {
        "line_token_count": line_token_count_values,
        "line_char_count": line_char_count_values,
        "page_line_count": page_line_count_values,
        "page_token_count": page_token_count_values,
        "page_char_count": page_char_count_values,
        "section_page_count": section_page_count_values,
        "section_line_count": section_line_count_values,
        "section_token_count": section_token_count_values,
        "section_char_count": section_char_count_values,
    }


def _section_for_folio(folio_id: str) -> str:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return "unknown"
    folio_num = int(match.group(1))
    for section, (start, end) in SECTION_RANGES.items():
        if start <= folio_num <= end:
            return section
    return "unknown"


def _print_metric_table(results: dict[str, Any]) -> None:
    table = Table(title="Reference-Number Signals by Metric")
    table.add_column("Metric", style="cyan")
    table.add_column("N", justify="right")
    table.add_column("Hits", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Local z", justify="right")
    table.add_column("Neighbor z", justify="right")
    table.add_column("Class", justify="right")

    metrics = results.get("metrics", {})
    for metric_name in sorted(metrics.keys()):
        row = metrics[metric_name]
        if row.get("status") != "ok":
            table.add_row(metric_name, "0", "n/a", "n/a", "n/a", "n/a", "insufficient")
            continue
        local_z = float(row["local_window_test"]["z_score"])
        neighbor_z = float(row["neighborhood_test"]["z_score"])
        table.add_row(
            metric_name,
            str(int(row["n_observations"])),
            str(int(row["target_count"])),
            f"{float(row['target_rate']):.4f}",
            f"{local_z:.2f}",
            f"{neighbor_z:.2f}",
            str(row["classification"]),
        )
    console.print(table)


def _print_aggregate_table(results: dict[str, Any]) -> None:
    agg = results.get("aggregate", {})
    table = Table(title="Reference-Number Aggregate")
    table.add_column("Field", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Assessment", str(agg.get("assessment", "unknown")))
    table.add_row("Metrics analyzed", str(int(agg.get("metric_count", 0))))
    table.add_row("Metrics with hits", str(int(agg.get("hit_metric_count", 0))))
    table.add_row("Strong signals", str(int(agg.get("strong_signal_metric_count", 0))))
    table.add_row("Weak signals", str(int(agg.get("weak_signal_metric_count", 0))))
    table.add_row("Max local z", f"{float(agg.get('max_local_z_score', 0.0)):.2f}")
    table.add_row("Max neighbor z", f"{float(agg.get('max_neighbor_z_score', 0.0)):.2f}")
    console.print(table)


if __name__ == "__main__":
    run_experiment(parse_args())

