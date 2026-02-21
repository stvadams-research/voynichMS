#!/usr/bin/env python3
"""Sprint B1: Tier-Stratified Offset Corrections + Sprint B2: Hapax Grouping.

Phase 14I found a single per-window mode offset adding +16.17pp.  But
this offset is dominated by common words.  Rare words may have
systematically different drift patterns masked by the common-word signal.

  B1: Fit separate per-window offsets for common/medium/rare tiers,
      cross-validated.
  B2: Group hapax words by suffix class and test group-level placement.
"""

import json
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

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
SUFFIX_MAP_PATH = project_root / "results/data/phase14_machine/suffix_window_map.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/tiered_corrections.json"

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}

# Suffix priority list (from Phase 14O)
SUFFIX_PRIORITY = [
    "dy", "in", "y", "or", "ol", "al", "ar", "r",
    "am", "an", "s", "m", "d", "l", "o", "ey",
]


# ── Helpers ───────────────────────────────────────────────────────────

def signed_circular_offset(a, b, n=NUM_WINDOWS):
    raw = (b - a) % n
    if raw > n / 2:
        raw -= n
    return raw


def get_folio_num(folio_id):
    m = re.search(r"f(\d+)", folio_id)
    return int(m.group(1)) if m else 0


def get_section(folio_num):
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


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


def load_lines_with_folios(store):
    """Load canonical ZL lines as list of (token_list, folio_id) pairs."""
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
        folios = []
        current_tokens = []
        current_folio = None
        current_line_id = None
        for content, folio_id, line_id, _line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    lines.append(current_tokens)
                    folios.append(current_folio)
                current_tokens = []
            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id
        if current_tokens:
            lines.append(current_tokens)
            folios.append(current_folio)
        return lines, folios
    finally:
        session.close()


def freq_tier(word, corpus_freq):
    """Classify word by frequency tier."""
    f = corpus_freq.get(word, 0)
    if f <= 1:
        return "hapax"
    if f < 10:
        return "rare"
    if f < 100:
        return "medium"
    return "common"


# ── B1: Tier-Stratified Offset Learning ──────────────────────────────

def learn_tiered_corrections(lines, lattice_map, corpus_freq, min_obs=5):
    """Learn separate per-window mode offsets for each frequency tier."""
    tier_groups = defaultdict(lambda: defaultdict(list))

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            offset = signed_circular_offset(prev_win, curr_win)
            tier = freq_tier(curr_word, corpus_freq)
            tier_groups[tier][prev_win].append(offset)

    corrections = {}
    stability = {}
    for tier in ["common", "medium", "rare", "hapax"]:
        corrections[tier] = {}
        stability[tier] = {"data_poor_windows": 0, "total_windows": 0}
        for w in range(NUM_WINDOWS):
            offsets = tier_groups[tier].get(w, [])
            stability[tier]["total_windows"] += 1
            if len(offsets) >= min_obs:
                corrections[tier][w] = Counter(offsets).most_common(1)[0][0]
            else:
                corrections[tier][w] = 0  # fallback to no correction
                stability[tier]["data_poor_windows"] += 1

    return corrections, stability


def score_tiered(lines, lattice_map, corrections, corpus_freq):
    """Score admissibility using tier-specific offset corrections."""
    tier_stats = defaultdict(lambda: {"total": 0, "admissible": 0})
    total_adm = 0
    total_count = 0

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            raw_offset = signed_circular_offset(prev_win, curr_win)
            tier = freq_tier(curr_word, corpus_freq)

            correction = corrections[tier].get(prev_win, 0)
            corrected_offset = raw_offset - correction
            if corrected_offset > NUM_WINDOWS // 2:
                corrected_offset -= NUM_WINDOWS
            elif corrected_offset < -NUM_WINDOWS // 2:
                corrected_offset += NUM_WINDOWS

            total_count += 1
            tier_stats[tier]["total"] += 1
            if abs(corrected_offset) <= 1:
                total_adm += 1
                tier_stats[tier]["admissible"] += 1

    return total_adm, total_count, dict(tier_stats)


def score_uniform(lines, lattice_map, corrections):
    """Score admissibility using single per-window correction (baseline)."""
    total_adm = 0
    total_count = 0

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            raw_offset = signed_circular_offset(prev_win, curr_win)

            correction = corrections.get(prev_win, 0)
            corrected_offset = raw_offset - correction
            if corrected_offset > NUM_WINDOWS // 2:
                corrected_offset -= NUM_WINDOWS
            elif corrected_offset < -NUM_WINDOWS // 2:
                corrected_offset += NUM_WINDOWS

            total_count += 1
            if abs(corrected_offset) <= 1:
                total_adm += 1

    return total_adm, total_count


