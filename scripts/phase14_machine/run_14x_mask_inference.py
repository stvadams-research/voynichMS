#!/usr/bin/env python3
"""Phase 14X: Per-Line Mask Offset Inference.

The emulator models 12 physical mask states where:
    visible_window = (base_window + mask_offset) % 50

If the real manuscript uses mask rotations, the scribe may set the disc
once per line (or per section).  This script:

1. For each line, tries all 50 possible mask offsets.
2. Picks the offset that maximizes within-line admissibility.
3. Checks if optimal offsets cluster into a small number of states.
4. Measures admissibility under the inferred mask schedule.
5. Compares with and without the reordered palette from 14W.
"""

import json
import re
import sys
from collections import Counter
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
ORIGINAL_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
REORDERED_PATH = (
    project_root / "results/data/phase14_machine/reordered_palette.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/mask_inference.json"
)
console = Console()

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
    """Extract numeric folio index from page id."""
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def get_section(folio_num):
    """Map folio number into the canonical section bins."""
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def get_hand(folio_num):
    """Approximate Currier hand assignment used in Phase 14 scripts."""
    if folio_num <= 66:
        return "Hand1"
    if 75 <= folio_num <= 84 or 103 <= folio_num <= 116:
        return "Hand2"
    return "Unknown"


def load_lines_with_metadata(store):
    """Load canonical ZL lines with folio and local line metadata.

    Returns:
        List of dict entries:
            {
              "tokens": [...],
              "folio_id": "f1r",
              "folio_num": 1,
              "line_index": 0,   # local within folio
              "section": "Herbal A",
              "hand": "Hand1",
            }
    """
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )

        lines = []
        current_tokens = []
        current_folio = None
        current_line_id = None
        folio_local_line_idx = {}

        for content, folio_id, line_id, _line_index in rows:
            clean = sanitize_token(content)
            if not clean:
                continue

            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    local_idx = folio_local_line_idx.get(current_folio, 0)
                    f_num = get_folio_num(current_folio)
                    lines.append(
                        {
                            "tokens": current_tokens,
                            "folio_id": current_folio,
                            "folio_num": f_num,
                            "line_index": local_idx,
                            "section": get_section(f_num),
                            "hand": get_hand(f_num),
                        }
                    )
                    folio_local_line_idx[current_folio] = local_idx + 1
                current_tokens = []

            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id

        if current_tokens:
            local_idx = folio_local_line_idx.get(current_folio, 0)
            f_num = get_folio_num(current_folio)
            lines.append(
                {
                    "tokens": current_tokens,
                    "folio_id": current_folio,
                    "folio_num": f_num,
                    "line_index": local_idx,
                    "section": get_section(f_num),
                    "hand": get_hand(f_num),
                }
            )

        return lines
    finally:
        session.close()


def load_palette(path):
    """Load lattice_map and window_contents from a palette JSON."""
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    # Handle both key styles
    lm_key = (
        "reordered_lattice_map"
        if "reordered_lattice_map" in results
        else "lattice_map"
    )
    wc_key = (
        "reordered_window_contents"
        if "reordered_window_contents" in results
        else "window_contents"
    )
    lattice_map = results[lm_key]
    window_contents = {int(k): v for k, v in results[wc_key].items()}
    return lattice_map, window_contents


def score_line_with_offset(
    line, offset, lattice_map, window_contents, num_wins
):
    """Score a single line's admissibility under a given mask offset.

    The offset shifts every window lookup:
        effective_window = (assigned_window - offset) % num_wins

    Returns (admissible_count, total_clamped).
    """
    admissible = 0
    total = 0
    current_window = 0

    for word in line:
        if word not in lattice_map:
            continue
        total += 1

        # Apply mask: shift the current tracking window
        shifted_win = (current_window + offset) % num_wins

        # Check drift ±1 around the shifted position
        found = False
        for d in [-1, 0, 1]:
            check_win = (shifted_win + d) % num_wins
            if word in window_contents.get(check_win, []):
                found = True
                # Advance tracking (un-shifted)
                assigned = lattice_map.get(word)
                if assigned is not None:
                    current_window = (assigned - offset) % num_wins
                break

        if found:
            admissible += 1
        else:
            # Snap to recover (un-shifted)
            assigned = lattice_map.get(word)
            if assigned is not None:
                current_window = (assigned - offset) % num_wins

    return admissible, total


def infer_mask_schedule(lines, lattice_map, window_contents, num_wins):
    """For each line, find the mask offset that maximizes admissibility."""
    line_offsets = []
    line_scores = []

    for line in lines:
        best_offset = 0
        best_score = -1
        best_total = 0

        for offset in range(num_wins):
            adm, total = score_line_with_offset(
                line, offset, lattice_map, window_contents, num_wins
            )
            if total > 0 and adm > best_score:
                best_score = adm
                best_offset = offset
                best_total = total

        line_offsets.append(best_offset)
        line_scores.append(
            best_score / best_total if best_total > 0 else 0
        )

    return line_offsets, line_scores


def measure_with_schedule(
    lines, offsets, lattice_map, window_contents, num_wins
):
    """Measure total admissibility using per-line mask offsets."""
    total_adm = 0
    total_tok = 0

    for line, offset in zip(lines, offsets, strict=True):
        adm, tok = score_line_with_offset(
            line, offset, lattice_map, window_contents, num_wins
        )
        total_adm += adm
        total_tok += tok

    return total_adm, total_tok


def measure_baseline(lines, lattice_map, window_contents, num_wins):
    """Measure admissibility with no mask (offset=0 for all lines)."""
    return measure_with_schedule(
        lines, [0] * len(lines), lattice_map, window_contents, num_wins
    )


