#!/usr/bin/env python3
"""Phase 20, Sprint 3: Window State Merging Analysis.

3.1: Define merge strategies (size-based, correction-based, usage-based)
3.2: Execute merges at target state counts [40, 35, 30, 25, 20, 15]
3.3: Re-evaluate admissibility under merged lattice + dimension devices

Tests whether reducing the number of active window states produces
a physically viable disc device while maintaining acceptable admissibility.
"""

import json
import math
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

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
OUTPUT_PATH = project_root / "results/data/phase20_state_machine/state_merging.json"

# Physical constants (same as Sprint 1)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
MARGIN_MM = 5.0

# Per-position footprint (from Sprint 1 calculation)
LABEL_WIDTH_MM = 2 * GLYPH_WIDTH_MM      # "18" = 2 chars
CORR_WIDTH_MM = 3 * GLYPH_WIDTH_MM       # "+13" = 3 chars
SEP_MM = 2.0
POSITION_WIDTH_MM = LABEL_WIDTH_MM + CORR_WIDTH_MM + SEP_MM + 2 * MARGIN_MM  # 32mm
POSITION_HEIGHT_MM = GLYPH_HEIGHT_MM + 2 * MARGIN_MM  # 15mm

TARGET_STATE_COUNTS = [40, 35, 30, 25, 20, 15]
BASELINE_ADMISSIBILITY = 0.6494
MAX_DEVICE_DIAMETER_MM = 350  # Apian range
MIN_ADMISSIBILITY = 0.55


# ── Helpers ───────────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = ("reordered_lattice_map" if "reordered_lattice_map" in results
              else "lattice_map")
    wc_key = ("reordered_window_contents" if "reordered_window_contents" in results
              else "window_contents")
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


def compute_window_usage(lines, lattice_map):
    """Count total token occurrences per window across the corpus."""
    usage = Counter()
    for line in lines:
        for tok in line:
            w = lattice_map.get(tok)
            if w is not None:
                usage[w] += 1
    return dict(usage)


def dimension_volvelle(num_states):
    """Compute volvelle diameter for a given number of angular sectors."""
    sector_angle_deg = 360.0 / num_states
    sector_angle_rad = math.radians(sector_angle_deg)
    r_min = POSITION_WIDTH_MM / sector_angle_rad
    diameter = 2 * (r_min + POSITION_HEIGHT_MM + MARGIN_MM)
    return {
        "diameter_mm": round(diameter),
        "sector_angle_deg": round(sector_angle_deg, 1),
        "fits_apian": diameter <= MAX_DEVICE_DIAMETER_MM,
    }


def dimension_tabula(num_states):
    """Compute tabula dimensions for a given number of states."""
    cols = max(1, round(math.sqrt(num_states)))
    rows = math.ceil(num_states / cols)
    width = cols * POSITION_WIDTH_MM + 2 * MARGIN_MM
    height = rows * POSITION_HEIGHT_MM + 2 * MARGIN_MM
    return {
        "grid": f"{rows}x{cols}",
        "width_mm": round(width),
        "height_mm": round(height),
    }


# ── Merge Strategies ─────────────────────────────────────────────────

def build_merge_plan_size(window_contents, target_n):
    """Merge smallest-vocabulary windows into nearest neighbor."""
    active = set(window_contents.keys())
    merge_map = {w: w for w in active}
    sizes = {w: len(words) for w, words in window_contents.items()}

    while len(active) > target_n:
        # Find smallest active window
        smallest = min(active, key=lambda w: (sizes.get(w, 0), w))
        active.discard(smallest)

        # Find nearest active neighbor by index distance
        nearest = min(active, key=lambda w: (abs(w - smallest), sizes.get(w, 0)))

        # Remap: smallest → nearest
        for w, target in merge_map.items():
            if target == smallest:
                merge_map[w] = nearest
        # Update sizes for the merged target
        sizes[nearest] = sizes.get(nearest, 0) + sizes.get(smallest, 0)

    return merge_map


