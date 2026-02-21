#!/usr/bin/env python3
"""Sprint D1: Structural Signature Definition.

Defines the quantitative "structural signature" that characterizes a
lattice-generated text.  Computes the Voynich reference card from
existing artifacts and establishes null distributions via 100 shuffled
corpus permutations.

Metrics:
  1. Drift admissibility (corrected, %)
  2. Overgeneration — BUR and TUR
  3. Branching factor (mean candidates per window)
  4. Moran's I on offset topology
  5. FFT dominant power fraction (k=1)
  6. BIC device model ranking (volvelle)
  7. Selection entropy (bits/word)
  8. Cross-section transfer rate (holdout success fraction)
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

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase14_machine.evaluation_engine import EvaluationEngine  # noqa: E402
from phase14_machine.palette_solver import GlobalPaletteSolver  # noqa: E402

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
PHYS_PATH = project_root / "results/data/phase14_machine/physical_integration.json"
BW_PATH = project_root / "results/data/phase17_finality/bandwidth_audit.json"
FREQ_PATH = project_root / "results/data/phase14_machine/frequency_lattice.json"
CORRECTIONS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
IVTFF_PATH = project_root / "data/raw/transliterations/ivtff2.0/ZL3b-n.txt"
OUTPUT_PATH = project_root / "results/data/phase18_comparative/signature_definition.json"

console = Console()


# ── Utilities ────────────────────────────────────────────────────────

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


def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = "reordered_lattice_map" if "reordered_lattice_map" in results else "lattice_map"
    wc_key = "reordered_window_contents" if "reordered_window_contents" in results else "window_contents"
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_ivtff_lines(path):
    """Load manuscript lines from IVTFF file."""
    lines = []
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#") or raw.startswith("<"):
                # Skip comments and metadata-only lines
                pass
            # Extract content after the tab (IVTFF format: <loc>\t<content>)
            if "\t" in raw:
                content = raw.split("\t", 1)[1]
            else:
                content = raw
            # Clean IVTFF markup
            content = content.replace("<%>", "").replace("{", "").replace("}", "")
            # Remove uncertainty markers
            import re
            content = re.sub(r"\[[^\]]*:[^\]]*\]", "", content)
            content = re.sub(r"[!*?]", "", content)
            # Tokenize on dots and spaces
            tokens = [t.strip() for t in content.replace(".", " ").split() if t.strip()]
            if tokens:
                lines.append(tokens)
    return lines


def signed_circular_offset(src, dst, num_windows=50):
    """Signed circular distance from src to dst."""
    raw = dst - src
    if raw > num_windows // 2:
        raw -= num_windows
    elif raw < -(num_windows // 2):
        raw += num_windows
    return raw


def learn_offset_corrections(lines, lattice_map, num_windows=50, min_obs=5):
    """Learn per-window mode offset corrections."""
    groups = defaultdict(list)
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            groups[prev_win].append(signed_circular_offset(prev_win, curr_win, num_windows))
    corrections = {}
    for key, offsets in groups.items():
        if len(offsets) >= min_obs:
            corrections[key] = Counter(offsets).most_common(1)[0][0]
    return corrections


def score_with_correction(lines, lattice_map, window_contents, corrections, num_windows=50):
    """Score admissibility using per-window corrections."""
    admissible = 0
    total = 0
    vocab = set(lattice_map.keys())
    current_window = 0
    for line in lines:
        for word in line:
            if word not in vocab:
                continue
            total += 1
            corr = corrections.get(current_window, 0)
            expected_win = (current_window + corr) % num_windows
            # Check drift ±1 around corrected position
            hit = False
            for offset in [-1, 0, 1]:
                check_win = (expected_win + offset) % num_windows
                if word in window_contents.get(check_win, []):
                    hit = True
                    current_window = check_win
                    break
            if hit:
                admissible += 1
            elif word in lattice_map:
                current_window = lattice_map[word]
    return admissible / total if total > 0 else 0


# ── D1.1: Metric Definitions ────────────────────────────────────────

def compute_voynich_signature(lines, lattice_map, window_contents):
    """Compute the full 8-metric signature for the Voynich manuscript."""
    console.rule("[bold blue]D1.1: Voynich Reference Signature")

    vocab = set(lattice_map.keys())
    engine = EvaluationEngine(vocab)
    num_windows = len(window_contents)

    # 1. Drift admissibility (corrected)
    corrections = learn_offset_corrections(lines, lattice_map, num_windows)
    corrected_rate = score_with_correction(
        lines, lattice_map, window_contents, corrections, num_windows
    )
    console.print(f"  1. Corrected admissibility: {corrected_rate:.4f}")

    # 2. Overgeneration (BUR/TUR) — use unigram sampling as proxy
    from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle
    emulator = HighFidelityVolvelle(
        lattice_map, window_contents, seed=42,
        offset_corrections=corrections
    )
    syn_lines = emulator.generate_mirror_corpus(num_lines=len(lines))
    overgen = engine.calculate_overgeneration(syn_lines, lines)
    bur = overgen["BUR"]["rate"]
    tur = overgen["TUR"]["rate"]
    console.print(f"  2. BUR: {bur:.4f}, TUR: {tur:.4f}")

    # 3. Branching factor (mean window size)
    window_sizes = [len(v) for v in window_contents.values()]
    mean_branching = np.mean(window_sizes)
    effective_bits = math.log2(mean_branching) if mean_branching > 1 else 0
    console.print(f"  3. Mean branching factor: {mean_branching:.1f} ({effective_bits:.2f} bits)")

    # 4. Moran's I on correction topology
    corr_vec = [corrections.get(w, 0) for w in range(num_windows)]
    morans_i = _compute_morans_i(corr_vec)
    console.print(f"  4. Moran's I: {morans_i:.4f}")

    # 5. FFT dominant power fraction
    fft_power = _compute_fft_dominant(corr_vec)
    console.print(f"  5. FFT dominant power: {fft_power:.4f}")

    # 6. BIC — fit sinusoidal (volvelle) vs linear (grille)
    bic_volvelle, bic_grille = _compute_bic_models(corr_vec)
    console.print(f"  6. BIC volvelle: {bic_volvelle:.1f}, BIC grille: {bic_grille:.1f}")

    # 7. Selection entropy
    all_tokens = [t for line in lines for t in line if t in vocab]
    counts = Counter(all_tokens)
    total = len(all_tokens)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    console.print(f"  7. Selection entropy: {entropy:.2f} bits/word")

    # 8. Cross-section transfer (leave-one-out)
    sections = _split_sections(lines)
    transfer_rate = _cross_section_transfer(sections, lattice_map, window_contents, num_windows)
    console.print(f"  8. Cross-section transfer: {transfer_rate:.2f} ({transfer_rate * len(sections):.0f}/{len(sections)} folds)")

    return {
        "corrected_admissibility": round(corrected_rate, 4),
        "bur": round(bur, 4),
        "tur": round(tur, 4),
        "mean_branching_factor": round(mean_branching, 1),
        "effective_bits": round(effective_bits, 2),
        "morans_i": round(morans_i, 4),
        "fft_dominant_power": round(fft_power, 4),
        "bic_volvelle": round(bic_volvelle, 1),
        "bic_grille": round(bic_grille, 1),
        "selection_entropy_bpw": round(entropy, 4),
        "cross_section_transfer": round(transfer_rate, 4),
    }


def _compute_morans_i(values):
    """Moran's I for a circular 1D sequence (adjacent-cell weights)."""
    n = len(values)
    if n < 3:
        return 0.0
    arr = np.array(values, dtype=float)
    mean = arr.mean()
    dev = arr - mean
    ss = np.sum(dev ** 2)
    if ss == 0:
        return 0.0
    # Circular adjacency: each cell neighbors its ±1
    w_sum = 0.0
    numerator = 0.0
    for i in range(n):
        for d in [-1, 1]:
            j = (i + d) % n
            w_sum += 1.0
            numerator += dev[i] * dev[j]
    return float((n / w_sum) * (numerator / ss))


