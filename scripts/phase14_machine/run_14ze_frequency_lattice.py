"""
Phase 14M — Frequency-Stratified Lattice Refinement

Sprints 1-3: Build a frequency-weighted lattice, evaluate per-tier admissibility,
test tier-specific offset corrections, and attempt OOV recovery.

Addresses the Phase 14L finding that vocabulary frequency is the dominant factor
in the ~40% residual (common words fail at 6.9%, rare at 84.5%).
"""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import sanitize_token
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase14_machine.palette_solver import GlobalPaletteSolver

console = Console()

# ── Constants ──────────────────────────────────────────────────────────
NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
SLIP_PATH = Path("results/data/phase12_mechanical/slip_detection_results.json")
PALETTE_PATH = Path("results/data/phase14_machine/reordered_palette.json")
OUTPUT_PATH = Path("results/data/phase14_machine/frequency_lattice.json")

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


# ── Helpers ────────────────────────────────────────────────────────────

def get_folio_num(folio_id: str) -> int:
    import re
    m = re.search(r"f(\d+)", folio_id)
    return int(m.group(1)) if m else 0


def get_section(folio_num: int) -> str:
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def signed_circular_offset(a: int, b: int, n: int = NUM_WINDOWS) -> int:
    raw = (b - a) % n
    if raw > n // 2:
        raw -= n
    return raw


def load_lines(store):
    """Load canonical ZL lines as list of token lists."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
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
        for content, _folio_id, line_id, _line_idx in rows:
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


def load_lines_with_folio(store):
    """Load lines with folio metadata for section analysis."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
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
        entries = []
        current_tokens = []
        current_folio = None
        current_line_id = None
        for content, folio_id, line_id, _line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    fnum = get_folio_num(current_folio)
                    entries.append({
                        "tokens": current_tokens,
                        "folio_id": current_folio,
                        "section": get_section(fnum),
                    })
                current_tokens = []
            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id
        if current_tokens:
            fnum = get_folio_num(current_folio)
            entries.append({
                "tokens": current_tokens,
                "folio_id": current_folio,
                "section": get_section(fnum),
            })
        return entries
    finally:
        session.close()


def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = "reordered_lattice_map" if "reordered_lattice_map" in results else "lattice_map"
    wc_key = "reordered_window_contents" if "reordered_window_contents" in results else "window_contents"
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_slips():
    if not SLIP_PATH.exists():
        return []
    with open(SLIP_PATH) as f:
        data = json.load(f)
    return data.get("results", data).get("slips", [])


def learn_offset_corrections(lines, lattice_map, min_obs=5):
    """Learn per-window mode offset corrections."""
    groups = defaultdict(list)
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            groups[prev_win].append(signed_circular_offset(prev_win, curr_win))
    corrections = {}
    for key, offsets in groups.items():
        if len(offsets) >= min_obs:
            corrections[key] = Counter(offsets).most_common(1)[0][0]
    return corrections


def score_admissibility(lines, lattice_map, corrections):
    """Score corrected admissibility. Returns (adm, base_adm, total)."""
    adm = base = total = 0
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            total += 1
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            raw = signed_circular_offset(prev_win, curr_win)
            if abs(raw) <= 1:
                base += 1
            correction = corrections.get(prev_win, 0)
            corrected = raw - correction
            if corrected > NUM_WINDOWS // 2:
                corrected -= NUM_WINDOWS
            elif corrected < -NUM_WINDOWS // 2:
                corrected += NUM_WINDOWS
            if abs(corrected) <= 1:
                adm += 1
    return adm, base, total


def freq_tier(freq):
    if freq <= 1:
        return "hapax"
    elif freq <= 9:
        return "rare"
    elif freq <= 99:
        return "medium"
    else:
        return "common"


def score_by_tier(lines, lattice_map, corrections, word_freq):
    """Score corrected admissibility broken down by frequency tier of target word."""
    tiers = defaultdict(lambda: {"total": 0, "adm": 0, "base": 0})
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            tier = freq_tier(word_freq.get(curr_w, 0))
            tiers[tier]["total"] += 1
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            raw = signed_circular_offset(prev_win, curr_win)
            if abs(raw) <= 1:
                tiers[tier]["base"] += 1
            correction = corrections.get(prev_win, 0)
            corrected = raw - correction
            if corrected > NUM_WINDOWS // 2:
                corrected -= NUM_WINDOWS
            elif corrected < -NUM_WINDOWS // 2:
                corrected += NUM_WINDOWS
            if abs(corrected) <= 1:
                tiers[tier]["adm"] += 1
    return dict(tiers)