def build_merge_plan_correction(corrections, window_contents, target_n):
    """Merge windows sharing the same correction value."""
    active = set(window_contents.keys())
    merge_map = {w: w for w in active}
    sizes = {w: len(words) for w, words in window_contents.items()}

    # Phase 1: Group by correction and merge within groups
    from collections import defaultdict
    corr_groups = defaultdict(list)
    for w in sorted(active):
        corr_groups[corrections.get(w, 0)].append(w)

    for _corr_val, group in sorted(corr_groups.items()):
        if len(group) <= 1:
            continue
        if len(active) <= target_n:
            break
        # Keep the largest window in the group as survivor
        survivor = max(group, key=lambda w: (sizes.get(w, 0), w))
        for w in group:
            if w != survivor and len(active) > target_n:
                active.discard(w)
                for orig, target in merge_map.items():
                    if target == w:
                        merge_map[orig] = survivor
                sizes[survivor] = sizes.get(survivor, 0) + sizes.get(w, 0)

    # Phase 2: Fall back to size-based if still above target
    while len(active) > target_n:
        smallest = min(active, key=lambda w: (sizes.get(w, 0), w))
        active.discard(smallest)
        nearest = min(active, key=lambda w: (abs(w - smallest), sizes.get(w, 0)))
        for orig, target in merge_map.items():
            if target == smallest:
                merge_map[orig] = nearest
        sizes[nearest] = sizes.get(nearest, 0) + sizes.get(smallest, 0)

    return merge_map


def build_merge_plan_usage(window_usage, window_contents, target_n):
    """Merge least-used windows into nearest more-used neighbor."""
    active = set(window_contents.keys())
    merge_map = {w: w for w in active}
    usage = dict(window_usage)

    while len(active) > target_n:
        # Find least-used active window
        least = min(active, key=lambda w: (usage.get(w, 0), w))
        active.discard(least)

        # Find nearest active neighbor
        nearest = min(active, key=lambda w: (abs(w - least), -usage.get(w, 0)))

        for orig, target in merge_map.items():
            if target == least:
                merge_map[orig] = nearest
        usage[nearest] = usage.get(nearest, 0) + usage.get(least, 0)

    return merge_map


# ── Merge Application ────────────────────────────────────────────────

def apply_merge(merge_map, lattice_map, window_contents, corrections):
    """Apply a merge plan to produce new lattice structures."""
    surviving = sorted(set(merge_map.values()))

    # Merged lattice map: token → surviving window
    merged_lm = {}
    for tok, w in lattice_map.items():
        merged_lm[tok] = merge_map.get(w, w)

    # Merged window contents: union of merged windows
    merged_wc = {s: [] for s in surviving}
    for w, words in window_contents.items():
        target = merge_map.get(w, w)
        merged_wc[target].extend(words)

    # Merged corrections: use survivor's correction
    merged_corr = {s: corrections.get(s, 0) for s in surviving}

    return merged_lm, merged_wc, merged_corr, surviving


# ── Admissibility Under Merged Lattice ───────────────────────────────

def evaluate_merged_admissibility(lines, merged_lm, merged_wc, surviving):
    """Compute drift admissibility under the merged window system.

    After merging, ±1 drift means the next/previous surviving window
    in sorted order (circular), NOT raw index ±1.
    """
    n_surv = len(surviving)
    if n_surv == 0:
        return {"strict": 0.0, "drift": 0.0, "total_transitions": 0}

    # Build lookup: surviving window → index in sorted list
    idx_of = {w: i for i, w in enumerate(surviving)}

    # Build adjacency: for each surviving window, which windows are ±1
    adjacent = {}
    for i, w in enumerate(surviving):
        prev_w = surviving[(i - 1) % n_surv]
        next_w = surviving[(i + 1) % n_surv]
        adjacent[w] = {prev_w, w, next_w}

    # Walk corpus
    total_transitions = 0
    strict_hits = 0
    drift_hits = 0
    current_window = None

    for line in lines:
        for tok in line:
            w = merged_lm.get(tok)
            if w is None:
                continue

            if current_window is None:
                current_window = w
                continue

            total_transitions += 1

            # Strict: token's window == current window
            if w == current_window:
                strict_hits += 1
                drift_hits += 1
            elif w in adjacent.get(current_window, set()):
                drift_hits += 1

            current_window = w

    if total_transitions == 0:
        return {"strict": 0.0, "drift": 0.0, "total_transitions": 0}

    return {
        "strict": round(strict_hits / total_transitions, 4),
        "drift": round(drift_hits / total_transitions, 4),
        "total_transitions": total_transitions,
    }


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_3_1(window_contents, corrections, window_usage):
    """3.1: Define merge candidates under each strategy."""
    console.rule("[bold blue]3.1: Merge Strategy Candidates")

    # Window profiles
    size_ranking = sorted(window_contents.keys(),
                          key=lambda w: len(window_contents[w]))
    usage_ranking = sorted(window_usage.keys(),
                           key=lambda w: window_usage.get(w, 0))

    # Correction groups
    from collections import defaultdict
    corr_groups = defaultdict(list)
    for w in sorted(corrections.keys()):
        corr_groups[corrections[w]].append(w)
    multi_groups = {c: ws for c, ws in corr_groups.items() if len(ws) > 1}

    # Display smallest windows
    table = Table(title="Smallest Windows (merge candidates)")
    table.add_column("Window", justify="right")
    table.add_column("Vocab", justify="right")
    table.add_column("Usage", justify="right")
    table.add_column("Correction", justify="right")

    for w in size_ranking[:15]:
        table.add_row(
            str(w),
            str(len(window_contents[w])),
            str(window_usage.get(w, 0)),
            f"{corrections.get(w, 0):+d}",
        )
    console.print(table)

    # Display correction groups with multiple members
    table2 = Table(title="Correction Groups (>1 window)")
    table2.add_column("Correction", justify="right")
    table2.add_column("Windows")
    table2.add_column("Count", justify="right")

    for c in sorted(multi_groups.keys()):
        ws = multi_groups[c]
        table2.add_row(f"{c:+d}", ", ".join(str(w) for w in ws), str(len(ws)))
    console.print(table2)

    # Count mergeable windows by strategy
    small_candidates = [w for w in size_ranking if len(window_contents[w]) < 50]
    corr_mergeable = sum(len(ws) - 1 for ws in multi_groups.values())
    low_usage = [w for w in usage_ranking[:20]]

    console.print(f"\n  Size-based candidates (<50 words): {len(small_candidates)}")
    console.print(f"  Correction-based mergeable: {corr_mergeable} windows "
                  f"across {len(multi_groups)} groups")
    console.print(f"  Usage-based bottom 20: windows {low_usage[:5]}... "
                  f"(combined {sum(window_usage.get(w, 0) for w in low_usage)} tokens)")

    return {
        "size_candidates": len(small_candidates),
        "correction_groups": {str(c): ws for c, ws in multi_groups.items()},
        "correction_mergeable": corr_mergeable,
        "usage_bottom_20_tokens": sum(window_usage.get(w, 0) for w in low_usage),
    }


