#!/usr/bin/env python3
"""Phase 14U: Copy-Reset Holdout Comparison.

Tests whether Copy-Reset generalizes across manuscript sections.
Trains on Herbal (f1-66), tests on Biological (f75-84) — same
split as 14G — and compares holdout performance against the Lattice.

If Copy-Reset fails to generalize while the Lattice does, the Lattice
has unique structural value even though Copy-Reset wins on full-corpus MDL.
"""

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

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/copyreset_holdout.json"
)
console = Console()


def get_folio_num(folio_id):
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


def build_copy_reset_model(lines, copy_window=5):
    """Estimate Copy-Reset parameters from training lines."""
    all_tokens = [t for line in lines for t in line]
    counts = Counter(all_tokens)
    total = len(all_tokens)

    # Unigram probabilities
    unigram_prob = {w: c / total for w, c in counts.items()}

    # Estimate copy rate
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


def copy_reset_holdout_score(model, test_lines):
    """
    Measure how well Copy-Reset predicts test tokens.

    "Admissibility" for Copy-Reset: a token is admissible if it appears
    in the recent copy window of the same line. This parallels the
    Lattice's drift-admissibility (token in current ± 1 window).

    Also computes log-likelihood for BPT comparison.
    """
    p_copy = model["p_copy"]
    p_emit = 1.0 - p_copy
    unigram_prob = model["unigram_prob"]
    copy_window = model["copy_window"]

    copy_admissible = 0
    total_tokens = 0
    total_nll = 0.0

    for line in test_lines:
        for i, word in enumerate(line):
            total_tokens += 1

            if i == 0:
                # First token: unigram only
                ug = unigram_prob.get(word, 1e-10)
                total_nll += -math.log2(max(ug, 1e-15))
                continue

            recent = set(line[max(0, i - copy_window):i])
            if word in recent:
                copy_admissible += 1
                total_nll += -math.log2(
                    max(p_copy, 1e-10) / len(recent)
                )
            else:
                ug = unigram_prob.get(word, 1e-10)
                total_nll += -math.log2(
                    max(p_emit, 1e-10) * max(ug, 1e-15)
                )

    admissibility = copy_admissible / total_tokens if total_tokens > 0 else 0
    bpt = total_nll / total_tokens if total_tokens > 0 else 0

    return {
        "copy_admissible": copy_admissible,
        "total_tokens": total_tokens,
        "admissibility_rate": admissibility,
        "bpt": bpt,
    }


def copy_reset_chance_baseline(model, test_lines, copy_window=5):
    """
    Compute chance baseline for Copy-Reset admissibility.

    Under null (random token placement), the probability that a token
    matches any of the previous k tokens is approximately:
    P(match) = 1 - (1 - 1/V)^k ≈ k/V for large V.
    """
    vocab_size = len(model["vocab"])
    if vocab_size == 0:
        return 0.0
    k = min(copy_window, vocab_size)
    return 1 - ((1 - 1 / vocab_size) ** k)


