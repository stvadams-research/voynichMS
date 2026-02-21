#!/usr/bin/env python3
"""Phase 14Z3: Cross-Transcription Validation.

All lattice analysis uses the Zandbergen-Landini (ZL) transcription.
This script tests whether the lattice structure holds when evaluated
against independently-transcribed versions of the same manuscript.

If admissibility ratios are near 1.0 across transcriptions, the lattice
captures genuine manuscript structure — not ZL-specific choices.

Tests 5 EVA sources (excludes Currier/D'Imperio uppercase):
- GC (Glen Claston), VT (Voynich Transcription), IT (Interim),
  RF (René Friedman), FG (Friedman Group)
"""

import json
import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import (  # noqa: E402
    load_canonical_lines,
)
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/cross_transcription.json"
)
console = Console()

CROSS_SOURCES = {
    "glen_claston": "GC",
    "voynich_transcription": "VT",
    "interim": "IT",
    "rene_friedman": "RF",
    "friedman_group": "FG",
}


def measure_admissibility(lines, lattice_map, window_contents, num_wins, drift=1):
    """Measure drift-admissibility for a set of lines.

    Args:
        drift: Maximum window distance considered admissible (1 = ±1, 3 = ±3).
    """
    admissible = 0
    total = 0
    current_window = 0

    for line in lines:
        for word in line:
            if word not in lattice_map:
                continue
            total += 1

            found = False
            for d in range(-drift, drift + 1):
                check_win = (current_window + d) % num_wins
                if word in window_contents.get(check_win, []):
                    found = True
                    current_window = lattice_map[word]
                    break

            if found:
                admissible += 1
            else:
                current_window = lattice_map[word]

    return admissible, total


def permutation_test(
    lines, lattice_map, window_contents, num_wins,
    observed_adm, n_permutations=1000, rng=None,
):
    """Test if observed admissibility exceeds chance via permutation.

    Randomly reassigns words to windows and measures admissibility.
    """
    if rng is None:
        rng = np.random.RandomState(42)

    words = list(lattice_map.keys())
    windows = list(lattice_map.values())
    null_scores = []

    for _ in range(n_permutations):
        # Shuffle window assignments
        shuffled_windows = rng.permutation(windows).tolist()
        shuffled_map = dict(zip(words, shuffled_windows, strict=False))

        # Build shuffled window_contents
        from collections import defaultdict
        shuffled_wc = defaultdict(list)
        for w, win_id in shuffled_map.items():
            shuffled_wc[win_id].append(w)

        adm, total = measure_admissibility(
            lines, shuffled_map, dict(shuffled_wc), num_wins,
        )
        rate = adm / total if total > 0 else 0
        null_scores.append(rate)

    null_mean = np.mean(null_scores)
    null_std = np.std(null_scores)
    z_score = (
        (observed_adm - null_mean) / null_std if null_std > 0 else 0
    )
    p_value = np.mean([s >= observed_adm for s in null_scores])

    return {
        "null_mean": float(null_mean),
        "null_std": float(null_std),
        "z_score": float(z_score),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
    }