def sprint_b1(lines, folios, lattice_map, corpus_freq, canonical_corrections):
    """Sprint B1: Tier-stratified offset corrections with cross-validation."""
    console.rule("[bold blue]Sprint B1: Tier-Stratified Offset Corrections")

    # Assign sections
    section_map = {}
    for i, folio in enumerate(folios):
        fnum = get_folio_num(folio)
        section_map[i] = get_section(fnum)

    sections = sorted(set(section_map.values()))
    sections = [s for s in sections if s != "Other"]

    # Cross-validated tiered corrections (leave-one-section-out)
    console.print(f"Running {len(sections)}-fold cross-validation...")

    fold_results = []
    for held_out in sections:
        train_lines = [lines[i] for i in range(len(lines)) if section_map.get(i) != held_out]
        test_lines = [lines[i] for i in range(len(lines)) if section_map.get(i) == held_out]
        if not test_lines:
            continue

        # Learn tiered corrections from training set
        tiered_corr, _ = learn_tiered_corrections(train_lines, lattice_map, corpus_freq)

        # Score test set with tiered corrections
        tiered_adm, tiered_total, tiered_tier_stats = score_tiered(
            test_lines, lattice_map, tiered_corr, corpus_freq,
        )

        # Score test set with canonical (uniform) corrections
        uniform_adm, uniform_total = score_uniform(test_lines, lattice_map, canonical_corrections)

        tiered_rate = tiered_adm / tiered_total if tiered_total > 0 else 0
        uniform_rate = uniform_adm / uniform_total if uniform_total > 0 else 0
        delta = tiered_rate - uniform_rate

        fold_results.append({
            "section": held_out,
            "tiered_rate": round(tiered_rate * 100, 2),
            "uniform_rate": round(uniform_rate * 100, 2),
            "delta_pp": round(delta * 100, 2),
            "test_transitions": tiered_total,
            "per_tier": {
                tier: {
                    "total": stats["total"],
                    "admissible": stats["admissible"],
                    "rate": round(stats["admissible"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0,
                }
                for tier, stats in tiered_tier_stats.items()
            },
        })

    # Display
    table = Table(title="Cross-Validated Tiered vs Uniform Corrections")
    table.add_column("Section", style="cyan")
    table.add_column("Tiered %", justify="right")
    table.add_column("Uniform %", justify="right")
    table.add_column("Delta (pp)", justify="right")
    table.add_column("N", justify="right")
    for fr in fold_results:
        delta_style = "green" if fr["delta_pp"] > 0 else ("red" if fr["delta_pp"] < 0 else "")
        table.add_row(
            fr["section"],
            f"{fr['tiered_rate']:.2f}",
            f"{fr['uniform_rate']:.2f}",
            f"{fr['delta_pp']:+.2f}",
            str(fr["test_transitions"]),
            style=delta_style if abs(fr["delta_pp"]) > 0.5 else "",
        )

    cv_mean_tiered = np.mean([f["tiered_rate"] for f in fold_results])
    cv_mean_uniform = np.mean([f["uniform_rate"] for f in fold_results])
    cv_mean_delta = cv_mean_tiered - cv_mean_uniform
    table.add_row(
        "MEAN", f"{cv_mean_tiered:.2f}", f"{cv_mean_uniform:.2f}",
        f"{cv_mean_delta:+.2f}", "—", style="bold",
    )
    console.print(table)

    # Full-corpus tiered corrections + stability
    tiered_full, stability = learn_tiered_corrections(lines, lattice_map, corpus_freq)
    tiered_adm_full, tiered_total_full, tier_stats_full = score_tiered(
        lines, lattice_map, tiered_full, corpus_freq,
    )
    tiered_rate_full = tiered_adm_full / tiered_total_full * 100 if tiered_total_full else 0

    # Display stability
    stab_table = Table(title="Tier Stability (Data-Poor Windows)")
    stab_table.add_column("Tier", style="cyan")
    stab_table.add_column("Data-Poor", justify="right")
    stab_table.add_column("Total", justify="right")
    stab_table.add_column("Fraction", justify="right")
    for tier in ["common", "medium", "rare", "hapax"]:
        s = stability[tier]
        frac = s["data_poor_windows"] / s["total_windows"] * 100 if s["total_windows"] > 0 else 0
        stab_table.add_row(tier, str(s["data_poor_windows"]), str(s["total_windows"]), f"{frac:.0f}%")
    console.print(stab_table)

    # Display full-corpus per-tier rates
    tier_table = Table(title="Full-Corpus Per-Tier Admissibility")
    tier_table.add_column("Tier", style="cyan")
    tier_table.add_column("Total", justify="right")
    tier_table.add_column("Admissible", justify="right")
    tier_table.add_column("Rate", justify="right")
    for tier in ["common", "medium", "rare", "hapax"]:
        s = tier_stats_full.get(tier, {"total": 0, "admissible": 0})
        rate = s["admissible"] / s["total"] * 100 if s["total"] > 0 else 0
        tier_table.add_row(tier, str(s["total"]), str(s["admissible"]), f"{rate:.2f}%")
    console.print(tier_table)

    # Gate check
    gate_pass = cv_mean_delta >= 2.0
    console.print(f"\n  CV mean delta: {cv_mean_delta:+.2f}pp")
    console.print(f"  Gate (≥+2.0pp): {'[green]PASS[/green]' if gate_pass else '[red]FAIL[/red]'}")

    return {
        "cv_folds": fold_results,
        "cv_mean_tiered": round(cv_mean_tiered, 2),
        "cv_mean_uniform": round(cv_mean_uniform, 2),
        "cv_mean_delta_pp": round(cv_mean_delta, 2),
        "full_corpus_tiered_rate": round(tiered_rate_full, 2),
        "stability": {tier: dict(s) for tier, s in stability.items()},
        "full_corpus_per_tier": {
            tier: {
                "total": s["total"],
                "admissible": s["admissible"],
                "rate": round(s["admissible"] / s["total"] * 100, 2) if s["total"] > 0 else 0,
            }
            for tier, s in tier_stats_full.items()
        },
        "gate_threshold_pp": 2.0,
        "gate_pass": gate_pass,
    }


# ── B2: Hapax Grouping ──────────────────────────────────────────────

def get_suffix_class(word):
    """Get suffix class for a word."""
    for sfx in SUFFIX_PRIORITY:
        if word.endswith(sfx) and len(word) > len(sfx):
            return sfx
    return None


def sprint_b2(lines, lattice_map, corpus_freq, canonical_corrections):
    """Sprint B2: Hapax grouping by suffix class."""
    console.rule("[bold blue]Sprint B2: Hapax Grouping")

    # Load suffix window map if available
    suffix_map = {}
    if SUFFIX_MAP_PATH.exists():
        with open(SUFFIX_MAP_PATH) as f:
            sdata = json.load(f)
        suffix_map = sdata.get("results", sdata).get("suffix_window_map", {})
        console.print(f"  Loaded suffix→window map: {len(suffix_map)} entries")

    # Identify hapax words in transitions
    hapax_words = {w for w, f in corpus_freq.items() if f == 1}
    console.print(f"  Hapax words: {len(hapax_words)}")

    # Feature extraction for hapax
    hapax_features = []
    for word in hapax_words:
        sfx = get_suffix_class(word)
        hapax_features.append({
            "word": word,
            "suffix_class": sfx,
            "glyph_count": len(word),
            "initial_glyph": word[0] if word else "",
            "has_suffix_map": sfx in suffix_map if sfx else False,
        })

    # Coverage
    with_suffix = sum(1 for h in hapax_features if h["suffix_class"] is not None)
    with_map = sum(1 for h in hapax_features if h["has_suffix_map"])

    console.print(f"  Hapax with suffix match: {with_suffix}/{len(hapax_words)} "
                  f"({with_suffix / len(hapax_words) * 100:.1f}%)")
    console.print(f"  Hapax with suffix→window mapping: {with_map}/{len(hapax_words)} "
                  f"({with_map / len(hapax_words) * 100:.1f}%)")

    # Suffix class distribution
    suffix_counts = Counter(h["suffix_class"] for h in hapax_features if h["suffix_class"])
    suffix_table = Table(title="Hapax Suffix Class Distribution")
    suffix_table.add_column("Suffix", style="cyan")
    suffix_table.add_column("Count", justify="right")
    suffix_table.add_column("Window", justify="right")
    for sfx, count in suffix_counts.most_common(16):
        win = suffix_map.get(sfx, "—")
        suffix_table.add_row(sfx, str(count), str(win))
    console.print(suffix_table)

    # Score hapax transitions with suffix-group assignment
    hapax_transitions = {"total": 0, "suffix_recovered": 0, "suffix_admissible": 0,
                         "baseline_admissible": 0}

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map:
                continue
            if curr_word not in hapax_words:
                continue
            if curr_word in lattice_map:
                continue  # hapax but in lattice (shouldn't happen, but guard)

            hapax_transitions["total"] += 1
            prev_win = lattice_map[prev_word]

            # Suffix-based window prediction
            sfx = get_suffix_class(curr_word)
            if sfx and sfx in suffix_map:
                predicted_win = suffix_map[sfx]
                hapax_transitions["suffix_recovered"] += 1

                # Is this admissible? (predicted window within ±1 of corrected expected)
                correction = canonical_corrections.get(prev_win, 0)
                expected_win = (prev_win + correction) % NUM_WINDOWS
                dist = signed_circular_offset(expected_win, predicted_win)
                if abs(dist) <= 1:
                    hapax_transitions["suffix_admissible"] += 1

            # Baseline: is the hapax transition admissible without any recovery?
            # (It can't be — the word isn't in the lattice map, so baseline = 0)

    # Also count overall impact
    total_transitions = sum(
        len(line) - 1
        for line in lines
        if len(line) > 1
    )
    # Count how many total transitions involve vocab words
    vocab_transitions = 0
    for line in lines:
        for i in range(1, len(line)):
            if line[i - 1] in lattice_map and line[i] in lattice_map:
                vocab_transitions += 1

    impact_pp = 0.0
    if vocab_transitions > 0 and hapax_transitions["suffix_admissible"] > 0:
        impact_pp = hapax_transitions["suffix_admissible"] / vocab_transitions * 100

    console.print(f"\n  Hapax transitions (prev in-vocab, curr hapax OOV): {hapax_transitions['total']}")
    console.print(f"  Suffix-recovered: {hapax_transitions['suffix_recovered']}")
    console.print(f"  Suffix-admissible: {hapax_transitions['suffix_admissible']}")
    console.print(f"  Potential impact on admissibility: +{impact_pp:.3f}pp")

    return {
        "n_hapax_words": len(hapax_words),
        "suffix_coverage": {
            "with_suffix": with_suffix,
            "with_map": with_map,
            "coverage_pct": round(with_suffix / len(hapax_words) * 100, 1) if hapax_words else 0,
            "mapped_pct": round(with_map / len(hapax_words) * 100, 1) if hapax_words else 0,
        },
        "suffix_distribution": dict(suffix_counts.most_common(16)),
        "hapax_transitions": hapax_transitions,
        "impact_pp": round(impact_pp, 3),
        "verdict": (
            "Hapax suffix grouping is worth integrating"
            if impact_pp >= 0.5
            else "Hapax suffix grouping has negligible impact"
        ),
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprints B1-B2: Frequency-Aware Modeling")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    canonical_corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines, folios = load_lines_with_folios(store)

    # Compute corpus frequencies
    corpus_freq = Counter(t for line in lines for t in line)

    console.print(f"  Palette: {len(lattice_map)} words")
    console.print(f"  Corpus: {len(lines)} lines, {sum(len(l) for l in lines)} tokens")
    console.print(f"  Unique words: {len(corpus_freq)}")
    console.print(f"  Frequency tiers: "
                  f"common={sum(1 for f in corpus_freq.values() if f >= 100)}, "
                  f"medium={sum(1 for f in corpus_freq.values() if 10 <= f < 100)}, "
                  f"rare={sum(1 for f in corpus_freq.values() if 2 <= f < 10)}, "
                  f"hapax={sum(1 for f in corpus_freq.values() if f == 1)}")

    # Sprint B1: Tiered corrections
    b1_results = sprint_b1(lines, folios, lattice_map, corpus_freq, canonical_corrections)

    # Sprint B2: Hapax grouping
    b2_results = sprint_b2(lines, lattice_map, corpus_freq, canonical_corrections)

    # Assemble results (sanitize numpy types for JSON)
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    results = sanitize({
        "sprint_b1_tiered_corrections": b1_results,
        "sprint_b2_hapax_grouping": b2_results,
    })

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14zh_tiered_corrections"}):
        main()
