#!/usr/bin/env python3
"""Phase 15D: Within-Window Selection Driver Analysis.

Phase 15 found 21.49% selection skew within windows.
Phase 16 proved it's NOT ergonomic (rho=-0.0003).
This script tests 5 hypotheses for what drives the bias:

1. Positional bias: scribe prefers top-of-window items
2. Bigram context: prev_word predicts chosen_word
3. Suffix affinity: chosen_word shares suffix with prev_word
4. Frequency bias: globally frequent words preferred
5. Recency bias: recently-used words in same window re-chosen
"""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table
from scipy import stats

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_selection/choice_stream_trace.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase15_selection/selection_drivers.json"
)
console = Console()


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


def test_positional_bias(choices):
    """Test if chosen_index is biased toward small values (top-of-window).

    H0: chosen_index / candidates_count ~ Uniform(0, 1)
    """
    console.print("\n[bold]Hypothesis A: Positional Bias[/bold]")

    # Compute relative position for each choice
    positions = []
    for c in choices:
        if c["candidates_count"] > 1:
            rel_pos = c["chosen_index"] / (c["candidates_count"] - 1)
            positions.append(rel_pos)

    positions = np.array(positions)
    mean_pos = np.mean(positions)
    median_pos = np.median(positions)

    # KS test against Uniform(0, 1)
    ks_stat, ks_p = stats.kstest(positions, "uniform")

    # Effect size: how much entropy is reduced vs uniform
    # Bin positions into 20 bins and measure entropy
    hist, _ = np.histogram(positions, bins=20, range=(0, 1))
    h_observed = entropy(hist.tolist())
    h_uniform = math.log2(20)  # max entropy for 20 bins
    bits_explained = h_uniform - h_observed

    console.print(
        f"  Mean relative position: {mean_pos:.4f} (0.5 = unbiased)"
    )
    console.print(f"  Median: {median_pos:.4f}")
    console.print(
        f"  KS test: D={ks_stat:.4f}, p={ks_p:.2e}"
    )
    console.print(f"  Entropy reduction: {bits_explained:.3f} bits")

    return {
        "mean_relative_position": float(mean_pos),
        "median_relative_position": float(median_pos),
        "ks_statistic": float(ks_stat),
        "ks_p_value": float(ks_p),
        "is_significant": ks_p < 0.01,
        "bits_explained": float(bits_explained),
        "n": len(positions),
        "direction": "top" if mean_pos < 0.45 else (
            "bottom" if mean_pos > 0.55 else "neutral"
        ),
    }


def test_bigram_context(choices):
    """Test if prev_word reduces entropy of chosen_word within window.

    Computes H(chosen | window) vs H(chosen | window, prev_word).
    """
    console.print("\n[bold]Hypothesis B: Bigram Context[/bold]")

    # H(chosen | window)
    window_choices = defaultdict(list)
    for c in choices:
        window_choices[c["window_id"]].append(c["chosen_word"])

    h_given_window = 0.0
    total = len(choices)
    for _win_id, words in window_choices.items():
        p_window = len(words) / total
        counts = list(Counter(words).values())
        h_given_window += p_window * entropy(counts)

    # H(chosen | window, prev_word) — filter to pairs with ≥5 obs
    pair_choices = defaultdict(list)
    for c in choices:
        if c["prev_word"]:
            key = (c["window_id"], c["prev_word"])
            pair_choices[key].append(c["chosen_word"])

    h_given_pair = 0.0
    eligible_total = 0
    eligible_pairs = 0
    for _key, words in pair_choices.items():
        if len(words) >= 5:
            eligible_total += len(words)
            eligible_pairs += 1

    # Recompute with eligible pairs only
    if eligible_total > 0:
        for _key, words in pair_choices.items():
            if len(words) >= 5:
                p_pair = len(words) / eligible_total
                counts = list(Counter(words).values())
                h_given_pair += p_pair * entropy(counts)

    info_gain = h_given_window - h_given_pair if eligible_total > 0 else 0

    console.print(
        f"  H(chosen | window) = {h_given_window:.3f} bits"
    )
    console.print(
        f"  H(chosen | window, prev) = {h_given_pair:.3f} bits "
        f"({eligible_pairs} eligible pairs)"
    )
    console.print(
        f"  Information gain: {info_gain:.3f} bits"
    )

    return {
        "h_given_window": float(h_given_window),
        "h_given_window_prev": float(h_given_pair),
        "information_gain_bits": float(info_gain),
        "eligible_pairs": eligible_pairs,
        "eligible_observations": eligible_total,
        "is_significant": info_gain > 0.1,
        "bits_explained": float(info_gain),
    }