def _compute_fft_dominant(values):
    """Fraction of spectral power in the k=1 (single-cycle) component."""
    arr = np.array(values, dtype=float)
    if len(arr) < 3:
        return 0.0
    fft_vals = np.fft.rfft(arr - arr.mean())
    power = np.abs(fft_vals) ** 2
    total_power = power[1:].sum()
    if total_power == 0:
        return 0.0
    return float(power[1] / total_power)


def _compute_bic_models(corr_vec):
    """BIC for sinusoidal (volvelle) and linear (grille) models."""
    n = len(corr_vec)
    x = np.arange(n, dtype=float)
    y = np.array(corr_vec, dtype=float)

    # Sinusoidal fit: y = A * sin(2π*x/N + φ) + c  (3 params: A, φ, c)
    # Approximate via FFT
    fft_vals = np.fft.rfft(y - y.mean())
    if len(fft_vals) > 1:
        A = 2 * np.abs(fft_vals[1]) / n
        phi = np.angle(fft_vals[1])
        y_sin = A * np.sin(2 * np.pi * x / n + phi) + y.mean()
        rss_sin = np.sum((y - y_sin) ** 2)
    else:
        rss_sin = np.sum((y - y.mean()) ** 2)
    k_sin = 3
    bic_sin = n * np.log(rss_sin / n + 1e-10) + k_sin * np.log(n)

    # Linear fit: y = a*x + b  (2 params)
    coeffs = np.polyfit(x, y, 1)
    y_lin = np.polyval(coeffs, x)
    rss_lin = np.sum((y - y_lin) ** 2)
    k_lin = 2
    bic_lin = n * np.log(rss_lin / n + 1e-10) + k_lin * np.log(n)

    return float(bic_sin), float(bic_lin)