def main():
    console.print(
        "[bold blue]Phase 14Z3: Cross-Transcription Validation[/bold blue]"
    )

    # 1. Load ZL-trained lattice
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}
    num_wins = len(window_contents)
    lattice_vocab = set(lattice_map.keys())

    console.print(
        f"ZL lattice: {len(lattice_map)} words, "
        f"{num_wins} windows"
    )

    # 2. Measure ZL baseline
    store = MetadataStore(DB_PATH)
    zl_lines = load_canonical_lines(store)
    zl_tokens = [t for line in zl_lines for t in line]
    zl_adm, zl_total = measure_admissibility(
        zl_lines, lattice_map, window_contents, num_wins, drift=1,
    )
    zl_ext_adm, _ = measure_admissibility(
        zl_lines, lattice_map, window_contents, num_wins, drift=3,
    )
    zl_rate = zl_adm / zl_total if zl_total > 0 else 0
    zl_ext_rate = zl_ext_adm / zl_total if zl_total > 0 else 0

    console.print(
        f"\nZL baseline: {zl_rate * 100:.2f}% (±1), "
        f"{zl_ext_rate * 100:.2f}% (±3), "
        f"{zl_total} clamped tokens"
    )

    # 3. Test each cross-transcription source
    source_results = {}

    for source_id, label in CROSS_SOURCES.items():
        console.print(f"\n[bold]Testing {label} ({source_id})...[/bold]")

        try:
            src_lines = load_canonical_lines(store, source_id=source_id)
        except Exception as e:
            console.print(f"  [red]Error loading: {e}[/red]")
            continue

        if not src_lines:
            console.print("  [yellow]No lines loaded, skipping.[/yellow]")
            continue

        src_tokens = [t for line in src_lines for t in line]
        src_vocab = set(src_tokens)

        # Vocabulary overlap
        type_overlap = len(src_vocab & lattice_vocab)
        type_overlap_rate = type_overlap / len(src_vocab) if src_vocab else 0

        # Token coverage
        covered_tokens = sum(1 for t in src_tokens if t in lattice_map)
        token_coverage = covered_tokens / len(src_tokens) if src_tokens else 0

        console.print(
            f"  Tokens: {len(src_tokens):,}, "
            f"Vocab: {len(src_vocab):,}"
        )
        console.print(
            f"  Type overlap with ZL lattice: {type_overlap_rate:.1%} "
            f"({type_overlap}/{len(src_vocab)})"
        )
        console.print(
            f"  Token coverage: {token_coverage:.1%} "
            f"({covered_tokens}/{len(src_tokens)})"
        )

        # Admissibility (±1)
        adm, total = measure_admissibility(
            src_lines, lattice_map, window_contents, num_wins, drift=1,
        )
        rate = adm / total if total > 0 else 0

        # Extended admissibility (±3)
        ext_adm, _ = measure_admissibility(
            src_lines, lattice_map, window_contents, num_wins, drift=3,
        )
        ext_rate = ext_adm / total if total > 0 else 0

        # Admissibility ratio
        adm_ratio = rate / zl_rate if zl_rate > 0 else 0
        ext_ratio = ext_rate / zl_ext_rate if zl_ext_rate > 0 else 0

        console.print(
            f"  Admissibility (±1): {rate * 100:.2f}% "
            f"(ratio: {adm_ratio:.3f})"
        )
        console.print(
            f"  Extended (±3): {ext_rate * 100:.2f}% "
            f"(ratio: {ext_ratio:.3f})"
        )

        # Permutation test (100 permutations for speed)
        console.print("  Running permutation test (100 shuffles)...")
        perm = permutation_test(
            src_lines, lattice_map, window_contents, num_wins,
            rate, n_permutations=100,
        )
        console.print(
            f"  Permutation: z={perm['z_score']:.1f}, "
            f"p={perm['p_value']:.4f}"
        )

        source_results[label] = {
            "source_id": source_id,
            "num_lines": len(src_lines),
            "num_tokens": len(src_tokens),
            "vocab_size": len(src_vocab),
            "type_overlap_rate": type_overlap_rate,
            "token_coverage": token_coverage,
            "admissibility": rate,
            "extended_admissibility": ext_rate,
            "admissibility_ratio": adm_ratio,
            "extended_ratio": ext_ratio,
            "clamped_tokens": total,
            "permutation_test": perm,
        }

    # 4. Summary table
    table = Table(title="Cross-Transcription Validation")
    table.add_column("Source", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_column("Vocab Overlap", justify="right")
    table.add_column("Token Cov.", justify="right")
    table.add_column("Adm. (±1)", justify="right")
    table.add_column("Ratio", justify="right", style="bold green")
    table.add_column("Z-Score", justify="right")

    # ZL baseline row
    table.add_row(
        "[bold]ZL (baseline)[/bold]",
        f"{len(zl_tokens):,}",
        "100.0%",
        "100.0%",
        f"{zl_rate * 100:.2f}%",
        "1.000",
        "—",
    )

    for label in ["GC", "VT", "IT", "RF", "FG"]:
        if label not in source_results:
            continue
        r = source_results[label]
        table.add_row(
            label,
            f"{r['num_tokens']:,}",
            f"{r['type_overlap_rate']:.1%}",
            f"{r['token_coverage']:.1%}",
            f"{r['admissibility'] * 100:.2f}%",
            f"{r['admissibility_ratio']:.3f}",
            f"{r['permutation_test']['z_score']:.1f}",
        )
    console.print(table)

    # 5. Mean admissibility ratio
    if source_results:
        ratios = [r["admissibility_ratio"] for r in source_results.values()]
        mean_ratio = np.mean(ratios)
        console.print(
            f"\nMean admissibility ratio: {mean_ratio:.3f} "
            f"(1.0 = perfect transcription independence)"
        )

        sig_count = sum(
            1 for r in source_results.values()
            if r["permutation_test"]["p_value"] < 0.05
        )
        console.print(
            f"Sources with significant structure (p < 0.05): "
            f"{sig_count}/{len(source_results)}"
        )

    # 6. Save results
    output = {
        "zl_baseline": {
            "admissibility": zl_rate,
            "extended_admissibility": zl_ext_rate,
            "tokens": len(zl_tokens),
            "clamped_tokens": zl_total,
        },
        "sources": source_results,
        "mean_admissibility_ratio": float(mean_ratio) if source_results else None,
        "significant_sources": sig_count if source_results else 0,
        "total_sources_tested": len(source_results),
    }

    ProvenanceWriter.save_results(output, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    # Interpretation
    if source_results and mean_ratio > 0.80:
        console.print(
            f"\n[bold green]STRONG:[/bold green] Mean ratio {mean_ratio:.3f} "
            "indicates the lattice captures genuine manuscript structure "
            "that is consistent across independent transcriptions."
        )
    elif source_results and mean_ratio > 0.60:
        console.print(
            f"\n[bold yellow]MODERATE:[/bold yellow] Mean ratio {mean_ratio:.3f}. "
            "The lattice partially transfers across transcriptions."
        )
    else:
        console.print(
            f"\n[bold]WEAK:[/bold] Mean ratio {mean_ratio:.3f}. "
            "The lattice may be overfitting to ZL-specific transcription choices."
        )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z3_cross_transcription"}
    ):
        main()