def binomial_z(k, n, p0):
    """Binomial z-score for k successes out of n vs null rate p0."""
    if n == 0 or p0 <= 0 or p0 >= 1:
        return 0.0
    return (k / n - p0) / math.sqrt(p0 * (1 - p0) / n)


# ── Sprint 1: Frequency-Weighted Palette Solver ───────────────────────

def build_frequency_weighted_lattice(lines, slips, top_n=8000):
    """Build a lattice where transition edges are weighted by bigram frequency."""
    all_tokens = [t for line in lines for t in line]
    counts = Counter(all_tokens)
    keep = set(w for w, _ in counts.most_common(top_n))

    solver = GlobalPaletteSolver()

    # Add slip edges (unchanged — high-confidence physical signals)
    for s in slips:
        word_a = s["word"]
        word_b = s["actual_context"][0]
        if word_a in keep and word_b in keep:
            solver.G.add_edge(word_a, word_b, weight=10.0, type="slip")

    # Add transition edges weighted by bigram frequency
    bigram_counts = Counter()
    for line in lines:
        for i in range(len(line) - 1):
            u, v = line[i], line[i + 1]
            if u in keep and v in keep:
                bigram_counts[(u, v)] += 1

    for (u, v), cnt in bigram_counts.items():
        weight = math.log2(1 + cnt)
        # Accumulate weights if edge already exists (from slips)
        if solver.G.has_edge(u, v):
            solver.G[u][v]["weight"] += weight
        else:
            solver.G.add_edge(u, v, weight=weight, type="transition")

    console.print(f"Frequency-weighted graph: {solver.G.number_of_nodes()} nodes, "
                  f"{solver.G.number_of_edges()} edges")

    solved_pos = solver.solve_grid(iterations=20)
    lattice_data = solver.cluster_lattice(solved_pos, num_windows=NUM_WINDOWS)
    reordered = solver.reorder_windows(
        lattice_data["word_to_window"],
        lattice_data["window_contents"],
        lines,
    )
    return reordered["word_to_window"], reordered["window_contents"]


def build_uniform_lattice(lines, slips, top_n=8000):
    """Build the standard uniform-weighted lattice (baseline)."""
    solver = GlobalPaletteSolver()
    solver.ingest_data(slips, lines, top_n=top_n)
    solved_pos = solver.solve_grid(iterations=20)
    lattice_data = solver.cluster_lattice(solved_pos, num_windows=NUM_WINDOWS)
    reordered = solver.reorder_windows(
        lattice_data["word_to_window"],
        lattice_data["window_contents"],
        lines,
    )
    return reordered["word_to_window"], reordered["window_contents"]


def compare_window_assignments(lm_a, lm_b, word_freq):
    """Compare how many words changed windows between two lattices, by tier."""
    shared_words = set(lm_a.keys()) & set(lm_b.keys())
    tier_stats = defaultdict(lambda: {"total": 0, "changed": 0})
    for w in shared_words:
        tier = freq_tier(word_freq.get(w, 0))
        tier_stats[tier]["total"] += 1
        if lm_a[w] != lm_b[w]:
            tier_stats[tier]["changed"] += 1
    overall_changed = sum(v["changed"] for v in tier_stats.values())
    overall_total = sum(v["total"] for v in tier_stats.values())
    return {
        "overall_changed": overall_changed,
        "overall_total": overall_total,
        "overall_pct": round(overall_changed / max(overall_total, 1) * 100, 1),
        "by_tier": {
            t: {
                "total": v["total"],
                "changed": v["changed"],
                "pct": round(v["changed"] / max(v["total"], 1) * 100, 1),
            }
            for t, v in tier_stats.items()
        },
    }


# ── Sprint 2: Tier-Specific Offset Corrections ────────────────────────

