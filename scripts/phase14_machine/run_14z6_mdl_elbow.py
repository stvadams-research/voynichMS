#!/usr/bin/env python3
"""Phase 14Z6: MDL Elbow Analysis.

Performs a dense sweep of window counts (K) to find the MDL-optimal
number of lattice windows using corrected two-part coding.

The existing minimality_sweep.json uses a simplified MDL formula and
only 9 data points. This script:

1. Solves the physical layout ONCE, then re-clusters at 20 K values.
2. Uses the corrected frequency-conditional L(model) from 14Z.
3. Computes L(data|model) as empirical conditional entropy H(word|window).
4. Identifies the knee-point via second-derivative and Kneedle algorithm.
5. Quantifies the penalty of K=50 vs the optimal K.
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

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase14_machine.palette_solver import GlobalPaletteSolver  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
SLIP_PATH = (
    project_root / "results/data/phase12_mechanical/slip_detection_results.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/mdl_elbow.json"
)
console = Console()

# Dense sweep: 20 values from 2 to 500
K_VALUES = [2, 3, 5, 7, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 100,
            150, 200, 350, 500]


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


def compute_corrected_l_model(lattice_map, corpus_freq, num_windows):
    """Compute frequency-conditional L(model).

    Groups words by corpus frequency bucket, then computes:
    L(model) = N_words * H(window | freq_bucket) + overhead

    This is the corrected computation from run_14z (Method 5).
    """
    num_words = len(lattice_map)

    # Frequency buckets
    bucket_groups = defaultdict(lambda: defaultdict(int))
    for word, win_id in lattice_map.items():
        freq = corpus_freq.get(word, 0)
        if freq == 0:
            bucket = "zero"
        elif freq == 1:
            bucket = "hapax"
        elif freq <= 5:
            bucket = "rare"
        elif freq <= 20:
            bucket = "low"
        elif freq <= 100:
            bucket = "medium"
        else:
            bucket = "high"
        bucket_groups[bucket][win_id] += 1

    # H(window | freq_bucket) weighted by bucket size
    h_freq_cond = 0.0
    for _bucket, win_counts in bucket_groups.items():
        bucket_total = sum(win_counts.values())
        h_bucket = entropy(list(win_counts.values()))
        h_freq_cond += (bucket_total / num_words) * h_bucket

    # L(model) = encoding cost + small overhead for bucket distributions
    freq_bits = num_words * h_freq_cond
    freq_overhead = len(bucket_groups) * num_windows
    return freq_bits + freq_overhead


def compute_l_data(lines, lattice_map, window_contents, num_windows):
    """Compute L(data|model) as empirical conditional entropy.

    L(data|model) = sum over tokens: -log2 P(word | window)

    For tokens not in the lattice, assign uniform cost log2(vocab).
    """
    # Build per-window word frequency from actual corpus usage
    window_word_freq = defaultdict(Counter)
    current_window = 0
    total_tokens = 0
    out_of_palette = 0
    vocab = set(lattice_map.keys())

    for line in lines:
        for word in line:
            total_tokens += 1
            if word not in lattice_map:
                out_of_palette += 1
                continue

            # Track which window the word appeared in
            window_word_freq[current_window][word] += 1
            current_window = lattice_map[word]

    # Total bits: for each token, -log2(P(word | effective_window))
    # But we don't have the true conditional distribution — approximate
    # with the unigram-within-window distribution
    total_bits = 0.0
    current_window = 0

    for line in lines:
        for word in line:
            if word not in lattice_map:
                # Uniform cost for OOV
                if len(vocab) > 0:
                    total_bits += math.log2(len(vocab) + 1)
                current_window = 0
                continue

            # P(word | window) from window contents (uniform within window)
            win_words = window_contents.get(current_window, [])
            if word in win_words and len(win_words) > 0:
                # Word is in the expected window
                total_bits += math.log2(len(win_words))
            else:
                # Word is not in expected window — penalty
                # Check drift windows
                found = False
                for d in [-1, 0, 1]:
                    check_win = (current_window + d) % num_windows
                    cw = window_contents.get(check_win, [])
                    if word in cw and len(cw) > 0:
                        total_bits += math.log2(len(cw))
                        found = True
                        break
                if not found:
                    # Full search penalty
                    total_bits += math.log2(len(vocab)) if len(vocab) > 0 else 0

            current_window = lattice_map[word]

    return total_bits


def measure_admissibility(lines, lattice_map, window_contents, num_windows):
    """Measure drift (±1) admissibility rate."""
    admissible = 0
    total = 0
    current_window = 0

    for line in lines:
        for word in line:
            if word not in lattice_map:
                continue
            total += 1

            found = False
            for d in [-1, 0, 1]:
                check_win = (current_window + d) % num_windows
                if word in window_contents.get(check_win, []):
                    found = True
                    current_window = lattice_map[word]
                    break

            if found:
                admissible += 1
            else:
                current_window = lattice_map[word]

    return admissible / total if total > 0 else 0, total


def kneedle_detect(x, y):
    """Kneedle algorithm for knee-point detection.

    Finds the point of maximum curvature in a curve.
    Returns the index of the knee-point.
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if len(x) < 3:
        return 0

    # Normalize to [0, 1]
    x_norm = (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x
    y_norm = (y - y.min()) / (y.max() - y.min()) if y.max() > y.min() else y

    # Compute the difference from the diagonal line (first to last)
    # The knee is where this difference is maximized
    line_y = np.linspace(y_norm[0], y_norm[-1], len(y_norm))
    differences = y_norm - line_y

    # For a decreasing curve (MDL should decrease then flatten),
    # the knee is where the curve bends — maximum positive difference
    # from the line connecting endpoints
    knee_idx = int(np.argmax(np.abs(differences)))
    return knee_idx


def second_derivative_detect(x, y):
    """Find knee-point via second derivative.

    Returns the index where the second derivative is maximized
    (point of maximum curvature).
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if len(x) < 3:
        return 0

    # Compute second derivative using finite differences
    dy = np.diff(y) / np.diff(x)
    d2y = np.diff(dy) / np.diff(x[:-1])

    if len(d2y) == 0:
        return 0

    # The knee is where the second derivative magnitude is highest
    knee_idx = int(np.argmax(np.abs(d2y))) + 1  # +1 for offset
    return knee_idx


def main():
    console.print(
        "[bold blue]Phase 14Z6: MDL Elbow Analysis[/bold blue]"
    )

    # ── 1. Load corpus ──
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    all_tokens = [t for line in lines for t in line]
    corpus_freq = Counter(all_tokens)
    total_tokens = len(all_tokens)
    console.print(f"Corpus: {total_tokens:,} tokens")

    # ── 2. Load slips ──
    slips = []
    if SLIP_PATH.exists():
        with open(SLIP_PATH) as f:
            slip_data = json.load(f)
        slips = slip_data.get("results", slip_data).get("slips", [])
        console.print(f"Loaded {len(slips)} mechanical slips.")

    # ── 3. Solve physical layout ONCE ──
    console.print("\nSolving physical layout (one-time)...")
    solver = GlobalPaletteSolver()
    solver.ingest_data(slips, lines, top_n=8000)
    solved_pos = solver.solve_grid(iterations=30)
    console.print(f"Layout solved for {len(solved_pos)} tokens.")

    # ── 4. Sweep K values ──
    sweep_results = []

    for k in K_VALUES:
        console.print(f"\n  [bold]K = {k}[/bold]")

        # Re-cluster at this K
        lattice_data = solver.cluster_lattice(solved_pos, num_windows=k)
        lattice_map = lattice_data["word_to_window"]
        window_contents = lattice_data["window_contents"]
        num_windows = len(window_contents)

        # Corrected L(model)
        l_model = compute_corrected_l_model(
            lattice_map, corpus_freq, num_windows
        )

        # L(data|model)
        l_data = compute_l_data(
            lines, lattice_map, window_contents, num_windows
        )

        l_total = l_model + l_data
        bpt = l_total / total_tokens

        # Admissibility
        adm_rate, adm_total = measure_admissibility(
            lines, lattice_map, window_contents, num_windows
        )

        console.print(
            f"    L(model)={l_model:,.0f}, L(data)={l_data:,.0f}, "
            f"L(total)={l_total:,.0f}"
        )
        console.print(
            f"    BPT={bpt:.4f}, Admissibility={adm_rate*100:.2f}%"
        )

        sweep_results.append({
            "K": k,
            "num_windows": num_windows,
            "l_model": l_model,
            "l_data": l_data,
            "l_total": l_total,
            "bpt": bpt,
            "admissibility": adm_rate,
            "clamped_tokens": adm_total,
            "lattice_size": len(lattice_map),
        })

    # ── 5. Knee-point detection ──
    k_values = [r["K"] for r in sweep_results]
    l_totals = [r["l_total"] for r in sweep_results]

    kneedle_idx = kneedle_detect(k_values, l_totals)
    second_deriv_idx = second_derivative_detect(k_values, l_totals)

    kneedle_k = k_values[kneedle_idx]
    second_deriv_k = k_values[second_deriv_idx]

    console.print(f"\n{'='*60}")
    console.print("[bold]Knee-Point Detection:[/bold]")
    console.print(f"  Kneedle algorithm: K = {kneedle_k}")
    console.print(f"  Second derivative: K = {second_deriv_k}")

    # Use the average or consensus
    optimal_k = kneedle_k
    if kneedle_k == second_deriv_k:
        console.print(f"  [green]Consensus: K = {optimal_k}[/green]")
    else:
        # Pick the one with lower BPT
        bpt_kneedle = sweep_results[kneedle_idx]["bpt"]
        bpt_2nd = sweep_results[second_deriv_idx]["bpt"]
        optimal_k = kneedle_k if bpt_kneedle <= bpt_2nd else second_deriv_k
        console.print(
            f"  [yellow]Disagreement: using K = {optimal_k} "
            f"(lower BPT)[/yellow]"
        )

    # ── 6. Penalty quantification ──
    # Find K=50 result
    k50_result = next(
        (r for r in sweep_results if r["K"] == 50), None
    )
    optimal_result = next(
        (r for r in sweep_results if r["K"] == optimal_k), None
    )

    if k50_result and optimal_result:
        penalty_bits = k50_result["l_total"] - optimal_result["l_total"]
        penalty_bpt = k50_result["bpt"] - optimal_result["bpt"]
        adm_tradeoff = k50_result["admissibility"] - optimal_result["admissibility"]

        console.print(f"\n[bold]K=50 Penalty vs Optimal K={optimal_k}:[/bold]")
        console.print(
            f"  L(total) penalty: {penalty_bits:+,.0f} bits "
            f"({penalty_bpt:+.4f} BPT)"
        )
        console.print(
            f"  Admissibility tradeoff: {adm_tradeoff:+.2%}"
        )

        if abs(penalty_bpt) < 0.5:
            console.print(
                f"  [green]JUSTIFIED:[/green] K=50 penalty is small "
                f"({penalty_bpt:+.4f} BPT < 0.5 threshold)"
            )
        else:
            console.print(
                f"  [yellow]FLAG:[/yellow] K=50 penalty is significant "
                f"({penalty_bpt:+.4f} BPT)"
            )

    # ── 7. Summary table ──
    table = Table(title="MDL Sweep Results")
    table.add_column("K", justify="right", style="cyan")
    table.add_column("L(model)", justify="right")
    table.add_column("L(data)", justify="right")
    table.add_column("L(total)", justify="right")
    table.add_column("BPT", justify="right", style="bold")
    table.add_column("Adm.", justify="right", style="green")
    table.add_column("Note", justify="left")

    for r in sweep_results:
        note = ""
        if r["K"] == 50:
            note = "← current"
        elif r["K"] == optimal_k:
            note = "← optimal"

        table.add_row(
            str(r["K"]),
            f"{r['l_model']:,.0f}",
            f"{r['l_data']:,.0f}",
            f"{r['l_total']:,.0f}",
            f"{r['bpt']:.4f}",
            f"{r['admissibility']*100:.1f}%",
            note,
        )
    console.print(table)

    # ── 8. Save results ──
    results = {
        "sweep": sweep_results,
        "knee_point": {
            "kneedle_k": kneedle_k,
            "kneedle_idx": kneedle_idx,
            "second_derivative_k": second_deriv_k,
            "second_derivative_idx": second_deriv_idx,
            "selected_optimal_k": optimal_k,
            "methods_agree": kneedle_k == second_deriv_k,
        },
        "penalty_at_k50": {
            "optimal_k": optimal_k,
            "k50_l_total": k50_result["l_total"] if k50_result else None,
            "optimal_l_total": optimal_result["l_total"] if optimal_result else None,
            "penalty_bits": penalty_bits if k50_result and optimal_result else None,
            "penalty_bpt": penalty_bpt if k50_result and optimal_result else None,
            "admissibility_tradeoff": adm_tradeoff if k50_result and optimal_result else None,
            "k50_justified": abs(penalty_bpt) < 0.5 if k50_result and optimal_result else None,
        },
        "total_tokens": total_tokens,
        "layout_size": len(solved_pos),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z6_mdl_elbow"}
    ):
        main()
