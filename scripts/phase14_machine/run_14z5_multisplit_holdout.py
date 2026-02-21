#!/usr/bin/env python3
"""Phase 14Z5: Multi-Split Holdout Validation.

Extends the single Herbal→Biological holdout (14G) to a full
leave-one-section-out validation across all 7 manuscript sections.

For each held-out section:
  1. Train a fresh lattice on the remaining 6 sections via GlobalPaletteSolver.
  2. Build a Copy-Reset model on the same training data.
  3. Test both on the held-out section.
  4. Report admissibility (strict + drift), z-scores, and chance baselines.

The aggregate table provides the strongest generalization evidence:
if the lattice beats chance (z > 3σ) in most splits, the structure
is not an artifact of any single training/test pair.
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

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
    project_root / "results/data/phase14_machine/multisplit_holdout.json"
)
console = Console()

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


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
                TranscriptionTokenRecord.line_id
                == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(
                TranscriptionLineRecord.source_id == "zandbergen_landini"
            )
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
                # Crossed out of range; flush
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


def measure_admissibility(lines, lattice_map, window_contents, num_wins):
    """Measure strict and drift admissibility for a set of lines.

    Returns dict with strict/drift rates, chance baselines, z-scores, counts.
    """
    strict_count = 0
    drift_count = 0
    total_tokens = 0
    current_window = 0

    # Chance baselines
    all_window_words = set()
    for words in window_contents.values():
        all_window_words.update(words)
    total_lattice_vocab = len(all_window_words)
    total_wc = sum(len(v) for v in window_contents.values())
    avg_window_size = total_wc / num_wins if num_wins > 0 else 0
    strict_chance = (
        avg_window_size / total_lattice_vocab
        if total_lattice_vocab > 0 else 0
    )
    drift_chance = min(1.0, 3 * strict_chance)

    for line in lines:
        for word in line:
            total_tokens += 1

            if word not in lattice_map:
                continue

            is_strict = word in window_contents.get(current_window, [])
            is_drift = is_strict

            if not is_drift:
                for offset in [-1, 1]:
                    check_win = (current_window + offset) % num_wins
                    if word in window_contents.get(check_win, []):
                        is_drift = True
                        current_window = check_win
                        break

            if is_strict:
                strict_count += 1
                drift_count += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            elif is_drift:
                drift_count += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            else:
                if word in lattice_map:
                    current_window = lattice_map[word]

    strict_rate = strict_count / total_tokens if total_tokens > 0 else 0
    drift_rate = drift_count / total_tokens if total_tokens > 0 else 0
    strict_z = binomial_z_score(strict_rate, strict_chance, total_tokens)
    drift_z = binomial_z_score(drift_rate, drift_chance, total_tokens)

    return {
        "strict_rate": strict_rate,
        "drift_rate": drift_rate,
        "strict_chance": strict_chance,
        "drift_chance": drift_chance,
        "strict_z": strict_z,
        "drift_z": drift_z,
        "total_tokens": total_tokens,
        "strict_count": strict_count,
        "drift_count": drift_count,
    }


def build_copy_reset_model(lines, copy_window=5):
    """Estimate Copy-Reset parameters from training lines."""
    all_tokens = [t for line in lines for t in line]
    counts = Counter(all_tokens)
    total = len(all_tokens)

    unigram_prob = {w: c / total for w, c in counts.items()}

    copy_hits = 0
    copy_eligible = 0
    for line in lines:
        for i in range(1, len(line)):
            copy_eligible += 1
            recent = set(line[max(0, i - copy_window):i])
            if line[i] in recent:
                copy_hits += 1

    p_copy = copy_hits / copy_eligible if copy_eligible > 0 else 0.0
    return {
        "p_copy": p_copy,
        "copy_window": copy_window,
        "unigram_prob": unigram_prob,
        "vocab": set(all_tokens),
    }


def copy_reset_admissibility(model, test_lines):
    """Measure Copy-Reset 'admissibility' on held-out lines.

    A token is CR-admissible if it appears in the recent copy window.
    """
    copy_window = model["copy_window"]
    copy_admissible = 0
    total_tokens = 0

    for line in test_lines:
        for i, word in enumerate(line):
            total_tokens += 1
            if i == 0:
                continue
            recent = set(line[max(0, i - copy_window):i])
            if word in recent:
                copy_admissible += 1

    rate = copy_admissible / total_tokens if total_tokens > 0 else 0
    return rate, total_tokens


def copy_reset_chance(model, copy_window=5):
    """Chance baseline for Copy-Reset: P(match in window of k)."""
    vocab_size = len(model["vocab"])
    if vocab_size == 0:
        return 0.0
    k = min(copy_window, vocab_size)
    return 1 - ((1 - 1 / vocab_size) ** k)


def main():
    console.print(
        "[bold green]Phase 14Z5: Multi-Split Holdout Validation[/bold green]"
    )

    store = MetadataStore(DB_PATH)

    # Pre-load all section lines
    section_data = {}
    for section_name, (lo, hi) in SECTIONS.items():
        lines = get_section_lines(store, lo, hi)
        tokens = sum(len(line) for line in lines)
        section_data[section_name] = {
            "lines": lines,
            "range": (lo, hi),
            "num_lines": len(lines),
            "num_tokens": tokens,
        }
        console.print(
            f"  {section_name}: {len(lines)} lines, {tokens:,} tokens "
            f"(f{lo}-f{hi})"
        )

    total_corpus_tokens = sum(d["num_tokens"] for d in section_data.values())
    console.print(f"\nTotal corpus: {total_corpus_tokens:,} tokens across 7 sections")

    # Run leave-one-out for each section
    split_results = {}

    for holdout_name in SECTIONS:
        console.print(
            f"\n{'='*60}\n"
            f"[bold]Holdout: {holdout_name}[/bold]"
        )

        # Build training set (all sections except holdout)
        train_lines = []
        for name, data in section_data.items():
            if name != holdout_name:
                train_lines.extend(data["lines"])

        test_lines = section_data[holdout_name]["lines"]
        train_tokens = sum(len(l) for l in train_lines)
        test_tokens = section_data[holdout_name]["num_tokens"]

        console.print(
            f"  Train: {len(train_lines)} lines ({train_tokens:,} tokens)"
        )
        console.print(
            f"  Test: {len(test_lines)} lines ({test_tokens:,} tokens)"
        )

        if len(test_lines) < 5:
            console.print(
                f"  [yellow]WARNING: Very few test lines ({len(test_lines)}). "
                f"Results may be unreliable.[/yellow]"
            )

        # ── Train Lattice ──
        console.print("  Training lattice on remaining sections...")
        solver = GlobalPaletteSolver()
        # Conservative: transitions only (no slips) for holdout
        solver.ingest_data([], train_lines, top_n=None)
        solved_pos = solver.solve_grid(iterations=20)
        lattice_data = solver.cluster_lattice(solved_pos, num_windows=50)

        lattice_map = lattice_data["word_to_window"]
        window_contents = lattice_data["window_contents"]
        num_windows = len(window_contents)

        # ── Test Lattice ──
        console.print("  Measuring lattice admissibility on holdout...")
        lattice_result = measure_admissibility(
            test_lines, lattice_map, window_contents, num_windows
        )

        console.print(
            f"  Lattice: strict={lattice_result['strict_rate']*100:.2f}%, "
            f"drift={lattice_result['drift_rate']*100:.2f}%, "
            f"z={lattice_result['drift_z']:.1f}σ"
        )

        # ── Train & Test Copy-Reset ──
        console.print("  Building Copy-Reset model...")
        cr_model = build_copy_reset_model(train_lines, copy_window=5)
        cr_rate, cr_total = copy_reset_admissibility(cr_model, test_lines)
        cr_chance = copy_reset_chance(cr_model, copy_window=5)
        cr_z = binomial_z_score(cr_rate, cr_chance, cr_total)

        console.print(
            f"  Copy-Reset: adm={cr_rate*100:.2f}%, z={cr_z:.1f}σ"
        )

        # ── Compare ──
        lattice_wins = lattice_result["drift_rate"] > cr_rate

        split_results[holdout_name] = {
            "train_tokens": train_tokens,
            "test_tokens": test_tokens,
            "train_lines": len(train_lines),
            "test_lines": len(test_lines),
            "lattice": {
                "strict_rate": lattice_result["strict_rate"],
                "drift_rate": lattice_result["drift_rate"],
                "strict_chance": lattice_result["strict_chance"],
                "drift_chance": lattice_result["drift_chance"],
                "strict_z": lattice_result["strict_z"],
                "drift_z": lattice_result["drift_z"],
                "total_tokens": lattice_result["total_tokens"],
            },
            "copy_reset": {
                "admissibility_rate": cr_rate,
                "chance_baseline": cr_chance,
                "z_score": cr_z,
                "total_tokens": cr_total,
                "p_copy": cr_model["p_copy"],
                "train_vocab_size": len(cr_model["vocab"]),
            },
            "lattice_wins": lattice_wins,
            "small_sample_warning": test_tokens < 2000,
        }

        if lattice_wins:
            console.print(
                f"  → [green]LATTICE WINS[/green] "
                f"({lattice_result['drift_rate']*100:.2f}% vs "
                f"{cr_rate*100:.2f}%)"
            )
        else:
            console.print(
                f"  → [yellow]COPY-RESET WINS[/yellow] "
                f"({cr_rate*100:.2f}% vs "
                f"{lattice_result['drift_rate']*100:.2f}%)"
            )

    # ── Summary Table ──
    console.print(f"\n{'='*60}")
    table = Table(title="Multi-Split Holdout Summary")
    table.add_column("Held Out", style="cyan")
    table.add_column("Test Tok.", justify="right")
    table.add_column("Lattice Drift", justify="right", style="green")
    table.add_column("Lattice Z", justify="right")
    table.add_column("CR Adm.", justify="right")
    table.add_column("CR Z", justify="right")
    table.add_column("Winner", justify="center")
    table.add_column("Flag", justify="center")

    lattice_z_scores = []
    cr_z_scores = []
    lattice_win_count = 0
    lattice_sig_count = 0

    for section_name in SECTIONS:
        r = split_results[section_name]
        lz = r["lattice"]["drift_z"]
        cz = r["copy_reset"]["z_score"]
        lattice_z_scores.append(lz)
        cr_z_scores.append(cz)
        if r["lattice_wins"]:
            lattice_win_count += 1
        if lz > 3:
            lattice_sig_count += 1

        flag = "⚠" if r["small_sample_warning"] else ""
        winner = "Lattice" if r["lattice_wins"] else "CR"
        winner_style = "green" if r["lattice_wins"] else "yellow"

        table.add_row(
            section_name,
            f"{r['test_tokens']:,}",
            f"{r['lattice']['drift_rate']*100:.2f}%",
            f"{lz:.1f}σ",
            f"{r['copy_reset']['admissibility_rate']*100:.2f}%",
            f"{cz:.1f}σ",
            f"[{winner_style}]{winner}[/{winner_style}]",
            flag,
        )

    console.print(table)

    # Aggregate statistics
    mean_lattice_z = sum(lattice_z_scores) / len(lattice_z_scores)
    mean_cr_z = sum(cr_z_scores) / len(cr_z_scores)

    console.print("\n[bold]Aggregate:[/bold]")
    console.print(
        f"  Mean lattice drift z-score: {mean_lattice_z:.1f}σ"
    )
    console.print(f"  Mean CR z-score: {mean_cr_z:.1f}σ")
    console.print(
        f"  Lattice significant (z > 3σ): {lattice_sig_count}/7 splits"
    )
    console.print(
        f"  Lattice wins: {lattice_win_count}/7 splits"
    )

    # Save results
    output = {
        "splits": split_results,
        "aggregate": {
            "mean_lattice_drift_z": mean_lattice_z,
            "mean_cr_z": mean_cr_z,
            "lattice_significant_count": lattice_sig_count,
            "lattice_win_count": lattice_win_count,
            "total_splits": 7,
            "lattice_z_scores": lattice_z_scores,
            "cr_z_scores": cr_z_scores,
        },
    }

    ProvenanceWriter.save_results(output, OUTPUT_PATH)
    console.print(f"\n[green]Saved {OUTPUT_PATH}[/green]")

    # Verdict
    if lattice_sig_count >= 5:
        console.print(
            f"\n[bold green]STRONG:[/bold green] Lattice is significant "
            f"(z > 3σ) in {lattice_sig_count}/7 leave-one-out splits. "
            f"Structure generalizes robustly across sections."
        )
    elif lattice_sig_count >= 3:
        console.print(
            f"\n[bold yellow]MODERATE:[/bold yellow] Lattice is significant "
            f"in {lattice_sig_count}/7 splits. Generalization is partial."
        )
    else:
        console.print(
            f"\n[bold red]WEAK:[/bold red] Lattice is significant in only "
            f"{lattice_sig_count}/7 splits."
        )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z5_multisplit_holdout"}
    ):
        main()
