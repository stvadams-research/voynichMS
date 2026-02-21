#!/usr/bin/env python3
"""Phase 14J Sprint 1: Second-Order Transition Analysis.

Phase 14I showed that first-order per-window mode offset correction adds
+16.17pp cross-validated admissibility with 50 parameters.  This is
P(offset | prev_window).

This script investigates second-order conditioning:
  P(offset | prev_window, curr_window)

There are 50×50 = 2,500 possible (prev_window, curr_window) pairs.
The question: does conditioning on the pair capture more info gain than
prev_window alone, and is the data sufficient to estimate pair-level
corrections reliably?

Analysis:
  1. Sparsity analysis of observed window pairs
  2. Second-order conditional entropy H(offset | prev_win, curr_win)
  3. Info gain decomposition: first-order vs second-order
  4. Per-pair mode offsets and divergence from first-order
  5. Theoretical ceilings at multiple min_obs thresholds
  6. Comparison table: unconditional vs first-order vs second-order
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

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/second_order_transitions.json"
)
console = Console()

NUM_WINDOWS = 50


# ── Helpers ──────────────────────────────────────────────────────────────

def entropy(counts):
    """Shannon entropy of a count distribution in bits."""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def signed_circular_offset(a, b, n=NUM_WINDOWS):
    """Signed circular distance from window a to window b, wrapped to [-n/2, +n/2]."""
    raw = (b - a) % n
    if raw > n // 2:
        raw -= n
    return raw


def load_palette(path):
    """Load lattice_map and window_contents from a palette JSON."""
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
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


def load_lines_with_metadata(store):
    """Load canonical ZL lines with folio metadata."""
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
                }
            )

        return lines
    finally:
        session.close()


# ── Analysis Functions ───────────────────────────────────────────────────

def build_trigram_records(lines, lattice_map):
    """Build per-trigram records for consecutive token triples.

    Each record contains (prev_window, curr_window, next_window) and the
    signed offset from curr_window to next_window.  We need triples so
    we can condition the offset on both prev_window and curr_window.
    """
    records = []
    for line_info in lines:
        tokens = line_info["tokens"]
        section = line_info["section"]
        for i in range(2, len(tokens)):
            prev_word = tokens[i - 2]
            curr_word = tokens[i - 1]
            next_word = tokens[i]
            if (prev_word not in lattice_map
                    or curr_word not in lattice_map
                    or next_word not in lattice_map):
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            next_win = lattice_map[next_word]
            offset = signed_circular_offset(curr_win, next_win)
            records.append({
                "prev_word": prev_word,
                "curr_word": curr_word,
                "next_word": next_word,
                "prev_window": prev_win,
                "curr_window": curr_win,
                "next_window": next_win,
                "signed_offset": offset,
                "distance": abs(offset),
                "admissible": abs(offset) <= 1,
                "section": section,
            })
    return records


def sparsity_analysis(records):
    """Analyze sparsity of (prev_window, curr_window) pairs."""
    pair_counts = defaultdict(int)
    for r in records:
        pair_counts[(r["prev_window"], r["curr_window"])] += 1

    total_possible = NUM_WINDOWS * NUM_WINDOWS
    observed = len(pair_counts)
    counts_list = list(pair_counts.values())

    thresholds = [1, 3, 5, 10, 20, 50]
    coverage = {}
    for thresh in thresholds:
        pairs_above = sum(1 for c in counts_list if c >= thresh)
        obs_above = sum(c for c in counts_list if c >= thresh)
        coverage[thresh] = {
            "pairs": pairs_above,
            "pairs_frac": round(pairs_above / total_possible, 4),
            "observations": obs_above,
            "obs_frac": round(obs_above / len(records), 4) if records else 0,
        }

    return {
        "total_possible_pairs": total_possible,
        "observed_pairs": observed,
        "observed_frac": round(observed / total_possible, 4),
        "total_transitions": len(records),
        "mean_obs_per_pair": round(np.mean(counts_list), 2) if counts_list else 0,
        "median_obs_per_pair": round(float(np.median(counts_list)), 1) if counts_list else 0,
        "max_obs": max(counts_list) if counts_list else 0,
        "min_obs": min(counts_list) if counts_list else 0,
        "coverage_by_threshold": coverage,
    }


def second_order_info_gain(records):
    """Compute info gain decomposition: unconditioned vs first-order vs second-order.

    We measure the offset from curr_window to next_window and condition on:
      Level 0: H(offset) — unconditional
      Level 1: H(offset | curr_window) — first-order (what Phase 14I uses)
      Level 1b: H(offset | prev_window) — first-order on predecessor
      Level 2: H(offset | prev_window, curr_window) — second-order
    """
    offsets = [r["signed_offset"] for r in records]
    h_uncond = entropy(list(Counter(offsets).values()))
    total = len(records)

    # Level 1: H(offset | curr_window)
    curr_groups = defaultdict(list)
    for r in records:
        curr_groups[r["curr_window"]].append(r["signed_offset"])
    h_given_curr = sum(
        (len(offs) / total) * entropy(list(Counter(offs).values()))
        for offs in curr_groups.values()
    )

    # Level 1b: H(offset | prev_window)
    prev_groups = defaultdict(list)
    for r in records:
        prev_groups[r["prev_window"]].append(r["signed_offset"])
    h_given_prev = sum(
        (len(offs) / total) * entropy(list(Counter(offs).values()))
        for offs in prev_groups.values()
    )

    # Level 2: H(offset | prev_window, curr_window)
    pair_groups = defaultdict(list)
    for r in records:
        pair_groups[(r["prev_window"], r["curr_window"])].append(r["signed_offset"])
    h_given_pair = sum(
        (len(offs) / total) * entropy(list(Counter(offs).values()))
        for offs in pair_groups.values()
    )

    # Also compute H(offset | curr_word) for comparison with word-level
    word_groups = defaultdict(list)
    for r in records:
        word_groups[r["curr_word"]].append(r["signed_offset"])
    h_given_word = sum(
        (len(offs) / total) * entropy(list(Counter(offs).values()))
        for offs in word_groups.values()
    )

    return {
        "total_transitions": total,
        "h_offset_unconditional": round(h_uncond, 4),
        "h_offset_given_curr_window": round(h_given_curr, 4),
        "h_offset_given_prev_window": round(h_given_prev, 4),
        "h_offset_given_pair": round(h_given_pair, 4),
        "h_offset_given_curr_word": round(h_given_word, 4),
        "ig_curr_window": round(h_uncond - h_given_curr, 4),
        "ig_prev_window": round(h_uncond - h_given_prev, 4),
        "ig_pair": round(h_uncond - h_given_pair, 4),
        "ig_curr_word": round(h_uncond - h_given_word, 4),
        "ig_pair_beyond_curr_window": round(h_given_curr - h_given_pair, 4),
        "ig_pair_beyond_prev_window": round(h_given_prev - h_given_pair, 4),
        "num_curr_windows": len(curr_groups),
        "num_prev_windows": len(prev_groups),
        "num_pairs": len(pair_groups),
        "num_curr_words": len(word_groups),
    }


def pair_mode_analysis(records, first_order_corrections):
    """Compute per-pair mode offsets and compare to first-order predictions.

    first_order_corrections: dict mapping curr_window → mode_offset
    (from Phase 14I, this is per-prev_window; here we use per-curr_window
    since that's what the offset is relative to).
    """
    pair_groups = defaultdict(list)
    for r in records:
        pair_groups[(r["prev_window"], r["curr_window"])].append(r["signed_offset"])

    # Learn first-order mode from curr_window (for comparison)
    curr_groups = defaultdict(list)
    for r in records:
        curr_groups[r["curr_window"]].append(r["signed_offset"])
    first_order_modes = {}
    for win, offs in curr_groups.items():
        first_order_modes[win] = Counter(offs).most_common(1)[0][0]

    pair_modes = {}
    divergent_count = 0
    total_analyzed = 0
    divergence_magnitudes = []

    for (pw, cw), offsets in pair_groups.items():
        if len(offsets) < 5:
            continue
        total_analyzed += 1
        mode = Counter(offsets).most_common(1)[0][0]
        first_order_mode = first_order_modes.get(cw, 0)
        diverges = mode != first_order_mode

        pair_modes[(pw, cw)] = {
            "count": len(offsets),
            "mode_offset": mode,
            "first_order_mode": first_order_mode,
            "diverges": diverges,
            "entropy": round(entropy(list(Counter(offsets).values())), 4),
        }

        if diverges:
            divergent_count += 1
            divergence_magnitudes.append(abs(mode - first_order_mode))

    return {
        "total_pairs_analyzed": total_analyzed,
        "divergent_pairs": divergent_count,
        "divergent_frac": round(divergent_count / total_analyzed, 4) if total_analyzed else 0,
        "mean_divergence_magnitude": round(np.mean(divergence_magnitudes), 2) if divergence_magnitudes else 0,
        "median_divergence_magnitude": round(float(np.median(divergence_magnitudes)), 1) if divergence_magnitudes else 0,
        "top_divergent": sorted(
            [
                {
                    "pair": f"{pw},{cw}",
                    "count": v["count"],
                    "pair_mode": v["mode_offset"],
                    "first_order_mode": v["first_order_mode"],
                    "delta": v["mode_offset"] - v["first_order_mode"],
                }
                for (pw, cw), v in pair_modes.items() if v["diverges"]
            ],
            key=lambda x: x["count"],
            reverse=True,
        )[:30],
    }


def theoretical_ceilings(records):
    """Compute admissibility ceilings for multiple model configurations.

    Models:
      0. Baseline: no correction (|offset| ≤ 1)
      1. First-order curr_window: mode(offset | curr_window)
      2. First-order prev_window: mode(offset | prev_window)  [Phase 14I style]
      3. Second-order pair: mode(offset | prev_window, curr_window)
         with fallback to first-order at multiple min_obs thresholds
    """
    total = len(records)
    baseline_adm = sum(1 for r in records if r["admissible"])

    # First-order: curr_window
    curr_groups = defaultdict(list)
    for r in records:
        curr_groups[r["curr_window"]].append(r["signed_offset"])
    curr_modes = {w: Counter(offs).most_common(1)[0][0] for w, offs in curr_groups.items()}

    first_curr_adm = 0
    for r in records:
        correction = curr_modes.get(r["curr_window"], 0)
        corrected = r["signed_offset"] - correction
        if corrected > NUM_WINDOWS // 2:
            corrected -= NUM_WINDOWS
        elif corrected < -NUM_WINDOWS // 2:
            corrected += NUM_WINDOWS
        if abs(corrected) <= 1:
            first_curr_adm += 1

    # First-order: prev_window (Phase 14I style)
    prev_groups = defaultdict(list)
    for r in records:
        prev_groups[r["prev_window"]].append(r["signed_offset"])
    prev_modes = {w: Counter(offs).most_common(1)[0][0] for w, offs in prev_groups.items()}

    first_prev_adm = 0
    for r in records:
        correction = prev_modes.get(r["prev_window"], 0)
        corrected = r["signed_offset"] - correction
        if corrected > NUM_WINDOWS // 2:
            corrected -= NUM_WINDOWS
        elif corrected < -NUM_WINDOWS // 2:
            corrected += NUM_WINDOWS
        if abs(corrected) <= 1:
            first_prev_adm += 1

    # Second-order: pair with fallback
    pair_groups = defaultdict(list)
    for r in records:
        pair_groups[(r["prev_window"], r["curr_window"])].append(r["signed_offset"])

    min_obs_values = [3, 5, 10, 20, 50]
    second_order_results = {}

    for min_obs in min_obs_values:
        pair_modes = {}
        for (pw, cw), offs in pair_groups.items():
            if len(offs) >= min_obs:
                pair_modes[(pw, cw)] = Counter(offs).most_common(1)[0][0]

        adm = 0
        pair_used = 0
        fallback_used = 0
        for r in records:
            pair_key = (r["prev_window"], r["curr_window"])
            if pair_key in pair_modes:
                correction = pair_modes[pair_key]
                pair_used += 1
            else:
                # Fallback to first-order curr_window
                correction = curr_modes.get(r["curr_window"], 0)
                fallback_used += 1

            corrected = r["signed_offset"] - correction
            if corrected > NUM_WINDOWS // 2:
                corrected -= NUM_WINDOWS
            elif corrected < -NUM_WINDOWS // 2:
                corrected += NUM_WINDOWS
            if abs(corrected) <= 1:
                adm += 1

        second_order_results[min_obs] = {
            "admissible": adm,
            "rate": round(adm / total, 4) if total else 0,
            "delta_pp": round((adm - baseline_adm) / total * 100, 2) if total else 0,
            "improvement_over_first_order_pp": round(
                (adm - first_curr_adm) / total * 100, 2
            ) if total else 0,
            "num_pair_corrections": len(pair_modes),
            "pair_used": pair_used,
            "fallback_used": fallback_used,
            "fallback_rate": round(fallback_used / total, 4) if total else 0,
        }

    return {
        "total_transitions": total,
        "baseline": {
            "admissible": baseline_adm,
            "rate": round(baseline_adm / total, 4) if total else 0,
        },
        "first_order_curr_window": {
            "admissible": first_curr_adm,
            "rate": round(first_curr_adm / total, 4) if total else 0,
            "delta_pp": round((first_curr_adm - baseline_adm) / total * 100, 2) if total else 0,
            "parameters": len(curr_modes),
        },
        "first_order_prev_window": {
            "admissible": first_prev_adm,
            "rate": round(first_prev_adm / total, 4) if total else 0,
            "delta_pp": round((first_prev_adm - baseline_adm) / total * 100, 2) if total else 0,
            "parameters": len(prev_modes),
        },
        "second_order_by_min_obs": second_order_results,
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14J Sprint 1: Second-Order Transition Analysis[/bold magenta]")

    # 1. Load data
    console.print("Loading palette...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    console.print(f"  Palette: {len(lattice_map)} words, {len(window_contents)} windows")

    console.print("Loading corpus...")
    store = MetadataStore(DB_PATH)
    lines = load_lines_with_metadata(store)
    total_tokens = sum(len(l["tokens"]) for l in lines)
    console.print(f"  Corpus: {len(lines)} lines, {total_tokens} tokens")

    # 2. Build trigram records (need triples for second-order)
    console.print("\n[bold]Building trigram transition records...[/bold]")
    records = build_trigram_records(lines, lattice_map)
    console.print(f"  {len(records)} consecutive-triple transitions")

    # 3. Sparsity analysis
    console.print("\n[bold]Sparsity analysis of (prev_window, curr_window) pairs...[/bold]")
    sparsity = sparsity_analysis(records)
    console.print(f"  Possible pairs: {sparsity['total_possible_pairs']}")
    console.print(f"  Observed pairs: {sparsity['observed_pairs']} ({sparsity['observed_frac']*100:.1f}%)")
    console.print(f"  Mean obs/pair:  {sparsity['mean_obs_per_pair']}")
    console.print(f"  Median obs/pair: {sparsity['median_obs_per_pair']}")

    cov_table = Table(title="Coverage by Minimum Observations")
    cov_table.add_column("min_obs", justify="right")
    cov_table.add_column("Pairs", justify="right")
    cov_table.add_column("% of 2500", justify="right")
    cov_table.add_column("Observations", justify="right")
    cov_table.add_column("% Coverage", justify="right")
    for thresh, cov in sparsity["coverage_by_threshold"].items():
        cov_table.add_row(
            str(thresh),
            str(cov["pairs"]),
            f"{cov['pairs_frac']*100:.1f}%",
            str(cov["observations"]),
            f"{cov['obs_frac']*100:.1f}%",
        )
    console.print(cov_table)

    # 4. Info gain decomposition
    console.print("\n[bold]Info gain decomposition (key analysis)...[/bold]")
    ig = second_order_info_gain(records)

    ig_table = Table(title="Offset Entropy Decomposition")
    ig_table.add_column("Conditioning", style="cyan")
    ig_table.add_column("H(offset)", justify="right")
    ig_table.add_column("Info Gain", justify="right")
    ig_table.add_column("Params", justify="right")
    ig_table.add_row(
        "None (unconditional)",
        f"{ig['h_offset_unconditional']:.4f}",
        "—",
        "0",
    )
    ig_table.add_row(
        "curr_window",
        f"{ig['h_offset_given_curr_window']:.4f}",
        f"{ig['ig_curr_window']:.4f}",
        str(ig["num_curr_windows"]),
    )
    ig_table.add_row(
        "prev_window",
        f"{ig['h_offset_given_prev_window']:.4f}",
        f"{ig['ig_prev_window']:.4f}",
        str(ig["num_prev_windows"]),
    )
    ig_table.add_row(
        "[bold](prev_win, curr_win)[/bold]",
        f"[bold]{ig['h_offset_given_pair']:.4f}[/bold]",
        f"[bold]{ig['ig_pair']:.4f}[/bold]",
        str(ig["num_pairs"]),
    )
    ig_table.add_row(
        "curr_word (all)",
        f"{ig['h_offset_given_curr_word']:.4f}",
        f"{ig['ig_curr_word']:.4f}",
        str(ig["num_curr_words"]),
    )
    ig_table.add_row(
        "[bold]Pair beyond curr_window[/bold]",
        "—",
        f"[bold]{ig['ig_pair_beyond_curr_window']:.4f}[/bold]",
        "—",
    )
    ig_table.add_row(
        "[bold]Pair beyond prev_window[/bold]",
        "—",
        f"[bold]{ig['ig_pair_beyond_prev_window']:.4f}[/bold]",
        "—",
    )
    console.print(ig_table)

    # 5. Pair mode divergence from first-order
    console.print("\n[bold]Pair mode divergence from first-order...[/bold]")
    pair_analysis = pair_mode_analysis(records, {})
    console.print(f"  Pairs analyzed (≥5 obs): {pair_analysis['total_pairs_analyzed']}")
    console.print(f"  Divergent from first-order: {pair_analysis['divergent_pairs']} "
                  f"({pair_analysis['divergent_frac']*100:.1f}%)")
    console.print(f"  Mean divergence magnitude: {pair_analysis['mean_divergence_magnitude']}")

    if pair_analysis["top_divergent"]:
        div_table = Table(title="Top Divergent Pairs (by count)")
        div_table.add_column("(prev, curr)", style="cyan")
        div_table.add_column("Count", justify="right")
        div_table.add_column("Pair Mode", justify="right")
        div_table.add_column("1st-Order Mode", justify="right")
        div_table.add_column("Delta", justify="right")
        for d in pair_analysis["top_divergent"][:15]:
            div_table.add_row(
                d["pair"],
                str(d["count"]),
                str(d["pair_mode"]),
                str(d["first_order_mode"]),
                str(d["delta"]),
            )
        console.print(div_table)

    # 6. Theoretical ceilings
    console.print("\n[bold]Theoretical admissibility ceilings...[/bold]")
    ceilings = theoretical_ceilings(records)

    ceil_table = Table(title="Admissibility Ceilings")
    ceil_table.add_column("Model", style="cyan")
    ceil_table.add_column("Admissible", justify="right")
    ceil_table.add_column("Rate", justify="right")
    ceil_table.add_column("Delta (pp)", justify="right")
    ceil_table.add_column("Params", justify="right")
    ceil_table.add_column("Fallback %", justify="right")

    bl = ceilings["baseline"]
    ceil_table.add_row(
        "Baseline (no correction)",
        str(bl["admissible"]),
        f"{bl['rate']*100:.2f}%",
        "—", "0", "—",
    )

    fo_curr = ceilings["first_order_curr_window"]
    ceil_table.add_row(
        "1st-order (curr_window)",
        str(fo_curr["admissible"]),
        f"{fo_curr['rate']*100:.2f}%",
        f"+{fo_curr['delta_pp']:.2f}",
        str(fo_curr["parameters"]),
        "0%",
    )

    fo_prev = ceilings["first_order_prev_window"]
    ceil_table.add_row(
        "1st-order (prev_window)",
        str(fo_prev["admissible"]),
        f"{fo_prev['rate']*100:.2f}%",
        f"+{fo_prev['delta_pp']:.2f}",
        str(fo_prev["parameters"]),
        "0%",
    )

    for min_obs, so in sorted(ceilings["second_order_by_min_obs"].items()):
        ceil_table.add_row(
            f"2nd-order (min_obs={min_obs})",
            str(so["admissible"]),
            f"{so['rate']*100:.2f}%",
            f"+{so['delta_pp']:.2f}",
            str(so["num_pair_corrections"]),
            f"{so['fallback_rate']*100:.1f}%",
        )

    console.print(ceil_table)

    # 7. Gate decision: is second-order worth cross-validating?
    best_first_order = max(fo_curr["rate"], fo_prev["rate"])
    best_second_order_rate = max(
        so["rate"] for so in ceilings["second_order_by_min_obs"].values()
    )
    ceiling_improvement_pp = (best_second_order_rate - best_first_order) * 100

    console.print("\n[bold yellow]Gate Decision:[/bold yellow]")
    console.print(f"  Best first-order ceiling:  {best_first_order*100:.2f}%")
    console.print(f"  Best second-order ceiling:  {best_second_order_rate*100:.2f}%")
    console.print(f"  Ceiling improvement: {ceiling_improvement_pp:+.2f}pp")

    if ceiling_improvement_pp >= 2.0:
        console.print("  [green]→ PASS: Second-order improves ceiling by ≥2pp. Proceed to Sprint 2.[/green]")
        gate_pass = True
    else:
        console.print("  [red]→ FAIL: Second-order improves ceiling by <2pp. Sprint 2 may not be warranted.[/red]")
        gate_pass = False

    # 8. Save results
    results = {
        "sparsity": sparsity,
        "info_gain": ig,
        "pair_mode_divergence": {
            "total_pairs_analyzed": pair_analysis["total_pairs_analyzed"],
            "divergent_pairs": pair_analysis["divergent_pairs"],
            "divergent_frac": pair_analysis["divergent_frac"],
            "mean_divergence_magnitude": pair_analysis["mean_divergence_magnitude"],
            "top_divergent": pair_analysis["top_divergent"],
        },
        "ceilings": ceilings,
        "gate_decision": {
            "best_first_order_rate": round(best_first_order, 4),
            "best_second_order_rate": round(best_second_order_rate, 4),
            "ceiling_improvement_pp": round(ceiling_improvement_pp, 2),
            "gate_pass": gate_pass,
            "threshold_pp": 2.0,
        },
    }

    with active_run(config={"seed": 42, "command": "run_14za_second_order_transitions"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")

    # 9. Key interpretation
    console.print("\n[bold yellow]Key Findings:[/bold yellow]")
    console.print(f"  H(offset) unconditional:         {ig['h_offset_unconditional']:.4f} bits")
    console.print(f"  H(offset | curr_window):         {ig['h_offset_given_curr_window']:.4f} bits  "
                  f"(IG = {ig['ig_curr_window']:.4f})")
    console.print(f"  H(offset | prev_win, curr_win):  {ig['h_offset_given_pair']:.4f} bits  "
                  f"(IG = {ig['ig_pair']:.4f})")
    console.print(f"  Pair beyond curr_window:         {ig['ig_pair_beyond_curr_window']:.4f} bits")
    console.print(f"  Divergent pairs: {pair_analysis['divergent_pairs']}/{pair_analysis['total_pairs_analyzed']} "
                  f"({pair_analysis['divergent_frac']*100:.1f}%)")


if __name__ == "__main__":
    main()
