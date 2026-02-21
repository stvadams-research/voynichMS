#!/usr/bin/env python3
"""Phase 14V: Failure Diagnosis.

Examines the remaining ~64% lattice failure rate post-consistency fix.
Categorizes failures by type and analyzes per-section variation to
determine whether failures are uniformly distributed or concentrated
in specific manuscript regions.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import sanitize_token  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/failure_diagnosis.json"
)
console = Console()

# Approximate folio ranges for major sections
SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Biological": (75, 84),
    "Astro": (67, 74),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


def get_folio_num(folio_id):
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def get_section(folio_num):
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def load_lines_with_folios(store):
    """Load ZL lines with folio IDs for section analysis."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
                TranscriptionLineRecord.id,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id
                == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(
                TranscriptionLineRecord.source_id == "zandbergen_landini"
            )
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )

        # Group by line, track folio
        lines = []
        current_line = []
        current_folio = None
        last_line_id = None

        for content, folio_id, line_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if last_line_id is not None and line_id != last_line_id:
                if current_line:
                    lines.append((current_folio, current_line))
                current_line = []
            current_line.append(clean)
            current_folio = folio_id
            last_line_id = line_id
        if current_line:
            lines.append((current_folio, current_line))
        return lines
    finally:
        session.close()


def main():
    console.print(
        "[bold yellow]Phase 14V: Failure Diagnosis "
        "(Understanding the 64%)[/bold yellow]"
    )

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load lattice
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {
        int(k): v for k, v in data["window_contents"].items()
    }
    num_wins = len(window_contents)

    # 2. Load lines with folio info
    store = MetadataStore(DB_PATH)
    folio_lines = load_lines_with_folios(store)
    console.print(f"Loaded {len(folio_lines)} lines with folio metadata.")

    # 3. Categorize each token
    failure_types = Counter()
    section_stats = defaultdict(lambda: {
        "total": 0, "admissible": 0, "not_in_palette": 0,
        "wrong_window": 0, "extreme_jump": 0,
    })
    current_window = 0

    # Top failing tokens
    token_failures = Counter()

    for folio_id, line in folio_lines:
        f_num = get_folio_num(folio_id)
        section = get_section(f_num)

        for word in line:
            section_stats[section]["total"] += 1

            # Category 1: Token not in palette at all
            if word not in lattice_map:
                failure_types["not_in_palette"] += 1
                section_stats[section]["not_in_palette"] += 1
                token_failures[word] += 1
                continue

            # Check distance to nearest window containing this token
            found_dist = None
            for dist in range(0, num_wins // 2 + 1):
                for direction in [1, -1]:
                    check_win = (current_window + (dist * direction)) % num_wins
                    if word in window_contents.get(check_win, []):
                        found_dist = dist
                        break
                if found_dist is not None:
                    break

            if found_dist is not None and found_dist <= 1:
                # Admissible
                failure_types["admissible"] += 1
                section_stats[section]["admissible"] += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            elif found_dist is not None and found_dist <= 10:
                # Wrong window but reachable
                failure_types["wrong_window"] += 1
                section_stats[section]["wrong_window"] += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            else:
                # Extreme jump
                failure_types["extreme_jump"] += 1
                section_stats[section]["extreme_jump"] += 1
                current_window = lattice_map[word]

    total_tokens = sum(failure_types.values())

    # 4. Compute per-section admissibility
    section_adm = {}
    for section, stats in section_stats.items():
        if stats["total"] > 0:
            section_adm[section] = stats["admissible"] / stats["total"]

    # 5. Top tokens not in palette
    top_missing = token_failures.most_common(20)

    # 6. Save and Report
    results = {
        "total_tokens": total_tokens,
        "failure_types": dict(failure_types),
        "failure_rates": {
            k: v / total_tokens for k, v in failure_types.items()
        },
        "section_stats": {
            k: dict(v) for k, v in section_stats.items()
        },
        "section_admissibility": section_adm,
        "top_missing_tokens": top_missing,
        "palette_size": len(lattice_map),
        "num_windows": num_wins,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Failure diagnosis complete.[/green]")

    # Failure type table
    table = Table(title="Failure Category Breakdown")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Rate", justify="right", style="bold green")

    for cat in ["admissible", "wrong_window", "extreme_jump", "not_in_palette"]:
        count = failure_types.get(cat, 0)
        rate = count / total_tokens if total_tokens > 0 else 0
        table.add_row(cat, f"{count:,}", f"{rate * 100:.2f}%")
    console.print(table)

    # Per-section table
    table2 = Table(title="Per-Section Admissibility")
    table2.add_column("Section", style="cyan")
    table2.add_column("Tokens", justify="right")
    table2.add_column("Admissible %", justify="right", style="bold green")
    table2.add_column("Not in Palette %", justify="right")
    table2.add_column("Extreme Jump %", justify="right")

    for section in sorted(
        section_stats.keys(),
        key=lambda s: section_stats[s]["total"],
        reverse=True,
    ):
        stats = section_stats[section]
        t = stats["total"]
        if t == 0:
            continue
        table2.add_row(
            section,
            f"{t:,}",
            f"{stats['admissible'] / t * 100:.1f}%",
            f"{stats['not_in_palette'] / t * 100:.1f}%",
            f"{stats['extreme_jump'] / t * 100:.1f}%",
        )
    console.print(table2)

    # Top missing tokens
    if top_missing:
        table3 = Table(title="Top 20 Tokens Not in Palette")
        table3.add_column("Token", style="cyan")
        table3.add_column("Occurrences", justify="right")
        for tok, count in top_missing:
            table3.add_row(tok, str(count))
        console.print(table3)

    # Overall verdict
    adm_rate = failure_types.get("admissible", 0) / total_tokens
    nip_rate = failure_types.get("not_in_palette", 0) / total_tokens
    console.print(
        f"\n[bold]Overall:[/bold] {adm_rate * 100:.1f}% admissible, "
        f"{nip_rate * 100:.1f}% not in palette"
    )
    if nip_rate > 0.3:
        console.print(
            f"[bold yellow]NOTE:[/bold yellow] {nip_rate * 100:.1f}% of "
            f"tokens are not in the palette. This is the primary "
            f"failure source — these tokens were filtered during "
            f"palette construction (top_n cutoff or sanitization edge)."
        )


if __name__ == "__main__":
    main()
