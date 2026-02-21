"""
Phase 14N — Physical Integration Analysis

Connects three independent physical signals that have never been jointly analyzed:
  1. Offset corrections (Phase 14I): 50 per-window signed drift values
  2. Mechanical slips (Phase 12): 202 verified vertical offsets
  3. Geometric layout (Phase 16): 81.5% grid efficiency

Tests whether these signals are mutually consistent with a single physical device.

Sprint 1: Offset correction topology (Moran's I, FFT, runs test, magnitude profile)
Sprint 2: Slip-offset correlation (per-window slip rate, Spearman, Mann-Whitney, clustering)
Sprint 3: Device geometry inference (volvelle vs tabula vs grille, BIC comparison)
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
from scipy.optimize import minimize_scalar

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

console = Console()

# ── Constants ──────────────────────────────────────────────────────────
NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
SLIPS_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/physical_integration.json"

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
    m = re.search(r"f(\d+)", folio_id)
    return int(m.group(1)) if m else 0


def get_section(folio_num: int) -> str:
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


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


def load_slips(path):
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data).get("slips", [])


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
        current_folio = None
        current_line_id = None
        folios = []
        for content, folio_id, line_id, _line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    lines.append(current_tokens)
                    folios.append(current_folio)
                current_tokens = []
            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id
        if current_tokens:
            lines.append(current_tokens)
            folios.append(current_folio)
        return lines, folios
    finally:
        session.close()


# ── Sprint 1: Offset Correction Topology ──────────────────────────────

def compute_morans_i(values, n_permutations=10000):
    """Compute Moran's I for values on a circular lattice (adjacent neighbors)."""
    n = len(values)
    x = np.array(values, dtype=float)
    x_bar = x.mean()
    x_dev = x - x_bar

    # Circular adjacency weight matrix (each position connected to ±1)
    # W_ij = 1 if |i-j| == 1 (mod n)
    numerator = 0.0
    for i in range(n):
        for j_offset in [-1, 1]:
            j = (i + j_offset) % n
            numerator += x_dev[i] * x_dev[j]

    denominator = np.sum(x_dev ** 2)
    w_sum = 2 * n  # Each of n positions has 2 neighbors
    observed_i = (n / w_sum) * (numerator / denominator) if denominator > 0 else 0.0

    # Permutation test
    rng = np.random.RandomState(42)
    count_extreme = 0
    for _ in range(n_permutations):
        perm = rng.permutation(x)
        p_dev = perm - perm.mean()
        p_num = 0.0
        for i in range(n):
            for j_offset in [-1, 1]:
                j = (i + j_offset) % n
                p_num += p_dev[i] * p_dev[j]
        p_denom = np.sum(p_dev ** 2)
        p_i = (n / w_sum) * (p_num / p_denom) if p_denom > 0 else 0.0
        if p_i >= observed_i:
            count_extreme += 1

    p_value = count_extreme / n_permutations
    return observed_i, p_value


def compute_fft_analysis(values):
    """FFT periodicity analysis on circular correction sequence."""
    x = np.array(values, dtype=float)
    n = len(x)
    fft_vals = np.fft.fft(x)
    power = np.abs(fft_vals) ** 2
    # Only first half (symmetric for real input)
    freqs = np.fft.fftfreq(n)
    half = n // 2

    # Skip DC component (k=0)
    power_half = power[1:half]
    freq_half = freqs[1:half]
    periods = 1.0 / np.abs(freq_half)

    dominant_idx = np.argmax(power_half)
    dominant_freq_k = dominant_idx + 1  # k=1 is first non-DC
    dominant_period = n / dominant_freq_k
    dominant_power = power_half[dominant_idx]
    total_power = np.sum(power_half)
    power_ratio = dominant_power / total_power if total_power > 0 else 0

    spectrum = []
    for i in range(min(10, len(power_half))):
        spectrum.append({
            "k": i + 1,
            "period": round(n / (i + 1), 2),
            "power": round(float(power_half[i]), 2),
            "power_fraction": round(float(power_half[i] / total_power), 4) if total_power > 0 else 0,
        })

    return {
        "dominant_k": int(dominant_freq_k),
        "dominant_period": round(dominant_period, 2),
        "dominant_power": round(float(dominant_power), 2),
        "dominant_power_fraction": round(power_ratio, 4),
        "total_power": round(float(total_power), 2),
        "spectrum_top10": spectrum,
    }