def test_suffix_affinity(choices, lattice_map, window_contents):
    """Test if chosen_word shares suffix with prev_word more than expected."""
    console.print("\n[bold]Hypothesis C: Suffix Affinity[/bold]")

    observed_matches = 0
    expected_rate_sum = 0.0
    valid_count = 0

    for c in choices:
        prev = c["prev_word"]
        chosen = c["chosen_word"]
        win_id = c["window_id"]

        if not prev or len(prev) < 2 or len(chosen) < 2:
            continue

        suffix = prev[-2:]

        # Check if chosen word shares suffix
        match = chosen[-2:] == suffix

        # Expected rate: proportion of window words sharing suffix
        win_words = window_contents.get(win_id, [])
        matching_in_window = sum(
            1 for w in win_words if len(w) >= 2 and w[-2:] == suffix
        )
        expected = matching_in_window / len(win_words) if win_words else 0

        if match:
            observed_matches += 1
        expected_rate_sum += expected
        valid_count += 1

    observed_rate = observed_matches / valid_count if valid_count > 0 else 0
    expected_rate = expected_rate_sum / valid_count if valid_count > 0 else 0

    # Chi-squared-like comparison
    if expected_rate > 0 and valid_count > 0:
        excess = observed_rate / expected_rate
        # Z-test for proportions
        se = math.sqrt(expected_rate * (1 - expected_rate) / valid_count)
        z = (observed_rate - expected_rate) / se if se > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    else:
        excess = 0
        z = 0
        p_value = 1.0

    console.print(
        f"  Observed suffix match rate: {observed_rate:.4f}"
    )
    console.print(
        f"  Expected (by window composition): {expected_rate:.4f}"
    )
    console.print(
        f"  Excess ratio: {excess:.2f}x"
    )
    console.print(
        f"  Z-test: z={z:.2f}, p={p_value:.2e}"
    )

    return {
        "observed_match_rate": float(observed_rate),
        "expected_match_rate": float(expected_rate),
        "excess_ratio": float(excess),
        "z_score": float(z),
        "p_value": float(p_value),
        "is_significant": p_value < 0.01,
        "valid_observations": valid_count,
        "bits_explained": float(
            abs(observed_rate - expected_rate) * math.log2(max(excess, 0.001))
        ) if excess > 0 else 0.0,
    }


def test_frequency_bias(choices, corpus_freq):
    """Test if globally frequent words are preferentially chosen within windows."""
    console.print("\n[bold]Hypothesis D: Frequency Bias[/bold]")

    # For each window, compute selection rate and corpus frequency per word
    window_word_selections = defaultdict(Counter)

    for c in choices:
        window_word_selections[c["window_id"]][c["chosen_word"]] += 1

    # Build per-window frequency vs selection arrays
    freq_ranks = []
    sel_rates = []

    for _win_id, selections in window_word_selections.items():
        total_selections = sum(selections.values())
        for word, sel_count in selections.items():
            sel_rate = sel_count / total_selections
            freq = corpus_freq.get(word, 0)
            freq_ranks.append(freq)
            sel_rates.append(sel_rate)

    # Spearman correlation
    rho, p_value = stats.spearmanr(freq_ranks, sel_rates)

    console.print(
        f"  Spearman rho (corpus_freq vs within-window selection): "
        f"{rho:.4f}"
    )
    console.print(f"  p-value: {p_value:.2e}")

    # Effect size: how much selection skew is explained by frequency
    bits_explained = abs(rho) * 0.5  # rough approximation

    return {
        "spearman_rho": float(rho),
        "p_value": float(p_value),
        "is_significant": p_value < 0.01,
        "n_word_window_pairs": len(freq_ranks),
        "bits_explained": float(bits_explained),
    }


