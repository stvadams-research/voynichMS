#!/usr/bin/env python3
"""Sprint E2–E3: Conditioned Structure Detection + Window 36 Deep Dive.

E2: Run the A3 structure battery on the *conditioned* residual (after all
    8 drivers from E1), not the raw normalized indices. Determines whether
    the STRUCTURED verdict from A3 survives driver conditioning.

E3: Deep dive into window 36 (80% of residual bits). Structure battery,
    driver saturation (bigram → trigram → 4-gram), and sequential MI.
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

CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_selection/choice_stream_trace.json"
)
EXTENDED_DRIVERS_PATH = (
    project_root / "results/data/phase17_finality/extended_drivers.json"
)
OUTPUT_PATH = project_root / "results/data/phase17_finality/conditioned_structure.json"
console = Console()

MAX_LAG = 50
N_PERMUTATIONS = 1000

# Section boundaries (same as E1)
SECTION_BOUNDARIES = [
    ("Herbal_A", 1, 1200),
    ("Herbal_B", 1201, 1500),
    ("Pharma", 1501, 2000),
    ("Astro", 2001, 2500),
    ("Cosmo", 2501, 2800),
    ("Biological", 2801, 4500),
    ("Stars", 4501, 5145),
]


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


# ── Helpers (reused from E1) ─────────────────────────────────────────

def position_bucket(token_pos):
    if token_pos <= 0:
        return 0
    if token_pos <= 2:
        return 1
    if token_pos <= 5:
        return 2
    if token_pos <= 9:
        return 3
    return 4


def section_from_line_no(line_no):
    for name, lo, hi in SECTION_BOUNDARIES:
        if lo <= line_no <= hi:
            return name
    return "Other"


def entropy_bits(counts):
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def conditional_entropy(groups):
    total = sum(len(v) for v in groups.values())
    if total == 0:
        return 0.0
    h = 0.0
    for words in groups.values():
        p_group = len(words) / total
        counts = list(Counter(words).values())
        h += p_group * entropy_bits(counts)
    return h


# ── Enrichment ───────────────────────────────────────────────────────

def enrich_choices(choices):
    """Add all 8 driver fields to each choice record."""
    # Build word-at index for trigram lookup
    word_at = {}
    for c in choices:
        word_at[(c["line_no"], c["token_pos"])] = c["chosen_word"]

    prev_window = None
    last_seen = {}
    enriched = []

    for i, c in enumerate(choices):
        line_no = c["line_no"]
        token_pos = c["token_pos"]
        prev = c.get("prev_word") or "__none__"

        # Trigram
        prev_prev = "__none__"
        if token_pos >= 2:
            pw = word_at.get((line_no, token_pos - 2))
            if pw is not None:
                prev_prev = pw

        # Section
        section = section_from_line_no(line_no)

        # Persistence
        same_window = 0
        if prev_window is not None and c["window_id"] == prev_window:
            same_window = 1
        prev_window = c["window_id"]

        # Recency
        key = (c["window_id"], c["chosen_word"])
        is_recent = 0
        if key in last_seen and (i - last_seen[key]) <= 50:
            is_recent = 1
        last_seen[key] = i

        suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"
        pos_b = position_bucket(token_pos)

        enriched.append({
            **c,
            "prev_prev_word": prev_prev,
            "section": section,
            "same_window": same_window,
            "is_recent": is_recent,
            "suffix": suffix,
            "pos_bucket": pos_b,
        })

    return enriched


# ── E2.1: Conditioned Residual Extraction ────────────────────────────

def extract_conditioned_residual(enriched, n_drivers=8):
    """Compute conditioned residuals by ranking within driver-key groups.

    For each choice, the 8-driver key defines its conditioning group.
    Within each group, we rank the actual chosen_index among all observed
    chosen_index values for that group, normalized to [0, 1].
    """
    console.rule("[bold blue]E2.1: Conditioned Residual Extraction")

    def make_key(c):
        prev = c.get("prev_word") or "__none__"
        if n_drivers == 5:
            return (c["window_id"], prev, c["pos_bucket"],
                    c["is_recent"], c["suffix"])
        return (c["window_id"], prev, c["pos_bucket"],
                c["is_recent"], c["suffix"],
                c["prev_prev_word"], c["section"], c["same_window"])

    # Group all choices by their conditioning key
    groups = defaultdict(list)
    for i, c in enumerate(enriched):
        groups[make_key(c)].append((i, c["chosen_index"]))

    # For each group, rank the chosen_index values
    residuals = [0.0] * len(enriched)
    for key, items in groups.items():
        indices = [idx for _, idx in items]
        sorted_vals = sorted(indices)
        n = len(sorted_vals)
        if n <= 1:
            for orig_i, _ in items:
                residuals[orig_i] = 0.5  # singleton — no information
            continue
        for orig_i, idx in items:
            # Rank of idx within the group's distribution
            rank = sorted_vals.index(idx)
            residuals[orig_i] = rank / (n - 1)

    stream = np.array(residuals)

    # Filter out singletons (residual = 0.5 exactly means no group info)
    non_singleton_mask = np.array([
        len(groups[make_key(enriched[i])]) > 1 for i in range(len(enriched))
    ])
    effective_stream = stream[non_singleton_mask]

    console.print(f"  Total choices: {len(stream)}")
    console.print(f"  Non-singleton choices: {len(effective_stream)} "
                  f"({len(effective_stream) / len(stream):.1%})")
    console.print(f"  Conditioned residual mean: {effective_stream.mean():.4f} "
                  f"(expected ~0.5)")
    console.print(f"  Conditioned residual std: {effective_stream.std():.4f}")

    # Also extract 5-driver residual for comparison
    groups_5 = defaultdict(list)
    for i, c in enumerate(enriched):
        prev = c.get("prev_word") or "__none__"
        key5 = (c["window_id"], prev, c["pos_bucket"],
                c["is_recent"], c["suffix"])
        groups_5[key5].append((i, c["chosen_index"]))

    residuals_5 = [0.0] * len(enriched)
    for key, items in groups_5.items():
        indices = [idx for _, idx in items]
        sorted_vals = sorted(indices)
        n = len(sorted_vals)
        if n <= 1:
            for orig_i, _ in items:
                residuals_5[orig_i] = 0.5
            continue
        for orig_i, idx in items:
            rank = sorted_vals.index(idx)
            residuals_5[orig_i] = rank / (n - 1)

    stream_5 = np.array(residuals_5)
    mask_5 = np.array([
        len(groups_5[(
            enriched[i]["window_id"],
            enriched[i].get("prev_word") or "__none__",
            enriched[i]["pos_bucket"],
            enriched[i]["is_recent"],
            enriched[i]["suffix"],
        )]) > 1 for i in range(len(enriched))
    ])
    effective_stream_5 = stream_5[mask_5]

    return effective_stream, effective_stream_5, {
        "total_choices": len(stream),
        "non_singleton_8d": len(effective_stream),
        "non_singleton_5d": len(effective_stream_5),
        "mean_8d": round(float(effective_stream.mean()), 4),
        "std_8d": round(float(effective_stream.std()), 4),
    }


# ── Structure Battery (shared by E2 and E3) ─────────────────────────

def run_structure_battery(stream, label=""):
    """Run the full A3-style structure battery on a stream."""
    n = len(stream)
    x = stream - stream.mean()
    var = np.sum(x ** 2) / n

    # ACF at lag 1
    acf1 = float(np.sum(x[:-1] * x[1:]) / (n * var)) if var > 0 else 0

    # Compression
    quantized = np.clip(stream * 256, 0, 255).astype(np.uint8).tobytes()
    comp_ratio = len(zlib.compress(quantized, level=9)) / len(quantized)

    # Spectral max
    fft_vals = np.fft.fft(x)
    power = np.abs(fft_vals) ** 2
    half = n // 2
    total_power = np.sum(power[1:half])
    max_power_frac = float(np.max(power[1:half]) / total_power) if total_power > 0 else 0

    # Permutation baseline
    rng = np.random.RandomState(42)
    perm_acf1, perm_comp, perm_power = [], [], []

    for _ in range(N_PERMUTATIONS):
        perm = rng.permutation(stream)
        xp = perm - perm.mean()
        var_p = np.sum(xp ** 2) / n

        a1 = float(np.sum(xp[:-1] * xp[1:]) / (n * var_p)) if var_p > 0 else 0
        perm_acf1.append(a1)

        qp = np.clip(perm * 256, 0, 255).astype(np.uint8).tobytes()
        perm_comp.append(len(zlib.compress(qp, level=9)) / len(qp))

        fp = np.fft.fft(xp)
        pp = np.abs(fp) ** 2
        tp = np.sum(pp[1:half])
        perm_power.append(float(np.max(pp[1:half]) / tp) if tp > 0 else 0)

    def z_score(real, perm_vals):
        m = np.mean(perm_vals)
        s = np.std(perm_vals)
        return float((real - m) / s) if s > 0 else 0.0

    z_acf = z_score(acf1, perm_acf1)
    z_comp = z_score(comp_ratio, perm_comp)
    z_power = z_score(max_power_frac, perm_power)

    sig_thresh = 2.576  # p < 0.01
    n_significant = sum(1 for z in [z_acf, z_comp, z_power] if abs(z) > sig_thresh)

    if n_significant == 0:
        verdict = "NO_STRUCTURE"
    elif n_significant <= 1:
        verdict = "MARGINAL_STRUCTURE"
    else:
        verdict = "STRUCTURED"

    return {
        "label": label,
        "n": n,
        "acf1": {"real": round(acf1, 4), "z_score": round(z_acf, 2),
                 "significant": bool(abs(z_acf) > sig_thresh)},
        "compression": {"real": round(comp_ratio, 4), "z_score": round(z_comp, 2),
                        "significant": bool(abs(z_comp) > sig_thresh)},
        "spectral_peak": {"real": round(max_power_frac, 6), "z_score": round(z_power, 2),
                          "significant": bool(abs(z_power) > sig_thresh)},
        "n_significant": n_significant,
        "verdict": verdict,
    }


# ── E2.2-E2.3: Structure battery comparison ─────────────────────────

def sprint_e2(stream_8d, stream_5d):
    """Run structure battery on conditioned residuals and compare."""
    console.rule("[bold blue]E2.2: Structure Battery on Conditioned Residuals")

    console.print("Running battery on 5-driver conditioned residual...")
    result_5d = run_structure_battery(stream_5d, "After 5 drivers")

    console.print("Running battery on 8-driver conditioned residual...")
    result_8d = run_structure_battery(stream_8d, "After 8 drivers")

    # E2.3: Comparison table
    console.rule("[bold blue]E2.3: Side-by-Side Comparison")

    # Raw A3 results (hardcoded from Sprint A3 output)
    raw_a3 = {
        "acf1_z": 6.95,
        "spectral_z": 43.70,
        "compression_z": 1.81,
        "verdict": "STRUCTURED",
    }

    table = Table(title="Structure Battery Comparison")
    table.add_column("Statistic", style="cyan")
    table.add_column("Raw (A3)", justify="right")
    table.add_column("After 5 drivers", justify="right")
    table.add_column("After 8 drivers", justify="right")

    table.add_row(
        "ACF(1) z-score",
        f"{raw_a3['acf1_z']:.2f}",
        f"{result_5d['acf1']['z_score']:.2f}",
        f"{result_8d['acf1']['z_score']:.2f}",
    )
    table.add_row(
        "Spectral peak z-score",
        f"{raw_a3['spectral_z']:.2f}",
        f"{result_5d['spectral_peak']['z_score']:.2f}",
        f"{result_8d['spectral_peak']['z_score']:.2f}",
    )
    table.add_row(
        "Compression z-score",
        f"{raw_a3['compression_z']:.2f}",
        f"{result_5d['compression']['z_score']:.2f}",
        f"{result_8d['compression']['z_score']:.2f}",
    )
    table.add_row(
        "Verdict",
        raw_a3["verdict"],
        result_5d["verdict"],
        result_8d["verdict"],
    )
    console.print(table)

    # Gate check
    acf_z = abs(result_8d["acf1"]["z_score"])
    spectral_z = abs(result_8d["spectral_peak"]["z_score"])
    if acf_z < 2.0 and spectral_z < 2.0:
        gate_verdict = "EXPLAINED"
        console.print(
            "\n[bold green]GATE: EXPLAINED[/bold green] — Structure vanishes "
            "under 8-driver conditioning. The A3 signal was unmodeled mechanics."
        )
    else:
        gate_verdict = "PERSISTENT"
        console.print(
            "\n[bold red]GATE: PERSISTENT[/bold red] — Structure survives "
            "8-driver conditioning. Evidence for non-mechanical structure "
            "(possible hidden content)."
        )

    return {
        "raw_a3": raw_a3,
        "after_5_drivers": result_5d,
        "after_8_drivers": result_8d,
        "gate_verdict": gate_verdict,
    }


# ── E3: Window 36 Deep Dive ─────────────────────────────────────────

def sprint_e3(enriched):
    """Deep dive into window 36 — the dominant residual window."""
    console.rule("[bold magenta]Sprint E3: Window 36 Deep Dive")

    # E3.1: Extract window 36 choices
    w36_choices = [c for c in enriched if c["window_id"] == 36]
    console.print(f"  Window 36: {len(w36_choices)} choices, "
                  f"{len(set(c['chosen_word'] for c in w36_choices))} unique words")

    if len(w36_choices) < 100:
        console.print("[yellow]Too few choices for reliable structure test.[/yellow]")
        return {"note": f"Only {len(w36_choices)} choices — insufficient for analysis"}

    # Extract normalized indices for window 36
    w36_stream = []
    for c in w36_choices:
        n = c["candidates_count"]
        if n > 1:
            w36_stream.append(c["chosen_index"] / (n - 1))
    w36_stream = np.array(w36_stream)

    console.print(f"  Stream length (n > 1): {len(w36_stream)}")

    # E3.1: Structure battery on window 36
    console.rule("[bold blue]E3.1: Window 36 Structure Battery")
    w36_result = run_structure_battery(w36_stream, "Window 36 raw")
    display_battery_result(w36_result)

    # E3.2: Driver saturation check
    console.rule("[bold blue]E3.2: Driver Saturation (Window 36)")
    saturation = driver_saturation_w36(w36_choices)

    # E3.3: Sequential MI
    console.rule("[bold blue]E3.3: Sequential Mutual Information (Window 36)")
    mi_profile = sequential_mi_w36(w36_choices)

    return {
        "n_choices": len(w36_choices),
        "n_unique_words": len(set(c["chosen_word"] for c in w36_choices)),
        "structure_battery": w36_result,
        "driver_saturation": saturation,
        "mi_profile": mi_profile,
    }


def display_battery_result(result):
    """Display a battery result in a table."""
    table = Table(title=f"Structure Battery: {result['label']}")
    table.add_column("Test", style="cyan")
    table.add_column("Z-score", justify="right", style="bold")
    table.add_column("Significant?", justify="center")
    for test_name, test_key in [("ACF(1)", "acf1"), ("Compression", "compression"),
                                 ("Spectral peak", "spectral_peak")]:
        z = result[test_key]["z_score"]
        sig = "[red]YES[/red]" if result[test_key]["significant"] else "no"
        table.add_row(test_name, f"{z:.2f}", sig)
    table.add_row("Verdict", result["verdict"], "", style="bold")
    console.print(table)


def driver_saturation_w36(w36_choices):
    """Test entropy convergence as n-gram context increases."""
    # All choices share window 36, so window is fixed.
    # Compute H(choice | bigram) → H(choice | trigram) → H(choice | 4-gram)

    # Bigram: H(choice | prev_word)
    groups_bi = defaultdict(list)
    for c in w36_choices:
        prev = c.get("prev_word") or "__none__"
        groups_bi[prev].append(c["chosen_word"])
    h_bi = conditional_entropy(groups_bi)

    # Trigram: H(choice | prev_word, prev_prev_word)
    groups_tri = defaultdict(list)
    for c in w36_choices:
        prev = c.get("prev_word") or "__none__"
        groups_tri[(prev, c["prev_prev_word"])].append(c["chosen_word"])
    h_tri = conditional_entropy(groups_tri)

    # 4-gram: approximate by adding suffix of prev_prev_word
    groups_4g = defaultdict(list)
    for c in w36_choices:
        prev = c.get("prev_word") or "__none__"
        pp = c["prev_prev_word"]
        pp_suffix = pp[-2:] if pp and len(pp) >= 2 and pp != "__none__" else "__"
        groups_4g[(prev, pp, pp_suffix)].append(c["chosen_word"])
    h_4g = conditional_entropy(groups_4g)

    # Marginal H
    all_words = [c["chosen_word"] for c in w36_choices]
    h_marginal = entropy_bits(list(Counter(all_words).values()))

    table = Table(title="Window 36 Driver Saturation")
    table.add_column("Context", style="cyan")
    table.add_column("H (bits)", justify="right", style="bold")
    table.add_column("Reduction", justify="right")
    table.add_row("Unconditioned", f"{h_marginal:.4f}", "—")
    table.add_row("Bigram", f"{h_bi:.4f}", f"-{h_marginal - h_bi:.4f}")
    table.add_row("Trigram", f"{h_tri:.4f}", f"-{h_bi - h_tri:.4f}")
    table.add_row("4-gram proxy", f"{h_4g:.4f}", f"-{h_tri - h_4g:.4f}")
    console.print(table)

    plateau = abs(h_tri - h_4g) < 0.05
    console.print(f"  Plateau reached: {'[green]YES[/green]' if plateau else '[red]NO[/red]'} "
                  f"(trigram→4gram delta = {abs(h_tri - h_4g):.4f})")

    return {
        "h_marginal": round(h_marginal, 4),
        "h_bigram": round(h_bi, 4),
        "h_trigram": round(h_tri, 4),
        "h_4gram_proxy": round(h_4g, 4),
        "plateau_reached": plateau,
        "trigram_to_4gram_delta": round(abs(h_tri - h_4g), 4),
    }


def sequential_mi_w36(w36_choices):
    """Compute mutual information between choice[i] and choice[i+k]."""
    # Use chosen_index as the observable
    indices = [c["chosen_index"] for c in w36_choices]
    n = len(indices)

    # Discretize to quartiles for MI computation
    arr = np.array(indices, dtype=float)
    quartiles = np.percentile(arr, [25, 50, 75])
    discretized = np.digitize(arr, quartiles)

    mi_values = []
    for lag in range(1, min(21, n // 10)):
        # MI(X, Y) = H(X) + H(Y) - H(X, Y)
        x_counts = Counter(discretized[:n - lag])
        y_counts = Counter(discretized[lag:])
        xy_counts = Counter(zip(discretized[:n - lag], discretized[lag:]))

        h_x = entropy_bits(list(x_counts.values()))
        h_y = entropy_bits(list(y_counts.values()))
        h_xy = entropy_bits(list(xy_counts.values()))
        mi = h_x + h_y - h_xy
        mi_values.append({"lag": lag, "mi": round(mi, 4)})

    table = Table(title="Window 36 Mutual Information by Lag")
    table.add_column("Lag", justify="right")
    table.add_column("MI (bits)", justify="right", style="bold")
    for mv in mi_values[:10]:
        table.add_row(str(mv["lag"]), f"{mv['mi']:.4f}")
    console.print(table)

    # Check for periodicity: is MI non-decaying?
    if len(mi_values) >= 5:
        mi_arr = np.array([mv["mi"] for mv in mi_values])
        # Fit linear regression to check for decay
        lags = np.arange(1, len(mi_arr) + 1)
        slope, _, _, _, _ = stats.linregress(lags, mi_arr)
        periodic = slope > -0.001  # non-decaying
        console.print(f"  MI slope: {slope:.6f} ({'non-decaying' if periodic else 'decaying'})")
    else:
        periodic = False
        slope = 0.0

    return {
        "mi_by_lag": mi_values,
        "slope": round(slope, 6),
        "non_decaying": periodic,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprints E2-E3: Conditioned Structure Detection")

    # Load choice stream
    if not CHOICE_STREAM_PATH.exists():
        console.print("[red]Error: Choice stream trace missing.[/red]")
        return
    with open(CHOICE_STREAM_PATH) as f:
        trace_data = json.load(f)
    choices = trace_data.get("results", trace_data).get("choices", [])
    console.print(f"Loaded {len(choices)} choice records.")

    # Enrich choices with all 8 drivers
    enriched = enrich_choices(choices)
    console.print(f"Enriched {len(enriched)} choices.")

    # E2.1: Extract conditioned residuals
    stream_8d, stream_5d, residual_stats = extract_conditioned_residual(enriched)

    # E2.2-E2.3: Structure battery comparison
    e2_results = sprint_e2(stream_8d, stream_5d)

    # E3: Window 36 deep dive
    e3_results = sprint_e3(enriched)

    # Assemble results
    results = {
        "residual_stats": residual_stats,
        "e2_structure_comparison": e2_results,
        "e3_window36_deep_dive": e3_results,
        "overall_verdict": e2_results["gate_verdict"],
    }

    ProvenanceWriter.save_results(sanitize(results), OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Final summary
    console.rule("[bold magenta]Overall Verdict")
    if e2_results["gate_verdict"] == "EXPLAINED":
        console.print(
            "[bold green]The A3 STRUCTURED signal is EXPLAINED by additional driver "
            "conditioning.[/bold green]\n"
            "After accounting for trigram context, section identity, and window "
            "persistence, the residual choice stream shows no significant structure. "
            "The 2.21 bpw RSB was unmodeled mechanical correlation, not hidden content."
        )
    else:
        console.print(
            "[bold red]The A3 STRUCTURED signal PERSISTS after extended conditioning."
            "[/bold red]\n"
            "Even with 8 drivers conditioned out, the residual choice stream retains "
            "sequential and/or spectral structure. This strengthens the case for "
            "non-mechanical content in the choice stream."
        )


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17h_conditioned_structure"}):
        main()