def compute_runs_test(values):
    """Runs test for sign changes in correction sequence."""
    signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in values]
    # Count sign changes (treating 0 as boundary)
    n_changes = 0
    runs = 1
    for i in range(1, len(signs)):
        if signs[i] != signs[i - 1]:
            n_changes += 1
            runs += 1

    # Identify contiguous zones
    zones = []
    current_sign = signs[0]
    start = 0
    for i in range(1, len(signs)):
        if signs[i] != current_sign:
            zones.append({"start": start, "end": i - 1,
                          "sign": "+" if current_sign > 0 else ("-" if current_sign < 0 else "0"),
                          "length": i - start})
            current_sign = signs[i]
            start = i
    zones.append({"start": start, "end": len(signs) - 1,
                  "sign": "+" if current_sign > 0 else ("-" if current_sign < 0 else "0"),
                  "length": len(signs) - start})

    # Anchors (zero-correction windows)
    anchors = [i for i, v in enumerate(values) if v == 0]

    # Transition points (where sign changes)
    transitions = [i for i in range(1, len(signs)) if signs[i] != signs[i - 1]]

    # Expected runs under independence (Wald-Wolfowitz)
    n_pos = sum(1 for s in signs if s > 0)
    n_neg = sum(1 for s in signs if s < 0)
    n_zero = sum(1 for s in signs if s == 0)
    n = len(signs)

    return {
        "num_runs": runs,
        "num_sign_changes": n_changes,
        "num_zones": len(zones),
        "zones": zones,
        "anchors": anchors,
        "anchor_count": len(anchors),
        "transitions": transitions,
        "n_positive": n_pos,
        "n_negative": n_neg,
        "n_zero": n_zero,
    }


def compute_magnitude_profile(corrections):
    """Mean |correction| by position decile."""
    n = len(corrections)
    decile_size = n // 10
    profile = []
    for d in range(10):
        start = d * decile_size
        end = start + decile_size if d < 9 else n
        vals = [abs(corrections[i]) for i in range(start, end)]
        profile.append({
            "decile": d,
            "windows": f"{start}-{end - 1}",
            "mean_abs_correction": round(np.mean(vals), 2),
            "max_abs_correction": int(max(vals)),
            "min_abs_correction": int(min(vals)),
        })
    return profile