def _split_sections(lines, n_sections=7):
    """Split lines into roughly equal sections for cross-validation."""
    chunk_size = max(1, len(lines) // n_sections)
    sections = []
    for i in range(0, len(lines), chunk_size):
        section = lines[i:i + chunk_size]
        if section:
            sections.append(section)
    # Merge trailing section if too small
    if len(sections) > n_sections and len(sections[-1]) < chunk_size // 2:
        sections[-2].extend(sections[-1])
        sections.pop()
    return sections[:n_sections]


def _cross_section_transfer(sections, lattice_map, window_contents, num_windows):
    """Leave-one-section-out: train corrections on N-1, test on 1."""
    successes = 0
    for holdout_idx in range(len(sections)):
        train_lines = []
        for i, s in enumerate(sections):
            if i != holdout_idx:
                train_lines.extend(s)
        test_lines = sections[holdout_idx]
        corrections = learn_offset_corrections(train_lines, lattice_map, num_windows)
        rate = score_with_correction(
            test_lines, lattice_map, window_contents, corrections, num_windows
        )
        # "Significant" if corrected rate beats uncorrected baseline
        baseline = score_with_correction(
            test_lines, lattice_map, window_contents, {}, num_windows
        )
        if rate > baseline + 0.005:  # at least 0.5pp improvement
            successes += 1
    return successes / len(sections) if sections else 0


# ── D1.2: Null Distribution ────────────────────────────────────────

def compute_null_distribution(lines, lattice_map, window_contents, n_shuffles=100):
    """Compute null distributions for each metric by shuffling within lines."""
    console.rule("[bold blue]D1.2: Null Distributions (100 shuffles)")
    rng = np.random.default_rng(42)
    num_windows = len(window_contents)
    vocab = set(lattice_map.keys())

    null_metrics = defaultdict(list)

    for i in range(n_shuffles):
        if (i + 1) % 20 == 0:
            console.print(f"  Shuffle {i + 1}/{n_shuffles}...")

        # Shuffle word order within each line
        shuffled = []
        for line in lines:
            perm = list(line)
            rng.shuffle(perm)
            shuffled.append(perm)

        # Compute metrics for shuffled corpus
        corrections = learn_offset_corrections(shuffled, lattice_map, num_windows)
        rate = score_with_correction(
            shuffled, lattice_map, window_contents, corrections, num_windows
        )
        null_metrics["corrected_admissibility"].append(rate)

        corr_vec = [corrections.get(w, 0) for w in range(num_windows)]
        null_metrics["morans_i"].append(_compute_morans_i(corr_vec))
        null_metrics["fft_dominant_power"].append(_compute_fft_dominant(corr_vec))

        all_tokens = [t for line in shuffled for t in line if t in vocab]
        counts = Counter(all_tokens)
        total = len(all_tokens)
        if total > 0:
            entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
        else:
            entropy = 0
        null_metrics["selection_entropy_bpw"].append(entropy)

    # Summarize
    summary = {}
    for metric, values in null_metrics.items():
        arr = np.array(values)
        summary[metric] = {
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std()), 4),
            "ci_95_lo": round(float(np.percentile(arr, 2.5)), 4),
            "ci_95_hi": round(float(np.percentile(arr, 97.5)), 4),
        }

    for metric, stats in summary.items():
        console.print(f"  {metric}: mean={stats['mean']:.4f} std={stats['std']:.4f}")

    return summary


