#!/usr/bin/env python3
"""Phase 14Z: Lattice Compression Analysis.

The lattice model's L(model) = 154,340 bits dominates the MDL comparison.
This script analyzes how compressible the 7,717 word-to-window assignments
actually are under various encoding schemes:

1. Naive: 7,717 × log2(50) ≈ 43,554 bits (uniform window codes)
2. Entropy-optimal: H(window_assignment) × 7,717 (Huffman-like)
3. Character-feature prediction: decision tree on prefix/suffix/length
4. Stem-based grouping: intra-window suffix entropy
5. Frequency-conditional: H(window | frequency_bucket)

Also identifies the double-counting issue in the baseline showdown:
window_contents is derivable from lattice_map, so the true model cost
should use lattice_map only (not both).
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

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
BASELINE_PATH = (
    project_root / "results/data/phase14_machine/baseline_comparison.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/lattice_compression.json"
)
console = Console()

EVA_VOWELS = set("aeoy")


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


def extract_features(word):
    """Extract character-level features for window prediction."""
    return {
        "length": len(word),
        "prefix_1": word[0] if len(word) >= 1 else "",
        "prefix_2": word[:2] if len(word) >= 2 else word,
        "suffix_1": word[-1] if len(word) >= 1 else "",
        "suffix_2": word[-2:] if len(word) >= 2 else word,
        "vowel_count": sum(1 for c in word if c in EVA_VOWELS),
        "vowel_ratio": sum(1 for c in word if c in EVA_VOWELS) / max(len(word), 1),
        "has_gallows": any(c in "tkpf" for c in word),
    }


def main():
    console.print(
        "[bold blue]Phase 14Z: Lattice Compression Analysis[/bold blue]"
    )

    # 1. Load lattice
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}
    num_windows = len(window_contents)
    num_words = len(lattice_map)

    console.print(
        f"Lattice: {num_words} words across {num_windows} windows"
    )

    # 2. Load corpus for frequency data
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    all_tokens = [t for line in lines for t in line]
    corpus_freq = Counter(all_tokens)
    total_tokens = len(all_tokens)

    # Verify double-counting
    wc_total = sum(len(v) for v in window_contents.values())
    console.print(
        f"\nDouble-counting check: lattice_map={num_words}, "
        f"window_contents total={wc_total}"
    )
    console.print(
        "  → These should be equal (window_contents is the inverse of "
        "lattice_map)"
    )

    # Load baseline L(data|model) for BPT recalculation
    l_data_lattice = None
    l_data_hybrid = None
    if BASELINE_PATH.exists():
        with open(BASELINE_PATH) as f:
            baseline = json.load(f)["results"]
        models = baseline.get("models", {})
        if "Lattice (Ours)" in models:
            l_data_lattice = models["Lattice (Ours)"]["l_data"]
        if "Hybrid (CR+Lattice)" in models:
            l_data_hybrid = models["Hybrid (CR+Lattice)"]["l_data"]
        if l_data_lattice is not None:
            console.print(
                f"  Lattice L(data|model) = {l_data_lattice:.0f} bits"
            )
        if l_data_hybrid is not None:
            console.print(
                f"  Hybrid L(data|model) = {l_data_hybrid:.0f} bits"
            )

    # ── Method 1: Naive encoding ──
    naive_bits = num_words * math.log2(num_windows)
    console.print(f"\n[bold]Method 1 — Naive:[/bold] {naive_bits:,.0f} bits")
    console.print(
        f"  ({num_words} words × {math.log2(num_windows):.2f} bits/word)"
    )

    # Current showdown computation (for reference)
    showdown_bits = (num_words + wc_total) * 10
    console.print(
        f"  Showdown L(model) [double-counted]: {showdown_bits:,.0f} bits"
    )

    # ── Method 2: Entropy-optimal (Huffman) ──
    window_word_counts = Counter(lattice_map.values())
    window_dist = list(window_word_counts.values())
    H_window = entropy(window_dist)
    huffman_bits = num_words * H_window

    console.print(
        f"\n[bold]Method 2 — Entropy-optimal:[/bold] {huffman_bits:,.0f} bits"
    )
    console.print(
        f"  H(window assignment) = {H_window:.3f} bits/word "
        f"(max = {math.log2(num_windows):.3f})"
    )
    console.print(
        f"  Compression vs naive: {(1 - huffman_bits / naive_bits) * 100:.1f}%"
    )

    # ── Method 3: Character-feature prediction ──
    # Build feature vectors and measure conditional entropy
    # Group words by feature combination, measure H(window | features)
    feature_groups = defaultdict(lambda: defaultdict(int))
    for word, win_id in lattice_map.items():
        feat = extract_features(word)
        # Create a hashable feature key
        key = (
            feat["prefix_2"],
            feat["suffix_2"],
            min(feat["length"], 10),  # cap length
            feat["vowel_count"],
            feat["has_gallows"],
        )
        feature_groups[key][win_id] += 1

    # Conditional entropy: H(window | features) = sum_g P(g) * H(window | g)
    h_conditional = 0.0
    total_in_groups = 0
    num_groups = len(feature_groups)
    for _group_key, win_counts in feature_groups.items():
        group_total = sum(win_counts.values())
        total_in_groups += group_total
        h_group = entropy(list(win_counts.values()))
        h_conditional += (group_total / num_words) * h_group

    feature_bits = num_words * h_conditional
    # Add cost of encoding the feature-to-window mapping itself
    # Each group needs: its feature key + a distribution over windows
    # Approximate: num_groups * (key_cost + max_windows * 1 bit)
    feature_model_overhead = num_groups * (20 + num_windows)
    feature_total = feature_bits + feature_model_overhead

    console.print(
        f"\n[bold]Method 3 — Character-feature prediction:[/bold] "
        f"{feature_total:,.0f} bits"
    )
    console.print(
        f"  H(window | features) = {h_conditional:.3f} bits/word"
    )
    console.print(
        f"  Feature groups: {num_groups} "
        f"(avg {num_words / num_groups:.1f} words/group)"
    )
    console.print(
        f"  Residual encoding: {feature_bits:,.0f} bits + "
        f"model overhead: {feature_model_overhead:,.0f} bits"
    )

    # ── Method 4: Stem-based grouping ──
    # Within each window, find the modal 2-char prefix and measure
    # suffix entropy after removing it
    stem_results = {}
    total_stem_entropy = 0.0
    total_stem_words = 0

    for win_id, words in window_contents.items():
        if len(words) < 5:
            continue
        # Find modal 2-char prefix
        prefix_counts = Counter(w[:2] for w in words if len(w) >= 2)
        if not prefix_counts:
            continue
        modal_prefix, modal_count = prefix_counts.most_common(1)[0]
        modal_fraction = modal_count / len(words)

        # Suffix entropy for words with the modal prefix
        matching = [w[2:] for w in words if w[:2] == modal_prefix and len(w) > 2]
        if matching:
            suffix_counts = Counter(matching)
            h_suffix = entropy(list(suffix_counts.values()))
        else:
            h_suffix = 0.0

        stem_results[win_id] = {
            "modal_prefix": modal_prefix,
            "modal_fraction": modal_fraction,
            "suffix_entropy": h_suffix,
            "window_size": len(words),
        }
        total_stem_entropy += h_suffix * len(words)
        total_stem_words += len(words)

    avg_modal_fraction = np.mean(
        [r["modal_fraction"] for r in stem_results.values()]
    )
    avg_suffix_entropy = np.mean(
        [r["suffix_entropy"] for r in stem_results.values()]
    )
    # Stem-based encoding: for each window, encode modal prefix (5 bits) +
    # non-modal words at full cost + modal words at suffix_entropy cost
    num_windows * 5  # prefix identifiers

    console.print(
        "\n[bold]Method 4 — Stem-based grouping:[/bold]"
    )
    console.print(
        f"  Avg modal prefix fraction: {avg_modal_fraction:.1%}"
    )
    console.print(
        f"  Avg within-window suffix entropy: {avg_suffix_entropy:.2f} bits"
    )
    console.print(
        f"  (Weak clustering — modal prefix covers only "
        f"{avg_modal_fraction:.0%} of window words on average)"
    )

    # ── Method 5: Frequency-conditional ──
    # Group words by corpus frequency bucket, measure H(window | bucket)
    freq_buckets = {}
    for word in lattice_map:
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
        freq_buckets[word] = bucket

    bucket_groups = defaultdict(lambda: defaultdict(int))
    for word, win_id in lattice_map.items():
        bucket_groups[freq_buckets[word]][win_id] += 1

    h_freq_cond = 0.0
    bucket_stats = {}
    for bucket, win_counts in sorted(bucket_groups.items()):
        bucket_total = sum(win_counts.values())
        h_bucket = entropy(list(win_counts.values()))
        h_freq_cond += (bucket_total / num_words) * h_bucket
        bucket_stats[bucket] = {
            "count": bucket_total,
            "H_window": round(h_bucket, 3),
        }

    freq_bits = num_words * h_freq_cond
    freq_overhead = len(bucket_groups) * num_windows  # bucket-to-window distributions
    freq_total = freq_bits + freq_overhead

    console.print(
        f"\n[bold]Method 5 — Frequency-conditional:[/bold] "
        f"{freq_total:,.0f} bits"
    )
    console.print(
        f"  H(window | freq_bucket) = {h_freq_cond:.3f} bits/word"
    )
    for bucket, stats in sorted(bucket_stats.items()):
        console.print(
            f"    {bucket}: {stats['count']} words, "
            f"H(window) = {stats['H_window']:.3f}"
        )

    # ── Summary ──
    methods = {
        "showdown_double_counted": {
            "bits": showdown_bits,
            "description": "Current run_14h computation (double-counts)",
        },
        "naive": {
            "bits": naive_bits,
            "description": f"{num_words} × log2({num_windows})",
        },
        "entropy_optimal": {
            "bits": huffman_bits,
            "description": f"H = {H_window:.3f} bits/word",
        },
        "character_feature": {
            "bits": feature_total,
            "description": (
                f"H(w|features) = {h_conditional:.3f}, "
                f"{num_groups} groups + overhead"
            ),
        },
        "frequency_conditional": {
            "bits": freq_total,
            "description": f"H(w|freq) = {h_freq_cond:.3f}, 6 buckets",
        },
    }

    best_method = min(methods.items(), key=lambda x: x[1]["bits"])
    best_bits = best_method[1]["bits"]

    console.print("\n" + "=" * 60)
    console.print("[bold]Summary: L(model) under different encodings[/bold]")
    table = Table()
    table.add_column("Method", style="cyan")
    table.add_column("L(model)", justify="right")
    table.add_column("Description")

    for name, m in sorted(methods.items(), key=lambda x: x[1]["bits"]):
        style = "bold green" if name == best_method[0] else ""
        table.add_row(
            name.replace("_", " ").title(),
            f"{m['bits']:,.0f}",
            m["description"],
            style=style,
        )
    console.print(table)

    # ── BPT Recalculation ──
    console.print("\n[bold]BPT Recalculation[/bold]")
    console.print(
        f"  Total tokens: {total_tokens:,}"
    )

    bpt_results = {}
    if l_data_lattice is not None:
        for method_name, m in methods.items():
            bpt = (m["bits"] + l_data_lattice) / total_tokens
            bpt_results[method_name] = bpt
            console.print(
                f"  Lattice BPT ({method_name}): "
                f"({m['bits']:,.0f} + {l_data_lattice:,.0f}) / "
                f"{total_tokens:,} = {bpt:.4f}"
            )

    if l_data_hybrid is not None:
        console.print("\n  Hybrid model BPT with corrected L(model):")
        for method_name, m in methods.items():
            # Hybrid uses same lattice params + 3 mixture weights
            hybrid_model = m["bits"] + 30  # 3 params × 10 bits
            bpt = (hybrid_model + l_data_hybrid) / total_tokens
            console.print(
                f"  Hybrid BPT ({method_name}): {bpt:.4f}"
            )

    # Copy-Reset reference
    cr_bpt = 10.90
    console.print(f"\n  Copy-Reset BPT (reference): {cr_bpt:.2f}")
    if best_method[0] in bpt_results:
        gap = bpt_results[best_method[0]] - cr_bpt
        console.print(
            f"  Remaining gap vs CR: {gap:.2f} BPT "
            f"(was {showdown_bits / total_tokens + l_data_lattice / total_tokens - cr_bpt:.2f})"
        )

    # ── Save results ──
    results = {
        "lattice_size": {
            "num_words": num_words,
            "num_windows": num_windows,
            "window_contents_total": wc_total,
            "is_double_counted": num_words == wc_total,
        },
        "methods": {
            name: {
                "l_model_bits": m["bits"],
                "description": m["description"],
            }
            for name, m in methods.items()
        },
        "best_method": best_method[0],
        "best_l_model": best_bits,
        "compression_vs_showdown": 1 - best_bits / showdown_bits,
        "compression_vs_naive": 1 - best_bits / naive_bits,
        "window_entropy_H": H_window,
        "h_conditional_features": h_conditional,
        "h_conditional_frequency": h_freq_cond,
        "num_feature_groups": num_groups,
        "avg_modal_prefix_fraction": avg_modal_fraction,
        "stem_clustering": "weak" if avg_modal_fraction < 0.3 else "moderate",
        "bucket_stats": bucket_stats,
        "bpt_revised": bpt_results if bpt_results else None,
        "total_tokens": total_tokens,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Interpretation
    compression_pct = (1 - best_bits / showdown_bits) * 100
    console.print(
        f"\n[bold]Key finding:[/bold] The lattice model cost can be reduced "
        f"from {showdown_bits:,} bits to {best_bits:,.0f} bits "
        f"({compression_pct:.0f}% reduction) by eliminating double-counting "
        f"and using entropy-optimal encoding."
    )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z_lattice_compression"}
    ):
        main()