def test_recency_bias(choices):
    """Test if recently-used words in the same window are re-chosen more often."""
    console.print("\n[bold]Hypothesis E: Recency Bias[/bold]")

    # Track last-seen position for each (window, word) pair
    last_seen = {}  # (window_id, word) -> last position in choice stream
    recency_scores = []  # 1 if word was seen recently, 0 otherwise

    recent_window = 50  # "recently" = within last 50 choices

    for i, c in enumerate(choices):
        win_id = c["window_id"]
        word = c["chosen_word"]
        key = (win_id, word)

        if key in last_seen:
            gap = i - last_seen[key]
            is_recent = 1 if gap <= recent_window else 0
            recency_scores.append(is_recent)
        else:
            recency_scores.append(0)

        last_seen[key] = i

    observed_recent_rate = np.mean(recency_scores) if recency_scores else 0

    # Expected rate: simulate random choices within windows
    # Use the overall re-encounter probability as baseline
    rng = np.random.RandomState(42)
    null_scores = []
    for _ in range(100):
        shuffled_last_seen = {}
        null_recency = []
        shuffled_choices = list(choices)
        rng.shuffle(shuffled_choices)
        for i, c in enumerate(shuffled_choices):
            key = (c["window_id"], c["chosen_word"])
            if key in shuffled_last_seen:
                gap = i - shuffled_last_seen[key]
                null_recency.append(1 if gap <= recent_window else 0)
            else:
                null_recency.append(0)
            shuffled_last_seen[key] = i
        null_scores.append(np.mean(null_recency))

    null_mean = np.mean(null_scores)
    null_std = np.std(null_scores)
    z = (observed_recent_rate - null_mean) / null_std if null_std > 0 else 0
    advantage = observed_recent_rate - null_mean

    console.print(
        f"  Recent reuse rate (within {recent_window} choices): "
        f"{observed_recent_rate:.4f}"
    )
    console.print(
        f"  Null expectation: {null_mean:.4f} ± {null_std:.4f}"
    )
    console.print(
        f"  Recency advantage: {advantage:.4f} (z={z:.2f})"
    )

    return {
        "observed_recent_rate": float(observed_recent_rate),
        "null_mean": float(null_mean),
        "null_std": float(null_std),
        "recency_advantage": float(advantage),
        "z_score": float(z),
        "is_significant": abs(z) > 2.576,  # p < 0.01
        "recent_window": recent_window,
        "bits_explained": float(abs(advantage) * 2),  # rough bits estimate
    }


def main():
    console.print(
        "[bold blue]Phase 15D: Within-Window Selection Drivers[/bold blue]"
    )

    # 1. Load choice stream
    with open(CHOICE_STREAM_PATH) as f:
        trace_data = json.load(f)

    # Handle provenance-wrapped format
    if "results" in trace_data:
        choices = trace_data["results"].get("choices", [])
        if not choices:
            # Try alternate key
            choices = trace_data["results"].get("choice_stream", [])
    else:
        choices = trace_data if isinstance(trace_data, list) else []

    if not choices:
        console.print("[red]No choice records found in trace file.[/red]")
        # Try to list available keys
        if "results" in trace_data:
            console.print(
                f"  Available keys: {list(trace_data['results'].keys())}"
            )
        return

    console.print(f"Loaded {len(choices)} choice records.")

    # 2. Load corpus frequencies and lattice
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    all_tokens = [t for line in lines for t in line]
    corpus_freq = Counter(all_tokens)

    # Load window_contents for suffix affinity test
    palette_path = (
        project_root / "results/data/phase14_machine/full_palette_grid.json"
    )
    with open(palette_path) as f:
        palette = json.load(f)["results"]
    lattice_map = palette["lattice_map"]
    window_contents = {int(k): v for k, v in palette["window_contents"].items()}

    # 3. Run hypothesis tests
    results = {}
    results["positional_bias"] = test_positional_bias(choices)
    results["bigram_context"] = test_bigram_context(choices)
    results["suffix_affinity"] = test_suffix_affinity(
        choices, lattice_map, window_contents,
    )
    results["frequency_bias"] = test_frequency_bias(choices, corpus_freq)
    results["recency_bias"] = test_recency_bias(choices)

    # 4. Rank by bits explained
    ranked = sorted(
        results.items(),
        key=lambda x: x[1].get("bits_explained", 0),
        reverse=True,
    )

    console.print("\n[bold]Ranked Selection Drivers[/bold]")
    table = Table()
    table.add_column("Hypothesis", style="cyan")
    table.add_column("Bits Explained", justify="right")
    table.add_column("Significant?", justify="center")
    table.add_column("Key Metric")

    for name, r in ranked:
        sig = "[green]YES[/green]" if r.get("is_significant") else "[red]no[/red]"
        if name == "positional_bias":
            key = f"mean_pos={r['mean_relative_position']:.3f}"
        elif name == "bigram_context":
            key = f"IG={r['information_gain_bits']:.3f} bits"
        elif name == "suffix_affinity":
            key = f"excess={r['excess_ratio']:.2f}x"
        elif name == "frequency_bias":
            key = f"rho={r['spearman_rho']:.4f}"
        elif name == "recency_bias":
            key = f"adv={r['recency_advantage']:.4f}"
        else:
            key = "—"

        table.add_row(
            name.replace("_", " ").title(),
            f"{r.get('bits_explained', 0):.3f}",
            sig,
            key,
        )

    console.print(table)

    # 5. Save results (convert numpy types to Python natives)
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        elif isinstance(obj, (np.bool_, np.integer)):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return obj

    output = sanitize({
        "num_choices": len(choices),
        "hypotheses": results,
        "ranked_drivers": [
            {"hypothesis": name, "bits_explained": r.get("bits_explained", 0)}
            for name, r in ranked
        ],
        "top_driver": ranked[0][0] if ranked else None,
    })

    ProvenanceWriter.save_results(output, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_15d_selection_drivers"}
    ):
        main()
