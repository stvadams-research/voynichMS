#!/usr/bin/env python3
"""Sprints G1–G2: Per-Section Device Analysis.

G1: Per-section corpus extraction, coverage curves, device dimensioning,
    historical plausibility, composite assessment.
G2: Per-section admissibility verification, cross-section boundary handling.

Determines whether section-specific devices resolve the C1/F2 monolithic
implausibility (678mm volvelle) by splitting the corpus into 7 manuscript
sections and running F1-F3 analysis independently for each.
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

console = Console()

NUM_WINDOWS = 50
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
SUFFIX_MAP_PATH = project_root / "results/data/phase14_machine/suffix_window_map.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/section_devices.json"

# Physical constants (same as C1/F2)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
LINE_SPACING_MM = 2.0
WORD_SPACING_MM = 3.0
MARGIN_MM = 5.0

HISTORICAL_DEVICES = {
    "Alberti cipher disc (1467)": {"diameter_mm": 120},
    "Llull Ars Magna (c.1305)": {"diameter_mm": 200},
    "Apian Astronomicum (1540)": {"diameter_mm": 350},
}

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}

# Subset sizes adapted for per-section analysis (smaller sections need finer
# granularity than the monolithic [50, 100, 200, 500, 1000, 2000]).
SUBSET_SIZES = [25, 50, 100, 200, 500, 1000, 2000]


# ── Helpers ───────────────────────────────────────────────────────────

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


def signed_circular_offset(a, b, n):
    """Signed shortest-path offset from a to b on a ring of size n."""
    d = (b - a) % n
    return d if d <= n // 2 else d - n


def compute_volvelle_diameter(subset_words, window_contents):
    """Compute volvelle diameter for a subset vocabulary.

    Uses the same methodology as F2: glyph sizing -> sector geometry -> ring
    layout. Returns diameter in mm.
    """
    # Map subset words to windows
    subset_per_window = defaultdict(list)
    for w in range(NUM_WINDOWS):
        for word in window_contents.get(w, []):
            if word in subset_words:
                subset_per_window[w].append(word)

    occupied_windows = len(subset_per_window)
    if occupied_windows == 0:
        return 0.0, 0, []

    sector_angle_rad = math.radians(360.0 / occupied_windows)

    # Compute window areas
    window_areas = {}
    for w, words in subset_per_window.items():
        n_words = len(words)
        avg_len = np.mean([len(word) for word in words]) if words else 0
        words_per_col = 18
        n_cols = math.ceil(n_words / words_per_col)
        col_width = avg_len * GLYPH_WIDTH_MM + WORD_SPACING_MM
        total_width = n_cols * col_width + 2 * MARGIN_MM
        total_height = (min(n_words, words_per_col)
                        * (GLYPH_HEIGHT_MM + LINE_SPACING_MM) + 2 * MARGIN_MM)
        window_areas[w] = {
            "n_words": n_words,
            "width_mm": total_width,
            "height_mm": total_height,
        }

    n_rings = min(3, max(1, occupied_windows // 10))
    sorted_windows = sorted(subset_per_window.keys(),
                            key=lambda w: len(subset_per_window[w]))
    current_radius = 0.0
    ring_specs = []
    windows_per_ring = math.ceil(occupied_windows / n_rings)

    for ring_idx in range(n_rings):
        start = ring_idx * windows_per_ring
        end = min(start + windows_per_ring, occupied_windows)
        ring_windows = sorted_windows[start:end]
        if not ring_windows:
            continue
        max_height = max(window_areas.get(w, {"height_mm": 0})["height_mm"]
                         for w in ring_windows)
        inner_r = current_radius + MARGIN_MM
        outer_r = inner_r + max_height
        current_radius = outer_r
        ring_specs.append({
            "ring": ring_idx + 1,
            "inner_radius_mm": round(inner_r, 1),
            "outer_radius_mm": round(outer_r, 1),
            "n_windows": len(ring_windows),
        })

    diameter = 2 * current_radius
    return diameter, occupied_windows, ring_specs


# ── G1: Per-Section Coverage and Device Dimensioning ─────────────────

def sprint_g1(section_data, lattice_map, window_contents, suffix_map):
    """G1.1-G1.5: Per-section coverage, dimensioning, plausibility."""
    console.rule("[bold blue]Sprint G1: Per-Section Coverage and Device Dimensioning")

    full_lattice_vocab = set(lattice_map.keys())
    section_results = {}

    for section_name, sdata in section_data.items():
        console.print(f"\n[bold cyan]── {section_name} ──[/bold cyan]")
        lines = sdata["lines"]

        # G1.1: Section corpus extraction
        all_tokens = [t for line in lines for t in line if t in lattice_map]
        freq = Counter(all_tokens)
        vocab = set(freq.keys())
        vocab_by_freq = [word for word, _ in freq.most_common()]
        total_tokens = len(all_tokens)

        # Windows occupied by this section's vocabulary
        section_windows = set()
        for word in vocab:
            section_windows.add(lattice_map[word])

        console.print(f"  Lines: {len(lines)}, Tokens: {total_tokens}, "
                      f"Vocab: {len(vocab)}, Windows: {len(section_windows)}")
        console.print(f"  Fraction of full vocab: "
                      f"{len(vocab) / len(full_lattice_vocab):.1%}")

        # G1.2: Token coverage thresholds
        thresholds = {50: None, 80: None, 90: None, 95: None}
        cumul = 0
        for i, word in enumerate(vocab_by_freq):
            cumul += freq[word]
            pct = cumul / total_tokens * 100
            for thresh in thresholds:
                if thresholds[thresh] is None and pct >= thresh:
                    thresholds[thresh] = i + 1

        # Transition coverage curve
        all_transitions = []
        for line in lines:
            for i in range(len(line) - 1):
                if line[i] in lattice_map and line[i + 1] in lattice_map:
                    all_transitions.append((line[i], line[i + 1]))

        total_transitions = len(all_transitions)
        transition_coverage = []
        for size in SUBSET_SIZES:
            if size > len(vocab_by_freq):
                break
            subset = set(vocab_by_freq[:size])
            covered = sum(1 for a, b in all_transitions
                          if a in subset and b in subset)
            cov = covered / total_transitions if total_transitions > 0 else 0
            transition_coverage.append({
                "vocab_size": size,
                "transitions_covered": covered,
                "total_transitions": total_transitions,
                "coverage": round(cov, 4),
            })

        # Also compute at full section vocab
        full_covered = sum(1 for a, b in all_transitions
                           if a in vocab and b in vocab)
        transition_coverage.append({
            "vocab_size": len(vocab_by_freq),
            "transitions_covered": full_covered,
            "total_transitions": total_transitions,
            "coverage": round(full_covered / total_transitions, 4)
            if total_transitions > 0 else 0,
        })

        # Find minimum subset for 80% transition coverage
        min_80_subset = None
        for tc in transition_coverage:
            if tc["coverage"] >= 0.80:
                min_80_subset = tc["vocab_size"]
                break

        console.print(f"  Token 80% coverage: {thresholds.get(80, '—')} words")
        console.print(f"  Min subset for 80% transition coverage: "
                      f"{min_80_subset if min_80_subset else 'not achieved'}")

        # G1.3: Device dimensioning for optimal subset
        # Use min_80_subset if achieved, else use full section vocab
        device_vocab_size = min_80_subset if min_80_subset else len(vocab_by_freq)
        device_words = set(vocab_by_freq[:device_vocab_size])

        diameter, windows_used, ring_specs = compute_volvelle_diameter(
            device_words, window_contents,
        )

        # Codebook: words not on the section device
        codebook_words = vocab - device_words
        codebook_size = len(codebook_words)

        # Codebook consultation rate
        device_hits = sum(1 for t in all_tokens if t in device_words)
        codebook_lookups = total_tokens - device_hits
        consultation_rate = codebook_lookups / total_tokens if total_tokens > 0 else 0
        words_between = 1 / consultation_rate if consultation_rate > 0 else float("inf")

        # Suffix recovery coverage of codebook
        suffix_covered = 0
        if suffix_map and codebook_words:
            for word in codebook_words:
                for sfx in suffix_map:
                    if word.endswith(sfx) and len(word) > len(sfx):
                        suffix_covered += 1
                        break

        console.print(f"  Device vocab: {device_vocab_size} words, "
                      f"Diameter: {diameter:.0f} mm")
        console.print(f"  Codebook: {codebook_size} entries, "
                      f"Consultation: every {words_between:.1f} words")

        # G1.4: Historical plausibility
        alberti_ratio = diameter / 120 if diameter > 0 else 0
        apian_ratio = diameter / 350 if diameter > 0 else 0
        fits_range = 100 <= diameter <= 400
        practical_codebook = words_between >= 3.0

        if fits_range and practical_codebook:
            verdict = "PLAUSIBLE"
        elif fits_range or practical_codebook:
            verdict = "MARGINAL"
        else:
            verdict = "IMPLAUSIBLE"

        console.print(f"  Fits 100-400mm range: {'YES' if fits_range else 'NO'}")
        console.print(f"  Verdict: [bold]{verdict}[/bold]")

        section_results[section_name] = {
            "corpus": {
                "lines": len(lines),
                "tokens": total_tokens,
                "vocab_size": len(vocab),
                "lattice_fraction": round(len(vocab) / len(full_lattice_vocab), 4),
                "windows_occupied": len(section_windows),
            },
            "coverage": {
                "token_thresholds": {str(k): v for k, v in thresholds.items()},
                "transition_coverage": transition_coverage,
                "min_80_transition_subset": min_80_subset,
            },
            "device": {
                "vocab_size": device_vocab_size,
                "diameter_mm": round(diameter, 0),
                "diameter_cm": round(diameter / 10, 1),
                "windows_used": windows_used,
                "n_rings": len(ring_specs),
                "ring_specs": ring_specs,
                "vs_alberti": round(alberti_ratio, 2),
                "vs_apian": round(apian_ratio, 2),
            },
            "codebook": {
                "entries": codebook_size,
                "suffix_recoverable": suffix_covered,
                "consultation_rate": round(consultation_rate, 4),
                "words_between_lookups": round(words_between, 1),
            },
            "plausibility": {
                "fits_historical_range": fits_range,
                "practical_codebook": practical_codebook,
                "verdict": verdict,
            },
        }

    # G1.5: Composite plausibility assessment
    console.rule("[bold blue]G1.5: Composite Plausibility Assessment")

    verdicts = {name: r["plausibility"]["verdict"]
                for name, r in section_results.items()}
    plausible_count = sum(1 for v in verdicts.values() if v == "PLAUSIBLE")
    marginal_count = sum(1 for v in verdicts.values() if v == "MARGINAL")

    # Total codebook: union of all section tails
    all_codebook_words = set()
    for section_name, sdata in section_data.items():
        sec_lines = sdata["lines"]
        sec_tokens = [t for line in sec_lines for t in line if t in lattice_map]
        sec_freq = Counter(sec_tokens)
        sec_vocab_by_freq = [word for word, _ in sec_freq.most_common()]
        sr = section_results[section_name]
        device_size = sr["device"]["vocab_size"]
        device_words = set(sec_vocab_by_freq[:device_size])
        all_codebook_words |= (set(sec_freq.keys()) - device_words)

    table = Table(title="Per-Section Device Summary")
    table.add_column("Section", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_column("Vocab", justify="right")
    table.add_column("Device Words", justify="right")
    table.add_column("Diameter", justify="right")
    table.add_column("Codebook", justify="right")
    table.add_column("Consult Rate", justify="right")
    table.add_column("Verdict", justify="center")

    for name, r in section_results.items():
        v = r["plausibility"]["verdict"]
        color = {"PLAUSIBLE": "green", "MARGINAL": "yellow",
                 "IMPLAUSIBLE": "red"}[v]
        table.add_row(
            name,
            str(r["corpus"]["tokens"]),
            str(r["corpus"]["vocab_size"]),
            str(r["device"]["vocab_size"]),
            f"{r['device']['diameter_mm']:.0f} mm",
            str(r["codebook"]["entries"]),
            f"{r['codebook']['consultation_rate']:.1%}",
            f"[{color}]{v}[/{color}]",
        )
    console.print(table)

    console.print(f"\n  PLAUSIBLE sections: {plausible_count}/7")
    console.print(f"  MARGINAL sections: {marginal_count}/7")
    console.print(f"  Total codebook (union): {len(all_codebook_words)} words")
    console.print("  Historical comparison: Trithemius used 24 cipher alphabets; "
                  "Llull's system had 4+ combinatorial wheels")
    console.print(f"  7 small devices + shared codebook is historically "
                  f"{'plausible' if plausible_count >= 5 else 'marginal'}"
                  f" vs. multi-device precedents")

    composite = {
        "per_section_verdicts": verdicts,
        "plausible_count": plausible_count,
        "marginal_count": marginal_count,
        "implausible_count": 7 - plausible_count - marginal_count,
        "total_codebook_union": len(all_codebook_words),
        "resolves_c1_implausibility": plausible_count >= 5,
        "historical_comparison": (
            "Trithemius (1508) used 24 cipher alphabets on a single tabula; "
            "Llull (c.1305) used 4+ combinatorial wheels; "
            "multiple small devices per-section is within 15th-century precedent "
            "if each device <=350mm."
        ),
    }

    return section_results, composite


# ── G2: Per-Section Admissibility Verification ───────────────────────

def sprint_g2(section_data, lattice_map, window_contents, corrections,
              section_results, suffix_map):
    """G2.1-G2.2: Per-section admissibility and cross-section boundaries."""
    console.rule("[bold blue]Sprint G2: Per-Section Admissibility Verification")

    g2_results = {}

    for section_name, sdata in section_data.items():
        console.print(f"\n[bold cyan]── {section_name} ──[/bold cyan]")
        lines = sdata["lines"]
        sr = section_results[section_name]

        all_tokens = [t for line in lines for t in line if t in lattice_map]
        freq = Counter(all_tokens)
        vocab_by_freq = [word for word, _ in freq.most_common()]
        device_size = sr["device"]["vocab_size"]
        subset = set(vocab_by_freq[:device_size])

        # G2.1: In-device admissibility
        in_device = 0
        in_device_admissible = 0
        off_device_in_out = 0
        off_device_out_in = 0
        off_device_out_out = 0
        suffix_recovered = 0
        suffix_admissible = 0

        for line in lines:
            for i in range(1, len(line)):
                prev_word = line[i - 1]
                curr_word = line[i]
                if prev_word not in lattice_map or curr_word not in lattice_map:
                    continue

                prev_in = prev_word in subset
                curr_in = curr_word in subset

                if prev_in and curr_in:
                    in_device += 1
                    prev_win = lattice_map[prev_word]
                    corrected_next = (prev_win + 1
                                      + corrections.get(prev_win, 0)) % NUM_WINDOWS
                    # Drift ±1
                    for offset in [-1, 0, 1]:
                        check_win = (corrected_next + offset) % NUM_WINDOWS
                        if curr_word in set(window_contents.get(check_win, [])):
                            in_device_admissible += 1
                            break

                elif prev_in and not curr_in:
                    off_device_in_out += 1
                    if suffix_map:
                        for sfx, sfx_win in suffix_map.items():
                            if (curr_word.endswith(sfx)
                                    and len(curr_word) > len(sfx)):
                                suffix_recovered += 1
                                prev_win = lattice_map[prev_word]
                                corrected_next = (
                                    prev_win + 1
                                    + corrections.get(prev_win, 0)
                                ) % NUM_WINDOWS
                                for offset in [-1, 0, 1]:
                                    check_win = (corrected_next
                                                 + offset) % NUM_WINDOWS
                                    if check_win == sfx_win:
                                        suffix_admissible += 1
                                        break
                                break

                elif not prev_in and curr_in:
                    off_device_out_in += 1

                else:
                    off_device_out_out += 1

        total = in_device + off_device_in_out + off_device_out_in + off_device_out_out
        in_device_rate = in_device_admissible / in_device if in_device > 0 else 0
        consolidated = in_device_admissible + suffix_admissible
        consolidated_rate = consolidated / total if total > 0 else 0

        console.print(f"  In-device transitions: {in_device} "
                      f"(admissible: {in_device_rate:.1%})")
        console.print(f"  Consolidated: {consolidated_rate:.1%} "
                      f"(gate >=55%: {'PASS' if consolidated_rate >= 0.55 else 'FAIL'})")

        g2_results[section_name] = {
            "transition_breakdown": {
                "in_device": in_device,
                "in_to_out": off_device_in_out,
                "out_to_in": off_device_out_in,
                "out_to_out": off_device_out_out,
                "total": total,
            },
            "in_device_admissibility": round(in_device_rate, 4),
            "suffix_recovery": {
                "recovered": suffix_recovered,
                "admissible": suffix_admissible,
            },
            "consolidated": {
                "admissible": consolidated,
                "total": total,
                "rate": round(consolidated_rate, 4),
                "vs_monolithic_64pp": round((consolidated_rate - 0.6413) * 100, 2),
                "gate_55_pass": consolidated_rate >= 0.55,
            },
        }

    # G2.2: Cross-section boundary transitions
    console.rule("[bold blue]G2.2: Cross-Section Boundary Transitions")

    # Reconstruct full ordered corpus with section labels
    boundary_transitions = 0
    boundary_admissible = 0
    total_transitions = 0

    # We need the full ordered corpus, not per-section. Reassemble from
    # section_data ordering.
    all_lines_ordered = []
    all_sections_ordered = []
    for section_name, sdata in section_data.items():
        for line in sdata["lines"]:
            all_lines_ordered.append(line)
            all_sections_ordered.append(section_name)

    for li in range(len(all_lines_ordered)):
        line = all_lines_ordered[li]
        section = all_sections_ordered[li]
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            total_transitions += 1

    # Boundary transitions: last word of line N in section A,
    # first word of line N+1 in section B (different section)
    for li in range(len(all_lines_ordered) - 1):
        section_curr = all_sections_ordered[li]
        section_next = all_sections_ordered[li + 1]
        if section_curr != section_next:
            line_curr = all_lines_ordered[li]
            line_next = all_lines_ordered[li + 1]
            if not line_curr or not line_next:
                continue
            last_word = line_curr[-1]
            first_word = line_next[0]
            if last_word not in lattice_map or first_word not in lattice_map:
                continue
            boundary_transitions += 1
            # Check admissibility at boundary
            prev_win = lattice_map[last_word]
            corrected_next = (prev_win + 1
                              + corrections.get(prev_win, 0)) % NUM_WINDOWS
            for offset in [-1, 0, 1]:
                check_win = (corrected_next + offset) % NUM_WINDOWS
                if first_word in set(window_contents.get(check_win, [])):
                    boundary_admissible += 1
                    break

    boundary_rate = (boundary_admissible / boundary_transitions
                     if boundary_transitions > 0 else 0)
    boundary_fraction = (boundary_transitions / total_transitions
                         if total_transitions > 0 else 0)

    console.print(f"  Cross-section boundary transitions: {boundary_transitions}")
    console.print(f"  Fraction of all transitions: {boundary_fraction:.2%}")
    console.print(f"  Boundary admissibility: {boundary_rate:.1%}")
    console.print(f"  Impact: {'NEGLIGIBLE' if boundary_fraction < 0.01 else 'NOTABLE'} "
                  f"({boundary_fraction:.2%} of corpus)")

    boundary_result = {
        "boundary_transitions": boundary_transitions,
        "boundary_admissible": boundary_admissible,
        "boundary_admissibility": round(boundary_rate, 4),
        "total_transitions": total_transitions,
        "boundary_fraction": round(boundary_fraction, 4),
        "impact": "NEGLIGIBLE" if boundary_fraction < 0.01 else "NOTABLE",
    }

    # Summary table
    table = Table(title="Per-Section Admissibility (G2)")
    table.add_column("Section", style="cyan")
    table.add_column("In-Device", justify="right")
    table.add_column("Consolidated", justify="right", style="bold")
    table.add_column("vs Monolithic", justify="right")
    table.add_column("Gate 55%", justify="center")

    gate_pass_count = 0
    for section_name, r in g2_results.items():
        passes = r["consolidated"]["gate_55_pass"]
        if passes:
            gate_pass_count += 1
        color = "green" if passes else "red"
        table.add_row(
            section_name,
            f"{r['in_device_admissibility']:.1%}",
            f"{r['consolidated']['rate']:.1%}",
            f"{r['consolidated']['vs_monolithic_64pp']:+.1f}pp",
            f"[{color}]{'PASS' if passes else 'FAIL'}[/{color}]",
        )
    console.print(table)

    console.print(f"\n  Sections passing gate: {gate_pass_count}/7")

    return g2_results, boundary_result, gate_pass_count


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprints G1-G2: Per-Section Device Analysis")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines, folios = load_lines_with_folios(store)

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

    # Split corpus into sections
    console.print("\n[bold]Splitting corpus into sections...[/bold]")
    section_data = {name: {"lines": [], "folios": []} for name in SECTIONS}

    for i, (line, folio) in enumerate(zip(lines, folios)):
        fnum = get_folio_num(folio)
        section = get_section(fnum)
        if section in section_data:
            section_data[section]["lines"].append(line)
            section_data[section]["folios"].append(folio)

    for name, sdata in section_data.items():
        n_tokens = sum(len(line) for line in sdata["lines"])
        console.print(f"  {name}: {len(sdata['lines'])} lines, "
                      f"{n_tokens} tokens")

    # G1: Coverage and dimensioning
    g1_sections, g1_composite = sprint_g1(
        section_data, lattice_map, window_contents, suffix_map,
    )

    # G2: Admissibility verification
    g2_sections, g2_boundary, gate_pass_count = sprint_g2(
        section_data, lattice_map, window_contents, corrections,
        g1_sections, suffix_map,
    )

    # Final verdict
    console.rule("[bold magenta]Final Verdict")

    resolves = g1_composite["resolves_c1_implausibility"]
    console.print(f"  Per-section devices resolve C1 implausibility: "
                  f"[bold {'green' if resolves else 'red'}]"
                  f"{'YES' if resolves else 'NO'}[/bold {'green' if resolves else 'red'}]")
    console.print(f"  G2 gate (>=55% admissibility): "
                  f"{gate_pass_count}/7 sections pass")

    # Assemble results
    results = {
        "g1_section_devices": g1_sections,
        "g1_composite": g1_composite,
        "g2_admissibility": g2_sections,
        "g2_boundary": g2_boundary,
        "g2_gate_pass_count": gate_pass_count,
        "resolves_c1_implausibility": resolves,
        "monolithic_baseline": {
            "diameter_mm": 678,
            "admissibility": 0.6413,
            "plausibility": "MARGINAL",
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17j_section_devices"}):
        main()
