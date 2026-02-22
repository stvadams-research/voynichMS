#!/usr/bin/env python3
"""Sprint H1: Canonical Admissibility Audit and Update.

H1.1: Determine whether the canonical 64.13% corrected admissibility already
      includes suffix recovery by running EvaluationEngine with and without
      suffix_window_map.
H1.2: Document the hapax recovery pipeline.
H1.3: Establish the definitive canonical admissibility rate.

Integrates B2's hapax suffix grouping into the canonical production evaluation.
"""

import json
import re
import sys
from collections import Counter, defaultdict
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
from phase14_machine.evaluation_engine import EvaluationEngine  # noqa: E402

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
SUFFIX_MAP_PATH = project_root / "results/data/phase14_machine/suffix_window_map.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/hapax_integration.json"

console = Console()


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


def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def load_lines(store):
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
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
        lines = []
        current_tokens = []
        current_line_id = None
        for content, line_id, _line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    lines.append(current_tokens)
                current_tokens = []
            current_tokens.append(clean)
            current_line_id = line_id
        if current_tokens:
            lines.append(current_tokens)
        return lines
    finally:
        session.close()


def corrected_admissibility(lines, lattice_map, window_contents, corrections,
                            suffix_map=None):
    """Compute admissibility using the manual correction path.

    This mirrors the computation in run_17f/run_17i: apply per-window mode
    corrections, then check drift ±1.  Optionally recovers OOV words via
    suffix_window_map.
    """
    admissible = 0
    total = 0
    oov_total = 0
    oov_recovered = 0
    oov_admissible = 0

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]

            prev_win = lattice_map.get(prev_word)
            curr_win = lattice_map.get(curr_word)

            if prev_win is None:
                continue

            # If curr_word is OOV
            if curr_win is None:
                if suffix_map is not None:
                    oov_total += 1
                    predicted = EvaluationEngine.resolve_oov_window(
                        curr_word, suffix_map,
                    )
                    if predicted is not None:
                        oov_recovered += 1
                        corrected_next = (
                            prev_win + 1 + corrections.get(prev_win, 0)
                        ) % NUM_WINDOWS
                        for offset in [-1, 0, 1]:
                            check_win = (corrected_next + offset) % NUM_WINDOWS
                            if check_win == predicted:
                                oov_admissible += 1
                                break
                continue

            total += 1
            corrected_next = (
                prev_win + 1 + corrections.get(prev_win, 0)
            ) % NUM_WINDOWS

            for offset in [-1, 0, 1]:
                check_win = (corrected_next + offset) % NUM_WINDOWS
                if curr_word in set(window_contents.get(check_win, [])):
                    admissible += 1
                    break

    base_rate = admissible / total if total > 0 else 0

    result = {
        "admissible": admissible,
        "total": total,
        "rate": round(base_rate, 6),
    }

    if suffix_map is not None:
        consolidated_total = total + oov_recovered
        consolidated_admissible = admissible + oov_admissible
        consolidated_rate = (consolidated_admissible / consolidated_total
                             if consolidated_total > 0 else 0)
        result["oov_total"] = oov_total
        result["oov_recovered"] = oov_recovered
        result["oov_admissible"] = oov_admissible
        result["consolidated_total"] = consolidated_total
        result["consolidated_admissible"] = consolidated_admissible
        result["consolidated_rate"] = round(consolidated_rate, 6)

    return result


# ── H1.1: Baseline Verification ──────────────────────────────────────