def sprint1_offset_topology(corrections_dict):
    """Sprint 1: Analyze the spatial structure of offset corrections."""
    console.rule("[bold blue]Sprint 1: Offset Correction Topology")

    # Ordered correction values
    corr_values = [corrections_dict.get(i, 0) for i in range(NUM_WINDOWS)]

    # 1.1 Moran's I
    console.print("Computing Moran's I (10K permutations)...")
    morans_i, morans_p = compute_morans_i(corr_values)
    console.print(f"  Moran's I = {morans_i:.4f}, p = {morans_p:.4f}")
    if morans_p < 0.01:
        console.print("  [green]Strongly spatially autocorrelated[/green]")
    elif morans_p < 0.05:
        console.print("  [yellow]Marginally spatially autocorrelated[/yellow]")
    else:
        console.print("  [red]Not spatially autocorrelated[/red]")

    # 1.2 FFT
    console.print("\nFFT periodicity analysis...")
    fft_result = compute_fft_analysis(corr_values)
    console.print(f"  Dominant frequency: k={fft_result['dominant_k']} "
                  f"(period={fft_result['dominant_period']:.1f} windows)")
    console.print(f"  Power fraction: {fft_result['dominant_power_fraction']:.1%}")

    t = Table(title="Power Spectrum (top 10)")
    t.add_column("k", justify="right")
    t.add_column("Period", justify="right")
    t.add_column("Power", justify="right")
    t.add_column("Fraction", justify="right")
    for entry in fft_result["spectrum_top10"]:
        t.add_row(str(entry["k"]), f"{entry['period']:.1f}",
                  f"{entry['power']:.1f}", f"{entry['power_fraction']:.1%}")
    console.print(t)

    # Physical interpretation
    if fft_result["dominant_k"] == 1:
        fft_interp = "single_cycle_drift"
        console.print("  Interpretation: Single-cycle drift — consistent with circular device rotation")
    elif fft_result["dominant_k"] == 2:
        fft_interp = "two_cycle_fold"
        console.print("  Interpretation: Two-cycle pattern — consistent with folded/bilateral device")
    else:
        fft_interp = f"multi_cycle_k{fft_result['dominant_k']}"
        console.print(f"  Interpretation: Multi-cycle pattern (k={fft_result['dominant_k']})")

    # 1.3 Runs test / phase structure
    console.print("\nPhase structure characterization...")
    runs_result = compute_runs_test(corr_values)
    console.print(f"  Zones: {runs_result['num_zones']}")
    console.print(f"  Sign changes: {runs_result['num_sign_changes']}")
    console.print(f"  Anchors (zero correction): {runs_result['anchor_count']} "
                  f"at windows {runs_result['anchors']}")
    console.print(f"  Positive windows: {runs_result['n_positive']}, "
                  f"Negative: {runs_result['n_negative']}, "
                  f"Zero: {runs_result['n_zero']}")

    for z in runs_result["zones"]:
        console.print(f"    Zone {z['sign']}: windows {z['start']}-{z['end']} "
                      f"(length {z['length']})")

    # 1.4 Magnitude profile
    console.print("\nCorrection magnitude by position decile...")
    mag_profile = compute_magnitude_profile(corr_values)
    t2 = Table(title="Magnitude Profile")
    t2.add_column("Decile", justify="right")
    t2.add_column("Windows", justify="center")
    t2.add_column("Mean |corr|", justify="right")
    t2.add_column("Max |corr|", justify="right")
    for entry in mag_profile:
        t2.add_row(str(entry["decile"]), entry["windows"],
                   f"{entry['mean_abs_correction']:.1f}",
                   str(entry["max_abs_correction"]))
    console.print(t2)

    # Classify shape
    means = [p["mean_abs_correction"] for p in mag_profile]
    if means[4] > means[0] and means[4] > means[9]:
        shape = "peaked_center"
    elif means[0] > means[9]:
        shape = "monotonic_decreasing"
    elif means[9] > means[0]:
        shape = "monotonic_increasing"
    else:
        shape = "flat_or_irregular"
    console.print(f"  Profile shape: {shape}")

    return {
        "morans_i": round(morans_i, 4),
        "morans_p": round(morans_p, 4),
        "spatially_autocorrelated": morans_p < 0.05,
        "fft": fft_result,
        "fft_interpretation": fft_interp,
        "phase_structure": runs_result,
        "magnitude_profile": mag_profile,
        "magnitude_shape": shape,
        "correction_values": corr_values,
    }


# ── Sprint 2: Slip-Offset Correlation ─────────────────────────────────