# ── D1.3: Signature Card ───────────────────────────────────────────

def build_signature_card(voynich_sig, null_dist):
    """Build the Voynich reference signature card with z-scores vs null."""
    console.rule("[bold blue]D1.3: Voynich Signature Card")

    card = {}
    for metric in ["corrected_admissibility", "morans_i", "fft_dominant_power",
                    "selection_entropy_bpw"]:
        real_val = voynich_sig[metric]
        null_mean = null_dist[metric]["mean"]
        null_std = null_dist[metric]["std"]
        z = (real_val - null_mean) / null_std if null_std > 0 else 0
        card[metric] = {
            "voynich_value": real_val,
            "null_mean": null_mean,
            "null_std": null_std,
            "z_score": round(z, 2),
        }

    # Metrics without null distribution (from existing artifacts)
    for metric in ["bur", "tur", "mean_branching_factor", "effective_bits",
                    "bic_volvelle", "bic_grille", "cross_section_transfer"]:
        card[metric] = {"voynich_value": voynich_sig[metric]}

    table = Table(title="Voynich Signature Card")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Null Mean", justify="right")
    table.add_column("Z-score", justify="right", style="bold")

    for metric, info in card.items():
        z_str = f"{info['z_score']:.2f}" if "z_score" in info else "—"
        null_str = f"{info['null_mean']:.4f}" if "null_mean" in info else "—"
        table.add_row(metric, f"{info['voynich_value']}", null_str, z_str)

    console.print(table)
    return card


# ── Main ─────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint D1: Structural Signature Definition")

    # Load Voynich data
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    lines = load_ivtff_lines(IVTFF_PATH)
    console.print(f"Loaded palette: {len(lattice_map)} tokens, {len(window_contents)} windows")
    console.print(f"Loaded corpus: {len(lines)} lines")

    # D1.1: Compute Voynich signature
    voynich_sig = compute_voynich_signature(lines, lattice_map, window_contents)

    # D1.2: Null distribution
    null_dist = compute_null_distribution(lines, lattice_map, window_contents, n_shuffles=100)

    # D1.3: Signature card
    card = build_signature_card(voynich_sig, null_dist)

    results = {
        "voynich_signature": voynich_sig,
        "null_distributions": null_dist,
        "signature_card": card,
    }

    ProvenanceWriter.save_results(sanitize(results), OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_18a_signature_battery"}):
        main()