def sprint_h1_1(lines, lattice_map, window_contents, corrections, suffix_map):
    """Determine whether 64.13% already includes suffix recovery."""
    console.rule("[bold blue]H1.1: Baseline Verification")

    vocab = set(lattice_map.keys())

    # Path A: EvaluationEngine (simpler — no per-window corrections)
    console.print("\n[bold]Path A: EvaluationEngine (uncorrected)[/bold]")
    engine = EvaluationEngine(vocab)

    ee_without = engine.calculate_admissibility(
        lines, lattice_map, window_contents,
    )
    ee_with = engine.calculate_admissibility(
        lines, lattice_map, window_contents,
        suffix_window_map=suffix_map,
    )

    ee_base = ee_without["drift_admissibility"]
    ee_consolidated = ee_with.get("consolidated_admissibility", ee_base)
    ee_delta = (ee_consolidated - ee_base) * 100

    console.print(f"  Without suffix: {ee_base:.4%} "
                  f"({ee_without['total_clamped_tokens']} transitions)")
    console.print(f"  With suffix:    {ee_consolidated:.4%} "
                  f"(OOV: {ee_with.get('oov_total', 0)} total, "
                  f"{ee_with.get('oov_recovered', 0)} recovered, "
                  f"{ee_with.get('oov_admissible', 0)} admissible)")
    console.print(f"  Delta: {ee_delta:+.2f}pp")

    # Path B: Manual correction path (same as run_17f/run_17i)
    console.print("\n[bold]Path B: Manual correction path (corrected)[/bold]")

    mc_without = corrected_admissibility(
        lines, lattice_map, window_contents, corrections,
    )
    mc_with = corrected_admissibility(
        lines, lattice_map, window_contents, corrections,
        suffix_map=suffix_map,
    )

    mc_base = mc_without["rate"]
    mc_consolidated = mc_with.get("consolidated_rate", mc_base)
    mc_delta = (mc_consolidated - mc_base) * 100

    console.print(f"  Without suffix: {mc_base:.4%} "
                  f"({mc_without['total']} transitions)")
    console.print(f"  With suffix:    {mc_consolidated:.4%} "
                  f"(OOV: {mc_with.get('oov_total', 0)} total, "
                  f"{mc_with.get('oov_recovered', 0)} recovered, "
                  f"{mc_with.get('oov_admissible', 0)} admissible)")
    console.print(f"  Delta: {mc_delta:+.2f}pp")

    # Verdict: was 64.13% suffix-inclusive?
    console.print("\n[bold]Verdict:[/bold]")
    canonical_ref = 0.6413
    closer_to_without = abs(mc_base - canonical_ref) < abs(mc_consolidated - canonical_ref)

    if closer_to_without:
        console.print(f"  The canonical 64.13% is CLOSER to the without-suffix "
                      f"rate ({mc_base:.2%})")
        console.print("  → 64.13% does NOT include suffix recovery")
        suffix_included = False
    else:
        console.print(f"  The canonical 64.13% is CLOSER to the with-suffix "
                      f"rate ({mc_consolidated:.2%})")
        console.print("  → 64.13% MAY already include suffix recovery")
        suffix_included = True

    return {
        "evaluation_engine_path": {
            "without_suffix": {
                "drift_admissibility": round(ee_base, 6),
                "total_transitions": ee_without["total_clamped_tokens"],
            },
            "with_suffix": {
                "consolidated_admissibility": round(ee_consolidated, 6),
                "oov_total": ee_with.get("oov_total", 0),
                "oov_recovered": ee_with.get("oov_recovered", 0),
                "oov_admissible": ee_with.get("oov_admissible", 0),
            },
            "delta_pp": round(ee_delta, 2),
        },
        "corrected_path": {
            "without_suffix": {
                "rate": mc_base,
                "admissible": mc_without["admissible"],
                "total": mc_without["total"],
            },
            "with_suffix": {
                "consolidated_rate": mc_consolidated,
                "consolidated_admissible": mc_with.get("consolidated_admissible", 0),
                "consolidated_total": mc_with.get("consolidated_total", 0),
                "oov_total": mc_with.get("oov_total", 0),
                "oov_recovered": mc_with.get("oov_recovered", 0),
                "oov_admissible": mc_with.get("oov_admissible", 0),
            },
            "delta_pp": round(mc_delta, 2),
        },
        "canonical_ref": canonical_ref,
        "suffix_already_included": suffix_included,
    }


# ── H1.2: Hapax-Specific Analysis ────────────────────────────────────

def sprint_h1_2(lines, lattice_map, suffix_map):
    """Document the hapax recovery pipeline."""
    console.rule("[bold blue]H1.2: Hapax-Specific Analysis")

    # Count hapax words in corpus
    all_tokens = [t for line in lines for t in line]
    freq = Counter(all_tokens)
    hapax_words = {w for w, c in freq.items() if c == 1}
    in_lattice = {w for w in hapax_words if w in lattice_map}
    oov_hapax = hapax_words - in_lattice

    console.print(f"  Total hapax words: {len(hapax_words)}")
    console.print(f"  Hapax in lattice: {len(in_lattice)}")
    console.print(f"  Hapax OOV: {len(oov_hapax)}")

    # Suffix coverage of OOV hapax
    suffix_covered = 0
    suffix_by_class = Counter()
    for word in oov_hapax:
        predicted = EvaluationEngine.resolve_oov_window(word, suffix_map)
        if predicted is not None:
            suffix_covered += 1
            for sfx in EvaluationEngine.SUFFIX_PRIORITY:
                if word.endswith(sfx) and len(word) > len(sfx) and sfx in suffix_map:
                    suffix_by_class[sfx] += 1
                    break

    oov_suffix_rate = suffix_covered / len(oov_hapax) if oov_hapax else 0
    console.print(f"  OOV hapax suffix-covered: {suffix_covered} "
                  f"({oov_suffix_rate:.1%})")

    # All hapax (in-lattice + OOV) suffix coverage
    all_suffix_covered = 0
    for word in hapax_words:
        predicted = EvaluationEngine.resolve_oov_window(word, suffix_map)
        if predicted is not None:
            all_suffix_covered += 1

    all_suffix_rate = all_suffix_covered / len(hapax_words) if hapax_words else 0
    console.print(f"  All hapax suffix-covered: {all_suffix_covered} "
                  f"({all_suffix_rate:.1%})")

    # Hapax transition analysis
    hapax_transitions = 0
    hapax_recoverable = 0
    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word in lattice_map and curr_word in hapax_words:
                if curr_word not in lattice_map:
                    hapax_transitions += 1
                    predicted = EvaluationEngine.resolve_oov_window(
                        curr_word, suffix_map,
                    )
                    if predicted is not None:
                        hapax_recoverable += 1

    console.print(f"  Hapax OOV transitions (in-vocab → OOV hapax): "
                  f"{hapax_transitions}")
    console.print(f"  Suffix-recoverable: {hapax_recoverable}")

    table = Table(title="Suffix Class Distribution (OOV Hapax)")
    table.add_column("Suffix", style="cyan")
    table.add_column("Count", justify="right", style="bold")
    for sfx, count in suffix_by_class.most_common():
        table.add_row(sfx, str(count))
    console.print(table)

    return {
        "total_hapax": len(hapax_words),
        "hapax_in_lattice": len(in_lattice),
        "hapax_oov": len(oov_hapax),
        "oov_suffix_covered": suffix_covered,
        "oov_suffix_coverage_rate": round(oov_suffix_rate, 4),
        "all_hapax_suffix_covered": all_suffix_covered,
        "all_hapax_suffix_coverage_rate": round(all_suffix_rate, 4),
        "hapax_oov_transitions": hapax_transitions,
        "hapax_recoverable": hapax_recoverable,
        "suffix_class_distribution": dict(suffix_by_class.most_common()),
    }