def sprint2_slip_correlation(corrections_dict, slips, lattice_map, lines, folios):
    """Sprint 2: Correlate mechanical slips with offset corrections."""
    console.rule("[bold blue]Sprint 2: Slip-Offset Correlation")

    corr_values = [corrections_dict.get(i, 0) for i in range(NUM_WINDOWS)]

    # Count tokens per window for normalization
    window_token_counts = Counter()
    for line in lines:
        for word in line:
            if word in lattice_map:
                window_token_counts[lattice_map[word]] += 1

    # 2.1 Map slips to windows
    console.print("Mapping slips to windows...")
    slip_windows = []
    unmapped = 0
    for slip in slips:
        word = slip["word"]
        if word in lattice_map:
            win = lattice_map[word]
            slip_windows.append({
                "word": word,
                "window": win,
                "line_index": slip["line_index"],
                "token_index": slip["token_index"],
                "correction": corrections_dict.get(win, 0),
            })
        else:
            unmapped += 1

    console.print(f"  Mapped: {len(slip_windows)}/{len(slips)} slips "
                  f"({unmapped} unmapped OOV)")

    # Per-window slip count and rate
    window_slip_counts = Counter(s["window"] for s in slip_windows)
    per_window = []
    for w in range(NUM_WINDOWS):
        sc = window_slip_counts.get(w, 0)
        tc = window_token_counts.get(w, 0)
        rate = sc / tc if tc > 0 else 0
        per_window.append({
            "window": w,
            "slip_count": sc,
            "token_count": tc,
            "slip_rate": round(rate, 6),
            "correction": corrections_dict.get(w, 0),
            "abs_correction": abs(corrections_dict.get(w, 0)),
        })

    # Top 10 by slip rate
    sorted_pw = sorted(per_window, key=lambda x: x["slip_rate"], reverse=True)
    t = Table(title="Top 10 Windows by Slip Rate")
    t.add_column("Window", justify="right")
    t.add_column("Slips", justify="right")
    t.add_column("Tokens", justify="right")
    t.add_column("Rate", justify="right")
    t.add_column("Correction", justify="right")
    for entry in sorted_pw[:10]:
        t.add_row(str(entry["window"]), str(entry["slip_count"]),
                  str(entry["token_count"]), f"{entry['slip_rate']:.4f}",
                  str(entry["correction"]))
    console.print(t)

    # 2.2 Spearman: slip rate vs |correction|
    slip_rates = [pw["slip_rate"] for pw in per_window]
    abs_corrections = [pw["abs_correction"] for pw in per_window]

    # Only include windows with tokens
    valid_idx = [i for i in range(NUM_WINDOWS) if per_window[i]["token_count"] > 0]
    sr_valid = [slip_rates[i] for i in valid_idx]
    ac_valid = [abs_corrections[i] for i in valid_idx]

    rho_magnitude, p_magnitude = stats.spearmanr(sr_valid, ac_valid)
    console.print(f"\n  Slip rate vs |correction|: rho={rho_magnitude:.4f}, p={p_magnitude:.4f}")

    # 2.3 Mann-Whitney: positive vs negative correction windows
    pos_rates = [slip_rates[i] for i in valid_idx if corr_values[i] > 0]
    neg_rates = [slip_rates[i] for i in valid_idx if corr_values[i] < 0]
    zero_rates = [slip_rates[i] for i in valid_idx if corr_values[i] == 0]

    if pos_rates and neg_rates:
        u_stat, p_sign = stats.mannwhitneyu(pos_rates, neg_rates, alternative="two-sided")
        console.print(f"  Positive vs negative windows: U={u_stat:.1f}, p={p_sign:.4f}")
        console.print(f"    Positive mean rate: {np.mean(pos_rates):.4f} (n={len(pos_rates)})")
        console.print(f"    Negative mean rate: {np.mean(neg_rates):.4f} (n={len(neg_rates)})")
        if zero_rates:
            console.print(f"    Zero mean rate: {np.mean(zero_rates):.4f} (n={len(zero_rates)})")
    else:
        u_stat, p_sign = 0.0, 1.0
        console.print("  [yellow]Insufficient data for sign comparison[/yellow]")

    # 2.4 Slip position × correction sign
    console.print("\n  Slip position × correction sign cross-tabulation...")
    cross_tab = defaultdict(lambda: defaultdict(int))
    for s in slip_windows:
        pos = min(s["token_index"], 5)  # bin positions 0-4, 5+
        sign = "positive" if s["correction"] > 0 else ("negative" if s["correction"] < 0 else "zero")
        cross_tab[pos][sign] += 1

    t2 = Table(title="Position × Correction Sign")
    t2.add_column("Position", justify="right")
    t2.add_column("Positive", justify="right")
    t2.add_column("Negative", justify="right")
    t2.add_column("Zero", justify="right")
    for pos in sorted(cross_tab.keys()):
        t2.add_row(str(pos) if pos < 5 else "5+",
                   str(cross_tab[pos].get("positive", 0)),
                   str(cross_tab[pos].get("negative", 0)),
                   str(cross_tab[pos].get("zero", 0)))
    console.print(t2)

    # 2.5 Temporal clustering
    console.print("\n  Temporal clustering of slips...")
    slip_line_indices = sorted(set(s["line_index"] for s in slip_windows))
    if len(slip_line_indices) > 1:
        intervals = [slip_line_indices[i + 1] - slip_line_indices[i]
                     for i in range(len(slip_line_indices) - 1)]
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        # Under independence, intervals should be geometric with mean = N/n
        expected_mean = len(lines) / len(slip_line_indices)
        cv = std_interval / mean_interval if mean_interval > 0 else 0
        console.print(f"    Mean inter-slip interval: {mean_interval:.1f} lines")
        console.print(f"    Expected under independence: {expected_mean:.1f} lines")
        console.print(f"    CV (coefficient of variation): {cv:.2f}")
        # CV > 1 suggests clustering; CV ≈ 1 is geometric (random)
        if cv > 1.2:
            temporal_pattern = "clustered"
        elif cv < 0.8:
            temporal_pattern = "regular"
        else:
            temporal_pattern = "random"
        console.print(f"    Temporal pattern: {temporal_pattern}")

        # Folio-level clustering
        slip_folios = []
        for s in slip_windows:
            li = s["line_index"]
            if 0 <= li < len(folios):
                slip_folios.append(folios[li])
        folio_slip_counts = Counter(slip_folios)
        top5_folios = folio_slip_counts.most_common(5)
        console.print("    Top 5 folios by slip count: "
                      + ", ".join(f"{f}({c})" for f, c in top5_folios))
    else:
        mean_interval = 0
        expected_mean = 0
        cv = 0
        temporal_pattern = "insufficient_data"
        intervals = []

    return {
        "slips_mapped": len(slip_windows),
        "slips_unmapped": unmapped,
        "per_window_summary": per_window,
        "correlation_magnitude": {
            "spearman_rho": round(rho_magnitude, 4),
            "p_value": round(p_magnitude, 4),
        },
        "sign_comparison": {
            "mann_whitney_u": round(u_stat, 2),
            "p_value": round(p_sign, 4),
            "positive_mean_rate": round(float(np.mean(pos_rates)), 6) if pos_rates else 0,
            "negative_mean_rate": round(float(np.mean(neg_rates)), 6) if neg_rates else 0,
            "n_positive_windows": len(pos_rates),
            "n_negative_windows": len(neg_rates),
        },
        "position_cross_tab": {str(k): dict(v) for k, v in cross_tab.items()},
        "temporal_clustering": {
            "mean_interval": round(mean_interval, 2),
            "expected_interval": round(expected_mean, 2),
            "cv": round(cv, 4),
            "pattern": temporal_pattern,
            "n_distinct_lines_with_slips": len(slip_line_indices),
        },
    }


