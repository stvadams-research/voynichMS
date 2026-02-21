#!/usr/bin/env python3
"""Phase 14I Sprint 2: Context-Conditioned Admissibility Evaluator.

Sprint 1 showed that per-window mode offset correction achieves a
theoretical ceiling of 64.37% admissibility (+18.46pp over baseline)
with only 50 parameters.  This script cross-validates that improvement
using leave-one-section-out holdout.

For each of 7 sections:
  1. Train a fresh lattice on the remaining 6 sections.
  2. Compute per-window offset correction from training transitions.
  3. Score held-out section under baseline and corrected models.
  4. Report improvement, z-score, and overfitting diagnostic.

Also sweeps min_obs thresholds and compares window-level vs word-level
correction under cross-validation.
"""

import json
import math
import re
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
from phase14_machine.palette_solver import GlobalPaletteSolver  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
SLIP_PATH = (
    project_root / "results/data/phase12_mechanical/slip_detection_results.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/bigram_conditioned.json"
)
console = Console()

NUM_WINDOWS = 50

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


# ── Helpers ──────────────────────────────────────────────────────────────

def get_folio_num(folio_id):
    """Extract numeric folio index from page id."""
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def get_section_lines(store, start_f, end_f):
    """Load canonical ZL lines filtered to a folio range."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
                TranscriptionLineRecord.id,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )

        lines = []
        current_line = []
        last_line_id = None
        for content, folio_id, line_id in rows:
            f_num = get_folio_num(folio_id)
            if start_f <= f_num <= end_f:
                clean = sanitize_token(content)
                if not clean:
                    continue
                if last_line_id is not None and line_id != last_line_id:
                    if current_line:
                        lines.append(current_line)
                    current_line = []
                current_line.append(clean)
                last_line_id = line_id
            elif last_line_id is not None and current_line:
                lines.append(current_line)
                current_line = []
                last_line_id = None

        if current_line:
            lines.append(current_line)
        return lines
    finally:
        session.close()


def binomial_z_score(observed_rate, chance_rate, n):
    """Compute z-score for observed rate vs binomial null."""
    if n == 0 or chance_rate <= 0 or chance_rate >= 1:
        return 0.0
    se = math.sqrt(chance_rate * (1 - chance_rate) / n)
    if se == 0:
        return 0.0
    return (observed_rate - chance_rate) / se


def signed_circular_offset(a, b, n=NUM_WINDOWS):
    """Signed circular distance from window a to window b."""
    raw = (b - a) % n
    if raw > n // 2:
        raw -= n
    return raw


def circular_distance(a, b, n=NUM_WINDOWS):
    """Unsigned circular distance between two window indices."""
    d = abs(a - b) % n
    return min(d, n - d)


# ── Core Functions ───────────────────────────────────────────────────────

def train_lattice(train_lines):
    """Train a fresh lattice on training lines."""
    solver = GlobalPaletteSolver()
    solver.ingest_data([], train_lines, top_n=None)
    solved_pos = solver.solve_grid(iterations=20)
    lattice_data = solver.cluster_lattice(solved_pos, num_windows=NUM_WINDOWS)
    lattice_map = lattice_data["word_to_window"]
    window_contents = lattice_data["window_contents"]
    return lattice_map, window_contents


def learn_offset_corrections(lines, lattice_map, level="window", min_obs=5):
    """Learn per-window or per-word mode offset corrections from training data.

    Returns a dict mapping correction_key → mode_offset.
    """
    groups = defaultdict(list)

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            offset = signed_circular_offset(prev_win, curr_win)

            if level == "window":
                groups[prev_win].append(offset)
            else:
                groups[prev_word].append(offset)

    corrections = {}
    for key, offsets in groups.items():
        if len(offsets) >= min_obs:
            corrections[key] = Counter(offsets).most_common(1)[0][0]

    return corrections


def score_with_correction(lines, lattice_map, corrections, level="window"):
    """Score admissibility on lines using offset corrections.

    Returns (corrected_admissible, baseline_admissible, total, coverage_count).
    """
    corrected_adm = 0
    baseline_adm = 0
    total = 0
    covered = 0  # tokens with a correction available

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue

            total += 1
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            raw_offset = signed_circular_offset(prev_win, curr_win)

            # Baseline: |raw_offset| ≤ 1
            if abs(raw_offset) <= 1:
                baseline_adm += 1

            # Corrected
            if level == "window":
                key = prev_win
            else:
                key = prev_word

            correction = corrections.get(key, 0)
            if correction != 0:
                covered += 1
            corrected_offset = raw_offset - correction
            # Wrap
            if corrected_offset > NUM_WINDOWS // 2:
                corrected_offset -= NUM_WINDOWS
            elif corrected_offset < -NUM_WINDOWS // 2:
                corrected_offset += NUM_WINDOWS
            if abs(corrected_offset) <= 1:
                corrected_adm += 1

    return corrected_adm, baseline_adm, total, covered


def chance_baseline_corrected(lattice_map, window_contents):
    """Compute chance baseline for corrected model.

    Conservative: assume 3 windows checked (same as drift baseline).
    """
    all_words = set()
    for words in window_contents.values():
        all_words.update(words)
    total_lattice_vocab = len(all_words)
    total_wc = sum(len(v) for v in window_contents.values())
    avg_window_size = total_wc / NUM_WINDOWS if NUM_WINDOWS > 0 else 0
    drift_chance = min(1.0, 3 * avg_window_size / total_lattice_vocab) if total_lattice_vocab > 0 else 0
    return drift_chance


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14I Sprint 2: Context-Conditioned Admissibility[/bold magenta]")

    store = MetadataStore(DB_PATH)

    # Load all section lines
    section_data = {}
    for section_name, (lo, hi) in SECTIONS.items():
        lines = get_section_lines(store, lo, hi)
        tokens = sum(len(line) for line in lines)
        section_data[section_name] = {
            "lines": lines,
            "range": (lo, hi),
            "num_tokens": tokens,
        }
        console.print(f"  {section_name}: {len(lines)} lines, {tokens:,} tokens")

    total_corpus = sum(d["num_tokens"] for d in section_data.values())
    console.print(f"\nTotal corpus: {total_corpus:,} tokens")

    # Load slips for palette solver
    slips = []
    if SLIP_PATH.exists():
        with open(SLIP_PATH) as f:
            slip_data = json.load(f)
        slips = slip_data.get("results", slip_data).get("slips", [])
        console.print(f"Loaded {len(slips)} slips for solver")

    # ── Cross-Validation ─────────────────────────────────────────────

    min_obs_values = [3, 5, 10, 20]
    levels = ["window", "word"]
    split_results = []

    for holdout_name in SECTIONS:
        console.print(f"\n{'='*60}")
        console.print(f"[bold]Held out: {holdout_name}[/bold]")

        # Build train/test split
        train_lines = []
        for name, data in section_data.items():
            if name != holdout_name:
                train_lines.extend(data["lines"])
        test_lines = section_data[holdout_name]["lines"]
        test_tokens = section_data[holdout_name]["num_tokens"]

        console.print(f"  Train: {sum(len(l) for l in train_lines)} lines")
        console.print(f"  Test: {len(test_lines)} lines, {test_tokens} tokens")

        # Train fresh lattice
        console.print("  Training lattice...")
        lattice_map, window_contents = train_lattice(train_lines)
        console.print(f"  Lattice: {len(lattice_map)} words, {len(window_contents)} windows")

        chance = chance_baseline_corrected(lattice_map, window_contents)

        split_result = {
            "section": holdout_name,
            "test_tokens": test_tokens,
            "chance_baseline": round(chance, 4),
            "models": {},
        }

        # Test each (level, min_obs) configuration
        for level in levels:
            for min_obs in min_obs_values:
                corrections = learn_offset_corrections(
                    train_lines, lattice_map, level=level, min_obs=min_obs
                )

                # Test set
                test_corr_adm, test_base_adm, test_total, test_covered = (
                    score_with_correction(test_lines, lattice_map, corrections, level=level)
                )

                # Train set (for overfitting check)
                train_corr_adm, train_base_adm, train_total, train_covered = (
                    score_with_correction(train_lines, lattice_map, corrections, level=level)
                )

                test_base_rate = test_base_adm / test_total if test_total else 0
                test_corr_rate = test_corr_adm / test_total if test_total else 0
                train_base_rate = train_base_adm / train_total if train_total else 0
                train_corr_rate = train_corr_adm / train_total if train_total else 0

                test_z = binomial_z_score(test_corr_rate, chance, test_total)
                train_z = binomial_z_score(train_corr_rate, chance, train_total)

                coverage = test_covered / test_total if test_total else 0

                model_key = f"{level}_min{min_obs}"
                split_result["models"][model_key] = {
                    "level": level,
                    "min_obs": min_obs,
                    "num_corrections": len(corrections),
                    "test_baseline_rate": round(test_base_rate, 4),
                    "test_corrected_rate": round(test_corr_rate, 4),
                    "test_delta_pp": round((test_corr_rate - test_base_rate) * 100, 2),
                    "test_z": round(test_z, 1),
                    "test_total": test_total,
                    "test_coverage": round(coverage, 4),
                    "train_baseline_rate": round(train_base_rate, 4),
                    "train_corrected_rate": round(train_corr_rate, 4),
                    "train_delta_pp": round((train_corr_rate - train_base_rate) * 100, 2),
                    "overfit_gap_pp": round((train_corr_rate - test_corr_rate) * 100, 2),
                }

        split_results.append(split_result)

        # Print key results for this split
        best_model = "window_min5"
        m = split_result["models"][best_model]
        console.print(
            f"  {best_model}: test {m['test_baseline_rate']*100:.1f}% → "
            f"{m['test_corrected_rate']*100:.1f}% "
            f"(+{m['test_delta_pp']:.1f}pp, z={m['test_z']:.1f}σ)"
        )

    # ── Aggregate Summary ────────────────────────────────────────────

    console.print(f"\n{'='*60}")
    console.print("[bold green]Aggregate Results[/bold green]")

    # Summary table for the primary model (window_min5)
    primary_model = "window_min5"
    table = Table(title=f"Cross-Validated Results ({primary_model})")
    table.add_column("Held Out", style="cyan")
    table.add_column("Test Tokens", justify="right")
    table.add_column("Baseline", justify="right")
    table.add_column("Corrected", justify="right")
    table.add_column("Delta (pp)", justify="right")
    table.add_column("Z-Score", justify="right")
    table.add_column("Train Corr", justify="right")
    table.add_column("Overfit Gap", justify="right")

    deltas = []
    z_scores = []
    for sr in split_results:
        m = sr["models"][primary_model]
        table.add_row(
            sr["section"],
            str(sr["test_tokens"]),
            f"{m['test_baseline_rate']*100:.1f}%",
            f"{m['test_corrected_rate']*100:.1f}%",
            f"+{m['test_delta_pp']:.1f}",
            f"{m['test_z']:.1f}σ",
            f"{m['train_corrected_rate']*100:.1f}%",
            f"{m['overfit_gap_pp']:.1f}pp",
        )
        deltas.append(m["test_delta_pp"])
        z_scores.append(m["test_z"])

    console.print(table)
    console.print(f"\nMean delta: +{np.mean(deltas):.2f}pp")
    console.print(f"Mean z-score: {np.mean(z_scores):.1f}σ")
    console.print(f"Splits with positive improvement: {sum(1 for d in deltas if d > 0)}/7")

    # Model comparison table
    console.print("\n[bold]Model Comparison (mean across 7 splits):[/bold]")
    comp_table = Table(title="Model Comparison")
    comp_table.add_column("Model", style="cyan")
    comp_table.add_column("Mean Delta (pp)", justify="right")
    comp_table.add_column("Mean Z-Score", justify="right")
    comp_table.add_column("Mean Overfit Gap", justify="right")
    comp_table.add_column("Params", justify="right")

    model_summary = {}
    for level in levels:
        for min_obs in min_obs_values:
            model_key = f"{level}_min{min_obs}"
            all_deltas = [sr["models"][model_key]["test_delta_pp"] for sr in split_results]
            all_z = [sr["models"][model_key]["test_z"] for sr in split_results]
            all_overfit = [sr["models"][model_key]["overfit_gap_pp"] for sr in split_results]
            all_params = [sr["models"][model_key]["num_corrections"] for sr in split_results]

            mean_delta = np.mean(all_deltas)
            mean_z = np.mean(all_z)
            mean_overfit = np.mean(all_overfit)
            mean_params = np.mean(all_params)

            comp_table.add_row(
                model_key,
                f"+{mean_delta:.2f}",
                f"{mean_z:.1f}σ",
                f"{mean_overfit:.1f}pp",
                f"{mean_params:.0f}",
            )

            model_summary[model_key] = {
                "mean_delta_pp": round(float(mean_delta), 2),
                "mean_z_score": round(float(mean_z), 1),
                "mean_overfit_gap_pp": round(float(mean_overfit), 1),
                "mean_num_corrections": round(float(mean_params)),
                "positive_splits": sum(1 for d in all_deltas if d > 0),
            }

    console.print(comp_table)

    # Find best model
    best_key = max(model_summary, key=lambda k: model_summary[k]["mean_delta_pp"])
    console.print(f"\n[bold green]Best model: {best_key} "
                  f"(+{model_summary[best_key]['mean_delta_pp']:.2f}pp mean improvement)[/bold green]")

    # ── Save Results ─────────────────────────────────────────────────

    results = {
        "primary_model": primary_model,
        "best_model": best_key,
        "split_results": split_results,
        "model_summary": model_summary,
        "aggregate": {
            "primary_mean_delta_pp": round(float(np.mean(deltas)), 2),
            "primary_mean_z_score": round(float(np.mean(z_scores)), 1),
            "primary_positive_splits": sum(1 for d in deltas if d > 0),
        },
    }

    with active_run(config={"seed": 42, "command": "run_14z8_bigram_conditioned"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