def learn_tier_corrections(lines, lattice_map, word_freq, min_obs=5):
    """Learn separate offset corrections per frequency tier."""
    tier_groups = defaultdict(lambda: defaultdict(list))
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            tier = freq_tier(word_freq.get(curr_w, 0))
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            tier_groups[tier][prev_win].append(
                signed_circular_offset(prev_win, curr_win)
            )
    # Learn mode per tier per window
    result = {}
    for tier, groups in tier_groups.items():
        corrections = {}
        for win, offsets in groups.items():
            if len(offsets) >= min_obs:
                corrections[win] = Counter(offsets).most_common(1)[0][0]
        result[tier] = corrections
    return result


def score_with_tier_corrections(lines, lattice_map, tier_corrections,
                                global_corrections, word_freq):
    """Score using tier-specific corrections (falling back to global)."""
    tiers = defaultdict(lambda: {"total": 0, "adm": 0})
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            tier = freq_tier(word_freq.get(curr_w, 0))
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            raw = signed_circular_offset(prev_win, curr_win)
            tiers[tier]["total"] += 1
            # Try tier-specific correction first, fall back to global
            correction = tier_corrections.get(tier, {}).get(
                prev_win, global_corrections.get(prev_win, 0)
            )
            corrected = raw - correction
            if corrected > NUM_WINDOWS // 2:
                corrected -= NUM_WINDOWS
            elif corrected < -NUM_WINDOWS // 2:
                corrected += NUM_WINDOWS
            if abs(corrected) <= 1:
                tiers[tier]["adm"] += 1
    return dict(tiers)


# ── Sprint 2b: Weighted Mode Estimation ────────────────────────────────

def learn_weighted_corrections(lines, lattice_map, word_freq, min_obs=5):
    """Learn per-window corrections using frequency-weighted mode."""
    groups = defaultdict(list)
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            offset = signed_circular_offset(prev_win, curr_win)
            weight = word_freq.get(prev_w, 1) + word_freq.get(curr_w, 1)
            groups[prev_win].append((offset, weight))

    corrections = {}
    for win, pairs in groups.items():
        if len(pairs) < min_obs:
            continue
        # Weighted mode: accumulate weights per offset value
        offset_weights = defaultdict(float)
        for off, w in pairs:
            offset_weights[off] += w
        corrections[win] = max(offset_weights, key=offset_weights.get)
    return corrections


# ── Sprint 3: OOV Recovery ─────────────────────────────────────────────

def build_suffix_window_map(lattice_map, word_freq, min_suffix_obs=10):
    """Map suffix classes to their most common window assignments."""
    suffix_windows = defaultdict(list)
    suffixes_to_check = ["dy", "in", "y", "or", "ol", "al", "ar", "r",
                         "am", "an", "s", "m", "d", "l", "o", "ey"]
    for word, win in lattice_map.items():
        for sfx in suffixes_to_check:
            if word.endswith(sfx) and len(word) > len(sfx):
                freq = word_freq.get(word, 1)
                suffix_windows[sfx].extend([win] * freq)
                break

    suffix_map = {}
    for sfx, wins in suffix_windows.items():
        if len(wins) >= min_suffix_obs:
            suffix_map[sfx] = Counter(wins).most_common(1)[0][0]
    return suffix_map


def oov_suffix_recovery(lines, lattice_map, corrections, word_freq, suffix_map):
    """Attempt to recover OOV transitions using suffix-based window prediction."""
    recovered = 0
    oov_total = 0
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            # Only target OOV transitions
            if prev_w in lattice_map and curr_w in lattice_map:
                continue
            oov_total += 1
            # Try to assign windows via suffix
            prev_win = lattice_map.get(prev_w)
            curr_win = lattice_map.get(curr_w)
            if prev_win is None:
                for sfx in ["dy", "in", "y", "or", "ol", "al", "ar", "r",
                             "am", "an", "s", "m", "d", "l", "o", "ey"]:
                    if prev_w.endswith(sfx) and sfx in suffix_map:
                        prev_win = suffix_map[sfx]
                        break
            if curr_win is None:
                for sfx in ["dy", "in", "y", "or", "ol", "al", "ar", "r",
                             "am", "an", "s", "m", "d", "l", "o", "ey"]:
                    if curr_w.endswith(sfx) and sfx in suffix_map:
                        curr_win = suffix_map[sfx]
                        break
            if prev_win is not None and curr_win is not None:
                raw = signed_circular_offset(prev_win, curr_win)
                correction = corrections.get(prev_win, 0)
                corrected = raw - correction
                if corrected > NUM_WINDOWS // 2:
                    corrected -= NUM_WINDOWS
                elif corrected < -NUM_WINDOWS // 2:
                    corrected += NUM_WINDOWS
                if abs(corrected) <= 1:
                    recovered += 1
    return {"oov_total": oov_total, "recovered": recovered,
            "recovery_rate": round(recovered / max(oov_total, 1), 4)}


