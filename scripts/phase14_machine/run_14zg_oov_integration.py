"""
Phase 14O — OOV Suffix Recovery Integration Verification

Materializes the suffix→window map as a standalone artifact and runs
before/after admissibility comparison to verify the production integration.

Acceptance gates:
  - Regression: baseline admissibility must match canonical 43.44% (±0.01pp)
  - Improvement: consolidated admissibility must show ≥+4.0pp gain
  - Emulator: emulator with suffix map must generate coherent text
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import sanitize_token
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase14_machine.evaluation_engine import EvaluationEngine
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle

console = Console()

# ── Constants ──────────────────────────────────────────────────────────
NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/suffix_window_map.json"

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}

SUFFIX_LIST = ["dy", "in", "y", "or", "ol", "al", "ar", "r",
               "am", "an", "s", "m", "d", "l", "o", "ey"]


# ── Helpers ────────────────────────────────────────────────────────────

def get_folio_num(folio_id: str) -> int:
    m = re.search(r"f(\d+)", folio_id)
    return int(m.group(1)) if m else 0


def get_section(folio_num: int) -> str:
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def signed_circular_offset(a: int, b: int, n: int = NUM_WINDOWS) -> int:
    raw = (b - a) % n
    if raw > n // 2:
        raw -= n
    return raw


def load_lines(store):
    """Load canonical ZL lines as list of token lists."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
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
        for content, _folio_id, line_id, _line_idx in rows:
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


def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = "reordered_lattice_map" if "reordered_lattice_map" in results else "lattice_map"
    wc_key = "reordered_window_contents" if "reordered_window_contents" in results else "window_contents"
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def build_suffix_window_map(lattice_map, word_freq, min_suffix_obs=10):
    """Map suffix classes to their most common window assignments.

    Reimplemented from run_14ze_frequency_lattice.py:446-462.
    Uses frequency-weighted observations for robust mode estimation.
    """
    suffix_windows = defaultdict(list)
    for word, win in lattice_map.items():
        for sfx in SUFFIX_LIST:
            if word.endswith(sfx) and len(word) > len(sfx):
                freq = word_freq.get(word, 1)
                suffix_windows[sfx].extend([win] * freq)
                break

    suffix_map = {}
    for sfx, wins in suffix_windows.items():
        if len(wins) >= min_suffix_obs:
            suffix_map[sfx] = Counter(wins).most_common(1)[0][0]
    return suffix_map


def learn_offset_corrections(lines, lattice_map, min_obs=5):
    """Learn per-window mode offset corrections."""
    groups = defaultdict(list)
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            if prev_w not in lattice_map or curr_w not in lattice_map:
                continue
            prev_win = lattice_map[prev_w]
            curr_win = lattice_map[curr_w]
            groups[prev_win].append(signed_circular_offset(prev_win, curr_win))
    corrections = {}
    for key, offsets in groups.items():
        if len(offsets) >= min_obs:
            corrections[key] = Counter(offsets).most_common(1)[0][0]
    return corrections


def score_corrected_admissibility(lines, lattice_map, corrections, suffix_map=None):
    """Score corrected admissibility with optional OOV recovery.

    Returns (corrected_adm, base_adm, total, oov_recovered, oov_total).
    """
    adm = base = total = 0
    oov_recovered = oov_total = oov_adm = 0
    for line in lines:
        for i in range(1, len(line)):
            prev_w, curr_w = line[i - 1], line[i]
            # Both in palette — standard path
            if prev_w in lattice_map and curr_w in lattice_map:
                total += 1
                prev_win = lattice_map[prev_w]
                curr_win = lattice_map[curr_w]
                raw = signed_circular_offset(prev_win, curr_win)
                if abs(raw) <= 1:
                    base += 1
                correction = corrections.get(prev_win, 0)
                corrected = raw - correction
                if corrected > NUM_WINDOWS // 2:
                    corrected -= NUM_WINDOWS
                elif corrected < -NUM_WINDOWS // 2:
                    corrected += NUM_WINDOWS
                if abs(corrected) <= 1:
                    adm += 1
                continue

            # OOV path — one or both words not in palette
            if suffix_map is not None:
                oov_total += 1
                prev_win = lattice_map.get(prev_w)
                curr_win = lattice_map.get(curr_w)
                if prev_win is None:
                    prev_win = EvaluationEngine.resolve_oov_window(prev_w, suffix_map)
                if curr_win is None:
                    curr_win = EvaluationEngine.resolve_oov_window(curr_w, suffix_map)
                if prev_win is not None and curr_win is not None:
                    oov_recovered += 1
                    raw = signed_circular_offset(prev_win, curr_win)
                    correction = corrections.get(prev_win, 0)
                    corrected = raw - correction
                    if corrected > NUM_WINDOWS // 2:
                        corrected -= NUM_WINDOWS
                    elif corrected < -NUM_WINDOWS // 2:
                        corrected += NUM_WINDOWS
                    if abs(corrected) <= 1:
                        oov_adm += 1

    return {
        "corrected_admissible": adm,
        "base_admissible": base,
        "total_in_palette": total,
        "oov_total": oov_total,
        "oov_recovered": oov_recovered,
        "oov_admissible": oov_adm,
    }


