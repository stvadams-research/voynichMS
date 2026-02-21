#!/usr/bin/env python3
"""Phase 14L: Residual Characterization.

After per-window offset correction, ~38% of token transitions remain
unexplained.  This script diagnoses the residual across multiple dimensions:

  Sprint 1: Positional & sequential analysis
    - Position-within-line failure rates
    - Sequential burst analysis (consecutive failure runs)
    - Folio-level failure rates
    - Line-length effect

  Sprint 2: Lexical analysis
    - Per-word failure rates (as target and as predecessor)
    - Top failure contributors
    - Word-class analysis (frequency tier, suffix, length)
    - Window occupancy vs failure rate

  Sprint 3: Diagnostic synthesis
    - Principal failure modes
    - Reducibility estimate
    - Recommendations
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
from scipy import stats

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
OFFSETS_PATH = (
    project_root / "results/data/phase14_machine/canonical_offsets.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/residual_characterization.json"
)
console = Console()

NUM_WINDOWS = 50


# ── Helpers ──────────────────────────────────────────────────────────────

def signed_circular_offset(a, b, n=NUM_WINDOWS):
    """Signed circular distance from window a to window b."""
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


def load_corrections(path):
    """Load canonical offset corrections."""
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


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
                    lines.append({
                        "tokens": current_tokens,
                        "folio_id": current_folio,
                        "folio_num": f_num,
                        "line_index": local_idx,
                        "section": get_section(f_num),
                    })
                    folio_local_line_idx[current_folio] = local_idx + 1
                current_tokens = []
            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id

        if current_tokens:
            local_idx = folio_local_line_idx.get(current_folio, 0)
            f_num = get_folio_num(current_folio)
            lines.append({
                "tokens": current_tokens,
                "folio_id": current_folio,
                "folio_num": f_num,
                "line_index": local_idx,
                "section": get_section(f_num),
            })
        return lines
    finally:
        session.close()


def is_admissible_corrected(prev_word, curr_word, lattice_map, corrections):
    """Check if a transition is admissible under the corrected model."""
    if prev_word not in lattice_map or curr_word not in lattice_map:
        return None  # can't score (OOV)
    prev_win = lattice_map[prev_word]
    curr_win = lattice_map[curr_word]
    raw_offset = signed_circular_offset(prev_win, curr_win)
    correction = corrections.get(prev_win, 0)
    corrected_offset = raw_offset - correction
    if corrected_offset > NUM_WINDOWS // 2:
        corrected_offset -= NUM_WINDOWS
    elif corrected_offset < -NUM_WINDOWS // 2:
        corrected_offset += NUM_WINDOWS
    return abs(corrected_offset) <= 1


# ── Build per-token failure records ──────────────────────────────────────

def build_failure_records(lines, lattice_map, corrections):
    """Build a per-token record marking admissible/failure under corrected model.

    Returns list of per-transition records (consecutive pairs).
    """
    records = []
    for line_info in lines:
        tokens = line_info["tokens"]
        section = line_info["section"]
        folio_id = line_info["folio_id"]
        line_idx = line_info["line_index"]
        line_len = len(tokens)

        for i in range(1, len(tokens)):
            prev_word = tokens[i - 1]
            curr_word = tokens[i]
            adm = is_admissible_corrected(prev_word, curr_word, lattice_map, corrections)
            if adm is None:
                # OOV — one or both tokens not in palette
                oov = True
                admissible = False
            else:
                oov = False
                admissible = adm

            records.append({
                "prev_word": prev_word,
                "curr_word": curr_word,
                "position": i,  # position of curr_word in line (1-indexed)
                "line_length": line_len,
                "section": section,
                "folio_id": folio_id,
                "line_index": line_idx,
                "admissible": admissible,
                "oov": oov,
            })
    return records


# ── Sprint 1: Positional & Sequential Analysis ──────────────────────────

def position_analysis(records):
    """Failure rate by position within line."""
    pos_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    for r in records:
        pos = min(r["position"], 10)  # cap at 10+
        pos_counts[pos]["total"] += 1
        if not r["admissible"]:
            pos_counts[pos]["fail"] += 1

    result = {}
    for pos in sorted(pos_counts.keys()):
        c = pos_counts[pos]
        result[pos] = {
            "total": c["total"],
            "failures": c["fail"],
            "failure_rate": round(c["fail"] / c["total"], 4) if c["total"] else 0,
        }
    return result


def burst_analysis(lines, lattice_map, corrections):
    """Analyze consecutive failure runs."""
    all_run_lengths = []
    total_transitions = 0
    total_failures = 0

    for line_info in lines:
        tokens = line_info["tokens"]
        current_run = 0
        for i in range(1, len(tokens)):
            total_transitions += 1
            adm = is_admissible_corrected(tokens[i - 1], tokens[i], lattice_map, corrections)
            if adm is None or not adm:
                current_run += 1
                total_failures += 1
            else:
                if current_run > 0:
                    all_run_lengths.append(current_run)
                current_run = 0
        if current_run > 0:
            all_run_lengths.append(current_run)

    if not all_run_lengths:
        return {"no_failures": True}

    run_counter = Counter(all_run_lengths)
    overall_fail_rate = total_failures / total_transitions if total_transitions else 0

    # Expected run length under independence: geometric distribution
    # E[run_length] = 1 / (1 - p_fail) ... actually for run of failures:
    # P(run=k) = p^k * (1-p), E[run] = p/(1-p)
    p = overall_fail_rate
    expected_mean_run = p / (1 - p) if p < 1 else float("inf")

    observed_mean_run = np.mean(all_run_lengths)

    # Chi-squared test: compare observed run-length distribution to geometric
    max_run = max(all_run_lengths)
    observed_counts = [run_counter.get(k, 0) for k in range(1, min(max_run + 1, 20))]
    n_runs = sum(observed_counts)
    expected_counts = [n_runs * (p ** k) * (1 - p) for k in range(1, len(observed_counts) + 1)]

    # Filter bins with expected > 5 for chi-squared validity
    valid_bins = [(o, e) for o, e in zip(observed_counts, expected_counts) if e >= 5]
    if len(valid_bins) >= 3:
        obs_v = [v[0] for v in valid_bins]
        exp_v = [v[1] for v in valid_bins]
        # Normalize expected to match observed sum (required by scipy)
        exp_sum = sum(exp_v)
        obs_sum = sum(obs_v)
        if exp_sum > 0:
            exp_v = [e * obs_sum / exp_sum for e in exp_v]
        chi2, p_val = stats.chisquare(obs_v, exp_v)
        chi2_result = {"chi2": round(chi2, 2), "p_value": round(p_val, 6), "df": len(valid_bins) - 1}
    else:
        chi2_result = {"chi2": None, "p_value": None, "note": "too few valid bins"}

    return {
        "total_transitions": total_transitions,
        "total_failures": total_failures,
        "failure_rate": round(overall_fail_rate, 4),
        "num_runs": len(all_run_lengths),
        "mean_run_length": round(observed_mean_run, 2),
        "expected_mean_run_length": round(expected_mean_run, 2),
        "median_run_length": int(np.median(all_run_lengths)),
        "max_run_length": max(all_run_lengths),
        "run_distribution": dict(sorted(run_counter.items())[:15]),
        "clustering_test": chi2_result,
    }


def folio_analysis(records):
    """Per-folio failure rates."""
    folio_counts = defaultdict(lambda: {"total": 0, "fail": 0, "section": ""})
    for r in records:
        fc = folio_counts[r["folio_id"]]
        fc["total"] += 1
        fc["section"] = r["section"]
        if not r["admissible"]:
            fc["fail"] += 1

    folio_stats = []
    for fid, c in folio_counts.items():
        folio_stats.append({
            "folio_id": fid,
            "section": c["section"],
            "total": c["total"],
            "failures": c["fail"],
            "failure_rate": round(c["fail"] / c["total"], 4) if c["total"] else 0,
        })

    folio_stats.sort(key=lambda x: x["failure_rate"], reverse=True)
    rates = [f["failure_rate"] for f in folio_stats]

    return {
        "num_folios": len(folio_stats),
        "mean_failure_rate": round(np.mean(rates), 4),
        "std_failure_rate": round(float(np.std(rates)), 4),
        "top_10_worst": folio_stats[:10],
        "top_10_best": folio_stats[-10:][::-1],
    }


def line_length_analysis(records):
    """Failure rate vs line length."""
    len_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    for r in records:
        ll = r["line_length"]
        len_counts[ll]["total"] += 1
        if not r["admissible"]:
            len_counts[ll]["fail"] += 1

    result = {}
    for ll in sorted(len_counts.keys()):
        c = len_counts[ll]
        result[ll] = {
            "total": c["total"],
            "failures": c["fail"],
            "failure_rate": round(c["fail"] / c["total"], 4) if c["total"] else 0,
        }

    # Correlation: line length vs failure rate
    lengths = []
    fail_rates = []
    for ll, c in len_counts.items():
        if c["total"] >= 20:
            lengths.append(ll)
            fail_rates.append(c["fail"] / c["total"])

    if len(lengths) >= 3:
        rho, p_val = stats.spearmanr(lengths, fail_rates)
        corr = {"rho": round(rho, 4), "p_value": round(p_val, 4)}
    else:
        corr = {"rho": None, "note": "insufficient data"}

    return {"by_length": result, "correlation": corr}


# ── Sprint 2: Lexical Analysis ──────────────────────────────────────────

def word_failure_analysis(records, lattice_map):
    """Per-word failure rates as target and as predecessor."""
    # As target (curr_word)
    target_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    # As predecessor (prev_word)
    pred_counts = defaultdict(lambda: {"total": 0, "fail": 0})

    for r in records:
        tc = target_counts[r["curr_word"]]
        tc["total"] += 1
        if not r["admissible"]:
            tc["fail"] += 1

        pc = pred_counts[r["prev_word"]]
        pc["total"] += 1
        if not r["admissible"]:
            pc["fail"] += 1

    # Top contributors by absolute failure count
    target_by_count = sorted(
        [(w, c) for w, c in target_counts.items()],
        key=lambda x: x[1]["fail"], reverse=True
    )

    # Top contributors by failure rate (min 20 occurrences)
    target_by_rate = sorted(
        [(w, c) for w, c in target_counts.items() if c["total"] >= 20],
        key=lambda x: x[1]["fail"] / x[1]["total"], reverse=True
    )

    pred_by_count = sorted(
        [(w, c) for w, c in pred_counts.items()],
        key=lambda x: x[1]["fail"], reverse=True
    )

    def fmt_top(lst, n=30):
        return [
            {
                "word": w,
                "total": c["total"],
                "failures": c["fail"],
                "failure_rate": round(c["fail"] / c["total"], 4) if c["total"] else 0,
                "in_palette": bool(w in lattice_map),
            }
            for w, c in lst[:n]
        ]

    # Overlap: words that appear in both top-50 as target and as predecessor
    top_target_words = {w for w, _ in target_by_count[:50]}
    top_pred_words = {w for w, _ in pred_by_count[:50]}
    overlap = top_target_words & top_pred_words

    return {
        "unique_target_words": len(target_counts),
        "unique_pred_words": len(pred_counts),
        "top_targets_by_count": fmt_top(target_by_count),
        "top_targets_by_rate": fmt_top(target_by_rate),
        "top_predecessors_by_count": fmt_top(pred_by_count),
        "top50_overlap_count": len(overlap),
        "top50_overlap_words": sorted(overlap)[:20],
    }


def word_class_analysis(records, lattice_map):
    """Failure rate by word class (frequency tier, suffix, length)."""
    # First compute global word frequencies
    word_freq = Counter()
    for r in records:
        word_freq[r["curr_word"]] += 1
        word_freq[r["prev_word"]] += 1

    # Failure counts by curr_word
    word_fail = defaultdict(lambda: {"total": 0, "fail": 0})
    for r in records:
        wf = word_fail[r["curr_word"]]
        wf["total"] += 1
        if not r["admissible"]:
            wf["fail"] += 1

    # Frequency tier: hapax (1), rare (2-9), medium (10-99), common (100+)
    def freq_tier(w):
        f = word_freq[w]
        if f <= 1:
            return "hapax"
        elif f <= 9:
            return "rare"
        elif f <= 99:
            return "medium"
        else:
            return "common"

    # Suffix class: last 1-2 characters
    def suffix_class(w):
        if len(w) >= 2:
            for suf in ["dy", "in", "ol", "or", "an", "al", "am"]:
                if w.endswith(suf):
                    return suf
        if w:
            return w[-1]
        return "?"

    # Length class
    def length_class(w):
        n = len(w)
        if n <= 3:
            return "short"
        elif n <= 5:
            return "medium"
        else:
            return "long"

    # Aggregate by class
    tier_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    suffix_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    length_counts = defaultdict(lambda: {"total": 0, "fail": 0})

    for r in records:
        w = r["curr_word"]
        fail = 0 if r["admissible"] else 1

        tc = tier_counts[freq_tier(w)]
        tc["total"] += 1
        tc["fail"] += fail

        sc = suffix_counts[suffix_class(w)]
        sc["total"] += 1
        sc["fail"] += fail

        lc = length_counts[length_class(w)]
        lc["total"] += 1
        lc["fail"] += fail

    def fmt_class(d):
        return {
            k: {
                "total": v["total"],
                "failures": v["fail"],
                "failure_rate": round(v["fail"] / v["total"], 4) if v["total"] else 0,
            }
            for k, v in sorted(d.items(), key=lambda x: x[1]["total"], reverse=True)
        }

    return {
        "by_frequency_tier": fmt_class(tier_counts),
        "by_suffix": fmt_class(suffix_counts),
        "by_length": fmt_class(length_counts),
    }


def window_occupancy_analysis(records, lattice_map, window_contents, corrections):
    """Failure rate by window and its properties."""
    # Per-window failure rate (window of the curr_word)
    win_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    for r in records:
        if r["curr_word"] in lattice_map:
            win = lattice_map[r["curr_word"]]
            wc = win_counts[win]
            wc["total"] += 1
            if not r["admissible"]:
                wc["fail"] += 1

    win_stats = []
    for win in range(NUM_WINDOWS):
        wc = win_counts[win]
        size = len(window_contents.get(win, []))
        correction = corrections.get(win, 0)
        fail_rate = wc["fail"] / wc["total"] if wc["total"] else 0
        win_stats.append({
            "window": win,
            "size": size,
            "correction": correction,
            "total": wc["total"],
            "failures": wc["fail"],
            "failure_rate": round(fail_rate, 4),
        })

    # Correlation: window size vs failure rate
    sizes = [ws["size"] for ws in win_stats if ws["total"] >= 10]
    rates = [ws["failure_rate"] for ws in win_stats if ws["total"] >= 10]
    if len(sizes) >= 5:
        rho_size, p_size = stats.spearmanr(sizes, rates)
    else:
        rho_size, p_size = None, None

    # Correlation: |correction| vs failure rate
    corrs = [abs(ws["correction"]) for ws in win_stats if ws["total"] >= 10]
    rates2 = [ws["failure_rate"] for ws in win_stats if ws["total"] >= 10]
    if len(corrs) >= 5:
        rho_corr, p_corr = stats.spearmanr(corrs, rates2)
    else:
        rho_corr, p_corr = None, None

    return {
        "per_window": win_stats,
        "size_vs_failure": {
            "rho": round(rho_size, 4) if rho_size is not None else None,
            "p_value": round(p_size, 4) if p_size is not None else None,
        },
        "correction_magnitude_vs_failure": {
            "rho": round(rho_corr, 4) if rho_corr is not None else None,
            "p_value": round(p_corr, 4) if p_corr is not None else None,
        },
    }


# ── Sprint 3: Diagnostic Synthesis ──────────────────────────────────────

def diagnostic_synthesis(records, burst, folio, position, word_class, window_occ):
    """Synthesize all analyses into a failure taxonomy."""
    total = len(records)
    total_fail = sum(1 for r in records if not r["admissible"])
    total_oov = sum(1 for r in records if r["oov"])

    # Positional: is failure rate flat or structured?
    pos_rates = [v["failure_rate"] for v in position.values()]
    pos_range = max(pos_rates) - min(pos_rates) if pos_rates else 0

    # Lexical: what fraction of failures come from hapax/rare words?
    freq_tiers = word_class["by_frequency_tier"]
    hapax_fails = freq_tiers.get("hapax", {}).get("failures", 0)
    rare_fails = freq_tiers.get("rare", {}).get("failures", 0)
    low_freq_fails = hapax_fails + rare_fails
    low_freq_frac = low_freq_fails / total_fail if total_fail else 0

    # Sequential: are failures clustered beyond random?
    burst_clustered = False
    if burst.get("clustering_test", {}).get("p_value") is not None:
        burst_clustered = burst["clustering_test"]["p_value"] < 0.001

    # OOV fraction
    oov_frac = total_oov / total if total else 0

    # Section variation
    section_counts = defaultdict(lambda: {"total": 0, "fail": 0})
    for r in records:
        sc = section_counts[r["section"]]
        sc["total"] += 1
        if not r["admissible"]:
            sc["fail"] += 1

    section_rates = {
        s: round(c["fail"] / c["total"], 4) if c["total"] else 0
        for s, c in section_counts.items()
    }
    section_range = max(section_rates.values()) - min(section_rates.values()) if section_rates else 0

    # Reducibility estimate
    reducibility = {
        "oov_tokens": total_oov,
        "oov_fraction": round(oov_frac, 4),
        "low_frequency_failures": low_freq_fails,
        "low_frequency_fraction": round(low_freq_frac, 4),
        "positional_range_pp": round(pos_range * 100, 1),
        "section_range_pp": round(section_range * 100, 1),
        "burst_clustered": bool(burst_clustered),
        "estimated_noise_fraction": round(oov_frac + low_freq_frac * 0.3, 4),
    }

    # Recommendations
    recommendations = []
    if oov_frac > 0.05:
        recommendations.append(
            "Expand vocabulary: OOV tokens account for "
            f"{oov_frac*100:.1f}% of failures. "
            "Increasing palette coverage could reduce residual."
        )
    if burst_clustered:
        recommendations.append(
            "Investigate burst regions: failures cluster beyond random expectation. "
            "These may correspond to sections with different production rules."
        )
    if section_range > 0.15:
        recommendations.append(
            f"Section variation is large ({section_range*100:.1f}pp range). "
            "Section-specific corrections may reduce the residual."
        )
    if low_freq_frac > 0.3:
        recommendations.append(
            f"Low-frequency words contribute {low_freq_frac*100:.1f}% of failures. "
            "The residual is partly a sparse-data artifact."
        )
    if not recommendations:
        recommendations.append(
            "The residual appears uniformly distributed with no dominant "
            "reducible category. Further lattice refinement has diminishing returns."
        )

    return {
        "total_transitions": total,
        "total_failures": total_fail,
        "overall_failure_rate": round(total_fail / total, 4) if total else 0,
        "oov_transitions": total_oov,
        "section_failure_rates": section_rates,
        "reducibility": reducibility,
        "recommendations": recommendations,
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14L: Residual Characterization[/bold magenta]")

    # 1. Load data
    console.print("Loading palette...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    console.print(f"  Palette: {len(lattice_map)} words, {len(window_contents)} windows")

    console.print("Loading corrections...")
    corrections = load_corrections(OFFSETS_PATH)
    nonzero = sum(1 for v in corrections.values() if v != 0)
    console.print(f"  Corrections: {len(corrections)} windows, {nonzero} non-zero")

    console.print("Loading corpus...")
    store = MetadataStore(DB_PATH)
    lines = load_lines_with_metadata(store)
    total_tokens = sum(len(l["tokens"]) for l in lines)
    console.print(f"  Corpus: {len(lines)} lines, {total_tokens} tokens")

    # 2. Build failure records
    console.print("\n[bold]Building per-transition failure records...[/bold]")
    records = build_failure_records(lines, lattice_map, corrections)
    total_fail = sum(1 for r in records if not r["admissible"])
    total_oov = sum(1 for r in records if r["oov"])
    console.print(f"  {len(records)} transitions, {total_fail} failures "
                  f"({total_fail/len(records)*100:.1f}%), {total_oov} OOV")

    # ── Sprint 1: Positional & Sequential ────────────────────────────

    console.print("\n[bold cyan]Sprint 1: Positional & Sequential Analysis[/bold cyan]")

    # Position within line
    console.print("\n[bold]Position-within-line failure rates...[/bold]")
    pos = position_analysis(records)
    pos_table = Table(title="Failure Rate by Position")
    pos_table.add_column("Position", justify="right")
    pos_table.add_column("Total", justify="right")
    pos_table.add_column("Failures", justify="right")
    pos_table.add_column("Rate", justify="right")
    for p_val, c in sorted(pos.items()):
        label = f"{p_val}" if p_val < 10 else "10+"
        pos_table.add_row(label, str(c["total"]), str(c["failures"]),
                          f"{c['failure_rate']*100:.1f}%")
    console.print(pos_table)

    # Burst analysis
    console.print("\n[bold]Sequential burst analysis...[/bold]")
    burst = burst_analysis(lines, lattice_map, corrections)
    if not burst.get("no_failures"):
        console.print(f"  Failure runs: {burst['num_runs']}")
        console.print(f"  Mean run length: {burst['mean_run_length']}")
        console.print(f"  Expected (independence): {burst['expected_mean_run_length']}")
        console.print(f"  Max run length: {burst['max_run_length']}")
        ct = burst["clustering_test"]
        if ct.get("chi2") is not None:
            sig = "CLUSTERED" if ct["p_value"] < 0.001 else "not clustered"
            console.print(f"  Chi-squared: {ct['chi2']}, p={ct['p_value']} ({sig})")

    # Folio analysis
    console.print("\n[bold]Folio-level failure rates...[/bold]")
    folio = folio_analysis(records)
    console.print(f"  {folio['num_folios']} folios, mean rate: "
                  f"{folio['mean_failure_rate']*100:.1f}% ± {folio['std_failure_rate']*100:.1f}pp")
    console.print("  Worst 5 folios:")
    for f in folio["top_10_worst"][:5]:
        console.print(f"    {f['folio_id']} ({f['section']}): "
                      f"{f['failure_rate']*100:.1f}% ({f['failures']}/{f['total']})")
    console.print("  Best 5 folios:")
    for f in folio["top_10_best"][:5]:
        console.print(f"    {f['folio_id']} ({f['section']}): "
                      f"{f['failure_rate']*100:.1f}% ({f['failures']}/{f['total']})")

    # Line length
    console.print("\n[bold]Line length vs failure rate...[/bold]")
    ll = line_length_analysis(records)
    if ll["correlation"].get("rho") is not None:
        console.print(f"  Correlation (Spearman): rho={ll['correlation']['rho']}, "
                      f"p={ll['correlation']['p_value']}")

    # ── Sprint 2: Lexical Analysis ───────────────────────────────────

    console.print("\n[bold cyan]Sprint 2: Lexical Analysis[/bold cyan]")

    # Per-word failure
    console.print("\n[bold]Per-word failure analysis...[/bold]")
    word_fail = word_failure_analysis(records, lattice_map)
    console.print(f"  Unique target words: {word_fail['unique_target_words']}")
    console.print(f"  Top-50 target/predecessor overlap: {word_fail['top50_overlap_count']} words")

    wf_table = Table(title="Top 10 Failure-Causing Target Words (by count)")
    wf_table.add_column("Word", style="cyan")
    wf_table.add_column("Total", justify="right")
    wf_table.add_column("Failures", justify="right")
    wf_table.add_column("Rate", justify="right")
    wf_table.add_column("In Palette", justify="right")
    for entry in word_fail["top_targets_by_count"][:10]:
        wf_table.add_row(
            entry["word"], str(entry["total"]), str(entry["failures"]),
            f"{entry['failure_rate']*100:.1f}%",
            "Y" if entry["in_palette"] else "N",
        )
    console.print(wf_table)

    # Word class
    console.print("\n[bold]Word class analysis...[/bold]")
    wc = word_class_analysis(records, lattice_map)

    wc_table = Table(title="Failure Rate by Frequency Tier")
    wc_table.add_column("Tier", style="cyan")
    wc_table.add_column("Total", justify="right")
    wc_table.add_column("Failures", justify="right")
    wc_table.add_column("Rate", justify="right")
    for tier, c in wc["by_frequency_tier"].items():
        wc_table.add_row(tier, str(c["total"]), str(c["failures"]),
                          f"{c['failure_rate']*100:.1f}%")
    console.print(wc_table)

    wc_table2 = Table(title="Failure Rate by Word Length")
    wc_table2.add_column("Length", style="cyan")
    wc_table2.add_column("Total", justify="right")
    wc_table2.add_column("Failures", justify="right")
    wc_table2.add_column("Rate", justify="right")
    for lclass, c in wc["by_length"].items():
        wc_table2.add_row(lclass, str(c["total"]), str(c["failures"]),
                           f"{c['failure_rate']*100:.1f}%")
    console.print(wc_table2)

    # Top suffixes
    console.print("\n  Top suffixes by failure count:")
    for suf, c in list(wc["by_suffix"].items())[:8]:
        console.print(f"    -{suf}: {c['failure_rate']*100:.1f}% "
                      f"({c['failures']}/{c['total']})")

    # Window occupancy
    console.print("\n[bold]Window occupancy vs failure...[/bold]")
    win_occ = window_occupancy_analysis(records, lattice_map, window_contents, corrections)
    sv = win_occ["size_vs_failure"]
    cv = win_occ["correction_magnitude_vs_failure"]
    if sv["rho"] is not None:
        console.print(f"  Window size vs failure rate: rho={sv['rho']}, p={sv['p_value']}")
    if cv["rho"] is not None:
        console.print(f"  |Correction| vs failure rate: rho={cv['rho']}, p={cv['p_value']}")

    # ── Sprint 3: Diagnostic Synthesis ───────────────────────────────

    console.print("\n[bold cyan]Sprint 3: Diagnostic Synthesis[/bold cyan]")
    synthesis = diagnostic_synthesis(records, burst, folio, pos, wc, win_occ)

    console.print(f"\n  Overall failure rate: {synthesis['overall_failure_rate']*100:.1f}%")
    console.print(f"  OOV transitions: {synthesis['oov_transitions']} "
                  f"({synthesis['reducibility']['oov_fraction']*100:.1f}%)")
    console.print(f"  Low-freq word failures: {synthesis['reducibility']['low_frequency_fraction']*100:.1f}%")
    console.print(f"  Positional range: {synthesis['reducibility']['positional_range_pp']:.1f}pp")
    console.print(f"  Section range: {synthesis['reducibility']['section_range_pp']:.1f}pp")

    console.print("\n  Section failure rates:")
    for s, r in sorted(synthesis["section_failure_rates"].items(), key=lambda x: x[1]):
        console.print(f"    {s}: {r*100:.1f}%")

    console.print("\n[bold yellow]Recommendations:[/bold yellow]")
    for rec in synthesis["recommendations"]:
        console.print(f"  • {rec}")

    # ── Save Results ─────────────────────────────────────────────────

    results = {
        "sprint1_positional": {
            "position_within_line": pos,
            "burst_analysis": burst,
            "folio_failure_rates": {
                "num_folios": folio["num_folios"],
                "mean_rate": folio["mean_failure_rate"],
                "std_rate": folio["std_failure_rate"],
                "top_10_worst": folio["top_10_worst"],
                "top_10_best": folio["top_10_best"],
            },
            "line_length": ll,
        },
        "sprint2_lexical": {
            "word_failure": {
                "unique_targets": word_fail["unique_target_words"],
                "unique_predecessors": word_fail["unique_pred_words"],
                "top50_overlap": word_fail["top50_overlap_count"],
                "top_targets_by_count": word_fail["top_targets_by_count"][:20],
                "top_targets_by_rate": word_fail["top_targets_by_rate"][:20],
                "top_predecessors_by_count": word_fail["top_predecessors_by_count"][:20],
            },
            "word_class": wc,
            "window_occupancy": {
                "size_vs_failure": win_occ["size_vs_failure"],
                "correction_vs_failure": win_occ["correction_magnitude_vs_failure"],
            },
        },
        "sprint3_synthesis": synthesis,
    }

    with active_run(config={"seed": 42, "command": "run_14zd_residual_characterization"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