def oov_nn_recovery(lines, lattice_map, corrections, word_freq):
    """Attempt OOV recovery via nearest-neighbor edit distance."""
    # Pre-build vocab list for NN search
    palette_words = list(lattice_map.keys())

    def min_edit_dist(w, candidates, max_dist=2):
        """Find closest candidate within edit distance max_dist."""
        best = None
        best_d = max_dist + 1
        w_len = len(w)
        for c in candidates:
            if abs(len(c) - w_len) > max_dist:
                continue
            # Quick Levenshtein
            if w_len <= 1 or len(c) <= 1:
                d = max(w_len, len(c))
            else:
                prev_row = list(range(len(c) + 1))
                for i, ch1 in enumerate(w, 1):
                    curr_row = [i]
                    for j, ch2 in enumerate(c, 1):
                        cost = 0 if ch1 == ch2 else 1
                        curr_row.append(min(
                            curr_row[j - 1] + 1,
                            prev_row[j] + 1,
                            prev_row[j - 1] + cost,
                        ))
                    prev_row = curr_row
                d = prev_row[-1]
            if d < best_d:
                best_d = d
                best = c
                if d == 0:
                    break
        return best if best_d <= max_dist else None

    recovered = 0
    oov_total = 0
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w in lattice_map and curr_w in lattice_map:
                continue
            oov_total += 1
            prev_win = lattice_map.get(prev_w)
            curr_win = lattice_map.get(curr_w)
            if prev_win is None:
                nn = min_edit_dist(prev_w, palette_words)
                if nn:
                    prev_win = lattice_map[nn]
            if curr_win is None:
                nn = min_edit_dist(curr_w, palette_words)
                if nn:
                    curr_win = lattice_map[nn]
            if prev_win is not None and curr_win is not None:
                raw = signed_circular_offset(prev_win, curr_win)
                correction = corrections.get(prev_win, 0)
                corrected = raw - correction
                if corrected > NUM_WINDOWS // 2:
                    corrected -= NUM_WINDOWS
                elif corrected < -NUM_WINDOWS // 2:
                    corrected += NUM_WINDOWS
                if abs(corrected) <= 1:
                    recovered += 1
    return {"oov_total": oov_total, "recovered": recovered,
            "recovery_rate": round(recovered / max(oov_total, 1), 4)}


# ── Cross-Validation (7-fold leave-one-section-out) ────────────────────

def cross_validate(line_entries, build_fn, slips, word_freq):
    """7-fold leave-one-section-out CV comparing uniform vs frequency lattice."""
    sections = list(SECTIONS.keys())
    results = []

    for held_out in sections:
        train_lines = [e["tokens"] for e in line_entries if e["section"] != held_out]
        test_lines = [e["tokens"] for e in line_entries if e["section"] == held_out]
        if not test_lines:
            continue

        console.print(f"  CV fold: held out [bold]{held_out}[/bold] "
                      f"({len(test_lines)} test lines)")

        lm, wc = build_fn(train_lines, slips)
        corrections = learn_offset_corrections(train_lines, lm, min_obs=5)
        adm, base, total = score_admissibility(test_lines, lm, corrections)

        results.append({
            "held_out": held_out,
            "test_lines": len(test_lines),
            "total_transitions": total,
            "base_adm": base,
            "base_rate": round(base / max(total, 1), 4),
            "corrected_adm": adm,
            "corrected_rate": round(adm / max(total, 1), 4),
        })

    return results


# ── Main ───────────────────────────────────────────────────────────────

