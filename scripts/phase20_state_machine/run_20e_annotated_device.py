#!/usr/bin/env python3
"""Phase 20, Sprint 7: Per-Window Annotated Device Coverage.

7.1: Per-window top-N coverage (fraction of each window's tokens covered)
7.2: Optimal annotation strategy (greedy allocation across windows)
7.3: Annotated folding tabula specification (physical device design)

Tests whether inscribing top-frequency words on the device can meaningfully
reduce codebook consultation rate, and designs the annotated device.
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

from phase1_foundation.core.data_loading import sanitize_token  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase20_state_machine/annotated_device.json"

# Physical constants (from Sprint 4)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
LINE_SPACING_MM = 2.0
WORD_SPACING_MM = 3.0
MARGIN_MM = 5.0

POSITION_WIDTH_MM = 32.0  # label + correction + sep + margins
POSITION_HEIGHT_MM = 15.0  # glyph + margins

AVG_WORD_CHARS = 5
AVG_WORD_WIDTH_MM = AVG_WORD_CHARS * GLYPH_WIDTH_MM + WORD_SPACING_MM  # 23mm

WORDS_PER_PAGE = 60  # codebook capacity (from Sprint 1)

TOP_N_LEVELS = [1, 2, 3, 5, 10, 15, 20]
BUDGET_LEVELS = [50, 100, 150, 200, 300, 500]


# ── Helpers ───────────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = ("reordered_lattice_map" if "reordered_lattice_map" in results
              else "lattice_map")
    wc_key = ("reordered_window_contents" if "reordered_window_contents" in results
              else "window_contents")
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_lines(store, lattice_map):
    """Load corpus tokens with window assignments."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
            )
            .join(TranscriptionLineRecord,
                  TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord,
                  TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index,
                      TranscriptionTokenRecord.token_index)
            .all()
        )

        tokens = []
        for content, _line_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            w = lattice_map.get(clean)
            if w is not None:
                tokens.append((clean, int(w)))
        return tokens
    finally:
        session.close()


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_7_1(tokens, window_contents):
    """7.1: Per-window top-N coverage."""
    console.rule("[bold blue]7.1: Per-Window Top-N Coverage")

    # Build per-window corpus frequency
    window_freq = defaultdict(Counter)
    for token, w in tokens:
        window_freq[w][token] += 1

    total_tokens = len(tokens)
    per_window_coverage = {}

    for w in range(NUM_WINDOWS):
        wf = window_freq[w]
        w_total = sum(wf.values())
        vocab_size = len(window_contents.get(w, []))

        coverage_at_n = {}
        for n in TOP_N_LEVELS:
            top_n = wf.most_common(n)
            covered = sum(count for _, count in top_n)
            coverage_at_n[n] = {
                "tokens_covered": covered,
                "fraction_of_window": round(covered / w_total, 4) if w_total else 0,
                "fraction_of_corpus": round(covered / total_tokens, 4),
                "words_inscribed": min(n, len(wf)),
            }

        per_window_coverage[w] = {
            "total_tokens": w_total,
            "corpus_fraction": round(w_total / total_tokens, 4),
            "vocab_size": vocab_size,
            "coverage": coverage_at_n,
        }

    # Display: focus on W18 and top-5 windows by token count
    table = Table(title="Per-Window Top-N Coverage (Top 5 Windows + W18)")
    table.add_column("Window", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Vocab", justify="right")
    table.add_column("Top-1", justify="right")
    table.add_column("Top-3", justify="right")
    table.add_column("Top-5", justify="right")
    table.add_column("Top-10", justify="right")
    table.add_column("Top-20", justify="right")

    sorted_windows = sorted(per_window_coverage.items(),
                            key=lambda x: x[1]["total_tokens"], reverse=True)
    display_windows = sorted_windows[:5]
    # Add W18 if not already in top 5
    if 18 not in [w for w, _ in display_windows]:
        display_windows.append((18, per_window_coverage[18]))

    for w, p in display_windows:
        style = "bold" if w == 18 else ""
        table.add_row(
            f"W{w}",
            str(p["total_tokens"]),
            str(p["vocab_size"]),
            f"{p['coverage'][1]['fraction_of_window']:.1%}",
            f"{p['coverage'][3]['fraction_of_window']:.1%}",
            f"{p['coverage'][5]['fraction_of_window']:.1%}",
            f"{p['coverage'][10]['fraction_of_window']:.1%}",
            f"{p['coverage'][20]['fraction_of_window']:.1%}",
            style=style,
        )
    console.print(table)

    # W18 analysis
    w18 = per_window_coverage[18]
    console.print("\n  [bold]W18 Analysis:[/bold]")
    console.print(f"  Tokens: {w18['total_tokens']} "
                  f"({w18['corpus_fraction']:.1%} of corpus)")
    console.print(f"  Vocabulary: {w18['vocab_size']} words")
    for n in [1, 3, 5, 10]:
        c = w18["coverage"][n]
        console.print(f"  Top-{n}: {c['fraction_of_window']:.1%} of W18, "
                      f"{c['fraction_of_corpus']:.1%} of corpus")

    # Global summary: if we inscribe top-N on EVERY window, total coverage
    table2 = Table(title="Global Coverage at Uniform Top-N")
    table2.add_column("N/Window", justify="right")
    table2.add_column("Words Inscribed", justify="right")
    table2.add_column("Tokens Covered", justify="right")
    table2.add_column("Coverage", justify="right", style="bold")
    table2.add_column("Consult Rate", justify="right")

    global_coverage = {}
    for n in TOP_N_LEVELS:
        total_covered = sum(
            p["coverage"][n]["tokens_covered"]
            for p in per_window_coverage.values()
        )
        total_inscribed = sum(
            p["coverage"][n]["words_inscribed"]
            for p in per_window_coverage.values()
        )
        frac = total_covered / total_tokens
        global_coverage[n] = {
            "words_inscribed": total_inscribed,
            "tokens_covered": total_covered,
            "coverage": round(frac, 4),
            "consultation_rate": round(1.0 - frac, 4),
        }
        table2.add_row(
            str(n),
            str(total_inscribed),
            str(total_covered),
            f"{frac:.1%}",
            f"{1.0 - frac:.1%}",
        )
    console.print(table2)

    return {
        "per_window": {
            str(w): {
                "total_tokens": p["total_tokens"],
                "corpus_fraction": p["corpus_fraction"],
                "vocab_size": p["vocab_size"],
                "coverage": {str(n): c for n, c in p["coverage"].items()},
            }
            for w, p in per_window_coverage.items()
        },
        "global_uniform": {str(n): c for n, c in global_coverage.items()},
        "w18_detail": {
            "total_tokens": w18["total_tokens"],
            "corpus_fraction": w18["corpus_fraction"],
            "vocab_size": w18["vocab_size"],
            "top3_coverage_of_window": w18["coverage"][3]["fraction_of_window"],
            "top3_coverage_of_corpus": w18["coverage"][3]["fraction_of_corpus"],
        },
    }, per_window_coverage, window_freq


def sprint_7_2(tokens, window_freq, per_window_coverage):
    """7.2: Optimal annotation strategy (greedy allocation)."""
    console.rule("[bold blue]7.2: Optimal Annotation Strategy")

    total_tokens = len(tokens)

    # Build a priority queue: for each window, the marginal gain of adding
    # the next word (sorted by corpus frequency contribution)
    # A "word candidate" = (window, word, corpus_frequency)
    candidates = []
    for w in range(NUM_WINDOWS):
        wf = window_freq[w]
        for word, count in wf.most_common():
            candidates.append((count, w, word))

    # Sort by frequency (highest first) — this IS the greedy order
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Track: for each budget level, which words are inscribed
    inscribed_set = set()
    tokens_covered = 0
    per_window_inscribed = Counter()  # window → count of inscribed words

    budget_results = []
    next_budget_idx = 0

    for rank, (count, w, word) in enumerate(candidates):
        inscribed_set.add(word)
        tokens_covered += count
        per_window_inscribed[w] += 1

        n_inscribed = rank + 1

        # Check if we've hit a budget level
        if (next_budget_idx < len(BUDGET_LEVELS)
                and n_inscribed >= BUDGET_LEVELS[next_budget_idx]):
            coverage = tokens_covered / total_tokens
            budget_results.append({
                "budget": BUDGET_LEVELS[next_budget_idx],
                "words_inscribed": n_inscribed,
                "tokens_covered": tokens_covered,
                "coverage": round(coverage, 4),
                "consultation_rate": round(1.0 - coverage, 4),
                "max_per_window": max(per_window_inscribed.values()),
                "min_per_window": (min(per_window_inscribed.get(w, 0)
                                       for w in range(NUM_WINDOWS))),
                "windows_with_words": sum(1 for w in range(NUM_WINDOWS)
                                          if per_window_inscribed[w] > 0),
            })
            next_budget_idx += 1
            if next_budget_idx >= len(BUDGET_LEVELS):
                break

    # Display
    table = Table(title="Greedy Annotation Allocation")
    table.add_column("Budget", justify="right")
    table.add_column("Coverage", justify="right", style="bold")
    table.add_column("Consult Rate", justify="right")
    table.add_column("Max/Window", justify="right")
    table.add_column("Min/Window", justify="right")
    table.add_column("Active Windows", justify="right")

    for br in budget_results:
        table.add_row(
            str(br["budget"]),
            f"{br['coverage']:.1%}",
            f"{br['consultation_rate']:.1%}",
            str(br["max_per_window"]),
            str(br["min_per_window"]),
            str(br["windows_with_words"]),
        )
    console.print(table)

    # Find the budget that achieves <80% consultation
    target_budget = None
    for br in budget_results:
        if br["consultation_rate"] < 0.80:
            target_budget = br
            break

    if target_budget:
        console.print(f"\n  First budget below 80% consultation: "
                      f"{target_budget['budget']} words")
        console.print(f"  Coverage: {target_budget['coverage']:.1%}, "
                      f"Consultation: {target_budget['consultation_rate']:.1%}")
    else:
        console.print("\n  [yellow]No budget level achieves <80% consultation[/yellow]")

    # Marginal gain analysis: how much does each additional word help?
    console.print("\n  Marginal gain at each budget:")
    for i, br in enumerate(budget_results):
        if i == 0:
            marginal = br["coverage"]
            per_word = marginal / br["budget"] * 100
        else:
            prev = budget_results[i - 1]
            marginal = br["coverage"] - prev["coverage"]
            per_word = marginal / (br["budget"] - prev["budget"]) * 100
        console.print(f"    B={br['budget']}: +{marginal:.1%} total, "
                      f"{per_word:.3f}% per word")

    return {
        "budget_results": budget_results,
        "target_below_80pct": target_budget,
        "greedy_order_top10": [
            {"word": word, "window": w, "corpus_count": count}
            for count, w, word in candidates[:10]
        ],
    }


def sprint_7_3(budget_results, per_window_coverage, window_freq):
    """7.3: Annotated folding tabula specification."""
    console.rule("[bold blue]7.3: Annotated Folding Tabula Specification")

    # Use B=200 as the recommended budget (reasonable annotation density)
    recommended = None
    for br in budget_results["budget_results"]:
        if br["budget"] == 200:
            recommended = br
            break
    if recommended is None:
        recommended = budget_results["budget_results"][-1]

    budget = recommended["budget"]
    console.print(f"  Annotation budget: {budget} words")
    console.print(f"  Coverage: {recommended['coverage']:.1%}")
    console.print(f"  Consultation rate: {recommended['consultation_rate']:.1%}")

    # Determine per-window allocation using greedy
    # Rebuild the allocation for the target budget
    candidates = []
    for w in range(NUM_WINDOWS):
        wf = window_freq[w]
        for word, count in wf.most_common():
            candidates.append((count, w, word))
    candidates.sort(key=lambda x: x[0], reverse=True)

    per_window_words = defaultdict(list)
    for rank, (count, w, word) in enumerate(candidates[:budget]):
        per_window_words[w].append({"word": word, "count": count})

    # Per-window annotation summary
    panel_allocations = {}
    for w in range(NUM_WINDOWS):
        words = per_window_words.get(w, [])
        panel_allocations[w] = {
            "n_words": len(words),
            "words": [wd["word"] for wd in words[:5]],  # top 5 for display
        }

    # Display per-window allocation (top 10 windows by annotation count)
    table = Table(title=f"Per-Window Annotation (B={budget})")
    table.add_column("Window", justify="right")
    table.add_column("Words", justify="right")
    table.add_column("Top Inscribed", style="cyan")

    sorted_alloc = sorted(panel_allocations.items(),
                          key=lambda x: x[1]["n_words"], reverse=True)
    for w, alloc in sorted_alloc[:10]:
        table.add_row(
            f"W{w}",
            str(alloc["n_words"]),
            ", ".join(alloc["words"][:3]),
        )
    console.print(table)

    # Folding tabula design
    # From Sprint 4: 10-panel tabula, 5 windows per panel
    n_panels = 10
    windows_per_panel = 5

    # Each window cell: state label + correction + annotated words
    max_words_per_cell = max(a["n_words"] for a in panel_allocations.values())
    word_line_height = GLYPH_HEIGHT_MM + LINE_SPACING_MM

    # Cell dimensions
    cell_width = POSITION_WIDTH_MM + AVG_WORD_WIDTH_MM  # label + word column
    cell_height = max(POSITION_HEIGHT_MM,
                      (max_words_per_cell + 1) * word_line_height + 2 * MARGIN_MM)

    panel_cols = 1  # one column of windows per panel (tall and narrow)
    panel_rows = windows_per_panel
    panel_width = cell_width + 2 * MARGIN_MM
    panel_height = panel_rows * cell_height + 2 * MARGIN_MM

    folded_max = max(panel_width, panel_height)

    console.print("\n  [bold]Annotated Folding Tabula Design:[/bold]")
    console.print(f"  Layout: {n_panels} panels × {windows_per_panel} windows")
    console.print(f"  Max words per cell: {max_words_per_cell}")
    console.print(f"  Cell size: {cell_width:.0f} × {cell_height:.0f} mm")
    console.print(f"  Panel size: {panel_width:.0f} × {panel_height:.0f} mm")
    console.print(f"  Folded max dimension: {folded_max:.0f} mm")

    if folded_max <= 200:
        size_cat = "PORTABLE"
    elif folded_max <= 300:
        size_cat = "HANDHELD"
    elif folded_max <= 500:
        size_cat = "DESKTOP"
    else:
        size_cat = "OVERSIZED"
    console.print(f"  Category: {size_cat}")

    # Codebook reduction
    total_vocab = sum(p["vocab_size"]
                      for p in per_window_coverage.values())
    remaining_vocab = total_vocab - budget
    remaining_pages = math.ceil(remaining_vocab / WORDS_PER_PAGE)
    original_pages = math.ceil(total_vocab / WORDS_PER_PAGE)
    reduction = 1.0 - remaining_pages / original_pages

    console.print("\n  Codebook reduction:")
    console.print(f"    Original: {total_vocab} words → {original_pages} pages")
    console.print(f"    After annotation: {remaining_vocab} words → "
                  f"{remaining_pages} pages")
    console.print(f"    Reduction: {reduction:.1%}")

    # Verdict
    plausible = folded_max <= 300 and recommended["consultation_rate"] < 0.80
    verdict = "PLAUSIBLE" if plausible else "MARGINAL"
    console.print(f"\n  Verdict: [bold]{verdict}[/bold]")

    return {
        "budget": budget,
        "coverage": recommended["coverage"],
        "consultation_rate": recommended["consultation_rate"],
        "design": {
            "n_panels": n_panels,
            "windows_per_panel": windows_per_panel,
            "max_words_per_cell": max_words_per_cell,
            "cell_dims_mm": {
                "width": round(cell_width),
                "height": round(cell_height),
            },
            "panel_dims_mm": {
                "width": round(panel_width),
                "height": round(panel_height),
            },
            "folded_max_dim_mm": round(folded_max),
            "size_category": size_cat,
        },
        "codebook_reduction": {
            "original_vocab": total_vocab,
            "original_pages": original_pages,
            "remaining_vocab": remaining_vocab,
            "remaining_pages": remaining_pages,
            "reduction_fraction": round(reduction, 4),
        },
        "per_window_allocation": {
            str(w): alloc["n_words"]
            for w, alloc in panel_allocations.items()
        },
        "verdict": verdict,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 20, Sprint 7: Per-Window Annotated "
                 "Device Coverage")

    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    store = MetadataStore(DB_PATH)
    tokens = load_lines(store, lattice_map)
    console.print(f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows")
    console.print(f"  Corpus tokens: {len(tokens)}")

    # 7.1
    s7_1, per_window_coverage, window_freq = sprint_7_1(tokens, window_contents)

    # 7.2
    s7_2 = sprint_7_2(tokens, window_freq, per_window_coverage)

    # 7.3
    s7_3 = sprint_7_3(s7_2, per_window_coverage, window_freq)

    results = {
        "per_window_coverage": s7_1,
        "optimal_allocation": s7_2,
        "annotated_tabula": s7_3,
        "summary": {
            "w18_top3_coverage": s7_1["w18_detail"]["top3_coverage_of_window"],
            "best_uniform_n10_coverage": s7_1["global_uniform"]["10"]["coverage"],
            "greedy_200_consultation": s7_2["target_below_80pct"]["consultation_rate"]
            if s7_2["target_below_80pct"] else None,
            "tabula_verdict": s7_3["verdict"],
        },
    }

    # Sanitize numpy types
    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    results = _sanitize(results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_20e_annotated_device"}):
        main()
