#!/usr/bin/env python3
"""Phase 14I Sprint 1: Bigram Transition Profiling.

Profiles the transition patterns at both window-level and word-level
granularity.  The current lattice is memoryless: word(n) → window(n+1).
Phase 14H showed 1.31 bits of information gain from prev_word on failure
distance, suggesting a richer transition model could improve admissibility.

This script:
  1. Builds a full transition record for ~34K consecutive token pairs
  2. Constructs the 50×50 window transition matrix P(next_win | curr_win)
  3. Compares H(offset), H(offset | prev_window), H(offset | prev_word)
  4. Profiles per-prev_word and per-prev_window offset distributions
  5. Computes theoretical admissibility ceilings under mode correction
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

from phase1_foundation.core.data_loading import (  # noqa: E402
    load_canonical_lines,
    sanitize_token,
)
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
    project_root / "results/data/phase14_machine/bigram_transitions.json"
)
console = Console()

NUM_WINDOWS = 50
MIN_OBS = 5  # Minimum observations for offset profiles


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


def circular_distance(a, b, n=NUM_WINDOWS):
    """Unsigned circular distance between two window indices."""
    d = abs(a - b) % n
    return min(d, n - d)


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

def build_transition_records(lines, lattice_map):
    """Build per-transition records for all consecutive token pairs."""
    records = []
    for line_info in lines:
        tokens = line_info["tokens"]
        section = line_info["section"]
        for i in range(1, len(tokens)):
            prev_word = tokens[i - 1]
            curr_word = tokens[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            offset = signed_circular_offset(prev_win, curr_win)
            dist = abs(offset)
            records.append({
                "prev_word": prev_word,
                "curr_word": curr_word,
                "prev_window": prev_win,
                "curr_window": curr_win,
                "signed_offset": offset,
                "distance": dist,
                "admissible": dist <= 1,
                "section": section,
            })
    return records


def build_transition_matrix(records):
    """Build 50×50 window transition matrix and compute stats."""
    matrix = np.zeros((NUM_WINDOWS, NUM_WINDOWS), dtype=int)
    for r in records:
        matrix[r["prev_window"], r["curr_window"]] += 1

    # Row-normalize for probabilities
    row_sums = matrix.sum(axis=1, keepdims=True)
    prob_matrix = np.where(row_sums > 0, matrix / row_sums, 0)

    # Per-row entropy
    row_entropies = []
    for i in range(NUM_WINDOWS):
        row_counts = [matrix[i, j] for j in range(NUM_WINDOWS) if matrix[i, j] > 0]
        row_entropies.append(entropy(row_counts))

    # Weighted average conditional entropy
    total = matrix.sum()
    h_next_given_curr = sum(
        (matrix[i].sum() / total) * row_entropies[i]
        for i in range(NUM_WINDOWS)
        if matrix[i].sum() > 0
    )

    return {
        "matrix": matrix.tolist(),
        "h_next_window_unconditional": entropy(matrix.sum(axis=0).tolist()),
        "h_next_window_given_current": h_next_given_curr,
        "info_gain_window_level": entropy(matrix.sum(axis=0).tolist()) - h_next_given_curr,
        "per_row_entropy": row_entropies,
    }


def compute_offset_info_gains(records):
    """Compare H(offset), H(offset | prev_window), H(offset | prev_word).

    This is the key analysis: does the 1.31 bits of info gain come from
    window identity or word identity?
    """
    offsets = [r["signed_offset"] for r in records]
    h_uncond = entropy(list(Counter(offsets).values()))

    # H(offset | prev_window)
    win_groups = defaultdict(list)
    for r in records:
        win_groups[r["prev_window"]].append(r["signed_offset"])

    total = len(records)
    h_given_window = 0.0
    for win, off_list in win_groups.items():
        p_win = len(off_list) / total
        h_given_window += p_win * entropy(list(Counter(off_list).values()))

    # H(offset | prev_word) — filtered to ≥ MIN_OBS
    word_groups = defaultdict(list)
    for r in records:
        word_groups[r["prev_word"]].append(r["signed_offset"])

    eligible_total = sum(len(v) for v in word_groups.values() if len(v) >= MIN_OBS)
    h_given_word = 0.0
    eligible_words = 0
    if eligible_total > 0:
        for pw, off_list in word_groups.items():
            if len(off_list) >= MIN_OBS:
                eligible_words += 1
                p_pw = len(off_list) / eligible_total
                h_given_word += p_pw * entropy(list(Counter(off_list).values()))

    # H(offset | prev_word) — all words, no filter
    h_given_word_all = 0.0
    for pw, off_list in word_groups.items():
        p_pw = len(off_list) / total
        h_given_word_all += p_pw * entropy(list(Counter(off_list).values()))

    return {
        "h_offset_unconditional": round(h_uncond, 4),
        "h_offset_given_prev_window": round(h_given_window, 4),
        "h_offset_given_prev_word_filtered": round(h_given_word, 4),
        "h_offset_given_prev_word_all": round(h_given_word_all, 4),
        "ig_window_level": round(h_uncond - h_given_window, 4),
        "ig_word_level_filtered": round(h_uncond - h_given_word, 4),
        "ig_word_level_all": round(h_uncond - h_given_word_all, 4),
        "ig_word_beyond_window": round(h_given_window - h_given_word_all, 4),
        "eligible_prev_words": eligible_words,
        "eligible_observations": eligible_total,
        "total_transitions": len(records),
        "unique_prev_words": len(word_groups),
    }


def profile_prev_word_offsets(records):
    """Per-prev_word offset profiles: mode, entropy, observation count."""
    word_groups = defaultdict(list)
    for r in records:
        word_groups[r["prev_word"]].append(r["signed_offset"])

    profiles = {}
    for pw, offsets in word_groups.items():
        if len(offsets) < MIN_OBS:
            continue
        counts = Counter(offsets)
        mode_offset = counts.most_common(1)[0][0]
        h = entropy(list(counts.values()))
        adm_count = sum(1 for o in offsets if abs(o) <= 1)
        profiles[pw] = {
            "count": len(offsets),
            "mode_offset": mode_offset,
            "entropy": round(h, 4),
            "admissible_rate": round(adm_count / len(offsets), 4),
            "offset_distribution": dict(counts.most_common(10)),
        }

    # Summary statistics
    mode_zero = sum(1 for p in profiles.values() if p["mode_offset"] == 0)
    mode_nonzero = sum(1 for p in profiles.values() if p["mode_offset"] != 0)

    return {
        "num_profiled": len(profiles),
        "mode_zero_count": mode_zero,
        "mode_nonzero_count": mode_nonzero,
        "mean_entropy": round(np.mean([p["entropy"] for p in profiles.values()]), 4) if profiles else 0,
        "mean_admissible_rate": round(np.mean([p["admissible_rate"] for p in profiles.values()]), 4) if profiles else 0,
        "top_nonzero_mode": sorted(
            [(pw, p) for pw, p in profiles.items() if p["mode_offset"] != 0],
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:20],
    }


def profile_prev_window_offsets(records):
    """Per-prev_window offset profiles."""
    win_groups = defaultdict(list)
    for r in records:
        win_groups[r["prev_window"]].append(r["signed_offset"])

    profiles = {}
    for win, offsets in win_groups.items():
        counts = Counter(offsets)
        mode_offset = counts.most_common(1)[0][0]
        h = entropy(list(counts.values()))
        adm_count = sum(1 for o in offsets if abs(o) <= 1)
        profiles[win] = {
            "count": len(offsets),
            "mode_offset": mode_offset,
            "entropy": round(h, 4),
            "admissible_rate": round(adm_count / len(offsets), 4),
        }

    mode_zero = sum(1 for p in profiles.values() if p["mode_offset"] == 0)
    mode_nonzero = sum(1 for p in profiles.values() if p["mode_offset"] != 0)

    return {
        "num_windows_profiled": len(profiles),
        "mode_zero_count": mode_zero,
        "mode_nonzero_count": mode_nonzero,
        "per_window": {str(k): v for k, v in sorted(profiles.items())},
    }


def compute_theoretical_ceilings(records):
    """Compute admissibility ceilings under per-word and per-window mode correction.

    Word-level: for each prev_word with ≥ MIN_OBS, use its mode offset as correction.
    Window-level: for each prev_window, use its mode offset as correction.
    """
    # Current baseline: admissible = distance ≤ 1
    baseline_adm = sum(1 for r in records if r["admissible"])
    total = len(records)

    # Word-level correction
    word_groups = defaultdict(list)
    for r in records:
        word_groups[r["prev_word"]].append(r["signed_offset"])

    word_mode = {}
    for pw, offsets in word_groups.items():
        if len(offsets) >= MIN_OBS:
            word_mode[pw] = Counter(offsets).most_common(1)[0][0]

    word_adm = 0
    word_fallback = 0
    for r in records:
        correction = word_mode.get(r["prev_word"], 0)
        if correction == 0:
            word_fallback += 1
        corrected_offset = r["signed_offset"] - correction
        # Wrap corrected offset
        if corrected_offset > NUM_WINDOWS // 2:
            corrected_offset -= NUM_WINDOWS
        elif corrected_offset < -NUM_WINDOWS // 2:
            corrected_offset += NUM_WINDOWS
        if abs(corrected_offset) <= 1:
            word_adm += 1

    # Window-level correction
    win_groups = defaultdict(list)
    for r in records:
        win_groups[r["prev_window"]].append(r["signed_offset"])

    win_mode = {}
    for win, offsets in win_groups.items():
        win_mode[win] = Counter(offsets).most_common(1)[0][0]

    win_adm = 0
    for r in records:
        correction = win_mode.get(r["prev_window"], 0)
        corrected_offset = r["signed_offset"] - correction
        if corrected_offset > NUM_WINDOWS // 2:
            corrected_offset -= NUM_WINDOWS
        elif corrected_offset < -NUM_WINDOWS // 2:
            corrected_offset += NUM_WINDOWS
        if abs(corrected_offset) <= 1:
            win_adm += 1

    return {
        "total_transitions": total,
        "baseline_admissible": baseline_adm,
        "baseline_rate": round(baseline_adm / total, 4) if total else 0,
        "word_level_admissible": word_adm,
        "word_level_rate": round(word_adm / total, 4) if total else 0,
        "word_level_delta_pp": round((word_adm - baseline_adm) / total * 100, 2) if total else 0,
        "word_level_fallback_count": word_fallback,
        "word_level_fallback_rate": round(word_fallback / total, 4) if total else 0,
        "window_level_admissible": win_adm,
        "window_level_rate": round(win_adm / total, 4) if total else 0,
        "window_level_delta_pp": round((win_adm - baseline_adm) / total * 100, 2) if total else 0,
        "word_mode_table_size": len(word_mode),
        "window_mode_table_size": len(win_mode),
    }


def offset_distribution_summary(records):
    """Summary of the overall offset distribution."""
    offsets = [r["signed_offset"] for r in records]
    counts = Counter(offsets)
    total = len(offsets)

    # Sort by absolute offset for display
    dist_table = []
    for off, cnt in sorted(counts.items(), key=lambda x: abs(x[0])):
        dist_table.append({
            "offset": off,
            "count": cnt,
            "rate": round(cnt / total, 4),
        })

    return {
        "total_transitions": total,
        "unique_offsets": len(counts),
        "admissible_count": sum(c for o, c in counts.items() if abs(o) <= 1),
        "admissible_rate": round(sum(c for o, c in counts.items() if abs(o) <= 1) / total, 4),
        "distribution": dist_table,
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14I Sprint 1: Bigram Transition Profiling[/bold magenta]")

    # 1. Load data
    console.print("Loading palette...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    console.print(f"  Palette: {len(lattice_map)} words, {len(window_contents)} windows")

    console.print("Loading corpus...")
    store = MetadataStore(DB_PATH)
    lines = load_lines_with_metadata(store)
    total_tokens = sum(len(l["tokens"]) for l in lines)
    console.print(f"  Corpus: {len(lines)} lines, {total_tokens} tokens")

    # 2. Build transition records
    console.print("\n[bold]Building transition records...[/bold]")
    records = build_transition_records(lines, lattice_map)
    console.print(f"  {len(records)} consecutive-pair transitions")

    # 3. Offset distribution summary
    console.print("\n[bold]Offset distribution...[/bold]")
    offset_dist = offset_distribution_summary(records)
    console.print(f"  Admissible (|offset| ≤ 1): {offset_dist['admissible_count']} ({offset_dist['admissible_rate']*100:.1f}%)")

    # 4. Window transition matrix
    console.print("\n[bold]Window transition matrix...[/bold]")
    trans_matrix = build_transition_matrix(records)
    console.print(f"  H(next_window): {trans_matrix['h_next_window_unconditional']:.3f} bits")
    console.print(f"  H(next_window | current_window): {trans_matrix['h_next_window_given_current']:.3f} bits")
    console.print(f"  Info gain (window level): {trans_matrix['info_gain_window_level']:.3f} bits")

    # 5. Three-level info gain comparison
    console.print("\n[bold]Info gain comparison (key analysis)...[/bold]")
    info_gains = compute_offset_info_gains(records)

    table = Table(title="Offset Entropy Decomposition")
    table.add_column("Conditioning", style="cyan")
    table.add_column("H(offset)", justify="right")
    table.add_column("Info Gain", justify="right")
    table.add_row("None (unconditional)", f"{info_gains['h_offset_unconditional']:.4f}", "—")
    table.add_row("prev_window (50 params)", f"{info_gains['h_offset_given_prev_window']:.4f}",
                   f"{info_gains['ig_window_level']:.4f}")
    table.add_row(f"prev_word (all {info_gains['unique_prev_words']})", f"{info_gains['h_offset_given_prev_word_all']:.4f}",
                   f"{info_gains['ig_word_level_all']:.4f}")
    table.add_row(f"prev_word (≥{MIN_OBS} obs, {info_gains['eligible_prev_words']})", f"{info_gains['h_offset_given_prev_word_filtered']:.4f}",
                   f"{info_gains['ig_word_level_filtered']:.4f}")
    table.add_row("[bold]Word beyond window[/bold]", "—",
                   f"[bold]{info_gains['ig_word_beyond_window']:.4f}[/bold]")
    console.print(table)

    # 6. Per-prev_word offset profiles
    console.print("\n[bold]Per-prev_word offset profiles...[/bold]")
    word_profiles = profile_prev_word_offsets(records)
    console.print(f"  Profiled: {word_profiles['num_profiled']} prev_words (≥{MIN_OBS} obs)")
    console.print(f"  Mode = 0: {word_profiles['mode_zero_count']}")
    console.print(f"  Mode ≠ 0: {word_profiles['mode_nonzero_count']}")
    console.print(f"  Mean offset entropy: {word_profiles['mean_entropy']:.3f} bits")

    if word_profiles["top_nonzero_mode"]:
        table2 = Table(title="Top prev_words with mode offset ≠ 0")
        table2.add_column("prev_word", style="cyan")
        table2.add_column("count", justify="right")
        table2.add_column("mode", justify="right")
        table2.add_column("H(offset)", justify="right")
        table2.add_column("adm_rate", justify="right")
        for pw, p in word_profiles["top_nonzero_mode"][:15]:
            table2.add_row(pw, str(p["count"]), str(p["mode_offset"]),
                          f"{p['entropy']:.2f}", f"{p['admissible_rate']:.2f}")
        console.print(table2)

    # 7. Per-prev_window offset profiles
    console.print("\n[bold]Per-prev_window offset profiles...[/bold]")
    win_profiles = profile_prev_window_offsets(records)
    console.print(f"  Windows with mode = 0: {win_profiles['mode_zero_count']}")
    console.print(f"  Windows with mode ≠ 0: {win_profiles['mode_nonzero_count']}")

    # 8. Theoretical ceilings
    console.print("\n[bold]Theoretical admissibility ceilings...[/bold]")
    ceilings = compute_theoretical_ceilings(records)

    table3 = Table(title="Admissibility Ceilings")
    table3.add_column("Model", style="cyan")
    table3.add_column("Admissible", justify="right")
    table3.add_column("Rate", justify="right")
    table3.add_column("Delta (pp)", justify="right")
    table3.add_column("Parameters", justify="right")
    table3.add_row("Baseline (no correction)", str(ceilings["baseline_admissible"]),
                   f"{ceilings['baseline_rate']*100:.2f}%", "—", "0")
    table3.add_row("Window-level mode", str(ceilings["window_level_admissible"]),
                   f"{ceilings['window_level_rate']*100:.2f}%",
                   f"+{ceilings['window_level_delta_pp']:.2f}",
                   str(ceilings["window_mode_table_size"]))
    table3.add_row("Word-level mode", str(ceilings["word_level_admissible"]),
                   f"{ceilings['word_level_rate']*100:.2f}%",
                   f"+{ceilings['word_level_delta_pp']:.2f}",
                   str(ceilings["word_mode_table_size"]))
    console.print(table3)

    word_fb = ceilings["word_level_fallback_rate"]
    console.print(f"  Word-level fallback rate (no correction available): {word_fb*100:.1f}%")

    # 9. Save results
    results = {
        "offset_distribution": offset_dist,
        "transition_matrix": {
            "h_next_window_unconditional": trans_matrix["h_next_window_unconditional"],
            "h_next_window_given_current": trans_matrix["h_next_window_given_current"],
            "info_gain_window_level": trans_matrix["info_gain_window_level"],
        },
        "info_gain_comparison": info_gains,
        "prev_word_profiles": {
            "num_profiled": word_profiles["num_profiled"],
            "mode_zero_count": word_profiles["mode_zero_count"],
            "mode_nonzero_count": word_profiles["mode_nonzero_count"],
            "mean_entropy": word_profiles["mean_entropy"],
            "mean_admissible_rate": word_profiles["mean_admissible_rate"],
        },
        "prev_window_profiles": {
            "num_windows_profiled": win_profiles["num_windows_profiled"],
            "mode_zero_count": win_profiles["mode_zero_count"],
            "mode_nonzero_count": win_profiles["mode_nonzero_count"],
            "per_window": win_profiles["per_window"],
        },
        "theoretical_ceilings": ceilings,
    }

    with active_run(config={"seed": 42, "command": "run_14z7_bigram_transitions"}):
        saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")

    # 10. Key interpretation
    console.print("\n[bold yellow]Key Findings:[/bold yellow]")
    ig_win = info_gains["ig_window_level"]
    ig_word = info_gains["ig_word_level_all"]
    ig_beyond = info_gains["ig_word_beyond_window"]
    console.print(f"  Info gain (window-level): {ig_win:.3f} bits")
    console.print(f"  Info gain (word-level): {ig_word:.3f} bits")
    console.print(f"  Word identity beyond window: {ig_beyond:.3f} bits")

    if ig_beyond < 0.1:
        console.print("  [green]→ Most info gain is at WINDOW level — simpler model suffices[/green]")
    else:
        console.print(f"  [yellow]→ Word identity adds {ig_beyond:.3f} bits beyond window — richer model warranted[/yellow]")

    baseline = ceilings["baseline_rate"] * 100
    win_ceil = ceilings["window_level_rate"] * 100
    word_ceil = ceilings["word_level_rate"] * 100
    console.print(f"\n  Baseline admissibility: {baseline:.2f}%")
    console.print(f"  Window-level ceiling:   {win_ceil:.2f}% (+{win_ceil - baseline:.2f}pp)")
    console.print(f"  Word-level ceiling:     {word_ceil:.2f}% (+{word_ceil - baseline:.2f}pp)")


if __name__ == "__main__":
    main()