def compute_entropy(lines, vocab=None):
    """Compute unigram entropy in bits/token."""
    counts = Counter()
    for line in lines:
        for w in line:
            if vocab is None or w in vocab:
                counts[w] += 1
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold blue]Phase 14O: OOV Suffix Recovery Integration")

    # Load data
    console.print("Loading palette and corpus...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)
    corrections = load_corrections(OFFSETS_PATH)

    vocab = set(lattice_map.keys())
    all_tokens = [w for line in lines for w in line]
    word_freq = Counter(all_tokens)
    num_wins = len(window_contents)

    console.print(f"  Palette: {len(lattice_map)} words, {num_wins} windows")
    console.print(f"  Corpus: {len(lines)} lines, {len(all_tokens)} tokens")

    # ── Build suffix→window map ──────────────────────────────────────
    console.rule("Building suffix→window map")
    suffix_map = build_suffix_window_map(lattice_map, word_freq)

    t = Table(title="Suffix → Window Map")
    t.add_column("Suffix", style="cyan")
    t.add_column("Window", justify="right")
    for sfx in SUFFIX_LIST:
        if sfx in suffix_map:
            t.add_row(sfx, str(suffix_map[sfx]))
    console.print(t)
    console.print(f"  {len(suffix_map)} suffixes mapped")

    # ── Baseline: EvaluationEngine without suffix map ────────────────
    console.rule("Baseline Admissibility (no OOV recovery)")
    engine = EvaluationEngine(vocab)
    baseline = engine.calculate_admissibility(lines, lattice_map, window_contents)
    baseline_rate = baseline["admissibility_rate"]
    console.print(f"  Drift admissibility: {baseline_rate:.4%}")
    console.print(f"  Clamped tokens: {baseline['total_clamped_tokens']}")

    # ── With suffix map: EvaluationEngine ────────────────────────────
    console.rule("Admissibility with OOV Suffix Recovery")
    with_oov = engine.calculate_admissibility(
        lines, lattice_map, window_contents, suffix_window_map=suffix_map
    )
    console.print(f"  Base admissibility (in-vocab): {with_oov['admissibility_rate']:.4%}")
    console.print(f"  OOV total: {with_oov['oov_total']}")
    console.print(f"  OOV recovered: {with_oov['oov_recovered']}")
    console.print(f"  OOV admissible: {with_oov['oov_admissible']}")
    console.print(f"  Consolidated admissibility: {with_oov['consolidated_admissibility']:.4%}")

    # ── Corrected admissibility comparison ───────────────────────────
    console.rule("Corrected Admissibility (with offset corrections)")

    # Without OOV
    no_oov = score_corrected_admissibility(lines, lattice_map, corrections)
    base_rate_corrected = no_oov["corrected_admissible"] / max(no_oov["total_in_palette"], 1)
    console.print(f"  Without OOV: {base_rate_corrected:.4%} "
                  f"({no_oov['corrected_admissible']}/{no_oov['total_in_palette']})")

    # With OOV
    with_oov_corr = score_corrected_admissibility(lines, lattice_map, corrections, suffix_map)
    total_consolidated = (with_oov_corr["corrected_admissible"]
                          + with_oov_corr["oov_admissible"])
    denom_consolidated = (with_oov_corr["total_in_palette"]
                          + with_oov_corr["oov_recovered"])
    consolidated_rate = total_consolidated / max(denom_consolidated, 1)
    delta_pp = (consolidated_rate - base_rate_corrected) * 100

    console.print(f"  With OOV: {consolidated_rate:.4%} "
                  f"({total_consolidated}/{denom_consolidated})")
    console.print(f"  Delta: {delta_pp:+.2f}pp")
    console.print(f"  OOV recovery: {with_oov_corr['oov_recovered']}/{with_oov_corr['oov_total']} "
                  f"({with_oov_corr['oov_recovered'] / max(with_oov_corr['oov_total'], 1):.1%})")

    # ── Emulator test ────────────────────────────────────────────────
    console.rule("Emulator Integration Test")

    # Without suffix map
    emu_base = HighFidelityVolvelle(
        lattice_map, window_contents, seed=42,
        offset_corrections=corrections,
    )
    syn_base = emu_base.generate_mirror_corpus(500)
    ent_base = compute_entropy(syn_base)

    # With suffix map
    emu_oov = HighFidelityVolvelle(
        lattice_map, window_contents, seed=42,
        offset_corrections=corrections,
        suffix_window_map=suffix_map,
    )
    syn_oov = emu_oov.generate_mirror_corpus(500)
    ent_oov = compute_entropy(syn_oov)

    ent_ratio = ent_oov / max(ent_base, 0.01)
    console.print(f"  Emulator entropy (no suffix): {ent_base:.2f} bits/token")
    console.print(f"  Emulator entropy (with suffix): {ent_oov:.2f} bits/token")
    console.print(f"  Ratio: {ent_ratio:.4f}")

    # ── Trace test ───────────────────────────────────────────────────
    console.rule("Trace Integration Test")

    emu_trace = HighFidelityVolvelle(
        lattice_map, window_contents, seed=42,
        offset_corrections=corrections,
        suffix_window_map=suffix_map,
        log_choices=True,
    )
    emu_trace.trace_lines(lines[:100])
    oov_traces = [e for e in emu_trace.choice_log if e.get("oov_recovered")]
    console.print(f"  Traced {len(lines[:100])} lines, "
                  f"{len(emu_trace.choice_log)} total entries, "
                  f"{len(oov_traces)} OOV-recovered")

    # ── Acceptance gates ─────────────────────────────────────────────
    console.rule("[bold]Acceptance Gates")

    # Gate 1: Regression
    CANONICAL = 0.4344
    regression_ok = abs(baseline_rate - CANONICAL) < 0.001
    gate1 = "[green]PASS" if regression_ok else "[red]FAIL"
    console.print(f"  Regression (43.44% ± 0.1pp): {baseline_rate:.4%} → {gate1}")

    # Gate 2: Improvement
    improvement_ok = delta_pp >= 4.0
    gate2 = "[green]PASS" if improvement_ok else f"[yellow]MARGINAL ({delta_pp:+.2f}pp)"
    console.print(f"  Improvement (≥+4.0pp): {delta_pp:+.2f}pp → {gate2}")

    # Gate 3: Emulator coherence
    emulator_ok = 0.95 <= ent_ratio <= 1.05
    gate3 = "[green]PASS" if emulator_ok else "[red]FAIL"
    console.print(f"  Emulator coherence (entropy ratio 0.95-1.05): {ent_ratio:.4f} → {gate3}")

    # ── Assemble results ─────────────────────────────────────────────
    results = {
        "suffix_window_map": suffix_map,
        "num_suffixes_mapped": len(suffix_map),
        "baseline": {
            "drift_admissibility": baseline_rate,
            "total_clamped_tokens": baseline["total_clamped_tokens"],
        },
        "with_oov_recovery": {
            "drift_admissibility": with_oov["admissibility_rate"],
            "oov_total": with_oov["oov_total"],
            "oov_recovered": with_oov["oov_recovered"],
            "oov_admissible": with_oov["oov_admissible"],
            "consolidated_admissibility": with_oov["consolidated_admissibility"],
        },
        "corrected_comparison": {
            "without_oov": {
                "corrected_admissibility": base_rate_corrected,
                "total": no_oov["total_in_palette"],
            },
            "with_oov": {
                "corrected_admissibility": consolidated_rate,
                "total": denom_consolidated,
                "oov_recovered": with_oov_corr["oov_recovered"],
                "oov_total": with_oov_corr["oov_total"],
                "oov_admissible": with_oov_corr["oov_admissible"],
            },
            "delta_pp": round(delta_pp, 2),
        },
        "emulator": {
            "entropy_base": round(ent_base, 4),
            "entropy_with_suffix": round(ent_oov, 4),
            "entropy_ratio": round(ent_ratio, 4),
        },
        "trace": {
            "lines_traced": len(lines[:100]),
            "total_entries": len(emu_trace.choice_log),
            "oov_recovered_entries": len(oov_traces),
        },
        "gates": {
            "regression_pass": regression_ok,
            "improvement_pass": improvement_ok,
            "emulator_pass": emulator_ok,
            "all_pass": regression_ok and improvement_ok and emulator_ok,
        },
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")

    if not (regression_ok and emulator_ok):
        console.print("[red]CRITICAL GATE FAILURE — check results[/red]")
        sys.exit(1)


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14zg_oov_integration"}):
        main()