# ── H1.3: Updated Canonical Number ───────────────────────────────────

def sprint_h1_3(h1_1_results, h1_2_results):
    """Establish the definitive canonical admissibility rate."""
    console.rule("[bold blue]H1.3: Updated Canonical Number")

    corrected = h1_1_results["corrected_path"]
    base_rate = corrected["without_suffix"]["rate"]
    consolidated_rate = corrected["with_suffix"]["consolidated_rate"]
    delta = corrected["delta_pp"]
    suffix_included = h1_1_results["suffix_already_included"]

    table = Table(title="Canonical Admissibility Stack")
    table.add_column("Component", style="cyan")
    table.add_column("Rate", justify="right", style="bold")
    table.add_column("Delta", justify="right")

    table.add_row(
        "Base corrected (no suffix)",
        f"{base_rate:.2%}",
        "—",
    )
    table.add_row(
        "+ OOV suffix recovery",
        f"{consolidated_rate:.2%}",
        f"+{delta:.2f}pp",
    )
    console.print(table)

    if suffix_included:
        canonical = base_rate
        console.print("\n  Suffix recovery was already included in canonical.")
        console.print(f"  Canonical admissibility: {canonical:.2%} (unchanged)")
        changed = False
    else:
        canonical = consolidated_rate
        console.print("\n  Suffix recovery was NOT included in canonical 64.13%.")
        console.print(f"  Updated canonical admissibility: "
                      f"[bold green]{canonical:.2%}[/bold green]")
        console.print(f"  Change: {delta:+.2f}pp")
        changed = True

    # B2 reference: +3.04pp from hapax suffix grouping
    # The discrepancy with our delta arises because B2 measured the impact
    # on hapax transitions specifically, while we measure the global impact
    # including all OOV words (not just hapax).
    console.print("\n  B2 hapax-specific impact: +3.04pp (on hapax transitions)")
    console.print(f"  Global OOV impact: {delta:+.2f}pp (on all transitions)")
    console.print("  Note: B2 measured hapax-only; global includes all OOV words")

    return {
        "base_corrected_rate": base_rate,
        "suffix_consolidated_rate": consolidated_rate,
        "suffix_delta_pp": round(delta, 2),
        "canonical_was_suffix_inclusive": suffix_included,
        "updated_canonical_rate": round(canonical, 6),
        "canonical_changed": changed,
        "b2_hapax_impact_pp": 3.04,
        "global_oov_impact_pp": round(delta, 2),
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint H1: Canonical Admissibility Audit")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)

    # Load suffix map
    suffix_map = {}
    if SUFFIX_MAP_PATH.exists():
        with open(SUFFIX_MAP_PATH) as f:
            sm_data = json.load(f)
        suffix_map = sm_data.get("results", sm_data)
        if isinstance(suffix_map, dict) and "suffix_window_map" in suffix_map:
            suffix_map = suffix_map["suffix_window_map"]
        suffix_map = {k: int(v) for k, v in suffix_map.items()}

    console.print(f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows")
    console.print(f"  Corpus: {len(lines)} lines")
    console.print(f"  Suffix map: {len(suffix_map)} entries")
    console.print(f"  Corrections: {len(corrections)} windows")

    # H1.1: Baseline verification
    h1_1 = sprint_h1_1(lines, lattice_map, window_contents, corrections,
                        suffix_map)

    # H1.2: Hapax-specific analysis
    h1_2 = sprint_h1_2(lines, lattice_map, suffix_map)

    # H1.3: Updated canonical number
    h1_3 = sprint_h1_3(h1_1, h1_2)

    # Assemble results
    results = {
        "h1_1_baseline_verification": h1_1,
        "h1_2_hapax_analysis": h1_2,
        "h1_3_canonical_update": h1_3,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17k_hapax_integration"}):
        main()