# ── Sprint 3: Device Geometry Inference ───────────────────────────────

def fit_volvelle(observed):
    """Fit a sinusoidal model (circular volvelle): A * sin(2π·i/N + φ)."""
    n = len(observed)
    x = np.array(observed, dtype=float)

    best_rss = np.inf
    best_params = {}

    # Grid search over phase, optimize amplitude analytically
    for phi_deg in range(0, 360, 5):
        phi = np.radians(phi_deg)
        basis = np.array([np.sin(2 * np.pi * i / n + phi) for i in range(n)])
        # Optimal amplitude: A = (x · basis) / (basis · basis)
        dot_xb = np.dot(x, basis)
        dot_bb = np.dot(basis, basis)
        if dot_bb > 0:
            a = dot_xb / dot_bb
        else:
            a = 0.0
        predicted = a * basis
        rss = np.sum((x - predicted) ** 2)
        if rss < best_rss:
            best_rss = rss
            best_params = {"amplitude": round(float(a), 2),
                           "phase_deg": phi_deg}

    predicted = best_params["amplitude"] * np.array(
        [np.sin(2 * np.pi * i / n + np.radians(best_params["phase_deg"]))
         for i in range(n)])

    return {
        "model": "volvelle",
        "geometry": "rotating_disc",
        "n_params": 2,
        "params": best_params,
        "rss": round(float(best_rss), 2),
        "predicted": [round(float(p), 2) for p in predicted],
    }


