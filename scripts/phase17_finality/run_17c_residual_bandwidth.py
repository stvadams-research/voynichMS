#!/usr/bin/env python3
"""Sprint A1: Residual Bandwidth Decomposition.

The raw 7.53 bpw realized bandwidth includes entropy explained by known
mechanical drivers (bigram context, positional bias, recency, suffix
affinity, frequency bias).  This script computes the progressive
conditional entropy chain to determine the *residual steganographic
bandwidth* (RSB) — the bits per word that cannot be explained by any
known mechanical or structural driver.

Tasks:
  A1.1 — Conditional entropy chain
  A1.2 — Independence check (joint vs sum-of-marginals)
  A1.3 — Per-window RSB profile
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

CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_selection/choice_stream_trace.json"
)
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/residual_bandwidth.json"
console = Console()


# ── Helpers ───────────────────────────────────────────────────────────

def entropy_bits(counts):
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


def conditional_entropy(groups):
    """Weighted average entropy across groups: H(Y | X) = sum p(x) H(Y|X=x)."""
    total = sum(len(v) for v in groups.values())
    if total == 0:
        return 0.0
    h = 0.0
    for words in groups.values():
        p_group = len(words) / total
        counts = list(Counter(words).values())
        h += p_group * entropy_bits(counts)
    return h


def position_bucket(token_pos, n_buckets=5):
    """Bin token position into buckets."""
    if token_pos <= 0:
        return 0
    if token_pos <= 2:
        return 1
    if token_pos <= 5:
        return 2
    if token_pos <= 9:
        return 3
    return 4


# ── A1.1: Conditional Entropy Chain ──────────────────────────────────

def compute_entropy_chain(choices):
    """Progressively condition choice entropy on each driver."""
    console.rule("[bold blue]A1.1: Conditional Entropy Chain")

    # 1. H(choice | window) — base entropy within windows
    groups_w = defaultdict(list)
    for c in choices:
        groups_w[c["window_id"]].append(c["chosen_word"])
    h_window = conditional_entropy(groups_w)
    console.print(f"  H(choice | window) = {h_window:.4f} bits")

    # 2. H(choice | window, prev_word)
    groups_wp = defaultdict(list)
    for c in choices:
        prev = c.get("prev_word") or "__none__"
        groups_wp[(c["window_id"], prev)].append(c["chosen_word"])
    h_window_prev = conditional_entropy(groups_wp)
    console.print(f"  H(choice | window, prev_word) = {h_window_prev:.4f} bits")

    # 3. H(choice | window, prev_word, position_bucket)
    groups_wpp = defaultdict(list)
    for c in choices:
        prev = c.get("prev_word") or "__none__"
        pos_b = position_bucket(c["token_pos"])
        groups_wpp[(c["window_id"], prev, pos_b)].append(c["chosen_word"])
    h_window_prev_pos = conditional_entropy(groups_wpp)
    console.print(f"  H(choice | window, prev, position) = {h_window_prev_pos:.4f} bits")

    # 4. H(choice | window, prev_word, position, recency)
    # Recency: was the chosen word used within the last 50 choices?
    last_seen = {}
    choices_with_recency = []
    for i, c in enumerate(choices):
        key = (c["window_id"], c["chosen_word"])
        is_recent = 0
        if key in last_seen and (i - last_seen[key]) <= 50:
            is_recent = 1
        last_seen[key] = i
        choices_with_recency.append({**c, "is_recent": is_recent})

    groups_wppr = defaultdict(list)
    for c in choices_with_recency:
        prev = c.get("prev_word") or "__none__"
        pos_b = position_bucket(c["token_pos"])
        groups_wppr[(c["window_id"], prev, pos_b, c["is_recent"])].append(
            c["chosen_word"]
        )
    h_window_prev_pos_rec = conditional_entropy(groups_wppr)
    console.print(
        f"  H(choice | window, prev, position, recency) = "
        f"{h_window_prev_pos_rec:.4f} bits"
    )

    # 5. H(choice | window, prev_word, position, recency, suffix)
    groups_wpprs = defaultdict(list)
    for c in choices_with_recency:
        prev = c.get("prev_word") or "__none__"
        pos_b = position_bucket(c["token_pos"])
        suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"
        groups_wpprs[
            (c["window_id"], prev, pos_b, c["is_recent"], suffix)
        ].append(c["chosen_word"])
    h_all_drivers = conditional_entropy(groups_wpprs)
    console.print(
        f"  H(choice | all 5 drivers) = {h_all_drivers:.4f} bits"
    )

    chain = [
        {"conditioning": "window", "h": round(h_window, 4)},
        {"conditioning": "window + prev_word", "h": round(h_window_prev, 4)},
        {"conditioning": "window + prev_word + position", "h": round(h_window_prev_pos, 4)},
        {
            "conditioning": "window + prev_word + position + recency",
            "h": round(h_window_prev_pos_rec, 4),
        },
        {
            "conditioning": "window + prev_word + position + recency + suffix",
            "h": round(h_all_drivers, 4),
        },
    ]

    # Display chain as table
    table = Table(title="Conditional Entropy Chain")
    table.add_column("Conditioning", style="cyan")
    table.add_column("H (bits)", justify="right", style="bold")
    table.add_column("Reduction", justify="right")
    for i, entry in enumerate(chain):
        reduction = (
            f"-{chain[i - 1]['h'] - entry['h']:.4f}"
            if i > 0
            else "—"
        )
        table.add_row(entry["conditioning"], f"{entry['h']:.4f}", reduction)
    console.print(table)

    console.print(
        f"\n  [bold]Residual Steganographic Bandwidth (RSB):[/bold] "
        f"{h_all_drivers:.4f} bits/word"
    )

    return chain, choices_with_recency


# ── A1.2: Independence Check ─────────────────────────────────────────

def independence_check(chain, drivers_data):
    """Compare sum of marginal reductions vs actual joint reduction."""
    console.rule("[bold blue]A1.2: Independence Check")

    h_window = chain[0]["h"]
    h_all = chain[-1]["h"]

    # Joint reduction: H(window) - H(all drivers)
    joint_reduction = h_window - h_all

    # Marginal reductions from Phase 15D
    marginal_sum = 2.4316 + 0.6365 + 0.2163 + 0.1629 + 0.1234  # ~3.57

    overlap = marginal_sum - joint_reduction
    overlap_pct = (overlap / marginal_sum * 100) if marginal_sum > 0 else 0

    console.print(f"  Joint reduction (actual): {joint_reduction:.4f} bits")
    console.print(f"  Sum of marginal reductions (Phase 15D): {marginal_sum:.4f} bits")
    console.print(f"  Overlap (correlated drivers): {overlap:.4f} bits ({overlap_pct:.1f}%)")

    if overlap > 0.5:
        console.print(
            "  [yellow]Substantial overlap — drivers share variance. "
            "RSB is higher than naive marginal subtraction would suggest.[/yellow]"
        )
    else:
        console.print(
            "  [green]Modest overlap — drivers are mostly independent.[/green]"
        )

    return {
        "joint_reduction_bits": round(joint_reduction, 4),
        "marginal_sum_bits": round(marginal_sum, 4),
        "overlap_bits": round(overlap, 4),
        "overlap_pct": round(overlap_pct, 2),
        "drivers_mostly_independent": overlap < 0.5,
    }


# ── A1.3: Per-Window RSB Profile ─────────────────────────────────────

def per_window_rsb(choices_with_recency):
    """Compute RSB for each window individually."""
    console.rule("[bold blue]A1.3: Per-Window RSB Profile")

    # H(choice | window=w) — marginal per-window entropy
    window_choices = defaultdict(list)
    for c in choices_with_recency:
        window_choices[c["window_id"]].append(c["chosen_word"])

    # H(choice | window=w, all other drivers)
    window_conditioned = defaultdict(list)
    for c in choices_with_recency:
        prev = c.get("prev_word") or "__none__"
        pos_b = position_bucket(c["token_pos"])
        suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"
        key = (prev, pos_b, c["is_recent"], suffix)
        window_conditioned[c["window_id"]].append((key, c["chosen_word"]))

    per_window = []
    for w in sorted(window_choices.keys()):
        # Marginal entropy for this window
        word_counts = Counter(window_choices[w])
        h_marginal = entropy_bits(list(word_counts.values()))

        # Conditioned entropy for this window
        groups = defaultdict(list)
        for key, word in window_conditioned[w]:
            groups[key].append(word)
        h_cond = conditional_entropy(groups)

        n_choices = len(window_choices[w])
        n_unique = len(word_counts)

        per_window.append({
            "window": w,
            "n_choices": n_choices,
            "n_unique_words": n_unique,
            "h_marginal": round(h_marginal, 4),
            "h_conditioned": round(h_cond, 4),
            "rsb": round(h_cond, 4),
            "reduction_bits": round(h_marginal - h_cond, 4),
        })

    # Summary stats
    rsb_values = [pw["rsb"] for pw in per_window if pw["n_choices"] > 0]
    rsb_mean = float(np.mean(rsb_values)) if rsb_values else 0
    rsb_min = float(np.min(rsb_values)) if rsb_values else 0
    rsb_max = float(np.max(rsb_values)) if rsb_values else 0
    rsb_std = float(np.std(rsb_values)) if rsb_values else 0

    # Find extremes
    sorted_pw = sorted(per_window, key=lambda x: x["rsb"])
    low_rsb = [pw for pw in sorted_pw[:5] if pw["n_choices"] > 0]
    high_rsb = [pw for pw in sorted_pw[-5:] if pw["n_choices"] > 0]

    # Display
    table = Table(title="Per-Window RSB Summary")
    table.add_column("Statistic", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Mean RSB", f"{rsb_mean:.4f} bits")
    table.add_row("Min RSB", f"{rsb_min:.4f} bits")
    table.add_row("Max RSB", f"{rsb_max:.4f} bits")
    table.add_row("Std RSB", f"{rsb_std:.4f} bits")
    table.add_row("Windows with RSB > 0", str(sum(1 for r in rsb_values if r > 0)))
    console.print(table)

    low_table = Table(title="Lowest RSB Windows (most constrained)")
    low_table.add_column("Window", justify="right")
    low_table.add_column("Choices", justify="right")
    low_table.add_column("RSB", justify="right")
    low_table.add_column("H(marginal)", justify="right")
    for pw in low_rsb:
        low_table.add_row(
            str(pw["window"]), str(pw["n_choices"]),
            f"{pw['rsb']:.4f}", f"{pw['h_marginal']:.4f}",
        )
    console.print(low_table)

    high_table = Table(title="Highest RSB Windows (most freedom)")
    high_table.add_column("Window", justify="right")
    high_table.add_column("Choices", justify="right")
    high_table.add_column("RSB", justify="right")
    high_table.add_column("H(marginal)", justify="right")
    for pw in high_rsb:
        high_table.add_row(
            str(pw["window"]), str(pw["n_choices"]),
            f"{pw['rsb']:.4f}", f"{pw['h_marginal']:.4f}",
        )
    console.print(high_table)

    return {
        "per_window": per_window,
        "summary": {
            "mean_rsb": round(rsb_mean, 4),
            "min_rsb": round(rsb_min, 4),
            "max_rsb": round(rsb_max, 4),
            "std_rsb": round(rsb_std, 4),
            "n_windows_with_rsb": sum(1 for r in rsb_values if r > 0),
            "n_windows_total": len(rsb_values),
        },
    }


# ── Bootstrap CI ──────────────────────────────────────────────────────

def bootstrap_rsb(choices_with_recency, n_bootstrap=1000):
    """Bootstrap confidence interval for the global RSB."""
    console.print("\nBootstrapping RSB (1000 resamples)...")
    rng = np.random.RandomState(42)
    n = len(choices_with_recency)
    rsb_samples = []

    for _ in range(n_bootstrap):
        indices = rng.randint(0, n, size=n)
        sample = [choices_with_recency[i] for i in indices]
        groups = defaultdict(list)
        for c in sample:
            prev = c.get("prev_word") or "__none__"
            pos_b = position_bucket(c["token_pos"])
            suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"
            key = (c["window_id"], prev, pos_b, c["is_recent"], suffix)
            groups[key].append(c["chosen_word"])
        rsb_samples.append(conditional_entropy(groups))

    ci_lo = float(np.percentile(rsb_samples, 2.5))
    ci_hi = float(np.percentile(rsb_samples, 97.5))
    rsb_mean = float(np.mean(rsb_samples))

    console.print(f"  RSB = {rsb_mean:.4f} bits, 95% CI [{ci_lo:.4f}, {ci_hi:.4f}]")

    return {
        "rsb_mean_bootstrap": round(rsb_mean, 4),
        "ci_95_lo": round(ci_lo, 4),
        "ci_95_hi": round(ci_hi, 4),
        "n_bootstrap": n_bootstrap,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint A1: Residual Bandwidth Decomposition")

    # Load choice stream
    if not CHOICE_STREAM_PATH.exists():
        console.print("[red]Error: Choice stream trace missing. Run 15A first.[/red]")
        return
    with open(CHOICE_STREAM_PATH) as f:
        trace_data = json.load(f)
    choices = trace_data.get("results", trace_data).get("choices", [])
    if not choices:
        choices = trace_data.get("results", trace_data).get("choice_stream", [])
    console.print(f"Loaded {len(choices)} choice records.")

    # A1.1: Conditional entropy chain
    chain, choices_with_recency = compute_entropy_chain(choices)

    # A1.2: Independence check
    independence = independence_check(chain, choices_with_recency)

    # A1.3: Per-window RSB profile
    per_window = per_window_rsb(choices_with_recency)

    # Bootstrap CI
    bootstrap = bootstrap_rsb(choices_with_recency)

    # Assemble results
    rsb = chain[-1]["h"]
    total_rsb_bits = rsb * len(choices)
    total_rsb_kb = total_rsb_bits / 8192

    results = {
        "num_choices": len(choices),
        "entropy_chain": chain,
        "rsb_bpw": round(rsb, 4),
        "rsb_total_bits": round(total_rsb_bits, 2),
        "rsb_total_kb": round(total_rsb_kb, 2),
        "rsb_latin_chars": round(total_rsb_bits / 4.1, 0),
        "independence_check": independence,
        "per_window_rsb": per_window,
        "bootstrap_ci": bootstrap,
        "interpretation": (
            f"After conditioning on all 5 known drivers, "
            f"{rsb:.2f} bits/word remain unexplained. "
            f"This is the upper bound on hidden information content. "
            f"Total residual capacity: {total_rsb_kb:.1f} KB "
            f"(~{total_rsb_bits / 4.1:,.0f} Latin characters)."
        ),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Final summary
    console.rule("[bold magenta]Summary")
    table = Table(title="Residual Steganographic Bandwidth")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Raw bandwidth (Phase 17B)", "7.53 bits/word")
    table.add_row("RSB (after all drivers)", f"{rsb:.4f} bits/word")
    table.add_row("Bits explained by drivers", f"{chain[0]['h'] - rsb:.4f} bits/word")
    table.add_row("Total RSB capacity", f"{total_rsb_kb:.1f} KB")
    table.add_row("RSB 95% CI", f"[{bootstrap['ci_95_lo']:.4f}, {bootstrap['ci_95_hi']:.4f}]")
    table.add_row("Latin chars equivalent", f"~{total_rsb_bits / 4.1:,.0f}")
    console.print(table)


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17c_residual_bandwidth"}):
        main()
