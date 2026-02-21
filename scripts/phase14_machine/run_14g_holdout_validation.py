#!/usr/bin/env python3
"""Phase 14G: Holdout Validation.

Trains the lattice on one section (Herbal) and tests admissibility
on another (Biological) to prove generalizability.

Reports both strict and drift admissibility with computed chance
baselines and formal z-scores.
"""

import math
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

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
SLIP_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/holdout_performance.json"
console = Console()

def get_folio_num(folio_id):
    match = re.search(r'f(\d+)', folio_id)
    return int(match.group(1)) if match else 0

def get_section_lines(store, start_f, end_f):
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
                if last_line_id is not None and line_id != last_line_id:
                    lines.append(current_line)
                    current_line = []
                current_line.append(content)
                last_line_id = line_id
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


def main():
    console.print(
        "[bold green]Phase 14G: Holdout Validation"
        " (The Generalization Test)[/bold green]"
    )

    store = MetadataStore(DB_PATH)

    # 1. Split Data: Train (Herbal: 1-66), Test (Biological: 75-84)
    console.print("Extracting Herbal section (Training)...")
    train_lines = get_section_lines(store, 1, 66)
    console.print(f"  Training on {len(train_lines)} lines.")

    console.print("Extracting Biological section (Testing)...")
    test_lines = get_section_lines(store, 75, 84)
    console.print(f"  Testing on {len(test_lines)} lines.")

    # 2. Train Lattice on Herbal
    solver = GlobalPaletteSolver()
    # Note: holdout uses transitions only (no slips) for a conservative test.
    # The production model additionally uses slips at weight=10.0.
    solver.ingest_data([], train_lines, top_n=2000)
    solved_pos = solver.solve_grid(iterations=20)
    lattice_data = solver.cluster_lattice(solved_pos, num_windows=50)

    lattice_map = lattice_data["word_to_window"]
    window_contents = lattice_data["window_contents"]
    num_windows = len(window_contents)

    # Precompute chance baselines from window sizes
    vocab_in_lattice = set(lattice_map.keys())
    avg_window_size = (
        sum(len(v) for v in window_contents.values()) / num_windows
        if num_windows > 0
        else 0
    )
    total_lattice_vocab = len(vocab_in_lattice)
    strict_chance = avg_window_size / total_lattice_vocab if total_lattice_vocab > 0 else 0
    drift_chance = min(1.0, 3 * strict_chance)

    # 3. Test Admissibility on Biological
    console.print("Measuring admissibility of Biological section under Herbal lattice...")
    strict_count = 0
    drift_count = 0
    total_tokens = 0
    current_window = 0

    for line in test_lines:
        for word in line:
            total_tokens += 1

            if word not in lattice_map:
                continue

            # Strict: current window only
            is_strict = word in window_contents.get(current_window, [])

            # Drift: current window ± 1
            is_drift = is_strict
            if not is_drift:
                for offset in [-1, 1]:
                    check_win = (current_window + offset) % num_windows
                    if word in window_contents.get(check_win, []):
                        is_drift = True
                        current_window = check_win
                        break

            if is_strict:
                strict_count += 1
                drift_count += 1
                current_window = lattice_map.get(word, (current_window + 1) % num_windows)
            elif is_drift:
                drift_count += 1
                current_window = lattice_map.get(word, (current_window + 1) % num_windows)
            else:
                # Snap to recover
                if word in lattice_map:
                    current_window = lattice_map[word]

    strict_rate = strict_count / total_tokens if total_tokens > 0 else 0
    drift_rate = drift_count / total_tokens if total_tokens > 0 else 0

    # 4. Compute z-scores
    strict_z = binomial_z_score(strict_rate, strict_chance, total_tokens)
    drift_z = binomial_z_score(drift_rate, drift_chance, total_tokens)

    # 5. Save and Report
    results = {
        "train_lines": len(train_lines),
        "test_lines": len(test_lines),
        "total_test_tokens": total_tokens,
        "note": (
            "Holdout uses transitions-only model (no slips)."
            " Production model uses slips at weight=10.0."
        ),
        "strict": {
            "admissibility_rate": strict_rate,
            "chance_baseline": strict_chance,
            "z_score": strict_z
        },
        "drift": {
            "admissibility_rate": drift_rate,
            "chance_baseline": drift_chance,
            "z_score": drift_z
        },
        # Keep backward-compatible key
        "admissibility_rate": drift_rate
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Holdout validation complete.[/green]")

    table = Table(title="Holdout Validation Results (Herbal → Biological)")
    table.add_column("Metric", style="cyan")
    table.add_column("Strict (offset=0)", justify="right")
    table.add_column("Drift (±1)", justify="right")

    table.add_row("Admissibility", f"{strict_rate*100:.2f}%", f"{drift_rate*100:.2f}%")
    table.add_row("Chance Baseline", f"{strict_chance*100:.2f}%", f"{drift_chance*100:.2f}%")
    table.add_row("Z-Score", f"{strict_z:.1f} σ", f"{drift_z:.1f} σ")
    table.add_row("Total Tokens", str(total_tokens), str(total_tokens))
    console.print(table)

    if drift_z > 10:
        console.print(
            f"\n[bold green]PASS:[/bold green] Holdout admissibility"
            f" is {drift_z:.1f}\u03c3 above chance."
            f" Lattice generalizes across sections."
        )
    elif drift_z > 3:
        console.print(
            f"\n[bold yellow]MARGINAL:[/bold yellow] Holdout"
            f" admissibility is {drift_z:.1f}\u03c3 above chance."
        )
    else:
        console.print(
            f"\n[bold red]FAIL:[/bold red] Holdout admissibility"
            f" not significantly above chance ({drift_z:.1f}\u03c3)."
        )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14g_holdout_validation"}):
        main()