def fit_tabula(observed):
    """Fit a 10×5 grid model: correction = row_drift[r] + col_drift[c]."""
    n = len(observed)
    x = np.array(observed, dtype=float)
    rows, cols = 10, 5

    # Each window i maps to row i//cols, col i%cols
    # Fit: x_i = a_r + b_c (additive row+column effects)
    # Use least-squares via pseudo-inverse
    design = np.zeros((n, rows + cols))
    for i in range(n):
        r = i // cols
        c = i % cols
        design[i, r] = 1.0
        design[i, rows + c] = 1.0

    # Solve via lstsq
    coeffs, _, _, _ = np.linalg.lstsq(design, x, rcond=None)
    predicted = design @ coeffs
    rss = float(np.sum((x - predicted) ** 2))

    row_effects = [round(float(coeffs[r]), 2) for r in range(rows)]
    col_effects = [round(float(coeffs[rows + c]), 2) for c in range(cols)]

    return {
        "model": "tabula",
        "geometry": "10x5_grid",
        "n_params": rows + cols,  # 15 (but rank-deficient by 1 → 14 effective)
        "params": {"row_effects": row_effects, "col_effects": col_effects},
        "rss": round(rss, 2),
        "predicted": [round(float(p), 2) for p in predicted],
    }


def fit_grille(observed):
    """Fit a linear model (sliding grille): correction = slope * i + intercept."""
    n = len(observed)
    x = np.array(observed, dtype=float)
    positions = np.arange(n, dtype=float)

    slope, intercept, r_value, p_value, std_err = stats.linregress(positions, x)
    predicted = slope * positions + intercept
    rss = float(np.sum((x - predicted) ** 2))

    return {
        "model": "grille",
        "geometry": "linear_strip",
        "n_params": 2,
        "params": {"slope": round(float(slope), 4),
                    "intercept": round(float(intercept), 2)},
        "rss": round(rss, 2),
        "r_squared": round(float(r_value ** 2), 4),
        "predicted": [round(float(p), 2) for p in predicted],
    }


def compute_bic(n, rss, k):
    """Bayesian Information Criterion: n·ln(RSS/n) + k·ln(n)."""
    if rss <= 0 or n <= 0:
        return float("inf")
    return n * math.log(rss / n) + k * math.log(n)


