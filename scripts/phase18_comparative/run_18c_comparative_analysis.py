#!/usr/bin/env python3
"""Sprint D3: Comparative Signature Analysis.

For each ingested corpus (from D2), build a lattice using the same
methodology as the Voynich canonical lattice, compute all signature
metrics (from D1), and compare against the Voynich reference card.

Outputs a distance matrix and discrimination assessment.
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

INGESTED_PATH = project_root / "results/data/phase18_comparative/ingested_corpora.json"
SIGNATURE_PATH = project_root / "results/data/phase18_comparative/signature_definition.json"
OUTPUT_PATH = project_root / "results/data/phase18_comparative/comparative_signatures.json"

console = Console()

NUM_WINDOWS = 50


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


def signed_circular_offset(src, dst, num_windows=50):
    raw = dst - src
    if raw > num_windows // 2:
        raw -= num_windows
    elif raw < -(num_windows // 2):
        raw += num_windows
    return raw


def learn_offset_corrections(lines, lattice_map, num_windows=50, min_obs=5):
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


def compute_morans_i(values):
    n = len(values)
    if n < 3:
        return 0.0
    arr = np.array(values, dtype=float)
    mean = arr.mean()
    dev = arr - mean
    ss = np.sum(dev ** 2)
    if ss == 0:
        return 0.0
    w_sum = 0.0
    numerator = 0.0
    for i in range(n):
        for d in [-1, 1]:
            j = (i + d) % n
            w_sum += 1.0
            numerator += dev[i] * dev[j]
    return float((n / w_sum) * (numerator / ss))


def compute_fft_dominant(values):
    arr = np.array(values, dtype=float)
    if len(arr) < 3:
        return 0.0
    fft_vals = np.fft.rfft(arr - arr.mean())
    power = np.abs(fft_vals) ** 2
    total_power = power[1:].sum()
    if total_power == 0:
        return 0.0
    return float(power[1] / total_power)


def compute_bic_models(corr_vec):
    n = len(corr_vec)
    x = np.arange(n, dtype=float)
    y = np.array(corr_vec, dtype=float)
    fft_vals = np.fft.rfft(y - y.mean())
    if len(fft_vals) > 1:
        A = 2 * np.abs(fft_vals[1]) / n
        phi = np.angle(fft_vals[1])
        y_sin = A * np.sin(2 * np.pi * x / n + phi) + y.mean()
        rss_sin = np.sum((y - y_sin) ** 2)
    else:
        rss_sin = np.sum((y - y.mean()) ** 2)
    bic_sin = n * np.log(rss_sin / n + 1e-10) + 3 * np.log(n)
    coeffs = np.polyfit(x, y, 1)
    y_lin = np.polyval(coeffs, x)
    rss_lin = np.sum((y - y_lin) ** 2)
    bic_lin = n * np.log(rss_lin / n + 1e-10) + 2 * np.log(n)
    return float(bic_sin), float(bic_lin)


def split_sections(lines, n_sections=7):
    chunk_size = max(1, len(lines) // n_sections)
    sections = []
    for i in range(0, len(lines), chunk_size):
        section = lines[i:i + chunk_size]
        if section:
            sections.append(section)
    if len(sections) > n_sections and len(sections[-1]) < chunk_size // 2:
        sections[-2].extend(sections[-1])
        sections.pop()
    return sections[:n_sections]


def cross_section_transfer(sections, lattice_map, window_contents, num_windows):
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
        baseline = score_with_correction(
            test_lines, lattice_map, window_contents, {}, num_windows
        )
        if rate > baseline + 0.005:
            successes += 1
    return successes / len(sections) if sections else 0


# ── D3.1: Build Lattice for a Corpus ────────────────────────────────

def build_lattice_for_corpus(lines, name, num_windows=50):
    """Build a lattice from scratch for any token sequence."""
    console.print(f"\n  Building lattice for [cyan]{name}[/cyan]...")

    solver = GlobalPaletteSolver()
    # No slips for non-Voynich texts — use transitions only
    solver.ingest_data(slips=[], lines=lines, top_n=8000)

    n_nodes = solver.G.number_of_nodes()
    n_edges = solver.G.number_of_edges()
    console.print(f"    Graph: {n_nodes} nodes, {n_edges} edges")

    if n_nodes < num_windows:
        console.print(f"    [yellow]Too few nodes ({n_nodes}) for {num_windows} windows — reducing[/yellow]")
        num_windows = max(3, n_nodes // 2)

    coords = solver.solve_grid(iterations=20)
    result = solver.cluster_lattice(coords, num_windows=num_windows)

    lattice_map = result["word_to_window"]
    window_contents = {int(k): v for k, v in result["window_contents"].items()}

    # Spectral reordering
    reordered = solver.reorder_windows(lattice_map, window_contents, lines)
    lattice_map = reordered["word_to_window"]
    window_contents = {int(k): v for k, v in reordered["window_contents"].items()}

    console.print(f"    Lattice: {len(lattice_map)} tokens, {len(window_contents)} windows")
    return lattice_map, window_contents


# ── D3.2: Compute Full Signature ───────────────────────────────────

def compute_signature(lines, lattice_map, window_contents, name):
    """Compute the full signature for a corpus given its lattice."""
    console.print(f"\n  Computing signature for [cyan]{name}[/cyan]...")

    vocab = set(lattice_map.keys())
    engine = EvaluationEngine(vocab)
    num_windows = len(window_contents)

    # 1. Corrected admissibility
    corrections = learn_offset_corrections(lines, lattice_map, num_windows)
    corrected_rate = score_with_correction(
        lines, lattice_map, window_contents, corrections, num_windows
    )

    # 2. Overgeneration — skip emulator for non-Voynich (use simple n-gram generation)
    # Generate pseudo-synthetic lines from window contents
    rng = np.random.default_rng(42)
    syn_lines = []
    window_ids = list(window_contents.keys())
    for _ in range(len(lines)):
        line_len = rng.integers(4, 11)
        syn_line = []
        win = rng.choice(window_ids)
        for _ in range(line_len):
            words = window_contents.get(win, [])
            if words:
                syn_line.append(rng.choice(words))
            win = (win + rng.integers(-1, 2)) % num_windows
        syn_lines.append(syn_line)

    overgen = engine.calculate_overgeneration(syn_lines, lines)
    bur = overgen["BUR"]["rate"]
    tur = overgen["TUR"]["rate"]

    # 3. Branching factor
    window_sizes = [len(v) for v in window_contents.values()]
    mean_branching = np.mean(window_sizes) if window_sizes else 0
    effective_bits = math.log2(mean_branching) if mean_branching > 1 else 0

    # 4. Moran's I
    corr_vec = [corrections.get(w, 0) for w in range(num_windows)]
    morans_i = compute_morans_i(corr_vec)

    # 5. FFT dominant power
    fft_power = compute_fft_dominant(corr_vec)

    # 6. BIC models
    bic_volvelle, bic_grille = compute_bic_models(corr_vec)

    # 7. Selection entropy
    all_tokens = [t for line in lines for t in line if t in vocab]
    counts = Counter(all_tokens)
    total = len(all_tokens)
    if total > 0:
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    else:
        entropy = 0

    # 8. Cross-section transfer
    sections = split_sections(lines)
    transfer_rate = cross_section_transfer(sections, lattice_map, window_contents, num_windows)

    sig = {
        "corrected_admissibility": round(corrected_rate, 4),
        "bur": round(bur, 4),
        "tur": round(tur, 4),
        "mean_branching_factor": round(float(mean_branching), 1),
        "effective_bits": round(effective_bits, 2),
        "morans_i": round(morans_i, 4),
        "fft_dominant_power": round(fft_power, 4),
        "bic_volvelle": round(float(bic_volvelle), 1),
        "bic_grille": round(float(bic_grille), 1),
        "selection_entropy_bpw": round(entropy, 4),
        "cross_section_transfer": round(transfer_rate, 4),
        "num_windows": num_windows,
        "vocab_in_lattice": len(lattice_map),
    }

    console.print(f"    Admissibility: {corrected_rate:.4f}, Moran's I: {morans_i:.4f}, "
                  f"FFT: {fft_power:.4f}, Entropy: {entropy:.2f}")

    return sig


# ── D3.3: Signature Comparison ─────────────────────────────────────

def compare_signatures(voynich_card, corpus_sigs, null_dist):
    """Compare each corpus signature against the Voynich reference."""
    console.rule("[bold blue]D3.3: Signature Comparison")

    # Metrics to compare (those with null distributions for z-scoring)
    z_metrics = ["corrected_admissibility", "morans_i", "fft_dominant_power",
                 "selection_entropy_bpw"]

    comparison = {}
    for name, sig in corpus_sigs.items():
        distances = {}
        for metric in z_metrics:
            voynich_val = voynich_card[metric]["voynich_value"]
            corpus_val = sig.get(metric, 0)
            null_std = null_dist.get(metric, {}).get("std", 1)
            null_mean = null_dist.get(metric, {}).get("mean", 0)

            # Z-score of corpus value against null
            z_corpus = (corpus_val - null_mean) / null_std if null_std > 0 else 0
            # Z-score of Voynich value against null
            z_voynich = voynich_card[metric].get("z_score", 0)
            # Distance between corpus and Voynich in null-z space
            distances[metric] = {
                "corpus_value": corpus_val,
                "voynich_value": voynich_val,
                "corpus_z": round(z_corpus, 2),
                "voynich_z": round(z_voynich, 2) if isinstance(z_voynich, (int, float)) else 0,
                "delta_z": round(abs(z_corpus - (z_voynich if isinstance(z_voynich, (int, float)) else 0)), 2),
            }

        # Euclidean distance in z-space
        z_diffs = [d["delta_z"] for d in distances.values()]
        euclidean = math.sqrt(sum(d ** 2 for d in z_diffs))

        comparison[name] = {
            "per_metric": distances,
            "euclidean_distance_z": round(euclidean, 2),
        }

    # Display
    table = Table(title="Distance from Voynich (z-space)")
    table.add_column("Corpus", style="cyan")
    table.add_column("Admiss. Δz", justify="right")
    table.add_column("Moran Δz", justify="right")
    table.add_column("FFT Δz", justify="right")
    table.add_column("Entropy Δz", justify="right")
    table.add_column("Euclidean", justify="right", style="bold")

    for name, comp in sorted(comparison.items(), key=lambda x: x[1]["euclidean_distance_z"]):
        m = comp["per_metric"]
        table.add_row(
            name,
            f"{m['corrected_admissibility']['delta_z']:.2f}",
            f"{m['morans_i']['delta_z']:.2f}",
            f"{m['fft_dominant_power']['delta_z']:.2f}",
            f"{m['selection_entropy_bpw']['delta_z']:.2f}",
            f"{comp['euclidean_distance_z']:.2f}",
        )

    console.print(table)
    return comparison


# ── D3.4: Discrimination Assessment ────────────────────────────────

def assess_discrimination(comparison):
    """Can the battery distinguish Voynich from other text types?"""
    console.rule("[bold blue]D3.4: Discrimination Assessment")

    assessments = {}
    for name, comp in comparison.items():
        dist = comp["euclidean_distance_z"]
        if dist < 2.0:
            verdict = "SIMILAR"
        elif dist < 5.0:
            verdict = "DISTINCT"
        else:
            verdict = "VERY_DISTINCT"

        assessments[name] = {
            "distance": dist,
            "verdict": verdict,
        }
        tag = {"SIMILAR": "[yellow]", "DISTINCT": "[blue]", "VERY_DISTINCT": "[green]"}[verdict]
        console.print(f"  {name}: {tag}{verdict}[/{tag[1:]} (d={dist:.2f})")

    return assessments


# ── Main ─────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint D3: Comparative Signature Analysis")

    # Load D1 outputs
    if not SIGNATURE_PATH.exists():
        console.print("[red]Error: Run D1 first (run_18a_signature_battery.py)[/red]")
        return
    with open(SIGNATURE_PATH) as f:
        sig_data = json.load(f)
    voynich_card = sig_data["results"]["signature_card"]
    null_dist = sig_data["results"]["null_distributions"]
    console.print("Loaded Voynich signature card and null distributions.")

    # Load D2 outputs
    if not INGESTED_PATH.exists():
        console.print("[red]Error: Run D2 first (run_18b_corpus_ingestion.py)[/red]")
        return
    with open(INGESTED_PATH) as f:
        ingest_data = json.load(f)
    corpora = ingest_data["results"]["corpora"]
    console.print(f"Loaded {len(corpora)} ingested corpora.")

    # D3.1-D3.2: Build lattice and compute signature for each corpus
    corpus_sigs = {}
    for name, data in corpora.items():
        if name == "voynich":
            continue  # Already have Voynich signature from D1

        lines = data["lines"]
        if not lines:
            console.print(f"  [yellow]Skipping {name} — no lines[/yellow]")
            continue

        lattice_map, window_contents = build_lattice_for_corpus(lines, name)
        sig = compute_signature(lines, lattice_map, window_contents, name)
        corpus_sigs[name] = sig

    # D3.3: Compare signatures
    comparison = compare_signatures(voynich_card, corpus_sigs, null_dist)

    # D3.4: Discrimination assessment
    assessments = assess_discrimination(comparison)

    # Summary
    console.rule("[bold magenta]Summary")
    console.print(
        "\n[bold]Key Finding:[/bold] The signature battery measures how closely "
        "each text's structural properties match the Voynich manuscript's unique "
        "lattice-generated fingerprint. Texts with high Euclidean distance in "
        "z-space are structurally different from the Voynich."
    )

    results = {
        "corpus_signatures": corpus_sigs,
        "comparison": comparison,
        "discrimination": assessments,
    }

    ProvenanceWriter.save_results(sanitize(results), OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_18c_comparative_analysis"}):
        main()
