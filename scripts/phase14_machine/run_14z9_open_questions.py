#!/usr/bin/env python3
"""Phase 14I Sprint 3: Close Remaining Open Questions.

STATUS.md Section 8 has three remaining open questions:
  1. Overgeneration bounding (4-gram, 5-gram)
  2. Per-position branching factor formalization
  3. Description length gap decomposition (Lattice 12.37 vs Copy-Reset 10.90 BPT)

This script addresses all three with targeted computation.
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
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
COMPRESSION_PATH = (
    project_root / "results/data/phase14_machine/lattice_compression.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/open_questions.json"
)
console = Console()

NUM_WINDOWS = 50


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


# ── Q1: Higher-Order Overgeneration ──────────────────────────────────────

def compute_ngram_overgeneration(real_lines, syn_lines, vocab, max_n=5):
    """Compute n-gram overgeneration rates for n=2..max_n."""
    results = {}

    for n in range(2, max_n + 1):
        real_ngrams = set()
        for line in real_lines:
            for i in range(len(line) - n + 1):
                ngram = tuple(line[i:i + n])
                if all(t in vocab for t in ngram):
                    real_ngrams.add(ngram)

        syn_ngrams = set()
        for line in syn_lines:
            for i in range(len(line) - n + 1):
                ngram = tuple(line[i:i + n])
                if all(t in vocab for t in ngram):
                    syn_ngrams.add(ngram)

        overlap = syn_ngrams & real_ngrams
        unattested = syn_ngrams - real_ngrams

        results[f"{n}-gram"] = {
            "n": n,
            "real_count": len(real_ngrams),
            "syn_count": len(syn_ngrams),
            "overlap_count": len(overlap),
            "unattested_count": len(unattested),
            "unattested_rate": round(len(unattested) / len(syn_ngrams), 4) if syn_ngrams else 0,
            "overgeneration_ratio": round(len(syn_ngrams) / len(real_ngrams), 2) if real_ngrams else 0,
            "overlap_rate": round(len(overlap) / len(real_ngrams), 4) if real_ngrams else 0,
        }

    return results


# ── Q2: Per-Position Branching Factor ────────────────────────────────────

def compute_branching_factor(real_lines, lattice_map, window_contents):
    """Compute admissible branching factor per line position."""
    # Precompute: for each window, the set of admissible next tokens (drift ±1)
    admissible_sets = {}
    for win in range(NUM_WINDOWS):
        tokens = set()
        for offset in [-1, 0, 1]:
            check_win = (win + offset) % NUM_WINDOWS
            tokens.update(window_contents.get(check_win, []))
        admissible_sets[win] = tokens

    # Per-position branching factor
    position_data = defaultdict(list)
    overall_branching = []

    for line in real_lines:
        current_window = 0
        for pos, word in enumerate(line):
            if word not in lattice_map:
                continue

            # Branching factor = |admissible tokens at this window|
            bf = len(admissible_sets.get(current_window, set()))
            capped_pos = min(pos, 9)  # Cap at position 9+
            position_data[capped_pos].append(bf)
            overall_branching.append(bf)

            # Advance window
            current_window = lattice_map[word]

    # Compute stats per position
    pos_stats = {}
    for pos in sorted(position_data.keys()):
        bfs = position_data[pos]
        pos_stats[str(pos)] = {
            "count": len(bfs),
            "mean_bf": round(float(np.mean(bfs)), 1),
            "median_bf": round(float(np.median(bfs)), 1),
            "std_bf": round(float(np.std(bfs)), 1),
            "min_bf": int(np.min(bfs)),
            "max_bf": int(np.max(bfs)),
            "effective_bits": round(math.log2(float(np.mean(bfs))), 2) if np.mean(bfs) > 0 else 0,
        }

    overall_mean = float(np.mean(overall_branching)) if overall_branching else 0
    return {
        "per_position": pos_stats,
        "overall_mean_bf": round(overall_mean, 1),
        "overall_effective_bits": round(math.log2(overall_mean), 2) if overall_mean > 1 else 0,
        "total_observations": len(overall_branching),
    }


# ── Q3: Description Length Gap Decomposition ─────────────────────────────

def decompose_mdl_gap(real_lines, lattice_map, window_contents, vocab):
    """Decompose the MDL gap between Lattice and Copy-Reset models."""
    all_tokens = [t for line in real_lines for t in line if t in vocab]
    n_tokens = len(all_tokens)
    n_vocab = len(vocab)

    # ── Lattice Model ──
    # L(model): frequency-conditional encoding
    # Load from compression results if available
    lattice_model_bits = len(lattice_map) * math.log2(NUM_WINDOWS)  # naive L(model)

    if COMPRESSION_PATH.exists():
        with open(COMPRESSION_PATH) as f:
            comp_data = json.load(f)
        comp_results = comp_data.get("results", comp_data)
        methods = comp_results.get("methods", {})
        if "frequency_conditional" in methods:
            fc = methods["frequency_conditional"]
            lattice_model_bits = fc.get("l_model_bits", fc.get("bits", lattice_model_bits))

    # L(data|model): for each token, encoding cost = log2(window_size)
    # where window_size is the number of candidates in the admissible windows
    lattice_data_bits = 0.0
    current_window = 0
    for line in real_lines:
        for word in line:
            if word not in vocab:
                continue
            # Admissible candidates in current ±1 windows
            candidates = set()
            for offset in [-1, 0, 1]:
                check_win = (current_window + offset) % NUM_WINDOWS
                candidates.update(window_contents.get(check_win, []))
            cand_count = max(len(candidates), 1)
            lattice_data_bits += math.log2(cand_count)

            # Advance
            if word in lattice_map:
                current_window = lattice_map[word]

    lattice_total = lattice_model_bits + lattice_data_bits
    lattice_bpt = lattice_total / n_tokens if n_tokens else 0

    # ── Copy-Reset Model ──
    # L(model): unigram distribution + copy probability
    # P(copy) parameter: 1 value + unigram distribution: V values
    token_counts = Counter(all_tokens)

    # Estimate p_copy from data
    copy_window = 5
    copy_hits = 0
    copy_eligible = 0
    for line in real_lines:
        for i in range(1, len(line)):
            if line[i] in vocab:
                copy_eligible += 1
                recent = set(line[max(0, i - copy_window):i])
                if line[i] in recent:
                    copy_hits += 1
    p_copy = copy_hits / copy_eligible if copy_eligible > 0 else 0

    # L(model) for CR: encode unigram distribution + copy parameter
    # Unigram: V values of ~10 bits each (standard precision)
    cr_model_bits = n_vocab * 10 + 10  # V × 10 bits + p_copy

    # L(data|model): for each token
    #   If copied: -log2(p_copy × 1/k) where k = copy_window match probability
    #   If novel: -log2((1-p_copy) × unigram_prob)
    cr_data_bits = 0.0
    for line in real_lines:
        for i, word in enumerate(line):
            if word not in vocab:
                continue
            p_unigram = token_counts[word] / n_tokens

            if i > 0:
                recent = set(line[max(0, i - copy_window):i])
                if word in recent:
                    # Copied
                    recent_count = len(recent)
                    p = p_copy * (1 / max(recent_count, 1))
                    cr_data_bits += -math.log2(max(p, 1e-10))
                    continue

            # Novel or first token
            p = (1 - p_copy) * p_unigram if i > 0 else p_unigram
            cr_data_bits += -math.log2(max(p, 1e-10))

    cr_total = cr_model_bits + cr_data_bits
    cr_bpt = cr_total / n_tokens if n_tokens else 0

    # ── Decomposition ──
    model_gap = lattice_model_bits - cr_model_bits
    data_gap = lattice_data_bits - cr_data_bits
    total_gap = lattice_total - cr_total
    gap_bpt = total_gap / n_tokens if n_tokens else 0

    return {
        "lattice": {
            "l_model": round(lattice_model_bits, 0),
            "l_data": round(lattice_data_bits, 0),
            "l_total": round(lattice_total, 0),
            "bpt": round(lattice_bpt, 3),
        },
        "copy_reset": {
            "l_model": round(cr_model_bits, 0),
            "l_data": round(cr_data_bits, 0),
            "l_total": round(cr_total, 0),
            "bpt": round(cr_bpt, 3),
            "p_copy": round(p_copy, 4),
        },
        "gap": {
            "model_gap_bits": round(model_gap, 0),
            "data_gap_bits": round(data_gap, 0),
            "total_gap_bits": round(total_gap, 0),
            "gap_bpt": round(gap_bpt, 3),
            "model_fraction": round(model_gap / total_gap, 3) if total_gap != 0 else 0,
            "data_fraction": round(data_gap / total_gap, 3) if total_gap != 0 else 0,
        },
        "n_tokens": n_tokens,
        "n_vocab": n_vocab,
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14I Sprint 3: Close Remaining Open Questions[/bold magenta]")

    # Load data
    console.print("Loading palette...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    console.print(f"  {len(lattice_map)} words, {len(window_contents)} windows")

    console.print("Loading corpus...")
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    real_vocab = set(t for line in real_lines for t in line)
    all_tokens = [t for line in real_lines for t in line]
    console.print(f"  {len(real_lines)} lines, {len(all_tokens)} tokens, {len(real_vocab)} vocab")

    lattice_vocab = set(lattice_map.keys())

    # ── Q1: Higher-Order Overgeneration ──────────────────────────────

    console.print("\n[bold cyan]Q1: Higher-Order Overgeneration[/bold cyan]")
    console.print("Generating synthetic corpus (100K lines, seed=42)...")

    emulator = HighFidelityVolvelle(lattice_map, window_contents, seed=42)
    syn_lines = emulator.generate_mirror_corpus(100000)
    console.print(f"  Generated {len(syn_lines)} lines, {sum(len(l) for l in syn_lines)} tokens")

    ngram_results = compute_ngram_overgeneration(real_lines, syn_lines, lattice_vocab, max_n=5)

    table = Table(title="N-gram Overgeneration Analysis")
    table.add_column("N-gram", style="cyan")
    table.add_column("Real", justify="right")
    table.add_column("Synthetic", justify="right")
    table.add_column("Overlap", justify="right")
    table.add_column("Unattested", justify="right")
    table.add_column("Unattest. Rate", justify="right")
    table.add_column("Overgen. Ratio", justify="right")

    for key, r in sorted(ngram_results.items()):
        table.add_row(
            key,
            f"{r['real_count']:,}",
            f"{r['syn_count']:,}",
            f"{r['overlap_count']:,}",
            f"{r['unattested_count']:,}",
            f"{r['unattested_rate']*100:.1f}%",
            f"{r['overgeneration_ratio']:.1f}×",
        )
    console.print(table)

    # ── Q2: Per-Position Branching Factor ────────────────────────────

    console.print("\n[bold cyan]Q2: Per-Position Branching Factor[/bold cyan]")

    bf_results = compute_branching_factor(real_lines, lattice_map, window_contents)

    table2 = Table(title="Branching Factor by Line Position")
    table2.add_column("Position", style="cyan")
    table2.add_column("Count", justify="right")
    table2.add_column("Mean BF", justify="right")
    table2.add_column("Median BF", justify="right")
    table2.add_column("Std", justify="right")
    table2.add_column("Eff. Bits", justify="right")

    for pos in sorted(bf_results["per_position"].keys(), key=int):
        s = bf_results["per_position"][pos]
        table2.add_row(
            pos if int(pos) < 9 else "9+",
            str(s["count"]),
            f"{s['mean_bf']:.1f}",
            f"{s['median_bf']:.1f}",
            f"{s['std_bf']:.1f}",
            f"{s['effective_bits']:.2f}",
        )
    console.print(table2)

    console.print(f"\nOverall mean branching factor: {bf_results['overall_mean_bf']:.1f}")
    console.print(f"Overall effective bits per position: {bf_results['overall_effective_bits']:.2f}")

    # ── Q3: MDL Gap Decomposition ────────────────────────────────────

    console.print("\n[bold cyan]Q3: Description Length Gap Decomposition[/bold cyan]")

    mdl_results = decompose_mdl_gap(real_lines, lattice_map, window_contents, lattice_vocab)

    table3 = Table(title="MDL Decomposition")
    table3.add_column("Component", style="cyan")
    table3.add_column("Lattice", justify="right")
    table3.add_column("Copy-Reset", justify="right")
    table3.add_column("Gap", justify="right")

    table3.add_row(
        "L(model)",
        f"{mdl_results['lattice']['l_model']:,.0f}",
        f"{mdl_results['copy_reset']['l_model']:,.0f}",
        f"{mdl_results['gap']['model_gap_bits']:,.0f}",
    )
    table3.add_row(
        "L(data|model)",
        f"{mdl_results['lattice']['l_data']:,.0f}",
        f"{mdl_results['copy_reset']['l_data']:,.0f}",
        f"{mdl_results['gap']['data_gap_bits']:,.0f}",
    )
    table3.add_row(
        "L(total)",
        f"{mdl_results['lattice']['l_total']:,.0f}",
        f"{mdl_results['copy_reset']['l_total']:,.0f}",
        f"{mdl_results['gap']['total_gap_bits']:,.0f}",
    )
    table3.add_row(
        "BPT",
        f"{mdl_results['lattice']['bpt']:.3f}",
        f"{mdl_results['copy_reset']['bpt']:.3f}",
        f"{mdl_results['gap']['gap_bpt']:.3f}",
    )
    console.print(table3)

    model_frac = mdl_results["gap"]["model_fraction"]
    data_frac = mdl_results["gap"]["data_fraction"]
    console.print(f"\nGap decomposition: {model_frac*100:.1f}% model overhead, {data_frac*100:.1f}% data encoding")
    console.print(f"Copy-Reset p_copy: {mdl_results['copy_reset']['p_copy']:.4f}")

    # ── Save Results ─────────────────────────────────────────────────

    results = {
        "q1_overgeneration": ngram_results,
        "q2_branching_factor": bf_results,
        "q3_mdl_decomposition": mdl_results,
    }

    with active_run(config={"seed": 42, "command": "run_14z9_open_questions"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")

    # ── Interpretation ───────────────────────────────────────────────

    console.print("\n[bold yellow]Interpretation:[/bold yellow]")

    # Q1
    for key in sorted(ngram_results.keys()):
        r = ngram_results[key]
        console.print(f"  {key}: {r['overgeneration_ratio']:.1f}× overgeneration "
                      f"({r['unattested_rate']*100:.1f}% unattested)")

    # Q2
    console.print(f"\n  Branching factor: {bf_results['overall_mean_bf']:.1f} candidates/position "
                  f"({bf_results['overall_effective_bits']:.2f} bits)")
    console.print("  Compare: 7.17 bits within-window selection (from Phase 15D)")

    # Q3
    if model_frac > 0.5:
        console.print(f"\n  MDL gap is primarily model overhead ({model_frac*100:.0f}%)")
        console.print("  → Lattice pays more to describe its structure, not worse data fit")
    else:
        console.print(f"\n  MDL gap is primarily data encoding ({data_frac*100:.0f}%)")
        console.print("  → Lattice is less efficient at predicting individual tokens")


if __name__ == "__main__":
    main()
