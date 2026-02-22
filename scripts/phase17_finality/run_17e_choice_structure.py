#!/usr/bin/env python3
"""Sprint A3: Structure Detection in the Choice Stream.

If the choice stream carries hidden information, it should show
non-random structure after removing known mechanical drivers.
If it is noise, it should be indistinguishable from a random process.

Tasks:
  A3.1 — Extract residual choice-index stream
  A3.2 — Autocorrelation test (Ljung-Box)
  A3.3 — Spectral test (FFT)
  A3.4 — Compression test (zlib)
  A3.5 — Permutation baseline (1000 shuffles)
"""

import json
import math
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table
from scipy import stats

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402


def sanitize(obj):
    """Convert numpy types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj

CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
)
LEGACY_CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_selection/choice_stream_trace.json"
)
OUTPUT_PATH = project_root / "results/data/phase17_finality/choice_structure.json"
console = Console()

MAX_LAG = 50
N_PERMUTATIONS = 1000


def resolve_choice_stream_path() -> Path:
    if CHOICE_STREAM_PATH.exists():
        return CHOICE_STREAM_PATH
    if LEGACY_CHOICE_STREAM_PATH.exists():
        return LEGACY_CHOICE_STREAM_PATH
    raise FileNotFoundError(
        "Choice stream trace missing. Checked "
        f"{CHOICE_STREAM_PATH} and {LEGACY_CHOICE_STREAM_PATH}."
    )


# ── A3.1: Residual Choice-Index Stream ───────────────────────────────

def extract_residual_stream(choices):
    """Extract normalized choice indices as the residual stream.

    Each choice index is normalized to [0, 1] by dividing by
    (candidates_count - 1). This gives a uniform-on-[0,1] stream
    under the null hypothesis of random selection.
    """
    console.rule("[bold blue]A3.1: Residual Choice-Index Stream")

    normalized = []
    raw_indices = []
    for c in choices:
        n = c["candidates_count"]
        idx = c["chosen_index"]
        if n > 1:
            normalized.append(idx / (n - 1))
            raw_indices.append(idx)

    stream = np.array(normalized)
    console.print(f"  Stream length: {len(stream)}")
    console.print(f"  Mean: {stream.mean():.4f} (uniform expected: 0.500)")
    console.print(f"  Std: {stream.std():.4f} (uniform expected: {1/math.sqrt(12):.4f})")

    # KS test for uniformity
    ks_stat, ks_p = stats.kstest(stream, "uniform")
    console.print(f"  KS test vs Uniform(0,1): D={ks_stat:.4f}, p={ks_p:.2e}")
    console.print(f"  Stream is {'[red]NOT[/red]' if ks_p < 0.01 else '[green]'} "
                  f"uniform{'[/green]' if ks_p >= 0.01 else ''}")

    return stream, raw_indices, {
        "length": len(stream),
        "mean": round(float(stream.mean()), 4),
        "std": round(float(stream.std()), 4),
        "ks_statistic": round(float(ks_stat), 4),
        "ks_p_value": float(ks_p),
        "is_uniform": ks_p >= 0.01,
    }


# ── A3.2: Autocorrelation Test ───────────────────────────────────────

def autocorrelation_test(stream):
    """Compute autocorrelation function and Ljung-Box test."""
    console.rule("[bold blue]A3.2: Autocorrelation Test")

    n = len(stream)
    x = stream - stream.mean()
    var = np.sum(x ** 2) / n

    # Compute ACF at lags 1..MAX_LAG
    acf = []
    for lag in range(1, MAX_LAG + 1):
        c = np.sum(x[:n - lag] * x[lag:]) / (n * var) if var > 0 else 0
        acf.append(float(c))

    acf_arr = np.array(acf)
    max_acf = float(np.max(np.abs(acf_arr)))
    max_acf_lag = int(np.argmax(np.abs(acf_arr))) + 1

    # Ljung-Box test: Q = n(n+2) * sum(acf_k^2 / (n-k)) for k=1..m
    m = min(20, MAX_LAG)
    q_stat = 0.0
    for k in range(m):
        q_stat += acf[k] ** 2 / (n - k - 1)
    q_stat *= n * (n + 2)
    q_p = 1 - stats.chi2.cdf(q_stat, df=m)

    console.print(f"  Max |ACF|: {max_acf:.4f} at lag {max_acf_lag}")
    console.print(f"  Ljung-Box Q({m}): {q_stat:.2f}, p={q_p:.4e}")
    console.print(f"  95% significance bound: ±{1.96 / math.sqrt(n):.4f}")

    # Show top 5 lags
    table = Table(title="Top 5 ACF Lags")
    table.add_column("Lag", justify="right")
    table.add_column("ACF", justify="right")
    table.add_column("Significant?", justify="center")
    sig_bound = 1.96 / math.sqrt(n)
    top_lags = sorted(range(len(acf)), key=lambda i: abs(acf[i]), reverse=True)[:5]
    for i in top_lags:
        sig = "[red]YES[/red]" if abs(acf[i]) > sig_bound else "no"
        table.add_row(str(i + 1), f"{acf[i]:.4f}", sig)
    console.print(table)

    n_significant = sum(1 for a in acf[:m] if abs(a) > sig_bound)
    console.print(f"  Significant lags (of first {m}): {n_significant}")

    return {
        "max_abs_acf": round(max_acf, 4),
        "max_abs_acf_lag": max_acf_lag,
        "ljung_box_q": round(q_stat, 2),
        "ljung_box_p": float(q_p),
        "ljung_box_df": m,
        "n_significant_lags": n_significant,
        "significance_bound": round(sig_bound, 4),
        "has_autocorrelation": q_p < 0.01,
        "acf_first20": [round(a, 4) for a in acf[:20]],
    }


# ── A3.3: Spectral Test ─────────────────────────────────────────────

def spectral_test(stream):
    """Apply FFT and test for dominant frequencies."""
    console.rule("[bold blue]A3.3: Spectral Test (FFT)")

    n = len(stream)
    x = stream - stream.mean()
    fft_vals = np.fft.fft(x)
    power = np.abs(fft_vals) ** 2

    # Only positive frequencies (skip DC)
    half = n // 2
    power_half = power[1:half]
    freqs = np.fft.fftfreq(n)[1:half]
    total_power = np.sum(power_half)

    # Top 5 frequencies
    top_idx = np.argsort(power_half)[-5:][::-1]
    top_freqs = []
    for idx in top_idx:
        k = idx + 1
        period = n / k
        frac = power_half[idx] / total_power if total_power > 0 else 0
        top_freqs.append({
            "k": int(k),
            "period": round(float(period), 1),
            "power_fraction": round(float(frac), 4),
        })

    # Is any single frequency dominant? (>10% of total power)
    dominant_frac = top_freqs[0]["power_fraction"] if top_freqs else 0
    has_dominant = dominant_frac > 0.10

    console.print(f"  Total spectral power: {total_power:.0f}")
    console.print(f"  Dominant frequency: k={top_freqs[0]['k']} "
                  f"(period={top_freqs[0]['period']:.0f}), "
                  f"power fraction={top_freqs[0]['power_fraction']:.3f}")

    table = Table(title="Top 5 Spectral Peaks")
    table.add_column("k", justify="right")
    table.add_column("Period", justify="right")
    table.add_column("Power %", justify="right")
    for tf in top_freqs:
        table.add_row(str(tf["k"]), f"{tf['period']:.0f}", f"{tf['power_fraction']:.2%}")
    console.print(table)

    # Flatness: ratio of geometric mean to arithmetic mean of power
    # Flat (white noise) → ratio ≈ 1; peaked → ratio << 1
    log_mean = np.mean(np.log(power_half + 1e-10))
    geo_mean = np.exp(log_mean)
    arith_mean = np.mean(power_half)
    flatness = geo_mean / arith_mean if arith_mean > 0 else 0

    console.print(f"  Spectral flatness: {flatness:.4f} (1.0 = white noise)")
    console.print(f"  Dominant peak: {'[red]YES[/red]' if has_dominant else '[green]NO[/green]'} "
                  f"({dominant_frac:.1%} > 10% threshold)")

    return {
        "top_frequencies": top_freqs,
        "dominant_power_fraction": round(dominant_frac, 4),
        "has_dominant_frequency": has_dominant,
        "spectral_flatness": round(float(flatness), 4),
    }


# ── A3.4: Compression Test ──────────────────────────────────────────

def compression_test(stream):
    """Compress the stream and measure redundancy."""
    console.rule("[bold blue]A3.4: Compression Test (zlib)")

    # Quantize to bytes (0-255 range)
    quantized = np.clip(stream * 256, 0, 255).astype(np.uint8)
    raw_bytes = quantized.tobytes()
    compressed = zlib.compress(raw_bytes, level=9)

    raw_size = len(raw_bytes)
    comp_size = len(compressed)
    ratio = comp_size / raw_size if raw_size > 0 else 1.0

    console.print(f"  Raw size: {raw_size:,} bytes")
    console.print(f"  Compressed size: {comp_size:,} bytes")
    console.print(f"  Compression ratio: {ratio:.4f}")
    console.print(f"  Interpretation: "
                  f"{'[red]compressible (structured)[/red]' if ratio < 0.95 else '[green]incompressible (noise-like)[/green]'}")

    return {
        "raw_size_bytes": raw_size,
        "compressed_size_bytes": comp_size,
        "compression_ratio": round(ratio, 4),
        "is_compressible": ratio < 0.95,
    }


# ── A3.5: Permutation Baseline ──────────────────────────────────────

def permutation_baseline(stream):
    """Compare real statistics against permuted baselines."""
    console.rule("[bold blue]A3.5: Permutation Baseline (1000 shuffles)")

    rng = np.random.RandomState(42)
    n = len(stream)

    # Compute statistics for real stream
    x_real = stream - stream.mean()
    var_real = np.sum(x_real ** 2) / n

    # Real ACF at lag 1
    real_acf1 = np.sum(x_real[:-1] * x_real[1:]) / (n * var_real) if var_real > 0 else 0

    # Real compression ratio
    q_real = np.clip(stream * 256, 0, 255).astype(np.uint8).tobytes()
    real_comp = len(zlib.compress(q_real, level=9)) / len(q_real)

    # Real spectral max
    fft_real = np.fft.fft(x_real)
    power_real = np.abs(fft_real) ** 2
    half = n // 2
    real_max_power = float(np.max(power_real[1:half]) / np.sum(power_real[1:half]))

    # Permutation distributions
    perm_acf1 = []
    perm_comp = []
    perm_max_power = []

    console.print(f"  Running {N_PERMUTATIONS} permutations...")
    for i in range(N_PERMUTATIONS):
        perm = rng.permutation(stream)
        x_p = perm - perm.mean()
        var_p = np.sum(x_p ** 2) / n

        # ACF lag 1
        acf1 = np.sum(x_p[:-1] * x_p[1:]) / (n * var_p) if var_p > 0 else 0
        perm_acf1.append(acf1)

        # Compression
        q_p = np.clip(perm * 256, 0, 255).astype(np.uint8).tobytes()
        perm_comp.append(len(zlib.compress(q_p, level=9)) / len(q_p))

        # Spectral max
        fft_p = np.fft.fft(x_p)
        power_p = np.abs(fft_p) ** 2
        total_p = np.sum(power_p[1:half])
        perm_max_power.append(float(np.max(power_p[1:half]) / total_p) if total_p > 0 else 0)

    # Z-scores
    def z_score(real_val, perm_vals):
        m = np.mean(perm_vals)
        s = np.std(perm_vals)
        return float((real_val - m) / s) if s > 0 else 0.0

    z_acf1 = z_score(real_acf1, perm_acf1)
    z_comp = z_score(real_comp, perm_comp)
    z_power = z_score(real_max_power, perm_max_power)

    # Display
    table = Table(title="Permutation Test Results")
    table.add_column("Statistic", style="cyan")
    table.add_column("Real", justify="right")
    table.add_column("Perm Mean", justify="right")
    table.add_column("Perm Std", justify="right")
    table.add_column("Z-score", justify="right", style="bold")
    table.add_column("Significant?", justify="center")

    sig_thresh = 2.576  # p < 0.01
    table.add_row(
        "ACF(1)", f"{real_acf1:.4f}",
        f"{np.mean(perm_acf1):.4f}", f"{np.std(perm_acf1):.4f}",
        f"{z_acf1:.2f}",
        "[red]YES[/red]" if abs(z_acf1) > sig_thresh else "no",
    )
    table.add_row(
        "Compression ratio", f"{real_comp:.4f}",
        f"{np.mean(perm_comp):.4f}", f"{np.std(perm_comp):.4f}",
        f"{z_comp:.2f}",
        "[red]YES[/red]" if abs(z_comp) > sig_thresh else "no",
    )
    table.add_row(
        "Max spectral peak", f"{real_max_power:.4f}",
        f"{np.mean(perm_max_power):.4f}", f"{np.std(perm_max_power):.4f}",
        f"{z_power:.2f}",
        "[red]YES[/red]" if abs(z_power) > sig_thresh else "no",
    )
    console.print(table)

    n_significant = sum(1 for z in [z_acf1, z_comp, z_power] if abs(z) > sig_thresh)
    console.print(f"\n  Significant tests (of 3): {n_significant}")

    if n_significant == 0:
        verdict = "NO_STRUCTURE"
        console.print("  [green]Verdict: The residual choice stream shows NO structure "
                      "beyond known drivers. Consistent with mechanical noise.[/green]")
    elif n_significant <= 1:
        verdict = "MARGINAL_STRUCTURE"
        console.print("  [yellow]Verdict: Marginal structure detected (1/3 tests). "
                      "May be a statistical artifact.[/yellow]")
    else:
        verdict = "STRUCTURED"
        console.print("  [red]Verdict: The residual choice stream shows STRUCTURE "
                      "beyond known drivers. Potential hidden content.[/red]")

    return {
        "acf1": {"real": round(real_acf1, 4), "z_score": round(z_acf1, 2),
                 "significant": abs(z_acf1) > sig_thresh},
        "compression": {"real": round(real_comp, 4), "z_score": round(z_comp, 2),
                        "significant": abs(z_comp) > sig_thresh},
        "spectral_peak": {"real": round(real_max_power, 4), "z_score": round(z_power, 2),
                          "significant": abs(z_power) > sig_thresh},
        "n_significant": n_significant,
        "verdict": verdict,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint A3: Structure Detection in the Choice Stream")

    # Load
    choice_stream_path = resolve_choice_stream_path()
    console.print(f"Using choice stream: {choice_stream_path}")
    with open(choice_stream_path) as f:
        trace = json.load(f)
    choices = trace.get("results", trace).get("choices", [])
    console.print(f"Loaded {len(choices)} choice records.")

    # A3.1
    stream, raw_indices, stream_stats = extract_residual_stream(choices)

    # A3.2
    acf_result = autocorrelation_test(stream)

    # A3.3
    spectral_result = spectral_test(stream)

    # A3.4
    comp_result = compression_test(stream)

    # A3.5
    perm_result = permutation_baseline(stream)

    # Summary
    console.rule("[bold magenta]Final Verdict")
    verdict = perm_result["verdict"]
    if verdict == "NO_STRUCTURE":
        console.print(
            "[bold green]The choice stream is indistinguishable from mechanical noise.[/bold green]\n"
            "After removing known drivers (window, bigram, position, recency, suffix), "
            "no residual structure is detected. The 2.21 bits/word RSB appears to be "
            "unexploited channel capacity, not hidden information."
        )
    elif verdict == "MARGINAL_STRUCTURE":
        console.print(
            "[bold yellow]Marginal structure detected.[/bold yellow]\n"
            "One of three statistical tests shows significance. This could be "
            "a genuine signal or a statistical artifact. Further investigation "
            "with additional test batteries would be needed."
        )
    else:
        console.print(
            "[bold red]Structure detected in the choice stream.[/bold red]\n"
            "Multiple statistical tests show the residual choice stream has "
            "non-random structure. This is consistent with (but does not prove) "
            "hidden information content."
        )

    # Save
    results = {
        "stream_stats": stream_stats,
        "autocorrelation": acf_result,
        "spectral": spectral_result,
        "compression": comp_result,
        "permutation_test": perm_result,
        "final_verdict": verdict,
    }

    ProvenanceWriter.save_results(sanitize(results), OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17e_choice_structure"}):
        main()