def sprint_3_2(lines, lattice_map, window_contents, corrections, window_usage):
    """3.2-3.3: Execute merges, evaluate, find sweet spot."""
    console.rule("[bold blue]3.2: Merge Execution + Evaluation")

    strategies = {
        "size_based": lambda t: build_merge_plan_size(window_contents, t),
        "correction_based": lambda t: build_merge_plan_correction(
            corrections, window_contents, t),
        "usage_based": lambda t: build_merge_plan_usage(
            window_usage, window_contents, t),
    }

    # Compute baseline (50 windows, no merge)
    baseline_volv = dimension_volvelle(NUM_WINDOWS)
    baseline_tab = dimension_tabula(NUM_WINDOWS)
    baseline_adm = evaluate_merged_admissibility(
        lines, lattice_map, window_contents, sorted(window_contents.keys()))

    console.print(f"\n  Baseline (50 states): volvelle {baseline_volv['diameter_mm']}mm, "
                  f"drift admissibility {baseline_adm['drift']:.4f}")

    all_results = {}
    viable_configs = []

    for strat_name, build_fn in strategies.items():
        strat_results = []
        console.print(f"\n  [bold]{strat_name}:[/bold]")

        table = Table(title=f"Merge Results: {strat_name}")
        table.add_column("States", justify="right")
        table.add_column("Merged", justify="right")
        table.add_column("Max Vocab", justify="right")
        table.add_column("Volvelle", justify="right")
        table.add_column("Fits Apian", justify="center")
        table.add_column("Strict Adm", justify="right")
        table.add_column("Drift Adm", justify="right")
        table.add_column("Delta pp", justify="right")

        for target in TARGET_STATE_COUNTS:
            merge_map = build_fn(target)
            m_lm, m_wc, m_corr, surviving = apply_merge(
                merge_map, lattice_map, window_contents, corrections)

            actual_states = len(surviving)
            max_vocab = max(len(words) for words in m_wc.values())
            volv = dimension_volvelle(actual_states)
            tab = dimension_tabula(actual_states)
            adm = evaluate_merged_admissibility(lines, m_lm, m_wc, surviving)

            delta_pp = round((adm["drift"] - BASELINE_ADMISSIBILITY) * 100, 2)
            fits = volv["fits_apian"]

            result = {
                "target_states": target,
                "actual_states": actual_states,
                "windows_merged": NUM_WINDOWS - actual_states,
                "largest_merged_vocab": max_vocab,
                "volvelle": volv,
                "tabula": tab,
                "admissibility": {
                    "strict": adm["strict"],
                    "drift": adm["drift"],
                    "total_transitions": adm["total_transitions"],
                    "delta_from_baseline_pp": delta_pp,
                },
            }
            strat_results.append(result)

            fits_color = "green" if fits else "red"
            adm_color = "green" if adm["drift"] >= MIN_ADMISSIBILITY else "red"

            table.add_row(
                str(actual_states),
                str(NUM_WINDOWS - actual_states),
                str(max_vocab),
                f"{volv['diameter_mm']}mm",
                f"[{fits_color}]{'YES' if fits else 'NO'}[/{fits_color}]",
                f"{adm['strict']:.4f}",
                f"[{adm_color}]{adm['drift']:.4f}[/{adm_color}]",
                f"{delta_pp:+.2f}",
            )

            if fits and adm["drift"] >= MIN_ADMISSIBILITY:
                viable_configs.append({
                    "strategy": strat_name,
                    "target_states": target,
                    "actual_states": actual_states,
                    "volvelle_diameter_mm": volv["diameter_mm"],
                    "drift_admissibility": adm["drift"],
                    "delta_pp": delta_pp,
                })

        console.print(table)
        all_results[strat_name] = strat_results

    return all_results, viable_configs, baseline_adm


