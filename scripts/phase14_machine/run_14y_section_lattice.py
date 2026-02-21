#!/usr/bin/env python3
"""Phase 14Y: Section-Aware Lattice Routing.

The global lattice treats all 7 manuscript sections identically, but
admissibility varies from 27.7% (Astro) to 53.2% (Biological).  This
script tests whether section-specific spectral reordering can close the
gap — the same 50 physical windows exist, but the scribe's traversal
pattern may differ by section/hand.

Approach:
1. Build per-section 50×50 transition matrices.
2. Compute section-specific Fiedler reorderings.
3. Route each line through its section's ordering.
4. Measure global and per-section admissibility.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import sanitize_token  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
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
    project_root / "results/data/phase14_machine/section_lattice.json"
)
console = Console()

# Manuscript section definitions (folio ranges)
SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
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


def spectral_reorder(word_to_window, window_contents, lines, num_wins):
    """Compute spectral reordering for a set of lines.

    Returns old_to_new mapping (dict: old_window_id -> new_window_id).
    """
    matrix = np.zeros((num_wins, num_wins), dtype=int)
    for line in lines:
        prev_win = None
        for word in line:
            if word in word_to_window:
                cur_win = word_to_window[word]
                if prev_win is not None:
                    matrix[prev_win][cur_win] += 1
                prev_win = cur_win

    sym = matrix + matrix.T
    row_sums = sym.sum(axis=1).astype(float)

    # Handle disconnected windows (zero row sum)
    if np.any(row_sums == 0):
        # Add tiny self-loops to prevent singular Laplacian
        for i in range(num_wins):
            if row_sums[i] == 0:
                sym[i][i] = 1
                row_sums[i] = 1

    D = np.diag(row_sums)
    L = D - sym.astype(float)
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    fiedler = eigenvectors[:, 1]
    order = [int(x) for x in np.argsort(fiedler)]
    return {old_id: new_id for new_id, old_id in enumerate(order)}


def apply_reordering(word_to_window, window_contents, old_to_new):
    """Apply a reordering map to produce new lattice_map and window_contents."""
    new_w2w = {}
    for word, old_win in word_to_window.items():
        if old_win in old_to_new:
            new_w2w[word] = int(old_to_new[old_win])

    new_wc = {}
    for old_id, words in window_contents.items():
        new_id = old_to_new.get(old_id)
        if new_id is not None:
            new_wc[new_id] = words

    return new_w2w, new_wc


def measure_admissibility(lines, word_to_window, window_contents, num_wins):
    """Measure drift-admissibility (±1) for a set of lines."""
    admissible = 0
    total = 0
    current_window = 0

    for line in lines:
        for word in line:
            if word not in word_to_window:
                continue
            total += 1

            found = False
            for d in [-1, 0, 1]:
                check_win = (current_window + d) % num_wins
                if word in window_contents.get(check_win, []):
                    found = True
                    current_window = word_to_window[word]
                    break

            if found:
                admissible += 1
            else:
                current_window = word_to_window[word]

    return admissible, total


def main():
    console.print(
        "[bold blue]Phase 14Y: Section-Aware Lattice Routing[/bold blue]"
    )

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load global palette (already spectrally reordered)
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    global_w2w = data["lattice_map"]
    global_wc = {int(k): v for k, v in data["window_contents"].items()}
    num_wins = len(global_wc)

    # 2. Load lines with folio metadata
    store = MetadataStore(DB_PATH)
    folio_lines = load_lines_with_folios(store)
    console.print(f"Loaded {len(folio_lines)} lines with folio metadata.")

    # 3. Group lines by section
    section_lines = defaultdict(list)
    for folio_id, line in folio_lines:
        f_num = get_folio_num(folio_id)
        section = get_section(f_num)
        section_lines[section].append(line)

    # 4. Measure global baseline (uniform reordering)
    all_lines = [line for _, line in folio_lines]
    base_adm, base_total = measure_admissibility(
        all_lines, global_w2w, global_wc, num_wins
    )
    base_rate = base_adm / base_total if base_total > 0 else 0
    console.print(
        f"\nGlobal baseline (uniform ordering): "
        f"{base_rate * 100:.2f}% ({base_adm}/{base_total})"
    )

    # 5. Compute per-section reorderings
    console.print("\nComputing per-section spectral reorderings...")
    section_reorderings = {}
    section_results = {}

    # We reorder from the ORIGINAL KMeans windows, not the global spectral ordering.
    # But we only have the globally-reordered palette. The section-specific ordering
    # is computed from the global reordered palette's transition patterns within
    # each section. This finds the optimal traversal order for each section.

    for section_name in sorted(SECTIONS.keys()):
        lines = section_lines.get(section_name, [])
        if len(lines) < 10:
            console.print(f"  {section_name}: too few lines ({len(lines)}), skipping")
            continue

        # Measure baseline on this section's lines
        sec_base_adm, sec_base_total = measure_admissibility(
            lines, global_w2w, global_wc, num_wins
        )
        sec_base_rate = (
            sec_base_adm / sec_base_total if sec_base_total > 0 else 0
        )

        # Compute section-specific reordering
        old_to_new = spectral_reorder(
            global_w2w, global_wc, lines, num_wins
        )
        sec_w2w, sec_wc = apply_reordering(
            global_w2w, global_wc, old_to_new
        )

        # Measure admissibility under section-specific ordering
        sec_adm, sec_total = measure_admissibility(
            lines, sec_w2w, sec_wc, num_wins
        )
        sec_rate = sec_adm / sec_total if sec_total > 0 else 0

        delta = (sec_rate - sec_base_rate) * 100

        section_reorderings[section_name] = old_to_new
        section_results[section_name] = {
            "num_lines": len(lines),
            "num_tokens": sec_total,
            "global_admissibility": sec_base_rate,
            "section_admissibility": sec_rate,
            "delta_pp": delta,
        }

        console.print(
            f"  {section_name}: {sec_base_rate * 100:.1f}% → "
            f"{sec_rate * 100:.1f}% ({delta:+.1f}pp) "
            f"[{len(lines)} lines, {sec_total} tokens]"
        )

    # 6. Measure global admissibility under section-aware routing
    # Each line uses its section's reordering
    console.print("\nMeasuring global admissibility with section-aware routing...")
    section_adm_total = 0
    section_tok_total = 0

    for folio_id, line in folio_lines:
        f_num = get_folio_num(folio_id)
        section = get_section(f_num)

        if section in section_reorderings:
            old_to_new = section_reorderings[section]
            sec_w2w, sec_wc = apply_reordering(
                global_w2w, global_wc, old_to_new
            )
        else:
            sec_w2w, sec_wc = global_w2w, global_wc

        adm, tok = measure_admissibility(
            [line], sec_w2w, sec_wc, num_wins
        )
        section_adm_total += adm
        section_tok_total += tok

    section_aware_rate = (
        section_adm_total / section_tok_total
        if section_tok_total > 0 else 0
    )
    global_delta = (section_aware_rate - base_rate) * 100

    console.print(
        f"\nGlobal section-aware: {section_aware_rate * 100:.2f}% "
        f"({global_delta:+.2f}pp vs uniform)"
    )

    # 7. Save results
    results = {
        "global_baseline": {
            "admissibility": base_rate,
            "admissible": base_adm,
            "total": base_total,
        },
        "section_aware_global": {
            "admissibility": section_aware_rate,
            "admissible": section_adm_total,
            "total": section_tok_total,
            "delta_pp": global_delta,
        },
        "per_section": section_results,
        "num_windows": num_wins,
        "num_sections": len(section_results),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Summary table
    table = Table(title="Section-Aware Lattice Routing")
    table.add_column("Section", style="cyan")
    table.add_column("Lines", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Global Ordering", justify="right")
    table.add_column("Section Ordering", justify="right", style="bold green")
    table.add_column("Delta", justify="right")

    for section in sorted(
        section_results.keys(),
        key=lambda s: section_results[s]["num_tokens"],
        reverse=True,
    ):
        r = section_results[section]
        table.add_row(
            section,
            str(r["num_lines"]),
            str(r["num_tokens"]),
            f"{r['global_admissibility'] * 100:.1f}%",
            f"{r['section_admissibility'] * 100:.1f}%",
            f"{r['delta_pp']:+.1f}pp",
        )
    table.add_row(
        "[bold]GLOBAL[/bold]",
        str(len(folio_lines)),
        str(section_tok_total),
        f"{base_rate * 100:.1f}%",
        f"[bold]{section_aware_rate * 100:.1f}%[/bold]",
        f"[bold]{global_delta:+.1f}pp[/bold]",
    )
    console.print(table)

    if global_delta > 2:
        console.print(
            f"\n[bold green]IMPROVEMENT:[/bold green] Section-aware routing "
            f"adds {global_delta:.1f}pp globally. Different sections use "
            f"different traversal patterns on the same physical windows."
        )
    elif global_delta > 0:
        console.print(
            f"\n[bold yellow]MARGINAL:[/bold yellow] Section-aware routing "
            f"adds only {global_delta:.1f}pp. The global ordering is already "
            f"a reasonable compromise across sections."
        )
    else:
        console.print(
            "\n[bold]NO IMPROVEMENT:[/bold] Section-specific reordering "
            "does not improve global admissibility. Sections share a common "
            "traversal pattern."
        )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14y_section_lattice"}
    ):
        main()
