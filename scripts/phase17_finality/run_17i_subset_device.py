#!/usr/bin/env python3
"""Sprint F1–F3: Subset Device Architecture.

F1: Cumulative coverage analysis (token, transition, window occupancy)
F2: Plausible device dimensioning (subset volvelle/tabula + codebook)
F3: Admissibility under subset architecture

Determines whether a historically plausible device can explain the corpus
by inscribing only the high-frequency vocabulary, with the remainder
covered by a codebook or suffix rules.
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
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

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
SUFFIX_MAP_PATH = project_root / "results/data/phase14_machine/suffix_window_map.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/subset_device.json"

# Physical constants (same as C1)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
LINE_SPACING_MM = 2.0
WORD_SPACING_MM = 3.0
MARGIN_MM = 5.0

HISTORICAL_DEVICES = {
    "Alberti cipher disc (1467)": {"diameter_mm": 120, "type": "volvelle"},
    "Llull Ars Magna (c.1305)": {"diameter_mm": 200, "type": "volvelle"},
    "Apian Astronomicum (1540)": {"diameter_mm": 350, "type": "volvelle"},
}

SUBSET_SIZES = [50, 100, 200, 500, 1000, 2000]


# ── Helpers ───────────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = "reordered_lattice_map" if "reordered_lattice_map" in results else "lattice_map"
    wc_key = "reordered_window_contents" if "reordered_window_contents" in results else "window_contents"
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def load_lines(store):
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
            )
            .join(TranscriptionLineRecord,
                  TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord,
                  TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index,
                      TranscriptionTokenRecord.token_index)
            .all()
        )
        lines = []
        current_tokens = []
        current_line_id = None
        for content, line_id, _line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    lines.append(current_tokens)
                current_tokens = []
            current_tokens.append(clean)
            current_line_id = line_id
        if current_tokens:
            lines.append(current_tokens)
        return lines
    finally:
        session.close()


def signed_circular_offset(a, b, n):
    """Signed shortest-path offset from a to b on a ring of size n."""
    d = (b - a) % n
    return d if d <= n // 2 else d - n


def learn_offset_corrections(lines, lattice_map, num_windows):
    """Learn per-window mode corrections from the manuscript."""
    offsets_by_window = defaultdict(list)
    for line in lines:
        for i in range(len(line) - 1):
            w_curr = lattice_map.get(line[i])
            w_next = lattice_map.get(line[i + 1])
            if w_curr is not None and w_next is not None:
                pred = (w_curr + 1) % num_windows
                off = signed_circular_offset(pred, w_next, num_windows)
                offsets_by_window[w_curr].append(off)

    corrections = {}
    for w, offs in offsets_by_window.items():
        if offs:
            counts = Counter(offs)
            corrections[w] = counts.most_common(1)[0][0]
        else:
            corrections[w] = 0
    return corrections


# ── F1: Cumulative Coverage Analysis ─────────────────────────────────

def sprint_f1(lines, lattice_map, window_contents):
    """Compute token, transition, and window coverage curves."""
    console.rule("[bold blue]Sprint F1: Cumulative Coverage Analysis")

    # Build frequency distribution
    all_tokens = [t for line in lines for t in line if t in lattice_map]
    freq = Counter(all_tokens)
    vocab_by_freq = [word for word, _ in freq.most_common()]
    total_tokens = len(all_tokens)

    # F1.1: Token coverage curve
    console.print("\n[bold]F1.1: Token Coverage Curve[/bold]")
    token_coverage = []
    cumulative = 0
    for i, word in enumerate(vocab_by_freq):
        cumulative += freq[word]
        if (i + 1) in SUBSET_SIZES or (i + 1) == len(vocab_by_freq):
            token_coverage.append({
                "vocab_size": i + 1,
                "tokens_covered": cumulative,
                "coverage": round(cumulative / total_tokens, 4),
            })

    # Also record at standard thresholds
    thresholds = {50: None, 80: None, 90: None, 95: None, 99: None}
    cumul = 0
    for i, word in enumerate(vocab_by_freq):
        cumul += freq[word]
        pct = cumul / total_tokens * 100
        for thresh in thresholds:
            if thresholds[thresh] is None and pct >= thresh:
                thresholds[thresh] = i + 1

    table = Table(title="Token Coverage Thresholds")
    table.add_column("Coverage %", justify="right", style="cyan")
    table.add_column("Words needed", justify="right", style="bold")
    for thresh, n_words in thresholds.items():
        table.add_row(f"{thresh}%", str(n_words) if n_words else "—")
    console.print(table)

    # F1.2: Transition coverage curve
    console.print("\n[bold]F1.2: Transition Coverage Curve[/bold]")
    all_transitions = []
    for line in lines:
        for i in range(len(line) - 1):
            if line[i] in lattice_map and line[i + 1] in lattice_map:
                all_transitions.append((line[i], line[i + 1]))

    total_transitions = len(all_transitions)
    transition_coverage = []

    for size in SUBSET_SIZES:
        subset = set(vocab_by_freq[:size])
        covered = sum(1 for a, b in all_transitions if a in subset and b in subset)
        transition_coverage.append({
            "vocab_size": size,
            "transitions_covered": covered,
            "total_transitions": total_transitions,
            "coverage": round(covered / total_transitions, 4) if total_transitions > 0 else 0,
        })

    table = Table(title="Transition Coverage by Subset Size")
    table.add_column("Vocab Size", justify="right", style="cyan")
    table.add_column("Transitions", justify="right")
    table.add_column("Coverage", justify="right", style="bold")
    for tc in transition_coverage:
        table.add_row(
            str(tc["vocab_size"]),
            f"{tc['transitions_covered']:,}",
            f"{tc['coverage']:.1%}",
        )
    console.print(table)

    # F1.3: Window coverage analysis
    console.print("\n[bold]F1.3: Window Coverage Analysis[/bold]")

    # Invert lattice_map: word → window
    word_to_window = {}
    for w in range(NUM_WINDOWS):
        for word in window_contents.get(w, []):
            word_to_window[word] = w

    window_coverage = []
    for size in SUBSET_SIZES:
        subset = set(vocab_by_freq[:size])
        occupied_windows = set()
        words_per_window = defaultdict(int)
        for word in subset:
            w = word_to_window.get(word)
            if w is not None:
                occupied_windows.add(w)
                words_per_window[w] += 1

        empty_windows = NUM_WINDOWS - len(occupied_windows)
        avg_words = np.mean(list(words_per_window.values())) if words_per_window else 0

        window_coverage.append({
            "vocab_size": size,
            "windows_occupied": len(occupied_windows),
            "windows_empty": empty_windows,
            "avg_words_per_window": round(float(avg_words), 1),
            "max_words_per_window": max(words_per_window.values()) if words_per_window else 0,
        })

    table = Table(title="Window Occupancy by Subset Size")
    table.add_column("Vocab Size", justify="right", style="cyan")
    table.add_column("Windows Used", justify="right")
    table.add_column("Empty", justify="right")
    table.add_column("Avg/Window", justify="right")
    table.add_column("Max/Window", justify="right")
    for wc in window_coverage:
        table.add_row(
            str(wc["vocab_size"]),
            str(wc["windows_occupied"]),
            str(wc["windows_empty"]),
            f"{wc['avg_words_per_window']:.1f}",
            str(wc["max_words_per_window"]),
        )
    console.print(table)

    # Identify breakpoint: where does transition coverage flatten?
    prev_cov = 0
    breakpoint_size = None
    for tc in transition_coverage:
        delta = tc["coverage"] - prev_cov
        if prev_cov > 0.80 and delta < 0.05:
            breakpoint_size = tc["vocab_size"]
            break
        prev_cov = tc["coverage"]

    if breakpoint_size:
        console.print(f"\n  Transition coverage flattens around vocab size ~{breakpoint_size}")

    return {
        "token_coverage_curve": token_coverage,
        "coverage_thresholds": {str(k): v for k, v in thresholds.items()},
        "transition_coverage_curve": transition_coverage,
        "window_coverage": window_coverage,
        "breakpoint_vocab_size": breakpoint_size,
        "total_lattice_vocab": len(vocab_by_freq),
        "total_tokens": total_tokens,
        "total_transitions": total_transitions,
    }


# ── F2: Plausible Device Dimensioning ────────────────────────────────

def sprint_f2(vocab_by_freq, freq, word_to_window, window_contents,
              transition_coverage, suffix_map):
    """Compute device dimensions for subset vocabulary."""
    console.rule("[bold blue]Sprint F2: Plausible Device Dimensioning")

    # Find the subset achieving ~90% transition coverage
    target_size = None
    for tc in transition_coverage:
        if tc["coverage"] >= 0.90:
            target_size = tc["vocab_size"]
            break
    if target_size is None:
        target_size = SUBSET_SIZES[-1]
        console.print(f"[yellow]No subset achieves 90% transition coverage. "
                      f"Using largest: {target_size}[/yellow]")

    subset = set(vocab_by_freq[:target_size])
    console.print(f"  Target subset: top {target_size} words "
                  f"({target_size / len(vocab_by_freq):.1%} of lattice vocab)")

    # F2.1: Subset volvelle specification
    console.print("\n[bold]F2.1: Subset Volvelle Specification[/bold]")

    # Count words per window in subset
    subset_per_window = defaultdict(list)
    for word in subset:
        w = word_to_window.get(word)
        if w is not None:
            subset_per_window[w].append(word)

    occupied_windows = len(subset_per_window)
    sector_angle_deg = 360.0 / occupied_windows if occupied_windows > 0 else 360.0
    sector_angle_rad = math.radians(sector_angle_deg)

    # Compute window areas for subset
    window_areas = {}
    for w, words in subset_per_window.items():
        n_words = len(words)
        avg_len = np.mean([len(word) for word in words]) if words else 0
        words_per_col = 18
        n_cols = math.ceil(n_words / words_per_col)
        col_width = avg_len * GLYPH_WIDTH_MM + WORD_SPACING_MM
        total_width = n_cols * col_width + 2 * MARGIN_MM
        total_height = min(n_words, words_per_col) * (GLYPH_HEIGHT_MM + LINE_SPACING_MM) + 2 * MARGIN_MM
        window_areas[w] = {
            "n_words": n_words,
            "width_mm": round(total_width, 1),
            "height_mm": round(total_height, 1),
        }

    # Volvelle with fewer rings
    n_rings = min(3, max(1, occupied_windows // 10))
    sorted_windows = sorted(subset_per_window.keys(),
                            key=lambda w: len(subset_per_window[w]))
    current_radius = 0
    ring_specs = []
    windows_per_ring = math.ceil(occupied_windows / n_rings)

    for ring_idx in range(n_rings):
        start = ring_idx * windows_per_ring
        end = min(start + windows_per_ring, occupied_windows)
        ring_windows = sorted_windows[start:end]
        if not ring_windows:
            continue
        max_height = max(window_areas.get(w, {"height_mm": 0})["height_mm"]
                         for w in ring_windows)
        inner_r = current_radius + MARGIN_MM
        outer_r = inner_r + max_height
        current_radius = outer_r
        ring_specs.append({
            "ring": ring_idx + 1,
            "inner_radius_mm": round(inner_r, 1),
            "outer_radius_mm": round(outer_r, 1),
            "n_windows": len(ring_windows),
        })

    subset_diameter = 2 * current_radius

    console.print(f"  Subset volvelle diameter: {subset_diameter:.0f} mm "
                  f"({subset_diameter / 10:.1f} cm)")
    console.print(f"  Windows used: {occupied_windows} (of {NUM_WINDOWS})")
    console.print(f"  Rings: {n_rings}")

    # Historical comparison
    table = Table(title="Subset Volvelle vs Historical Devices")
    table.add_column("Device", style="cyan")
    table.add_column("Diameter (mm)", justify="right")
    table.add_column("Ratio", justify="right", style="bold")

    for name, spec in HISTORICAL_DEVICES.items():
        ratio = subset_diameter / spec["diameter_mm"]
        table.add_row(name, str(spec["diameter_mm"]), f"{ratio:.2f}×")
    table.add_row("Subset Volvelle", f"{subset_diameter:.0f}", "1.0×",
                  style="bold green")
    console.print(table)

    # F2.2: Subset tabula
    console.print("\n[bold]F2.2: Subset Tabula Specification[/bold]")
    max_cell_w = max((a["width_mm"] for a in window_areas.values()), default=50)
    max_cell_h = max((a["height_mm"] for a in window_areas.values()), default=50)
    n_cols_tab = min(5, math.ceil(math.sqrt(occupied_windows)))
    n_rows_tab = math.ceil(occupied_windows / n_cols_tab)
    tabula_w = n_cols_tab * max_cell_w + 2 * MARGIN_MM
    tabula_h = n_rows_tab * max_cell_h + 2 * MARGIN_MM
    console.print(f"  Grid: {n_rows_tab}×{n_cols_tab}")
    console.print(f"  Dimensions: {tabula_w:.0f} × {tabula_h:.0f} mm "
                  f"({tabula_w / 10:.1f} × {tabula_h / 10:.1f} cm)")

    # F2.3: Codebook specification
    console.print("\n[bold]F2.3: Codebook Specification[/bold]")
    tail_words = set(vocab_by_freq) - subset
    tail_count = len(tail_words)

    # Suffix coverage of tail
    suffix_covered = 0
    if suffix_map:
        for word in tail_words:
            for sfx in suffix_map:
                if word.endswith(sfx) and len(word) > len(sfx):
                    suffix_covered += 1
                    break

    # Consultation frequency: how often does the scribe need the codebook?
    all_tokens_flat = [t for line in lines_global for t in line if t in lattice_map_global]
    device_hits = sum(1 for t in all_tokens_flat if t in subset)
    codebook_lookups = len(all_tokens_flat) - device_hits
    consultation_rate = codebook_lookups / len(all_tokens_flat) if all_tokens_flat else 0
    words_between_lookups = 1 / consultation_rate if consultation_rate > 0 else float("inf")

    console.print(f"  Codebook entries: {tail_count}")
    console.print(f"  Suffix-recoverable: {suffix_covered} "
                  f"({suffix_covered / tail_count:.1%})" if tail_count > 0 else "")
    console.print(f"  Consultation rate: {consultation_rate:.1%} of tokens")
    console.print(f"  Average words between lookups: {words_between_lookups:.1f}")

    # F2.4: Historical plausibility
    console.print("\n[bold]F2.4: Historical Plausibility Assessment[/bold]")

    alberti_ratio = subset_diameter / 120
    apian_ratio = subset_diameter / 350

    fits_known_range = 100 <= subset_diameter <= 400
    practical_codebook = words_between_lookups >= 3.0

    if fits_known_range and practical_codebook:
        plausibility = "PLAUSIBLE"
        color = "green"
    elif fits_known_range or practical_codebook:
        plausibility = "MARGINAL"
        color = "yellow"
    else:
        plausibility = "IMPLAUSIBLE"
        color = "red"

    console.print(f"  Device fits historical range (100-400mm): "
                  f"{'YES' if fits_known_range else 'NO'}")
    console.print(f"  Codebook is practical (≥3 words between): "
                  f"{'YES' if practical_codebook else 'NO'}")
    console.print(f"  [bold {color}]Plausibility verdict: {plausibility}[/bold {color}]")

    return {
        "target_subset_size": target_size,
        "volvelle": {
            "diameter_mm": round(subset_diameter, 0),
            "diameter_cm": round(subset_diameter / 10, 1),
            "n_rings": n_rings,
            "ring_specs": ring_specs,
            "windows_used": occupied_windows,
            "vs_alberti": round(alberti_ratio, 2),
            "vs_apian": round(apian_ratio, 2),
        },
        "tabula": {
            "grid": f"{n_rows_tab}x{n_cols_tab}",
            "width_mm": round(tabula_w, 0),
            "height_mm": round(tabula_h, 0),
        },
        "codebook": {
            "entries": tail_count,
            "suffix_recoverable": suffix_covered,
            "suffix_coverage_pct": round(suffix_covered / tail_count * 100, 1) if tail_count > 0 else 0,
            "consultation_rate": round(consultation_rate, 4),
            "words_between_lookups": round(words_between_lookups, 1),
        },
        "plausibility": plausibility,
        "fits_historical_range": fits_known_range,
        "practical_codebook": practical_codebook,
    }


# ── F3: Admissibility Under Subset Architecture ─────────────────────

def sprint_f3(lines, lattice_map, window_contents, corrections,
              vocab_by_freq, target_size, suffix_map):
    """Compute admissibility under the two-system model."""
    console.rule("[bold blue]Sprint F3: Admissibility Under Subset Architecture")

    subset = set(vocab_by_freq[:target_size])

    # F3.1: In-device admissibility
    console.print("\n[bold]F3.1: In-Device Admissibility[/bold]")

    in_device_transitions = 0
    in_device_admissible_strict = 0
    in_device_admissible_drift = 0

    off_device_in_out = 0  # in-vocab → OOV
    off_device_out_in = 0  # OOV → in-vocab
    off_device_out_out = 0  # OOV → OOV
    suffix_recovered = 0
    suffix_admissible = 0

    current_window = 0

    for line in lines:
        for i, word in enumerate(line):
            if word not in lattice_map:
                continue

            if i == 0:
                current_window = lattice_map[word]
                continue

            prev_word = line[i - 1]
            curr_word = word

            prev_in = prev_word in subset
            curr_in = curr_word in subset

            if prev_in and curr_in:
                # Both on device
                in_device_transitions += 1

                # Apply corrected admissibility
                corrected_next = (current_window + 1 + corrections.get(current_window, 0)) % NUM_WINDOWS

                # Strict: word in corrected window
                target_words = set(window_contents.get(corrected_next, []))
                if curr_word in target_words:
                    in_device_admissible_strict += 1
                    in_device_admissible_drift += 1
                else:
                    # Drift ±1
                    for offset in [-1, 1]:
                        check_win = (corrected_next + offset) % NUM_WINDOWS
                        if curr_word in set(window_contents.get(check_win, [])):
                            in_device_admissible_drift += 1
                            break

            elif prev_in and not curr_in:
                off_device_in_out += 1
                # Device gives next window, codebook gives word
                # Suffix recovery applicable
                if suffix_map:
                    for sfx, sfx_win in suffix_map.items():
                        if curr_word.endswith(sfx) and len(curr_word) > len(sfx):
                            suffix_recovered += 1
                            # Check if suffix window is admissible
                            corrected_next = (current_window + 1 + corrections.get(current_window, 0)) % NUM_WINDOWS
                            for offset in [-1, 0, 1]:
                                check_win = (corrected_next + offset) % NUM_WINDOWS
                                if check_win == sfx_win:
                                    suffix_admissible += 1
                                    break
                            break

            elif not prev_in and curr_in:
                off_device_out_in += 1

            else:
                off_device_out_out += 1

            # Update window
            if curr_word in lattice_map:
                current_window = lattice_map[curr_word]

    total_transitions = (in_device_transitions + off_device_in_out +
                         off_device_out_in + off_device_out_out)

    in_device_strict_rate = (in_device_admissible_strict / in_device_transitions
                             if in_device_transitions > 0 else 0)
    in_device_drift_rate = (in_device_admissible_drift / in_device_transitions
                            if in_device_transitions > 0 else 0)

    table = Table(title="Transition Breakdown")
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Fraction", justify="right")
    table.add_row("In-device (both on)", str(in_device_transitions),
                  f"{in_device_transitions / total_transitions:.1%}" if total_transitions > 0 else "—")
    table.add_row("In→Out (codebook)", str(off_device_in_out),
                  f"{off_device_in_out / total_transitions:.1%}" if total_transitions > 0 else "—")
    table.add_row("Out→In (recovery)", str(off_device_out_in),
                  f"{off_device_out_in / total_transitions:.1%}" if total_transitions > 0 else "—")
    table.add_row("Out→Out (worst)", str(off_device_out_out),
                  f"{off_device_out_out / total_transitions:.1%}" if total_transitions > 0 else "—")
    table.add_row("Total", str(total_transitions), "100%", style="bold")
    console.print(table)

    console.print(f"\n  In-device strict admissibility: {in_device_strict_rate:.1%}")
    console.print(f"  In-device drift admissibility: {in_device_drift_rate:.1%}")

    # F3.2: Codebook transition handling
    console.print("\n[bold]F3.2: Codebook Transition Handling[/bold]")
    console.print(f"  In→Out suffix recovered: {suffix_recovered}")
    console.print(f"  In→Out suffix admissible: {suffix_admissible}")

    # F3.3: Consolidated rate
    console.print("\n[bold]F3.3: Consolidated Admissibility[/bold]")

    # Consolidated = in-device admissible + suffix admissible out of total
    consolidated_admissible = in_device_admissible_drift + suffix_admissible
    consolidated_rate = (consolidated_admissible / total_transitions
                         if total_transitions > 0 else 0)

    console.print(f"  Consolidated admissible: {consolidated_admissible} / {total_transitions}")
    console.print(f"  Consolidated rate: {consolidated_rate:.1%}")
    console.print("  Monolithic baseline: 64.94%")
    console.print(f"  Delta: {(consolidated_rate - 0.6494) * 100:+.2f}pp")

    gate_pass = consolidated_rate >= 0.60
    if gate_pass:
        console.print("  [green]Gate PASS: ≥60%[/green]")
    else:
        console.print("  [red]Gate FAIL: <60%[/red]")

    return {
        "transition_breakdown": {
            "in_device": in_device_transitions,
            "in_to_out": off_device_in_out,
            "out_to_in": off_device_out_in,
            "out_to_out": off_device_out_out,
            "total": total_transitions,
        },
        "in_device_admissibility": {
            "strict": round(in_device_strict_rate, 4),
            "drift": round(in_device_drift_rate, 4),
        },
        "suffix_recovery": {
            "recovered": suffix_recovered,
            "admissible": suffix_admissible,
        },
        "consolidated": {
            "admissible": consolidated_admissible,
            "total": total_transitions,
            "rate": round(consolidated_rate, 4),
            "vs_monolithic": round((consolidated_rate - 0.6494) * 100, 2),
            "gate_pass": gate_pass,
        },
    }


# ── Main ──────────────────────────────────────────────────────────────

# Module-level references for sprint_f2's consultation rate calculation
lines_global = []
lattice_map_global = {}


def main():
    global lines_global, lattice_map_global

    console.rule("[bold magenta]Sprints F1-F3: Subset Device Architecture")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)

    # Load suffix map
    suffix_map = {}
    if SUFFIX_MAP_PATH.exists():
        with open(SUFFIX_MAP_PATH) as f:
            sm_data = json.load(f)
        suffix_map = sm_data.get("results", sm_data)
        if isinstance(suffix_map, dict) and "suffix_window_map" in suffix_map:
            suffix_map = suffix_map["suffix_window_map"]
        # Ensure values are ints
        suffix_map = {k: int(v) for k, v in suffix_map.items()}

    lines_global = lines
    lattice_map_global = lattice_map

    console.print(f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows")
    console.print(f"  Corpus: {len(lines)} lines")
    console.print(f"  Suffix map: {len(suffix_map)} entries")

    # Build frequency-sorted vocab
    all_tokens = [t for line in lines for t in line if t in lattice_map]
    freq = Counter(all_tokens)
    vocab_by_freq = [word for word, _ in freq.most_common()]

    # Word → window mapping
    word_to_window = {}
    for w in range(NUM_WINDOWS):
        for word in window_contents.get(w, []):
            word_to_window[word] = w

    # F1: Coverage analysis
    f1_results = sprint_f1(lines, lattice_map, window_contents)

    # F2: Device dimensioning
    f2_results = sprint_f2(
        vocab_by_freq, freq, word_to_window, window_contents,
        f1_results["transition_coverage_curve"], suffix_map,
    )

    # F3: Admissibility under subset
    f3_results = sprint_f3(
        lines, lattice_map, window_contents, corrections,
        vocab_by_freq, f2_results["target_subset_size"], suffix_map,
    )

    # Assemble results
    results = {
        "f1_coverage_analysis": f1_results,
        "f2_device_dimensioning": f2_results,
        "f3_subset_admissibility": f3_results,
        "overall_plausibility": f2_results["plausibility"],
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Final summary
    console.rule("[bold magenta]Summary")
    table = Table(title="Subset Device Architecture Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Subset size for 90% transitions",
                  str(f2_results["target_subset_size"]))
    table.add_row("Subset volvelle diameter",
                  f"{f2_results['volvelle']['diameter_mm']:.0f} mm")
    table.add_row("vs Alberti", f"{f2_results['volvelle']['vs_alberti']:.2f}×")
    table.add_row("vs Apian", f"{f2_results['volvelle']['vs_apian']:.2f}×")
    table.add_row("Codebook entries", str(f2_results["codebook"]["entries"]))
    table.add_row("Consultation rate",
                  f"{f2_results['codebook']['consultation_rate']:.1%}")
    table.add_row("Words between lookups",
                  f"{f2_results['codebook']['words_between_lookups']:.1f}")
    table.add_row("In-device admissibility",
                  f"{f3_results['in_device_admissibility']['drift']:.1%}")
    table.add_row("Consolidated admissibility",
                  f"{f3_results['consolidated']['rate']:.1%}")
    table.add_row("Plausibility", f2_results["plausibility"])
    console.print(table)


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17i_subset_device"}):
        main()