def main():
    console.print(
        "[bold magenta]Phase 14X: Per-Line Mask Offset Inference[/bold magenta]"
    )

    if not ORIGINAL_PATH.exists():
        console.print(f"[red]Error: {ORIGINAL_PATH} not found.[/red]")
        return

    store = MetadataStore(DB_PATH)
    line_entries = load_lines_with_metadata(store)
    lines = [entry["tokens"] for entry in line_entries]
    console.print(f"Loaded {len(lines)} lines.")

    # Test with both original and reordered palettes
    palette_configs = [("Original", ORIGINAL_PATH)]
    if REORDERED_PATH.exists():
        palette_configs.append(("Reordered", REORDERED_PATH))

    all_results = {}

    for palette_name, palette_path in palette_configs:
        console.print(f"\n[bold]=== {palette_name} Palette ===[/bold]")
        lattice_map, window_contents = load_palette(palette_path)
        num_wins = len(window_contents)

        # Baseline (no mask)
        base_adm, base_tok = measure_baseline(
            lines, lattice_map, window_contents, num_wins
        )
        base_rate = base_adm / base_tok * 100 if base_tok > 0 else 0
        console.print(f"  Baseline (no mask): {base_rate:.2f}%")

        # Infer per-line mask offsets
        console.print(
            f"  Inferring optimal mask offsets for {len(lines)} lines..."
        )
        offsets, scores = infer_mask_schedule(
            lines, lattice_map, window_contents, num_wins
        )

        # Measure with inferred schedule
        mask_adm, mask_tok = measure_with_schedule(
            lines, offsets, lattice_map, window_contents, num_wins
        )
        mask_rate = mask_adm / mask_tok * 100 if mask_tok > 0 else 0
        console.print(f"  With inferred mask: {mask_rate:.2f}%")
        console.print(
            f"  Improvement: {mask_rate - base_rate:+.2f}pp"
        )

        # Analyze offset distribution
        offset_counts = Counter(offsets)
        n_unique = len(offset_counts)
        top_offsets = offset_counts.most_common(12)

        # How much of the corpus do the top-K offsets cover?
        cumulative_coverage = {}
        sorted_offsets = offset_counts.most_common()
        cum = 0
        for i, (_off, cnt) in enumerate(sorted_offsets):
            cum += cnt
            if (i + 1) in [1, 3, 5, 8, 12, 20]:
                cumulative_coverage[i + 1] = cum / len(lines) * 100

        console.print(f"  Unique offsets used: {n_unique}")
        console.print("  Top-K offset coverage:")
        for k, cov in cumulative_coverage.items():
            console.print(f"    Top {k}: {cov:.1f}% of lines")

        # Measure with restricted offset set (top-12 only)
        top12_set = set(off for off, _ in top_offsets)
        restricted_offsets = []
        for off in offsets:
            if off in top12_set:
                restricted_offsets.append(off)
            else:
                # Fall back to offset=0
                restricted_offsets.append(0)

        r12_adm, r12_tok = measure_with_schedule(
            lines, restricted_offsets,
            lattice_map, window_contents, num_wins,
        )
        r12_rate = r12_adm / r12_tok * 100 if r12_tok > 0 else 0
        console.print(
            f"  Restricted to top-12 offsets: {r12_rate:.2f}%"
        )

        line_schedule = []
        for idx, entry in enumerate(line_entries):
            best_offset = offsets[idx]
            line_schedule.append(
                {
                    "folio_id": entry["folio_id"],
                    "folio_num": int(entry["folio_num"]),
                    "line_index": int(entry["line_index"]),
                    "section": entry["section"],
                    "hand": entry["hand"],
                    "best_offset": int(best_offset),
                    "line_score": float(scores[idx]),
                }
            )

        all_results[palette_name] = {
            "baseline_admissibility": base_rate / 100,
            "mask_admissibility": mask_rate / 100,
            "improvement_pp": mask_rate - base_rate,
            "restricted_12_admissibility": r12_rate / 100,
            "unique_offsets": n_unique,
            "top_12_offsets": [
                {"offset": int(o), "count": int(c)}
                for o, c in top_offsets
            ],
            "cumulative_coverage": cumulative_coverage,
            "avg_line_score": float(np.mean(scores)),
            "line_schedule": line_schedule,
        }

    # Save combined results
    ProvenanceWriter.save_results(all_results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Summary table
    table = Table(title="Mask Inference Results")
    table.add_column("Configuration", style="cyan")
    table.add_column("No Mask", justify="right")
    table.add_column("Per-Line Mask", justify="right", style="bold green")
    table.add_column("Top-12 Restricted", justify="right")
    table.add_column("Delta", justify="right")

    for name, r in all_results.items():
        table.add_row(
            name,
            f"{r['baseline_admissibility'] * 100:.2f}%",
            f"{r['mask_admissibility'] * 100:.2f}%",
            f"{r['restricted_12_admissibility'] * 100:.2f}%",
            f"{r['improvement_pp']:+.2f}pp",
        )
    console.print(table)

    # Interpretation
    best_result = max(all_results.values(), key=lambda x: x["mask_admissibility"])
    if best_result["mask_admissibility"] > 0.55:
        console.print(
            "\n[bold green]SIGNIFICANT:[/bold green] Mask inference raises "
            "admissibility above 55%. The manuscript likely uses physical "
            "disc rotation (mask states)."
        )
    elif best_result["improvement_pp"] > 10:
        console.print(
            "\n[bold yellow]MODERATE:[/bold yellow] Mask inference provides "
            f"{best_result['improvement_pp']:.1f}pp improvement. "
            "Physical rotation is plausible but not conclusive."
        )
    else:
        console.print(
            "\n[bold]WEAK:[/bold] Mask inference provides limited improvement. "
            "The extreme jumps are likely not caused by disc rotation."
        )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14x_mask_inference"}
    ):
        main()