def sprint_3_3(viable_configs):
    """3.3: Sweet spot analysis."""
    console.rule("[bold blue]3.3: Sweet Spot Analysis")

    if not viable_configs:
        console.print("  [red]No viable configurations found "
                      f"(≤{MAX_DEVICE_DIAMETER_MM}mm AND ≥{MIN_ADMISSIBILITY:.0%} "
                      "admissibility)[/red]")
        return {
            "found": False,
            "best_config": None,
            "all_viable": [],
        }

    # Score: admissibility_retention × (MAX_DEVICE / diameter)
    for cfg in viable_configs:
        retention = cfg["drift_admissibility"] / BASELINE_ADMISSIBILITY
        size_score = MAX_DEVICE_DIAMETER_MM / max(cfg["volvelle_diameter_mm"], 1)
        cfg["combined_score"] = round(retention * min(size_score, 1.0), 4)

    viable_configs.sort(key=lambda c: c["combined_score"], reverse=True)

    table = Table(title="Viable Configurations (ranked)")
    table.add_column("Strategy")
    table.add_column("States", justify="right")
    table.add_column("Diameter", justify="right")
    table.add_column("Drift Adm", justify="right")
    table.add_column("Delta pp", justify="right")
    table.add_column("Score", justify="right", style="bold")

    for cfg in viable_configs:
        table.add_row(
            cfg["strategy"],
            str(cfg["actual_states"]),
            f"{cfg['volvelle_diameter_mm']}mm",
            f"{cfg['drift_admissibility']:.4f}",
            f"{cfg['delta_pp']:+.2f}pp",
            f"{cfg['combined_score']:.4f}",
        )
    console.print(table)

    best = viable_configs[0]
    console.print(f"\n  [green bold]Best configuration:[/green bold] "
                  f"{best['strategy']} at {best['actual_states']} states")
    console.print(f"  Volvelle: {best['volvelle_diameter_mm']}mm, "
                  f"Admissibility: {best['drift_admissibility']:.4f} "
                  f"({best['delta_pp']:+.2f}pp from baseline)")

    return {
        "found": True,
        "best_config": best,
        "all_viable": viable_configs,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 20, Sprint 3: Window State Merging Analysis")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)

    console.print(f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows")
    console.print(f"  Corpus: {len(lines)} lines")
    console.print(f"  Corrections: {len(corrections)} windows")

    # Compute usage
    window_usage = compute_window_usage(lines, lattice_map)

    # Sprint 3.1: Define candidates
    s3_1 = sprint_3_1(window_contents, corrections, window_usage)

    # Sprint 3.2: Execute merges
    merge_results, viable_configs, baseline_adm = sprint_3_2(
        lines, lattice_map, window_contents, corrections, window_usage)

    # Sprint 3.3: Sweet spot
    sweet_spot = sprint_3_3(viable_configs)

    # Assemble results
    results = {
        "baseline": {
            "num_windows": NUM_WINDOWS,
            "drift_admissibility": baseline_adm["drift"],
            "volvelle_diameter_mm": dimension_volvelle(NUM_WINDOWS)["diameter_mm"],
            "tabula_dims_mm": dimension_tabula(NUM_WINDOWS),
        },
        "merge_candidates": s3_1,
        "merge_results": merge_results,
        "sweet_spot": sweet_spot,
    }

    # Sanitize numpy types
    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    results = _sanitize(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_20b_state_merging"}):
        main()