def main():
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)
    line_entries = load_lines_with_folio(store)
    slips = load_slips()
    all_tokens = [t for line in lines for t in line]
    word_freq = Counter(all_tokens)

    console.print("\n[bold]Phase 14M: Frequency-Stratified Lattice Refinement[/bold]")
    console.print(f"Corpus: {len(lines)} lines, {len(all_tokens)} tokens, "
                  f"{len(word_freq)} unique words, {len(slips)} slips")

    # Load existing (canonical) lattice for comparison
    canon_lm, canon_wc = load_palette(PALETTE_PATH)
    canon_corrections = learn_offset_corrections(lines, canon_lm, min_obs=5)

    # ── Sprint 1: Build frequency-weighted lattice ──────────────────────
    console.rule("[bold cyan]Sprint 1: Frequency-Weighted Palette[/bold cyan]")

    console.print("\n[yellow]Building uniform lattice (fresh, for fair comparison)...[/yellow]")
    uni_lm, uni_wc = build_uniform_lattice(lines, slips)
    uni_corrections = learn_offset_corrections(lines, uni_lm, min_obs=5)

    console.print("\n[yellow]Building frequency-weighted lattice...[/yellow]")
    freq_lm, freq_wc = build_frequency_weighted_lattice(lines, slips)
    freq_corrections = learn_offset_corrections(lines, freq_lm, min_obs=5)

    # A/B comparison: overall admissibility
    uni_adm, uni_base, uni_total = score_admissibility(lines, uni_lm, uni_corrections)
    freq_adm, freq_base, freq_total = score_admissibility(lines, freq_lm, freq_corrections)
    canon_adm, canon_base, canon_total = score_admissibility(
        lines, canon_lm, canon_corrections
    )

    console.print("\n[bold]Overall Admissibility (full corpus, not cross-validated):[/bold]")
    t = Table()
    t.add_column("Variant")
    t.add_column("Base %", justify="right")
    t.add_column("Corrected %", justify="right")
    t.add_column("Total")
    t.add_row("Canonical (existing)", f"{canon_base/max(canon_total,1)*100:.1f}",
              f"{canon_adm/max(canon_total,1)*100:.1f}", str(canon_total))
    t.add_row("Uniform (fresh)", f"{uni_base/max(uni_total,1)*100:.1f}",
              f"{uni_adm/max(uni_total,1)*100:.1f}", str(uni_total))
    t.add_row("Frequency-weighted", f"{freq_base/max(freq_total,1)*100:.1f}",
              f"{freq_adm/max(freq_total,1)*100:.1f}", str(freq_total))
    console.print(t)

    # Per-tier comparison
    uni_tiers = score_by_tier(lines, uni_lm, uni_corrections, word_freq)
    freq_tiers = score_by_tier(lines, freq_lm, freq_corrections, word_freq)
    canon_tiers = score_by_tier(lines, canon_lm, canon_corrections, word_freq)

    console.print("\n[bold]Per-Tier Corrected Admissibility:[/bold]")
    t2 = Table(title="Corrected Admissibility by Frequency Tier")
    t2.add_column("Tier")
    t2.add_column("Canonical %", justify="right")
    t2.add_column("Uniform %", justify="right")
    t2.add_column("Freq-Wt %", justify="right")
    t2.add_column("Delta (FW-Uni)", justify="right")
    for tier in ["common", "medium", "rare", "hapax"]:
        c_d = canon_tiers.get(tier, {"total": 0, "adm": 0})
        u_d = uni_tiers.get(tier, {"total": 0, "adm": 0})
        f_d = freq_tiers.get(tier, {"total": 0, "adm": 0})
        c_rate = c_d["adm"] / max(c_d["total"], 1) * 100
        u_rate = u_d["adm"] / max(u_d["total"], 1) * 100
        f_rate = f_d["adm"] / max(f_d["total"], 1) * 100
        delta = f_rate - u_rate
        t2.add_row(tier, f"{c_rate:.1f}", f"{u_rate:.1f}", f"{f_rate:.1f}",
                   f"{delta:+.1f}pp")
    console.print(t2)

    # Window displacement analysis
    displacement = compare_window_assignments(uni_lm, freq_lm, word_freq)
    console.print(f"\nWindow displacement: {displacement['overall_pct']}% of words "
                  f"changed windows ({displacement['overall_changed']}/{displacement['overall_total']})")

    # Sprint 1 gate check for Sprint 2
    medium_displaced = displacement["by_tier"].get("medium", {}).get("pct", 0)
    sprint2_gate = medium_displaced >= 10.0
    console.print(f"\n[bold]Sprint 2 gate:[/bold] Medium-tier displacement = {medium_displaced}% "
                  f"{'≥' if sprint2_gate else '<'} 10% → "
                  f"{'[green]PASS[/green]' if sprint2_gate else '[red]FAIL (Sprint 2 skipped)[/red]'}")

    # ── Cross-validation ─────────────────────────────────────────────────
    console.rule("[bold cyan]Cross-Validation (7-fold)[/bold cyan]")

    console.print("\n[yellow]CV: Uniform lattice...[/yellow]")
    cv_uni = cross_validate(line_entries, build_uniform_lattice, slips, word_freq)

    console.print("\n[yellow]CV: Frequency-weighted lattice...[/yellow]")
    cv_freq = cross_validate(line_entries, build_frequency_weighted_lattice, slips, word_freq)

    # CV summary
    console.print("\n[bold]Cross-Validated Corrected Admissibility:[/bold]")
    t3 = Table()
    t3.add_column("Section (held out)")
    t3.add_column("Uniform %", justify="right")
    t3.add_column("Freq-Wt %", justify="right")
    t3.add_column("Delta", justify="right")
    for u, f in zip(cv_uni, cv_freq):
        u_rate = u["corrected_rate"] * 100
        f_rate = f["corrected_rate"] * 100
        t3.add_row(u["held_out"], f"{u_rate:.1f}", f"{f_rate:.1f}",
                   f"{f_rate - u_rate:+.1f}pp")
    mean_u = np.mean([r["corrected_rate"] for r in cv_uni]) * 100
    mean_f = np.mean([r["corrected_rate"] for r in cv_freq]) * 100
    t3.add_row("[bold]Mean[/bold]", f"[bold]{mean_u:.1f}[/bold]",
               f"[bold]{mean_f:.1f}[/bold]", f"[bold]{mean_f - mean_u:+.1f}pp[/bold]")
    console.print(t3)

    # ── Sprint 2: Tier-Specific Corrections (gated) ─────────────────────
    sprint2_results = None
    weighted_mode_results = None

    if sprint2_gate:
        console.rule("[bold cyan]Sprint 2: Tier-Specific Corrections[/bold cyan]")

        # 2.1 Tier-specific corrections
        tier_corr = learn_tier_corrections(lines, freq_lm, word_freq, min_obs=5)
        tier_scored = score_with_tier_corrections(
            lines, freq_lm, tier_corr, freq_corrections, word_freq
        )
        console.print("\n[bold]Tier-Specific Corrections (full corpus):[/bold]")
        t4 = Table()
        t4.add_column("Tier")
        t4.add_column("Global Corr %", justify="right")
        t4.add_column("Tier-Specific %", justify="right")
        t4.add_column("Delta", justify="right")
        for tier in ["common", "medium", "rare", "hapax"]:
            g_d = freq_tiers.get(tier, {"total": 0, "adm": 0})
            t_d = tier_scored.get(tier, {"total": 0, "adm": 0})
            g_rate = g_d["adm"] / max(g_d["total"], 1) * 100
            t_rate = t_d["adm"] / max(t_d["total"], 1) * 100
            t4.add_row(tier, f"{g_rate:.1f}", f"{t_rate:.1f}", f"{t_rate - g_rate:+.1f}pp")
        console.print(t4)

        sprint2_results = {
            tier: {
                "total": v["total"],
                "adm": v["adm"],
                "rate": round(v["adm"] / max(v["total"], 1), 4),
                "num_corrections": len(tier_corr.get(tier, {})),
            }
            for tier, v in tier_scored.items()
        }

        # 2.2 Weighted mode estimation
        console.print("\n[yellow]Testing weighted mode corrections...[/yellow]")
        wt_corr = learn_weighted_corrections(lines, freq_lm, word_freq, min_obs=5)
        wt_adm, wt_base, wt_total = score_admissibility(lines, freq_lm, wt_corr)
        wt_rate = wt_adm / max(wt_total, 1) * 100
        plain_rate = freq_adm / max(freq_total, 1) * 100
        console.print(f"Weighted mode: {wt_rate:.1f}% vs plain mode: {plain_rate:.1f}% "
                      f"(delta: {wt_rate - plain_rate:+.1f}pp)")

        # Count how many corrections differ
        diff_count = sum(
            1 for w in set(freq_corrections) & set(wt_corr)
            if freq_corrections[w] != wt_corr[w]
        )
        console.print(f"Weighted mode differs from plain mode in {diff_count}/{len(freq_corrections)} windows")

        weighted_mode_results = {
            "weighted_adm": wt_adm,
            "weighted_rate": round(wt_rate, 2),
            "plain_rate": round(plain_rate, 2),
            "delta_pp": round(wt_rate - plain_rate, 2),
            "differing_windows": diff_count,
            "total_windows": len(freq_corrections),
        }
    else:
        console.print("\n[dim]Sprint 2 skipped (gate failed)[/dim]")

    # ── Sprint 3: OOV Recovery ──────────────────────────────────────────
    console.rule("[bold cyan]Sprint 3: OOV Recovery & Consolidation[/bold cyan]")

    # Use the best lattice variant (freq-weighted or uniform based on CV results)
    best_is_freq = mean_f > mean_u
    best_lm = freq_lm if best_is_freq else uni_lm
    best_wc = freq_wc if best_is_freq else uni_wc
    best_corr = freq_corrections if best_is_freq else uni_corrections
    best_label = "frequency-weighted" if best_is_freq else "uniform"
    console.print(f"\nBest lattice variant: [bold]{best_label}[/bold] "
                  f"(CV mean: {max(mean_f, mean_u):.1f}%)")

    # 3.1 Suffix-based OOV recovery
    suffix_map = build_suffix_window_map(best_lm, word_freq)
    console.print(f"Suffix map: {len(suffix_map)} suffix classes → window assignments")
    suffix_result = oov_suffix_recovery(lines, best_lm, best_corr, word_freq, suffix_map)
    console.print(f"Suffix recovery: {suffix_result['recovered']}/{suffix_result['oov_total']} "
                  f"OOV transitions recovered ({suffix_result['recovery_rate']*100:.1f}%)")

    # 3.2 Nearest-neighbor OOV recovery
    console.print("[yellow]Running nearest-neighbor OOV recovery (may take a moment)...[/yellow]")
    nn_result = oov_nn_recovery(lines, best_lm, best_corr, word_freq)
    console.print(f"NN recovery: {nn_result['recovered']}/{nn_result['oov_total']} "
                  f"OOV transitions recovered ({nn_result['recovery_rate']*100:.1f}%)")

    # 3.3 Consolidated best model
    best_overall_adm = freq_adm if best_is_freq else uni_adm
    best_overall_total = freq_total if best_is_freq else uni_total
    best_overall_rate = best_overall_adm / max(best_overall_total, 1) * 100

    # Add OOV recoveries to overall count
    best_oov = max(suffix_result["recovered"], nn_result["recovered"])
    best_oov_method = "suffix" if suffix_result["recovered"] >= nn_result["recovered"] else "nn"
    consolidated_adm = best_overall_adm + best_oov
    consolidated_total = best_overall_total + suffix_result["oov_total"]
    consolidated_rate = consolidated_adm / max(consolidated_total, 1) * 100

    console.print("\n[bold]Consolidated Best Model:[/bold]")
    console.print(f"  Lattice: {best_label}")
    console.print("  Corrections: global mode (50 params)")
    console.print(f"  OOV recovery: {best_oov_method} ({best_oov} recovered)")
    console.print(f"  In-palette admissibility: {best_overall_rate:.1f}% "
                  f"({best_overall_adm}/{best_overall_total})")
    console.print(f"  With OOV recovery: {consolidated_rate:.1f}% "
                  f"({consolidated_adm}/{consolidated_total})")

    # 3.4 Diminishing returns assessment
    # What's the theoretical maximum improvement from medium-tier?
    medium_tier_data = freq_tiers.get("medium", {"total": 0, "adm": 0})
    medium_failures = medium_tier_data["total"] - medium_tier_data["adm"]
    if_all_medium_fixed = (best_overall_adm + medium_failures) / max(best_overall_total, 1) * 100
    actual_delta = best_overall_rate - (canon_adm / max(canon_total, 1) * 100)

    console.print("\n[bold]Diminishing Returns:[/bold]")
    console.print(f"  If ALL medium-tier failures fixed: {if_all_medium_fixed:.1f}% "
                  f"(+{if_all_medium_fixed - best_overall_rate:.1f}pp)")
    console.print(f"  Actual improvement over canonical: {actual_delta:+.1f}pp")
    console.print(f"  OOV recovery adds: +{best_oov} transitions "
                  f"({best_oov / max(consolidated_total, 1) * 100:.2f}pp)")

    # ── Assemble results ────────────────────────────────────────────────
    results = {
        "sprint1_frequency_lattice": {
            "overall": {
                "canonical": {
                    "base_rate": round(canon_base / max(canon_total, 1), 4),
                    "corrected_rate": round(canon_adm / max(canon_total, 1), 4),
                    "total": canon_total,
                },
                "uniform": {
                    "base_rate": round(uni_base / max(uni_total, 1), 4),
                    "corrected_rate": round(uni_adm / max(uni_total, 1), 4),
                    "total": uni_total,
                },
                "frequency_weighted": {
                    "base_rate": round(freq_base / max(freq_total, 1), 4),
                    "corrected_rate": round(freq_adm / max(freq_total, 1), 4),
                    "total": freq_total,
                },
            },
            "per_tier": {
                tier: {
                    "canonical": {
                        "total": canon_tiers.get(tier, {}).get("total", 0),
                        "adm": canon_tiers.get(tier, {}).get("adm", 0),
                        "rate": round(canon_tiers.get(tier, {}).get("adm", 0) /
                                      max(canon_tiers.get(tier, {}).get("total", 1), 1), 4),
                    },
                    "uniform": {
                        "total": uni_tiers.get(tier, {}).get("total", 0),
                        "adm": uni_tiers.get(tier, {}).get("adm", 0),
                        "rate": round(uni_tiers.get(tier, {}).get("adm", 0) /
                                      max(uni_tiers.get(tier, {}).get("total", 1), 1), 4),
                    },
                    "frequency_weighted": {
                        "total": freq_tiers.get(tier, {}).get("total", 0),
                        "adm": freq_tiers.get(tier, {}).get("adm", 0),
                        "rate": round(freq_tiers.get(tier, {}).get("adm", 0) /
                                      max(freq_tiers.get(tier, {}).get("total", 1), 1), 4),
                    },
                }
                for tier in ["common", "medium", "rare", "hapax"]
            },
            "displacement": displacement,
            "sprint2_gate": {
                "medium_displaced_pct": medium_displaced,
                "threshold": 10.0,
                "passed": sprint2_gate,
            },
        },
        "cross_validation": {
            "uniform": cv_uni,
            "frequency_weighted": cv_freq,
            "mean_uniform_rate": round(mean_u / 100, 4),
            "mean_freq_rate": round(mean_f / 100, 4),
            "mean_delta_pp": round(mean_f - mean_u, 2),
        },
        "sprint2_tier_corrections": sprint2_results,
        "sprint2_weighted_mode": weighted_mode_results,
        "sprint3_oov_recovery": {
            "suffix": suffix_result,
            "nearest_neighbor": nn_result,
            "best_method": best_oov_method,
        },
        "sprint3_consolidated": {
            "best_lattice": best_label,
            "best_corrections": "global_mode",
            "in_palette_rate": round(best_overall_rate, 2),
            "in_palette_adm": best_overall_adm,
            "in_palette_total": best_overall_total,
            "oov_method": best_oov_method,
            "oov_recovered": best_oov,
            "consolidated_rate": round(consolidated_rate, 2),
            "consolidated_adm": consolidated_adm,
            "consolidated_total": consolidated_total,
        },
        "diminishing_returns": {
            "if_all_medium_fixed_rate": round(if_all_medium_fixed, 2),
            "actual_delta_pp": round(actual_delta, 2),
            "oov_recovery_pp": round(best_oov / max(consolidated_total, 1) * 100, 2),
        },
    }

    with active_run(config={"seed": 42, "command": "run_14ze_frequency_lattice"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
