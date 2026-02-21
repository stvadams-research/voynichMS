#!/usr/bin/env python3
"""Sprint E1: Extended Driver Conditioning.

Adds 3 new candidate drivers to the conditioning chain and measures their
entropy contribution beyond the original 5 drivers from Sprint A1:

  E1.1 — Trigram context (prev_prev_word)
  E1.2 — Section proxy (line_no buckets)
  E1.3 — Window persistence (same window as previous choice)
  E1.4 — Updated entropy chain with all 8 drivers
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
OUTPUT_PATH = project_root / "results/data/phase17_finality/extended_drivers.json"
console = Console()

# Section boundaries by line_no (approximate from IVTFF folio ranges)
SECTION_BOUNDARIES = [
    ("Herbal_A", 1, 1200),
    ("Herbal_B", 1201, 1500),
    ("Pharma", 1501, 2000),
    ("Astro", 2001, 2500),
    ("Cosmo", 2501, 2800),
    ("Biological", 2801, 4500),
    ("Stars", 4501, 5145),
]


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


def section_from_line_no(line_no):
    """Map line_no to manuscript section."""
    for name, lo, hi in SECTION_BOUNDARIES:
        if lo <= line_no <= hi:
            return name
    return "Other"


# ── Enrichment: derive new drivers ───────────────────────────────────

def enrich_choices(choices):
    """Add trigram, section, and persistence fields to each choice record."""
    enriched = []

    # Derive prev_prev_word: track the 2-deep buffer per line
    prev_by_line = {}  # line_no -> list of (token_pos, chosen_word)
    for c in choices:
        line_no = c["line_no"]
        if line_no not in prev_by_line:
            prev_by_line[line_no] = []
        prev_by_line[line_no].append((c["token_pos"], c["chosen_word"]))

    # Sort each line's choices by token_pos for reliable linking
    for line_no in prev_by_line:
        prev_by_line[line_no].sort(key=lambda x: x[0])

    # Build index: (line_no, token_pos) -> chosen_word for lookups
    word_at = {}
    for line_no, items in prev_by_line.items():
        for pos, word in items:
            word_at[(line_no, pos)] = word

    # Track previous window for persistence
    prev_window = None

    # Recency tracking (same as run_17c)
    last_seen = {}

    for i, c in enumerate(choices):
        line_no = c["line_no"]
        token_pos = c["token_pos"]

        # Trigram: prev_prev_word
        prev_prev = "__none__"
        if token_pos >= 2:
            pw = word_at.get((line_no, token_pos - 2))
            if pw is not None:
                prev_prev = pw

        # Section proxy
        section = section_from_line_no(line_no)

        # Window persistence
        same_window = 0
        if prev_window is not None and c["window_id"] == prev_window:
            same_window = 1
        prev_window = c["window_id"]

        # Recency (matching A1 methodology)
        key = (c["window_id"], c["chosen_word"])
        is_recent = 0
        if key in last_seen and (i - last_seen[key]) <= 50:
            is_recent = 1
        last_seen[key] = i

        # Suffix of prev_word
        prev = c.get("prev_word") or "__none__"
        suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"

        enriched.append({
            **c,
            "prev_prev_word": prev_prev,
            "section": section,
            "same_window": same_window,
            "is_recent": is_recent,
            "suffix": suffix,
            "pos_bucket": position_bucket(token_pos),
        })

    return enriched


# ── E1.1-E1.3: Marginal entropy reductions ──────────────────────────

def compute_marginal_reductions(enriched):
    """Compute marginal entropy reduction from each new driver."""
    console.rule("[bold blue]E1.1–E1.3: Marginal Entropy Reductions")

    prev = lambda c: c.get("prev_word") or "__none__"  # noqa: E731

    # Baseline: H(choice | window, prev_word, pos, recency, suffix) — the A1 chain
    groups_5d = defaultdict(list)
    for c in enriched:
        key = (c["window_id"], prev(c), c["pos_bucket"], c["is_recent"], c["suffix"])
        groups_5d[key].append(c["chosen_word"])
    h_5drivers = conditional_entropy(groups_5d)

    console.print(f"  H(choice | 5 original drivers) = {h_5drivers:.4f} bits")

    # E1.1: + trigram
    groups_6d = defaultdict(list)
    for c in enriched:
        key = (c["window_id"], prev(c), c["pos_bucket"], c["is_recent"],
               c["suffix"], c["prev_prev_word"])
        groups_6d[key].append(c["chosen_word"])
    h_6_trigram = conditional_entropy(groups_6d)
    trigram_reduction = h_5drivers - h_6_trigram

    console.print(f"  + trigram → H = {h_6_trigram:.4f} bits "
                  f"(reduction: {trigram_reduction:.4f})")

    # E1.2: + section (on top of 5 original)
    groups_6s = defaultdict(list)
    for c in enriched:
        key = (c["window_id"], prev(c), c["pos_bucket"], c["is_recent"],
               c["suffix"], c["section"])
        groups_6s[key].append(c["chosen_word"])
    h_6_section = conditional_entropy(groups_6s)
    section_reduction = h_5drivers - h_6_section

    console.print(f"  + section → H = {h_6_section:.4f} bits "
                  f"(reduction: {section_reduction:.4f})")

    # E1.3: + persistence (on top of 5 original)
    groups_6p = defaultdict(list)
    for c in enriched:
        key = (c["window_id"], prev(c), c["pos_bucket"], c["is_recent"],
               c["suffix"], c["same_window"])
        groups_6p[key].append(c["chosen_word"])
    h_6_persist = conditional_entropy(groups_6p)
    persist_reduction = h_5drivers - h_6_persist

    console.print(f"  + persistence → H = {h_6_persist:.4f} bits "
                  f"(reduction: {persist_reduction:.4f})")

    return {
        "h_5_drivers": round(h_5drivers, 4),
        "trigram": {
            "h_after": round(h_6_trigram, 4),
            "marginal_reduction": round(trigram_reduction, 4),
        },
        "section": {
            "h_after": round(h_6_section, 4),
            "marginal_reduction": round(section_reduction, 4),
        },
        "persistence": {
            "h_after": round(h_6_persist, 4),
            "marginal_reduction": round(persist_reduction, 4),
        },
    }


# ── E1.4: Full extended chain ────────────────────────────────────────

def compute_extended_chain(enriched):
    """Compute the full 8-driver conditioning chain."""
    console.rule("[bold blue]E1.4: Full Extended Entropy Chain")

    prev = lambda c: c.get("prev_word") or "__none__"  # noqa: E731

    # Progressive chain — same order as A1 plus new drivers
    chain_steps = [
        ("window", lambda c: (c["window_id"],)),
        ("+ prev_word", lambda c: (c["window_id"], prev(c))),
        ("+ position", lambda c: (c["window_id"], prev(c), c["pos_bucket"])),
        ("+ recency", lambda c: (c["window_id"], prev(c), c["pos_bucket"],
                                  c["is_recent"])),
        ("+ suffix", lambda c: (c["window_id"], prev(c), c["pos_bucket"],
                                 c["is_recent"], c["suffix"])),
        ("+ trigram", lambda c: (c["window_id"], prev(c), c["pos_bucket"],
                                  c["is_recent"], c["suffix"],
                                  c["prev_prev_word"])),
        ("+ section", lambda c: (c["window_id"], prev(c), c["pos_bucket"],
                                  c["is_recent"], c["suffix"],
                                  c["prev_prev_word"], c["section"])),
        ("+ persistence", lambda c: (c["window_id"], prev(c), c["pos_bucket"],
                                      c["is_recent"], c["suffix"],
                                      c["prev_prev_word"], c["section"],
                                      c["same_window"])),
    ]

    chain = []
    for label, key_fn in chain_steps:
        groups = defaultdict(list)
        for c in enriched:
            groups[key_fn(c)].append(c["chosen_word"])
        h = conditional_entropy(groups)
        chain.append({"conditioning": label, "h": round(h, 4)})

    # Display
    table = Table(title="Extended Entropy Chain (8 Drivers)")
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

    rsb_8 = chain[-1]["h"]
    rsb_5 = chain[4]["h"]  # after suffix (5th driver)
    new_drivers_reduction = rsb_5 - rsb_8
    pct_explained = (new_drivers_reduction / rsb_5 * 100) if rsb_5 > 0 else 0

    console.print(f"\n  RSB after 5 drivers: {rsb_5:.4f} bits/word")
    console.print(f"  RSB after 8 drivers: {rsb_8:.4f} bits/word")
    console.print(f"  New drivers explain: {new_drivers_reduction:.4f} bits "
                  f"({pct_explained:.1f}% of remaining)")

    return chain, {
        "rsb_5_drivers": round(rsb_5, 4),
        "rsb_8_drivers": round(rsb_8, 4),
        "new_drivers_reduction": round(new_drivers_reduction, 4),
        "pct_remaining_explained": round(pct_explained, 2),
    }


# ── Per-window RSB with 8 drivers ────────────────────────────────────

def per_window_rsb_8(enriched):
    """Compute RSB for each window with all 8 drivers."""
    console.rule("[bold blue]Per-Window RSB (8 Drivers)")

    prev = lambda c: c.get("prev_word") or "__none__"  # noqa: E731

    window_choices = defaultdict(list)
    window_conditioned = defaultdict(list)
    for c in enriched:
        w = c["window_id"]
        window_choices[w].append(c["chosen_word"])
        key = (prev(c), c["pos_bucket"], c["is_recent"], c["suffix"],
               c["prev_prev_word"], c["section"], c["same_window"])
        window_conditioned[w].append((key, c["chosen_word"]))

    per_window = []
    for w in sorted(window_choices.keys()):
        word_counts = Counter(window_choices[w])
        h_marginal = entropy_bits(list(word_counts.values()))

        groups = defaultdict(list)
        for key, word in window_conditioned[w]:
            groups[key].append(word)
        h_cond = conditional_entropy(groups)

        per_window.append({
            "window": w,
            "n_choices": len(window_choices[w]),
            "n_unique": len(word_counts),
            "h_marginal": round(h_marginal, 4),
            "rsb_8": round(h_cond, 4),
        })

    # Summary
    rsb_values = [pw["rsb_8"] for pw in per_window if pw["n_choices"] > 0]
    table = Table(title="Top 10 Windows by RSB (8 drivers)")
    table.add_column("Window", justify="right")
    table.add_column("Choices", justify="right")
    table.add_column("Unique", justify="right")
    table.add_column("RSB(8)", justify="right", style="bold")
    table.add_column("H(marginal)", justify="right")
    sorted_pw = sorted(per_window, key=lambda x: x["rsb_8"], reverse=True)
    for pw in sorted_pw[:10]:
        table.add_row(
            str(pw["window"]), str(pw["n_choices"]),
            str(pw["n_unique"]), f"{pw['rsb_8']:.4f}",
            f"{pw['h_marginal']:.4f}",
        )
    console.print(table)

    return {
        "per_window": per_window,
        "summary": {
            "mean_rsb": round(float(np.mean(rsb_values)), 4),
            "max_rsb": round(float(np.max(rsb_values)), 4),
            "min_rsb": round(float(np.min(rsb_values)), 4),
            "n_windows_with_rsb": sum(1 for r in rsb_values if r > 0),
        },
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint E1: Extended Driver Conditioning")

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

    # Enrich with new drivers
    enriched = enrich_choices(choices)
    console.print(f"Enriched {len(enriched)} choices with trigram, section, persistence.")

    # Section distribution
    section_counts = Counter(c["section"] for c in enriched)
    console.print("\nSection distribution:")
    for sec, cnt in sorted(section_counts.items(), key=lambda x: -x[1]):
        console.print(f"  {sec}: {cnt} ({cnt / len(enriched):.1%})")

    # E1.1-E1.3: Marginal reductions
    marginals = compute_marginal_reductions(enriched)

    # E1.4: Full extended chain
    chain, chain_summary = compute_extended_chain(enriched)

    # Per-window RSB
    per_window = per_window_rsb_8(enriched)

    # Assemble results
    rsb_8 = chain_summary["rsb_8_drivers"]
    total_rsb_bits = rsb_8 * len(enriched)

    results = {
        "num_choices": len(enriched),
        "marginal_reductions": marginals,
        "entropy_chain": chain,
        "chain_summary": chain_summary,
        "per_window_rsb": per_window,
        "total_rsb_bits": round(total_rsb_bits, 2),
        "total_rsb_kb": round(total_rsb_bits / 8192, 2),
        "interpretation": (
            f"After conditioning on all 8 drivers, "
            f"{rsb_8:.2f} bits/word remain unexplained "
            f"(down from 2.21 with 5 drivers). "
            f"New drivers explain {chain_summary['new_drivers_reduction']:.2f} bits "
            f"({chain_summary['pct_remaining_explained']:.1f}% of the 5-driver residual). "
            f"Total residual capacity: {total_rsb_bits / 8192:.1f} KB."
        ),
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Final summary
    console.rule("[bold magenta]Summary")
    table = Table(title="Extended Driver Conditioning Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("RSB (5 drivers)", f"{chain_summary['rsb_5_drivers']:.4f} bpw")
    table.add_row("RSB (8 drivers)", f"{rsb_8:.4f} bpw")
    table.add_row("Trigram marginal", f"{marginals['trigram']['marginal_reduction']:.4f} bits")
    table.add_row("Section marginal", f"{marginals['section']['marginal_reduction']:.4f} bits")
    table.add_row("Persistence marginal", f"{marginals['persistence']['marginal_reduction']:.4f} bits")
    table.add_row("New drivers total", f"{chain_summary['new_drivers_reduction']:.4f} bits")
    table.add_row("% remaining explained", f"{chain_summary['pct_remaining_explained']:.1f}%")
    table.add_row("Total residual capacity", f"{total_rsb_bits / 8192:.1f} KB")
    console.print(table)


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17g_extended_drivers"}):
        main()