def sprint3_device_inference(corrections_dict, sprint1_results, sprint2_results):
    """Sprint 3: Compare candidate device geometries."""
    console.rule("[bold blue]Sprint 3: Device Geometry Inference")

    observed = [corrections_dict.get(i, 0) for i in range(NUM_WINDOWS)]
    n = len(observed)

    # Fit each candidate model
    volvelle = fit_volvelle(observed)
    tabula = fit_tabula(observed)
    grille = fit_grille(observed)

    models = [volvelle, tabula, grille]

    # Compute BIC for each
    for m in models:
        m["bic"] = round(compute_bic(n, m["rss"], m["n_params"]), 2)

    # Rank by BIC
    models.sort(key=lambda m: m["bic"])

    t = Table(title="Device Model Comparison")
    t.add_column("Model", style="cyan")
    t.add_column("Geometry")
    t.add_column("Params", justify="right")
    t.add_column("RSS", justify="right")
    t.add_column("BIC", justify="right")
    t.add_column("Rank", justify="right")
    for rank, m in enumerate(models, 1):
        style = "bold green" if rank == 1 else ""
        t.add_row(m["model"], m["geometry"], str(m["n_params"]),
                  f"{m['rss']:.1f}", f"{m['bic']:.1f}", str(rank),
                  style=style)
    console.print(t)

    best_model = models[0]
    console.print(f"\n  Best-fit model: [bold]{best_model['model']}[/bold] "
                  f"(BIC={best_model['bic']:.1f})")

    # BIC differences
    bic_deltas = {m["model"]: round(m["bic"] - best_model["bic"], 2) for m in models}
    console.print(f"  BIC deltas from best: {bic_deltas}")

    # Physical constraints summary
    console.print("\n[bold]Physical Constraints Summary:[/bold]")

    # From Sprint 1
    spatial = "spatially clustered" if sprint1_results["spatially_autocorrelated"] else "random"
    console.print(f"  Spatial structure: {spatial} (Moran's I={sprint1_results['morans_i']:.3f})")
    console.print(f"  Periodicity: {sprint1_results['fft_interpretation']}")
    console.print(f"  Phase structure: {sprint1_results['phase_structure']['num_zones']} zones, "
                  f"{sprint1_results['phase_structure']['anchor_count']} anchor points")
    console.print(f"  Magnitude shape: {sprint1_results['magnitude_shape']}")

    # From Sprint 2
    rho = sprint2_results["correlation_magnitude"]["spearman_rho"]
    p = sprint2_results["correlation_magnitude"]["p_value"]
    console.print(f"  Slip-offset correlation: rho={rho:.3f}, p={p:.4f}")
    console.print(f"  Temporal slip pattern: {sprint2_results['temporal_clustering']['pattern']}")

    # From Sprint 3
    console.print(f"  Best geometry: {best_model['model']} ({best_model['geometry']})")

    # Physical profile
    physical_profile = {
        "best_device_model": best_model["model"],
        "best_device_geometry": best_model["geometry"],
        "spatial_autocorrelation": sprint1_results["spatially_autocorrelated"],
        "periodicity": sprint1_results["fft_interpretation"],
        "n_phase_zones": sprint1_results["phase_structure"]["num_zones"],
        "n_anchors": sprint1_results["phase_structure"]["anchor_count"],
        "anchor_positions": sprint1_results["phase_structure"]["anchors"],
        "magnitude_shape": sprint1_results["magnitude_shape"],
        "slip_offset_rho": rho,
        "slip_offset_p": p,
        "slip_temporal_pattern": sprint2_results["temporal_clustering"]["pattern"],
        "bic_ranking": [{"model": m["model"], "bic": m["bic"],
                         "delta_bic": bic_deltas[m["model"]]} for m in models],
    }

    return {
        "models": {m["model"]: {k: v for k, v in m.items() if k != "predicted"}
                   for m in models},
        "model_predictions": {m["model"]: m["predicted"] for m in models},
        "bic_deltas": bic_deltas,
        "best_model": best_model["model"],
        "physical_profile": physical_profile,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 14N: Physical Integration Analysis")

    # Load all inputs
    console.print("Loading data...")
    corrections = load_corrections(OFFSETS_PATH)
    slips = load_slips(SLIPS_PATH)
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    store = MetadataStore(DB_PATH)
    lines, folios = load_lines(store)

    console.print(f"  Corrections: {len(corrections)} windows")
    console.print(f"  Slips: {len(slips)} verified")
    console.print(f"  Palette: {len(lattice_map)} words")
    console.print(f"  Corpus: {len(lines)} lines")

    # Sprint 1
    s1 = sprint1_offset_topology(corrections)

    # Sprint 2
    s2 = sprint2_slip_correlation(corrections, slips, lattice_map, lines, folios)

    # Sprint 3
    s3 = sprint3_device_inference(corrections, s1, s2)

    # Assemble results
    results = {
        "sprint1_offset_topology": {
            k: v for k, v in s1.items() if k != "correction_values"
        },
        "sprint2_slip_correlation": s2,
        "sprint3_device_inference": {
            k: v for k, v in s3.items() if k != "model_predictions"
        },
        "physical_profile": s3["physical_profile"],
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14zf_physical_integration"}):
        main()
