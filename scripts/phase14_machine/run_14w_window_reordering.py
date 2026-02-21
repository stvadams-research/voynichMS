#!/usr/bin/env python3
"""Phase 14W: Window Reordering via Transition Graph.

The palette solver assigns window IDs via KMeans on 2D spring-layout
coordinates.  These IDs bear no relation to the scribe's sequential
traversal order.  This script:

1. Builds a 50x50 window-transition matrix from the real corpus.
2. Solves for the optimal circular ordering (greedy nearest-neighbor TSP).
3. Renumbers every window so that the most-common transitions become
   distance-1 moves.
4. Re-measures admissibility under the new ordering.
5. Saves the reordered palette for downstream use.
"""

import json
import sys
from collections import Counter
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
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/reordered_palette.json"
)
console = Console()


def build_transition_matrix(lines, lattice_map, num_wins):
    """Build window-to-window transition count matrix from real corpus."""
    matrix = np.zeros((num_wins, num_wins), dtype=int)
    for line in lines:
        prev_win = None
        for word in line:
            if word in lattice_map:
                cur_win = lattice_map[word]
                if prev_win is not None:
                    matrix[prev_win][cur_win] += 1
                prev_win = cur_win
    return matrix


def greedy_tsp(matrix):
    """Greedy nearest-neighbor TSP on the transition matrix.

    Finds a circular ordering that maximizes the total weight of
    adjacent-in-order transitions.  Starts from the window with the
    highest total transition volume.
    """
    n = matrix.shape[0]
    # Use symmetric version: we want windows that frequently transition
    # in EITHER direction to be adjacent
    sym = matrix + matrix.T

    # Start from the most-connected window
    start = int(np.argmax(sym.sum(axis=1)))
    visited = [start]
    remaining = set(range(n)) - {start}

    while remaining:
        last = visited[-1]
        # Pick the unvisited neighbor with highest transition weight
        best = max(remaining, key=lambda w: sym[last][w])
        visited.append(best)
        remaining.remove(best)

    return visited


def spectral_ordering(matrix):
    """Spectral ordering using the Fiedler vector of the transition graph.

    The Fiedler vector (2nd smallest eigenvector of the graph Laplacian)
    provides an optimal 1D embedding that minimizes transition distances.
    """
    sym = matrix + matrix.T
    # Degree matrix
    D = np.diag(sym.sum(axis=1))
    # Laplacian
    L = D - sym

    # Compute eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(L)

    # Fiedler vector is the 2nd smallest eigenvector
    # (1st is always the constant vector with eigenvalue 0)
    fiedler = eigenvectors[:, 1]

    # Sort windows by their Fiedler coordinate
    order = [int(x) for x in np.argsort(fiedler)]
    return order