def main():
    console.print(
        "[bold cyan]Phase 14U: Copy-Reset Holdout Comparison[/bold cyan]"
    )

    store = MetadataStore(DB_PATH)

    # 1. Split Data (same as 14G)
    console.print("Extracting Herbal section (Training: f1-66)...")
    train_lines = get_section_lines(store, 1, 66)
    console.print(f"  Training on {len(train_lines)} lines.")

    console.print("Extracting Biological section (Testing: f75-84)...")
    test_lines = get_section_lines(store, 75, 84)
    console.print(f"  Testing on {len(test_lines)} lines.")

    # 2. Build Copy-Reset model on training data
    console.print("Building Copy-Reset model on Herbal section...")
    cr_model = build_copy_reset_model(train_lines, copy_window=5)
    console.print(
        f"  P(copy) = {cr_model['p_copy']:.4f}, "
        f"Vocab = {len(cr_model['vocab'])}"
    )

    # 3. Evaluate on test data
    console.print("Evaluating on Biological section...")
    cr_results = copy_reset_holdout_score(cr_model, test_lines)

    # 4. Compute chance baseline and z-score
    cr_chance = copy_reset_chance_baseline(cr_model, test_lines)
    cr_z = binomial_z_score(
        cr_results["admissibility_rate"],
        cr_chance,
        cr_results["total_tokens"],
    )

    # 5. Load Lattice holdout results for comparison
    lattice_holdout_path = (
        project_root / "results/data/phase14_machine/holdout_performance.json"
    )
    lattice_holdout = {}
    if lattice_holdout_path.exists():
        import json
        with open(lattice_holdout_path) as f:
            lh = json.load(f)
        lh_results = lh.get("results", lh)
        lattice_holdout = {
            "drift_admissibility": lh_results.get("drift", {}).get(
                "admissibility_rate", 0
            ),
            "drift_z": lh_results.get("drift", {}).get("z_score", 0),
            "strict_admissibility": lh_results.get("strict", {}).get(
                "admissibility_rate", 0
            ),
            "strict_z": lh_results.get("strict", {}).get("z_score", 0),
        }

    # 6. Save and Report
    results = {
        "train_lines": len(train_lines),
        "test_lines": len(test_lines),
        "copy_reset": {
            "p_copy": cr_model["p_copy"],
            "copy_window": 5,
            "train_vocab_size": len(cr_model["vocab"]),
            "holdout_admissibility": cr_results["admissibility_rate"],
            "holdout_chance": cr_chance,
            "holdout_z_score": cr_z,
            "holdout_bpt": cr_results["bpt"],
            "total_test_tokens": cr_results["total_tokens"],
        },
        "lattice_holdout": lattice_holdout,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Copy-Reset holdout complete.[/green]")

    # Comparison Table
    table = Table(title="Holdout: Lattice vs Copy-Reset (Herbal → Biological)")
    table.add_column("Metric", style="cyan")
    table.add_column("Lattice (Drift ±1)", justify="right")
    table.add_column("Copy-Reset (k=5)", justify="right")

    lat_adm = lattice_holdout.get("drift_admissibility", 0)
    lat_z = lattice_holdout.get("drift_z", 0)

    table.add_row(
        "Admissibility",
        f"{lat_adm * 100:.2f}%",
        f"{cr_results['admissibility_rate'] * 100:.2f}%",
    )
    table.add_row(
        "Chance Baseline",
        "(see 14G)",
        f"{cr_chance * 100:.4f}%",
    )
    table.add_row(
        "Z-Score",
        f"{lat_z:.1f} σ",
        f"{cr_z:.1f} σ",
    )
    table.add_row(
        "Test Tokens",
        str(cr_results["total_tokens"]),
        str(cr_results["total_tokens"]),
    )
    console.print(table)

    # Verdict
    if lat_adm > cr_results["admissibility_rate"]:
        console.print(
            f"\n[bold green]LATTICE WINS:[/bold green] Lattice "
            f"({lat_adm * 100:.2f}%) generalizes better than "
            f"Copy-Reset ({cr_results['admissibility_rate'] * 100:.2f}%) "
            f"across sections."
        )
    elif cr_results["admissibility_rate"] > lat_adm:
        console.print(
            f"\n[bold yellow]COPY-RESET WINS:[/bold yellow] Copy-Reset "
            f"({cr_results['admissibility_rate'] * 100:.2f}%) generalizes "
            f"better than Lattice ({lat_adm * 100:.2f}%)."
        )
    else:
        console.print("\n[bold]TIE:[/bold] Both models generalize equally.")

    if cr_z < 3 and lat_z > 3:
        console.print(
            "[bold green]CRITICAL:[/bold green] Copy-Reset fails the "
            "generalization test while Lattice passes. The Lattice "
            "captures cross-section structure that Copy-Reset cannot."
        )


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14u_copyreset_holdout"}):
        main()