def measure_admissibility(lines, lattice_map, window_contents, num_wins):
    """Measure drift-±1 admissibility and categorize transitions."""
    categories = Counter()
    current_window = 0

    for line in lines:
        for word in line:
            if word not in lattice_map:
                continue

            found_dist = None
            for dist in range(0, num_wins // 2 + 1):
                for direction in [1, -1]:
                    check_win = (current_window + (dist * direction)) % num_wins
                    if word in window_contents.get(check_win, []):
                        found_dist = dist
                        break
                if found_dist is not None:
                    break

            if found_dist is None:
                categories["extreme_jump"] += 1
                current_window = lattice_map[word]
            elif found_dist <= 1:
                categories["admissible"] += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            elif found_dist <= 3:
                categories["extended_drift"] += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            elif found_dist <= 10:
                categories["mechanical_slip"] += 1
                current_window = lattice_map.get(
                    word, (current_window + 1) % num_wins
                )
            else:
                categories["extreme_jump"] += 1
                current_window = lattice_map[word]

    total = sum(categories.values())
    return categories, total


def apply_reordering(order, old_lattice_map, old_window_contents):
    """Renumber windows according to the new order.

    order[i] = old_window_id means new_window i corresponds to old_window order[i].
    """
    # Build old_id -> new_id mapping
    old_to_new = {old_id: new_id for new_id, old_id in enumerate(order)}

    new_lattice_map = {
        word: int(old_to_new[old_win])
        for word, old_win in old_lattice_map.items()
        if old_win in old_to_new
    }

    new_window_contents = {}
    for old_id, words in old_window_contents.items():
        new_id = old_to_new.get(old_id)
        if new_id is not None:
            new_window_contents[new_id] = words

    return new_lattice_map, new_window_contents


def main():
    console.print(
        "[bold green]Phase 14W: Window Reordering "
        "(Transition Graph Optimization)[/bold green]"
    )

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load palette and data
    with open(PALETTE_PATH) as f:
        p_data = json.load(f)["results"]
    old_lattice_map = p_data["lattice_map"]
    old_window_contents = {
        int(k): v for k, v in p_data["window_contents"].items()
    }
    num_wins = len(old_window_contents)

    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    console.print(f"Loaded {len(lines)} lines, {num_wins} windows.")

    # 2. Measure baseline admissibility (original ordering)
    console.print("\nBaseline (original KMeans ordering):")
    base_cats, base_total = measure_admissibility(
        lines, old_lattice_map, old_window_contents, num_wins
    )
    base_adm = base_cats.get("admissible", 0) / base_total * 100
    base_jump = base_cats.get("extreme_jump", 0) / base_total * 100
    console.print(
        f"  Admissible: {base_adm:.2f}%, "
        f"Extreme jump: {base_jump:.2f}%"
    )

    # 3. Build transition matrix
    console.print("\nBuilding window transition matrix...")
    trans_matrix = build_transition_matrix(
        lines, old_lattice_map, num_wins
    )

    # Log transition matrix stats
    total_trans = trans_matrix.sum()
    diag_trans = np.trace(trans_matrix)
    adj_trans = sum(
        trans_matrix[i][(i + d) % num_wins]
        for i in range(num_wins)
        for d in [-1, 1]
    )
    console.print(
        f"  Total transitions: {total_trans:,}"
        f"  Same-window: {diag_trans:,} ({diag_trans / total_trans * 100:.1f}%)"
        f"  Adjacent: {adj_trans:,} ({adj_trans / total_trans * 100:.1f}%)"
    )

    # 4. Try both ordering methods
    console.print("\nComputing greedy TSP ordering...")
    greedy_order = greedy_tsp(trans_matrix)

    console.print("Computing spectral (Fiedler) ordering...")
    spectral_order = spectral_ordering(trans_matrix)

    # 5. Evaluate both orderings
    results_table = {}
    best_order = None
    best_adm = base_adm
    best_name = "Original"

    for name, order in [
        ("Greedy TSP", greedy_order),
        ("Spectral", spectral_order),
    ]:
        new_lm, new_wc = apply_reordering(
            order, old_lattice_map, old_window_contents
        )
        cats, total = measure_admissibility(lines, new_lm, new_wc, num_wins)
        adm = cats.get("admissible", 0) / total * 100
        ext = (
            cats.get("admissible", 0) + cats.get("extended_drift", 0)
        ) / total * 100
        jump = cats.get("extreme_jump", 0) / total * 100

        results_table[name] = {
            "admissible": adm,
            "extended": ext,
            "extreme_jump": jump,
            "order": order,
        }

        console.print(
            f"  {name}: Admissible {adm:.2f}%, "
            f"Extended {ext:.2f}%, "
            f"Extreme jump {jump:.2f}%"
        )

        if adm > best_adm:
            best_adm = adm
            best_order = order
            best_name = name

    # 6. Adopt the best ordering
    if best_order is None:
        console.print(
            "\n[yellow]No reordering improved admissibility. "
            "Keeping original.[/yellow]"
        )
        final_lm = old_lattice_map
        final_wc = old_window_contents
        adopted = "Original"
    else:
        console.print(
            f"\n[green]Adopting {best_name} ordering "
            f"({best_adm:.2f}% admissible).[/green]"
        )
        final_lm, final_wc = apply_reordering(
            best_order, old_lattice_map, old_window_contents
        )
        adopted = best_name

    # 7. Final measurement with detailed categories
    final_cats, final_total = measure_admissibility(
        lines, final_lm, final_wc, num_wins
    )

    # 8. Compute transition distance distribution under new ordering
    jump_dist = Counter()
    current_window = 0
    for line in lines:
        for word in line:
            if word in final_lm:
                new_win = final_lm[word]
                delta = abs(new_win - current_window)
                if delta > num_wins // 2:
                    delta = num_wins - delta
                jump_dist[min(delta, 25)] += 1
                current_window = new_win
    total_jumps = sum(jump_dist.values())

    # 9. Save results
    results = {
        "adopted_ordering": adopted,
        "baseline_admissibility": base_adm / 100,
        "final_admissibility": final_cats.get("admissible", 0)
        / final_total,
        "final_extended": (
            final_cats.get("admissible", 0)
            + final_cats.get("extended_drift", 0)
        )
        / final_total,
        "final_extreme_jump": final_cats.get("extreme_jump", 0)
        / final_total,
        "improvement_pp": best_adm - base_adm,
        "categories": {
            k: v / final_total for k, v in final_cats.items()
        },
        "num_windows": num_wins,
        "reordered_lattice_map": final_lm,
        "reordered_window_contents": {
            str(k): v for k, v in final_wc.items()
        },
    }

    if best_order is not None:
        results["window_order"] = best_order

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved reordered palette to {OUTPUT_PATH}[/green]")

    # Report tables
    table = Table(title="Window Reordering Comparison")
    table.add_column("Ordering", style="cyan")
    table.add_column("Admissible (±1)", justify="right", style="bold green")
    table.add_column("Extreme Jump", justify="right")
    table.add_column("Delta", justify="right")

    table.add_row(
        "Original (KMeans)",
        f"{base_adm:.2f}%",
        f"{base_jump:.2f}%",
        "—",
    )
    for name, data in results_table.items():
        delta = data["admissible"] - base_adm
        table.add_row(
            name,
            f"{data['admissible']:.2f}%",
            f"{data['extreme_jump']:.2f}%",
            f"{delta:+.2f}pp",
        )
    console.print(table)

    # Jump distance distribution
    table2 = Table(title="Transition Distances (Final Ordering)")
    table2.add_column("Distance", justify="right", style="cyan")
    table2.add_column("Count", justify="right")
    table2.add_column("Rate", justify="right")
    table2.add_column("Cumulative", justify="right", style="bold green")

    cumulative = 0
    for d in sorted(jump_dist.keys()):
        pct = jump_dist[d] / total_jumps * 100
        cumulative += pct
        table2.add_row(
            str(d),
            f"{jump_dist[d]:,}",
            f"{pct:.1f}%",
            f"{cumulative:.1f}%",
        )
    console.print(table2)


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14w_window_reordering"}
    ):
        main()
