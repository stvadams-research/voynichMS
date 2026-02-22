#!/usr/bin/env python3
"""Phase 20, Sprint 11: Production Workflow Synthesis.

11.1: Collect component specifications from Phases 14-20
11.2: Integrated workflow model (state machine protocol)
11.3: Per-section production profiles
11.4: Error model formalization
11.5: Generate PRODUCTION_MODEL.md

Consolidates the complete production model — scattered across dozens
of JSON files and report sections — into a single definitive specification.
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

# ── Paths ────────────────────────────────────────────────────────────

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
CODEBOOK_PATH = (
    project_root / "results/data/phase20_state_machine/codebook_architecture.json"
)
HAND_PATH = project_root / "results/data/phase20_state_machine/hand_analysis.json"
LINEAR_PATH = project_root / "results/data/phase20_state_machine/linear_devices.json"
BANDWIDTH_PATH = project_root / "results/data/phase17_finality/bandwidth_audit.json"
SLIP_PATH = (
    project_root / "results/data/phase12_mechanical/slip_detection_results.json"
)

OUTPUT_JSON = (
    project_root / "results/data/phase20_state_machine/production_synthesis.json"
)
OUTPUT_REPORT = (
    project_root / "results/reports/phase20_state_machine/PRODUCTION_MODEL.md"
)

NUM_WINDOWS = 50

# Manuscript section definitions (folio ranges)
SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}

# Hand definitions (folio ranges — from Sprint 8)
HAND_RANGES = {
    "Hand 1": [(1, 66)],
    "Hand 2": [(75, 84), (103, 116)],
}


# ── Data Loading ─────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data)


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


def extract_folio_num(page_id):
    """Extract folio number from page ID like 'f1r', 'f2v', 'f85v2'."""
    m = re.match(r"f(\d+)", page_id)
    return int(m.group(1)) if m else None


def load_corpus_by_section(store):
    """Load corpus organized by folio number → lines of tokens."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
                PageRecord.id.label("page_id"),
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

        # Organize into lines with folio info
        lines_by_folio = defaultdict(list)
        current_tokens = []
        current_line_id = None
        current_folio = None

        for content, line_id, _line_idx, page_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            folio = extract_folio_num(page_id)
            if folio is None:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens and current_folio is not None:
                    lines_by_folio[current_folio].append(current_tokens)
                current_tokens = []
            current_tokens.append(clean)
            current_line_id = line_id
            current_folio = folio

        if current_tokens and current_folio is not None:
            lines_by_folio[current_folio].append(current_tokens)

        return dict(lines_by_folio)
    finally:
        session.close()


def folio_to_section(folio_num):
    """Map a folio number to its section name."""
    for section, (start, end) in SECTIONS.items():
        if start <= folio_num <= end:
            return section
    return "Unknown"


def folio_in_hand(folio_num):
    """Map a folio number to its scribal hand."""
    for hand, ranges in HAND_RANGES.items():
        for start, end in ranges:
            if start <= folio_num <= end:
                return hand
    return "Unknown"


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_11_1(lattice_map, window_contents, corrections):
    """11.1: Collect component specifications."""
    console.rule("[bold blue]11.1: Component Specifications")

    # Load pre-computed artifacts
    codebook_data = load_json(CODEBOOK_PATH)
    hand_data = load_json(HAND_PATH)
    linear_data = load_json(LINEAR_PATH)
    bandwidth_data = load_json(BANDWIDTH_PATH)

    # Slip data
    slip_data = None
    if SLIP_PATH.exists():
        slip_data = load_json(SLIP_PATH)

    # Lattice structure
    lattice_spec = {
        "vocabulary_size": len(lattice_map),
        "num_windows": NUM_WINDOWS,
        "window_sizes": {
            str(w): len(words) for w, words in sorted(window_contents.items())
        },
        "max_window_size": max(len(v) for v in window_contents.values()),
        "min_window_size": min(len(v) for v in window_contents.values()),
        "hub_window": 18,
        "hub_window_size": len(window_contents.get(18, [])),
    }

    # Correction model
    corr_values = list(corrections.values())
    correction_spec = {
        "num_corrections": len(corrections),
        "range": [min(corr_values), max(corr_values)],
        "nonzero_count": sum(1 for v in corr_values if v != 0),
        "zero_windows": [w for w, v in corrections.items() if v == 0],
    }

    # Physical device (from linear_devices ranking)
    device_ranking = linear_data.get("device_ranking", [])
    recommended = device_ranking[0] if device_ranking else {}

    physical_spec = {
        "recommended_device": recommended.get("name", "Tabula + codebook"),
        "tabula_dimensions": "170 x 160mm",
        "tabula_grid": "10 x 5 (50 windows)",
        "codebook_pages": codebook_data.get("codebook_estimation", {}).get(
            "total_pages", 154),
        "codebook_quires": codebook_data.get("codebook_estimation", {}).get(
            "num_quires", 10),
        "combined_score": recommended.get("combined_score", 0.865),
    }

    # Scribal profiles
    profiles = hand_data.get("profiles", {})
    hand_spec = {}
    for hand_name in ["Hand 1", "Hand 2"]:
        hp = profiles.get(hand_name, {})
        hand_spec[hand_name] = {
            "token_count": hp.get("token_count", 0),
            "vocab_size": hp.get("vocab_size", 0),
            "window_entropy": hp.get("window_entropy", 0),
        }

    # Admissibility from hand analysis
    adm_data = hand_data.get("admissibility", {})
    hand_spec["Hand 1"]["admissibility"] = adm_data.get("Hand 1", {}).get(
        "drift_rate", 0.561)
    hand_spec["Hand 2"]["admissibility"] = adm_data.get("Hand 2", {}).get(
        "drift_rate", 0.645)

    # Bandwidth
    bandwidth_spec = {
        "realized_bpw": round(bandwidth_data.get("realized_bandwidth_bpw", 7.53), 2),
        "total_capacity_kb": round(bandwidth_data.get("total_capacity_kb", 11.5), 1),
        "latin_chars": round(bandwidth_data.get("latin_chars_equivalent", 22979)),
        "num_decisions": bandwidth_data.get("num_decisions", 12519),
    }

    # Slips
    slip_spec = {"detected": 0, "density_pct": 0.0}
    if slip_data:
        slips = slip_data if isinstance(slip_data, list) else slip_data.get("slips", [])
        if isinstance(slips, list):
            slip_spec["detected"] = len(slips)
            slip_spec["density_pct"] = round(len(slips) / 5145 * 100, 2)

    # Print summary
    table = Table(title="Component Specifications Summary")
    table.add_column("Component", min_width=20)
    table.add_column("Key Metric")
    table.add_column("Value", justify="right")

    table.add_row("Lattice", "Vocabulary", str(lattice_spec["vocabulary_size"]))
    table.add_row("Lattice", "Windows", str(lattice_spec["num_windows"]))
    table.add_row("Lattice", "Hub window (W18)", str(lattice_spec["hub_window_size"]))
    table.add_row("Corrections", "Range",
                  f"{correction_spec['range'][0]:+d} to {correction_spec['range'][1]:+d}")
    table.add_row("Device", "Recommended", physical_spec["recommended_device"])
    table.add_row("Device", "Tabula size", physical_spec["tabula_dimensions"])
    table.add_row("Device", "Codebook", f"{physical_spec['codebook_pages']} pages")
    table.add_row("Hand 1", "Tokens / Adm",
                  f"{hand_spec['Hand 1']['token_count']} / "
                  f"{hand_spec['Hand 1']['admissibility']:.1%}")
    table.add_row("Hand 2", "Tokens / Adm",
                  f"{hand_spec['Hand 2']['token_count']} / "
                  f"{hand_spec['Hand 2']['admissibility']:.1%}")
    table.add_row("Bandwidth", "Realized", f"{bandwidth_spec['realized_bpw']} bpw")
    table.add_row("Bandwidth", "Total capacity", f"{bandwidth_spec['total_capacity_kb']} KB")
    table.add_row("Slips", "Detected", str(slip_spec["detected"]))
    console.print(table)

    return {
        "lattice": lattice_spec,
        "corrections": correction_spec,
        "physical_device": physical_spec,
        "scribal_hands": hand_spec,
        "bandwidth": bandwidth_spec,
        "slips": slip_spec,
    }


def sprint_11_2(lattice_map, window_contents, corrections):
    """11.2: Integrated workflow model."""
    console.rule("[bold blue]11.2: Integrated Workflow Model")

    # Define the production protocol steps
    protocol = [
        {
            "step": 1,
            "action": "INITIALIZE",
            "description": "Begin a new line. Set current_window to the "
                           "window of the previous line's last word, or W18 "
                           "if starting a new page.",
        },
        {
            "step": 2,
            "action": "READ STATE",
            "description": "Consult the tabula card to read the current "
                           "window number and its correction offset.",
        },
        {
            "step": 3,
            "action": "LOOK UP VOCABULARY",
            "description": "Open the codebook to the section for the current "
                           "window. All admissible words for this position "
                           "are listed there.",
        },
        {
            "step": 4,
            "action": "SELECT WORD",
            "description": "Choose a word from the current window's vocabulary "
                           "list. Selection is influenced by scribal preference "
                           "(hand-specific suffix bias and frequency habits).",
        },
        {
            "step": 5,
            "action": "WRITE WORD",
            "description": "Inscribe the chosen word on the manuscript page.",
        },
        {
            "step": 6,
            "action": "ADVANCE STATE",
            "description": "Look up the written word in the lattice map to "
                           "determine the raw next window number.",
        },
        {
            "step": 7,
            "action": "APPLY CORRECTION",
            "description": "Add the per-window correction offset to the raw "
                           "window number (modulo 50) to get the corrected "
                           "next window. This accounts for the device's "
                           "systematic drift.",
        },
        {
            "step": 8,
            "action": "REPEAT",
            "description": "Return to step 2 with the new current_window. "
                           "Continue until the line is complete.",
        },
    ]

    # Interruption model
    interruptions = [
        {
            "event": "LINE BREAK",
            "behavior": "The current window carries over to the next line. "
                        "No state reset occurs.",
        },
        {
            "event": "PAGE BREAK",
            "behavior": "The current window MAY reset to W18 (the hub) or "
                        "carry over. Empirically, W18 dominates all folio "
                        "starts (100% of 101 folios).",
        },
        {
            "event": "SECTION TRANSITION",
            "behavior": "No device reconfiguration. All sections use the "
                        "same 50-window lattice and codebook. Thematic "
                        "variation arises from vocabulary selection within "
                        "windows, not different device states.",
        },
        {
            "event": "SCRIBAL ERROR (SLIP)",
            "behavior": "The scribe mis-indexes the codebook or misreads "
                        "the tabula, producing a word from the wrong window. "
                        "Slips concentrate at W18 (92.6% of observed slips) "
                        "because W18 has the largest codebook section "
                        "(396 words across 7+ pages).",
        },
    ]

    # Print protocol
    table = Table(title="Production Protocol: Step-by-Step")
    table.add_column("Step", justify="right")
    table.add_column("Action", min_width=15)
    table.add_column("Description", min_width=50)

    for p in protocol:
        table.add_row(str(p["step"]), p["action"], p["description"])
    console.print(table)

    # Print interruptions
    table2 = Table(title="Interruption Handling")
    table2.add_column("Event", min_width=20)
    table2.add_column("Behavior", min_width=50)

    for i in interruptions:
        table2.add_row(i["event"], i["behavior"])
    console.print(table2)

    return {
        "protocol_steps": protocol,
        "interruptions": interruptions,
        "state_machine": {
            "states": NUM_WINDOWS,
            "transitions": "word-level (each word determines next window)",
            "correction": "per-window offset (range -20 to +13)",
            "reset": "W18 at page boundaries (empirical)",
        },
    }


def sprint_11_3(lines_by_folio, lattice_map, window_contents, corrections):
    """11.3: Per-section production profiles."""
    console.rule("[bold blue]11.3: Per-Section Production Profiles")

    section_profiles = {}

    for section, (folio_start, folio_end) in SECTIONS.items():
        section_lines = []
        section_folios = 0
        for folio, flines in lines_by_folio.items():
            if folio_start <= folio <= folio_end:
                section_lines.extend(flines)
                section_folios += 1

        if not section_lines:
            section_profiles[section] = {"folios": 0, "note": "No data"}
            continue

        # Basic stats
        total_tokens = sum(len(line) for line in section_lines)
        total_lines = len(section_lines)
        words_per_line = total_tokens / total_lines if total_lines > 0 else 0
        lines_per_folio = total_lines / section_folios if section_folios > 0 else 0

        # Window usage
        window_counts = Counter()
        for line in section_lines:
            for tok in line:
                w = lattice_map.get(tok)
                if w is not None:
                    window_counts[w] += 1

        mapped_tokens = sum(window_counts.values())
        top_windows = window_counts.most_common(5)

        # Admissibility for this section
        strict_hits = 0
        drift_hits = 0
        transitions = 0
        prev_w = None

        surviving = sorted(window_contents.keys())
        n_surv = len(surviving)
        adjacent = {}
        for i, w in enumerate(surviving):
            prev_win = surviving[(i - 1) % n_surv]
            next_win = surviving[(i + 1) % n_surv]
            adjacent[w] = {prev_win, w, next_win}

        for line in section_lines:
            for tok in line:
                w = lattice_map.get(tok)
                if w is None:
                    continue
                if prev_w is not None:
                    transitions += 1
                    if w == prev_w:
                        strict_hits += 1
                        drift_hits += 1
                    elif w in adjacent.get(prev_w, set()):
                        drift_hits += 1
                prev_w = w

        drift_adm = drift_hits / transitions if transitions > 0 else 0

        # Consultation rate: 100% (all tokens require codebook)
        consultation_rate = 1.0

        profile = {
            "folios": section_folios,
            "folio_range": f"f{folio_start}-f{folio_end}",
            "total_tokens": total_tokens,
            "total_lines": total_lines,
            "words_per_line": round(words_per_line, 1),
            "lines_per_folio": round(lines_per_folio, 1),
            "mapped_tokens": mapped_tokens,
            "top_5_windows": [
                {"window": w, "count": c, "share": round(c / mapped_tokens, 3)}
                for w, c in top_windows
            ] if mapped_tokens > 0 else [],
            "drift_admissibility": round(drift_adm, 4),
            "transitions": transitions,
            "consultation_rate": consultation_rate,
        }
        section_profiles[section] = profile

    # Print table
    table = Table(title="Per-Section Production Profiles")
    table.add_column("Section")
    table.add_column("Folios", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Lines", justify="right")
    table.add_column("W/Line", justify="right")
    table.add_column("L/Folio", justify="right")
    table.add_column("Drift Adm", justify="right")
    table.add_column("Top Window")

    for section in SECTIONS:
        p = section_profiles.get(section, {})
        if p.get("folios", 0) == 0:
            continue
        top_w = (str(p["top_5_windows"][0]["window"])
                 if p.get("top_5_windows") else "N/A")
        top_share = (f" ({p['top_5_windows'][0]['share']:.0%})"
                     if p.get("top_5_windows") else "")
        table.add_row(
            section,
            str(p["folios"]),
            str(p["total_tokens"]),
            str(p["total_lines"]),
            f"{p['words_per_line']:.1f}",
            f"{p['lines_per_folio']:.1f}",
            f"{p['drift_admissibility']:.4f}",
            f"W{top_w}{top_share}",
        )
    console.print(table)

    return section_profiles


def sprint_11_4(lines_by_folio, lattice_map, window_contents, corrections):
    """11.4: Error model formalization."""
    console.rule("[bold blue]11.4: Error Model Formalization")

    # Load slip data
    slip_data = load_json(SLIP_PATH) if SLIP_PATH.exists() else {}
    slips = slip_data if isinstance(slip_data, list) else slip_data.get("slips", [])
    if not isinstance(slips, list):
        slips = []

    # Compute per-window failure rates from full corpus
    all_lines = []
    for folio, flines in sorted(lines_by_folio.items()):
        all_lines.extend(flines)

    window_transitions = Counter()
    window_failures = Counter()
    prev_w = None

    surviving = sorted(window_contents.keys())
    n_surv = len(surviving)
    adjacent = {}
    for i, w in enumerate(surviving):
        prev_win = surviving[(i - 1) % n_surv]
        next_win = surviving[(i + 1) % n_surv]
        adjacent[w] = {prev_win, w, next_win}

    for line in all_lines:
        for tok in line:
            w = lattice_map.get(tok)
            if w is None:
                continue
            if prev_w is not None:
                window_transitions[prev_w] += 1
                if w != prev_w and w not in adjacent.get(prev_w, set()):
                    window_failures[prev_w] += 1
            prev_w = w

    # Identify highest-failure windows
    failure_rates = {}
    for w in sorted(window_contents.keys()):
        trans = window_transitions.get(w, 0)
        fails = window_failures.get(w, 0)
        rate = fails / trans if trans > 0 else 0
        failure_rates[w] = {
            "transitions": trans,
            "failures": fails,
            "rate": round(rate, 4),
        }

    top_failures = sorted(failure_rates.items(),
                          key=lambda x: -x[1]["failures"])[:10]

    # Hapax analysis
    token_freq = Counter()
    for line in all_lines:
        for tok in line:
            if tok in lattice_map:
                token_freq[tok] += 1

    hapax_count = sum(1 for t, f in token_freq.items() if f == 1)
    rare_count = sum(1 for t, f in token_freq.items() if f < 10)
    total_types = len(token_freq)

    # Print error model
    table = Table(title="Top-10 Windows by Failure Count")
    table.add_column("Window", justify="right")
    table.add_column("Transitions", justify="right")
    table.add_column("Failures", justify="right")
    table.add_column("Rate", justify="right")

    for w, data in top_failures:
        table.add_row(
            str(w),
            str(data["transitions"]),
            str(data["failures"]),
            f"{data['rate']:.1%}",
        )
    console.print(table)

    console.print(
        "\n  Hapax (frequency=1):"
        f" {hapax_count}/{total_types} types ({hapax_count/total_types:.1%})"
        f"\n  Rare (<10 occurrences):"
        f" {rare_count}/{total_types} types ({rare_count/total_types:.1%})"
        f"\n  Mechanical slips detected: {len(slips)}"
    )

    # Hand-specific error rates (from Phase 20 Sprint 8)
    hand_adm = {
        "Hand 1": {"admissibility": 0.561, "drift_param": 15,
                    "dominant_suffix": "-dy"},
        "Hand 2": {"admissibility": 0.645, "drift_param": 25,
                    "dominant_suffix": "-in"},
    }

    return {
        "per_window_failures": {
            str(w): data for w, data in failure_rates.items()
        },
        "top_failure_windows": [
            {"window": w, **data} for w, data in top_failures
        ],
        "vocabulary_frequency": {
            "total_types": total_types,
            "hapax_count": hapax_count,
            "hapax_pct": round(hapax_count / total_types * 100, 1),
            "rare_count": rare_count,
            "rare_pct": round(rare_count / total_types * 100, 1),
        },
        "mechanical_slips": {
            "total_detected": len(slips),
            "density_pct": round(len(slips) / max(1, len(all_lines)) * 100, 2),
            "w18_concentration": "92.6% of observed slips",
        },
        "hand_specific": hand_adm,
    }


def sprint_11_5(specs, workflow, section_profiles, error_model):
    """11.5: Generate PRODUCTION_MODEL.md report."""
    console.rule("[bold blue]11.5: Generating PRODUCTION_MODEL.md")

    lines = []
    lines.append("# The Voynich Production Model: Complete Specification")
    lines.append("")
    lines.append("**Generated:** Phase 20, Sprint 11 — Production Workflow Synthesis")
    lines.append("")
    lines.append("This document presents the complete, integrated production model "
                 "for the Voynich Manuscript as reconstructed across Phases 14-20. "
                 "A third party can use this specification to understand how the "
                 "manuscript was produced using a mechanical constraint system.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Physical Tool
    lines.append("## 1. Physical Tool Specification")
    lines.append("")
    lines.append("The production tool consists of two components:")
    lines.append("")
    lines.append("### 1.1 State Tracker (Tabula)")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|:---|:---|")
    lines.append("| Form | Flat card (tabula) |")
    lines.append("| Dimensions | 170 x 160mm |")
    lines.append("| Layout | 10 x 5 grid (50 window positions) |")
    lines.append("| Per-cell content | Window number + correction offset |")
    lines.append("| Materials | Parchment or stiff paper |")
    lines.append("| Historical parallel | Alberti cipher disc (1467), "
                 "Trithemius tabula recta (1508) |")
    lines.append("")
    lines.append("The tabula encodes 50 window states, each labeled with a "
                 "window number (0-49) and a correction offset (range "
                 f"{specs['corrections']['range'][0]:+d} to "
                 f"{specs['corrections']['range'][1]:+d}). "
                 f"{specs['corrections']['nonzero_count']} of 50 windows have "
                 "non-zero corrections.")
    lines.append("")

    lines.append("### 1.2 Vocabulary Codebook")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|:---|:---|")
    lines.append(f"| Total words | {specs['lattice']['vocabulary_size']} |")
    lines.append(f"| Pages | {specs['physical_device']['codebook_pages']} |")
    lines.append(f"| Quires | {specs['physical_device']['codebook_quires']} |")
    lines.append("| Organization | By window number (W0-W49) |")
    lines.append("| Page capacity | ~60 words per page (2 columns x 30 rows) |")
    lines.append(f"| Largest section | W18: "
                 f"{specs['lattice']['hub_window_size']} words |")
    lines.append("| Consultation rate | 100% (annotation impractical) |")
    lines.append("")
    lines.append("The codebook is organized by window number. The scribe opens "
                 "to the section for the current window and selects a word. "
                 "Window 18 alone contains "
                 f"{specs['lattice']['hub_window_size']} words "
                 "and produces ~50% of all corpus tokens, making it the "
                 "production hub.")
    lines.append("")

    # Section 2: Lattice Structure
    lines.append("## 2. Lattice Structure")
    lines.append("")
    lines.append(f"The manuscript's text is generated by traversing a "
                 f"{NUM_WINDOWS}-window lattice containing "
                 f"{specs['lattice']['vocabulary_size']} unique words.")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|:---|:---|")
    lines.append(f"| Windows | {NUM_WINDOWS} |")
    lines.append(f"| Vocabulary | {specs['lattice']['vocabulary_size']} words |")
    lines.append(f"| Window size range | "
                 f"{specs['lattice']['min_window_size']}-"
                 f"{specs['lattice']['max_window_size']} words |")
    lines.append("| Transition type | First-order Markov at window level |")
    lines.append("| Canonical admissibility | 64.94% (corrected + suffix recovery) |")
    lines.append("| Overgeneration | ~20x at all n-gram orders |")
    lines.append("| Branching factor | 761.7 candidates per position "
                 "(9.57 effective bits) |")
    lines.append("")
    lines.append("Each word in the codebook maps to a specific next window. "
                 "When the scribe writes a word, the lattice determines which "
                 "window to consult next. The per-window correction offset "
                 "adjusts for systematic drift in the device.")
    lines.append("")

    # Section 3: Production Protocol
    lines.append("## 3. Production Protocol")
    lines.append("")
    lines.append("### 3.1 Step-by-Step Procedure")
    lines.append("")
    for step in workflow["protocol_steps"]:
        lines.append(f"**Step {step['step']}: {step['action']}**")
        lines.append(f": {step['description']}")
        lines.append("")

    lines.append("### 3.2 Interruption Handling")
    lines.append("")
    lines.append("| Event | Behavior |")
    lines.append("|:---|:---|")
    for i in workflow["interruptions"]:
        # Escape pipes in description
        desc = i["behavior"].replace("|", "\\|")
        lines.append(f"| {i['event']} | {desc} |")
    lines.append("")

    # Section 4: Scribal Variation
    lines.append("## 4. Scribal Variation")
    lines.append("")
    lines.append("Two scribal hands operate the same device with different "
                 "fluency profiles:")
    lines.append("")
    lines.append("| Dimension | Hand 1 (f1-66) | Hand 2 (f75-84, f103-116) |")
    lines.append("|:---|:---|:---|")
    h1 = specs["scribal_hands"].get("Hand 1", {})
    h2 = specs["scribal_hands"].get("Hand 2", {})
    lines.append(f"| Tokens | {h1.get('token_count', 'N/A')} | "
                 f"{h2.get('token_count', 'N/A')} |")
    lines.append(f"| Vocabulary | {h1.get('vocab_size', 'N/A')} | "
                 f"{h2.get('vocab_size', 'N/A')} |")
    lines.append(f"| Drift admissibility | {h1.get('admissibility', 0):.1%} | "
                 f"{h2.get('admissibility', 0):.1%} |")
    lines.append("| Dominant suffix | -dy | -in |")
    lines.append("| Window distribution | JSD=0.012, cosine=0.998 (identical) | "
                 "Same device |")
    lines.append("| Vocabulary overlap | 15.6% shared types "
                 "(but 66-72% shared token coverage) | |")
    lines.append("")
    lines.append("Both hands traverse the same lattice with the same window "
                 "distribution. They differ in word selection preferences, "
                 "suffix habits, and adherence to drift rules. Hand 2 "
                 "follows the device more accurately (64.5% vs 56.1% "
                 "admissibility).")
    lines.append("")

    # Section 5: Per-Section Profiles
    lines.append("## 5. Per-Section Production Profiles")
    lines.append("")
    lines.append("| Section | Folios | Tokens | Words/Line | Lines/Folio | "
                 "Drift Adm | Top Window |")
    lines.append("|:---|---:|---:|---:|---:|---:|:---|")
    for section in SECTIONS:
        p = section_profiles.get(section, {})
        if p.get("folios", 0) == 0:
            continue
        top_w = (f"W{p['top_5_windows'][0]['window']} "
                 f"({p['top_5_windows'][0]['share']:.0%})"
                 if p.get("top_5_windows") else "N/A")
        lines.append(f"| {section} | {p['folios']} | {p['total_tokens']} | "
                     f"{p['words_per_line']:.1f} | {p['lines_per_folio']:.1f} | "
                     f"{p['drift_admissibility']:.4f} | {top_w} |")
    lines.append("")
    lines.append("All sections use the same device and codebook. "
                 "Thematic variation arises from vocabulary selection "
                 "within windows, not from different device configurations.")
    lines.append("")

    # Section 6: Error Model
    lines.append("## 6. Error Model")
    lines.append("")
    lines.append("### 6.1 Mechanical Slips")
    lines.append("")
    slips = error_model["mechanical_slips"]
    lines.append(f"- **Detected:** {slips['total_detected']} vertical offset errors")
    lines.append(f"- **Density:** {slips['density_pct']:.2f}% of lines")
    lines.append(f"- **W18 concentration:** {slips['w18_concentration']}")
    lines.append("- **Mechanism:** Scribe mis-indexes the codebook, producing "
                 "a word from an adjacent window. W18's codebook section "
                 "(396 words, 7+ pages) is the largest, making indexing "
                 "errors most likely there.")
    lines.append("")

    lines.append("### 6.2 Drift Violations")
    lines.append("")
    lines.append("~35% of token transitions are not admissibly reached under "
                 "the canonical model. The residual is frequency-dominated:")
    lines.append("")
    lines.append("| Frequency Tier | Failure Rate | Share of All Failures |")
    lines.append("|:---|---:|---:|")
    lines.append("| Common (>100 occ.) | 6.9% | 6.8% |")
    lines.append("| Medium (10-100) | 35.1% | 25.9% |")
    lines.append("| Rare (<10) | 84.5% | 55.8% |")
    lines.append("| Hapax (1 occ.) | 97.8% | 11.5% |")
    lines.append("")

    lines.append("### 6.3 Vocabulary Frequency")
    lines.append("")
    vf = error_model["vocabulary_frequency"]
    lines.append(f"- **Total word types:** {vf['total_types']}")
    lines.append(f"- **Hapax (frequency=1):** {vf['hapax_count']} "
                 f"({vf['hapax_pct']}%)")
    lines.append(f"- **Rare (<10 occurrences):** {vf['rare_count']} "
                 f"({vf['rare_pct']}%)")
    lines.append("")

    lines.append("### 6.4 Hand-Specific Error Rates")
    lines.append("")
    lines.append("| Hand | Admissibility | Drift Param | Dominant Suffix |")
    lines.append("|:---|---:|---:|:---|")
    for hand, data in error_model["hand_specific"].items():
        lines.append(f"| {hand} | {data['admissibility']:.1%} | "
                     f"{data['drift_param']} | {data['dominant_suffix']} |")
    lines.append("")

    # Section 7: Steganographic Bandwidth
    lines.append("## 7. Steganographic Bandwidth")
    lines.append("")
    bw = specs["bandwidth"]
    lines.append(f"- **Realized bandwidth:** {bw['realized_bpw']} bits per word")
    lines.append(f"- **Admissible decisions:** {bw['num_decisions']}")
    lines.append(f"- **Total capacity:** {bw['total_capacity_kb']} KB "
                 f"(~{bw['latin_chars']} Latin characters)")
    lines.append("")
    lines.append("The lattice provides sufficient bandwidth for sparse encoding "
                 "(confirmed by Latin Vulgate encoding test: RSB = 2.21 bpw). "
                 "However, high-density natural language is structurally "
                 "unlikely given the entropy profile. The model bounds "
                 "capacity but cannot prove absence of hidden content.")
    lines.append("")

    # Section 8: Historical Context
    lines.append("## 8. Historical Context")
    lines.append("")
    lines.append("The reconstructed production system has direct parallels:")
    lines.append("")
    lines.append("| System | Date | State Device | Reference | "
                 "Similarity |")
    lines.append("|:---|:---|:---|:---|:---|")
    lines.append("| Alberti cipher | 1467 | 120mm disc (24 positions) | "
                 "External alphabet | State tracker + codebook |")
    lines.append("| Trithemius steganography | 1499 | Key table | "
                 "Word codebook | Tabula + codebook |")
    lines.append("| Llull Ars Magna | c.1305 | 200mm disc (9-16 positions) | "
                 "Concept tables | Combinatorial state tracker |")
    lines.append("| **Voynich production tool** | **c.1400-1450** | "
                 "**170x160mm tabula (50 windows)** | "
                 "**154pp codebook** | **State tracker + codebook** |")
    lines.append("")
    lines.append("The Voynich system is most similar to Trithemius's "
                 "steganographic architecture: a flat reference table "
                 "(tabula) paired with a vocabulary codebook organized "
                 "by state. The key difference is scale — 50 states and "
                 "7,717 words versus Trithemius's simpler key tables.")
    lines.append("")

    # Section 9: What This Does Not Tell You
    lines.append("## 9. What This Does Not Tell You")
    lines.append("")
    lines.append("- **Author intent:** The model is agnostic. Medical reference, "
                 "philosophical exercise, hoax, and devotional artifact could "
                 "all produce this structure.")
    lines.append("- **Whether meaning exists:** 7.53 bits/word is sufficient "
                 "for sparse encoding. The model bounds capacity but cannot "
                 "prove absence.")
    lines.append("- **Physical survival:** The model specifies functional "
                 "requirements. Whether a specific artifact survives is an "
                 "archaeological question.")
    lines.append("- **The residual:** ~35% of transitions are unexplained. "
                 "If structured, the residual could carry information the "
                 "model does not capture.")
    lines.append("")

    # Write report
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(lines)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report_text)

    console.print(f"  Written {len(lines)} lines to {OUTPUT_REPORT}")
    return {"report_path": str(OUTPUT_REPORT), "line_count": len(lines)}


# ── Main ─────────────────────────────────────────────────────────────

def _sanitize(obj):
    """Recursively convert numpy types to native Python."""
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


def main():
    console.rule("[bold magenta]Phase 20, Sprint 11: Production Workflow Synthesis")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines_by_folio = load_corpus_by_section(store)

    console.print(
        f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows"
        f"\n  Folios loaded: {len(lines_by_folio)}"
        f"\n  Corrections: {len(corrections)} windows"
    )

    # 11.1: Component specifications
    specs = sprint_11_1(lattice_map, window_contents, corrections)

    # 11.2: Integrated workflow
    workflow = sprint_11_2(lattice_map, window_contents, corrections)

    # 11.3: Per-section profiles
    section_profiles = sprint_11_3(
        lines_by_folio, lattice_map, window_contents, corrections)

    # 11.4: Error model
    error_model = sprint_11_4(
        lines_by_folio, lattice_map, window_contents, corrections)

    # 11.5: Generate report
    report = sprint_11_5(specs, workflow, section_profiles, error_model)

    # Assemble results
    results = {
        "component_specs": specs,
        "workflow_model": workflow,
        "section_profiles": section_profiles,
        "error_model": error_model,
        "report": report,
    }

    results = _sanitize(results)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_JSON)
    console.print(f"\n[green]Saved to {OUTPUT_JSON}[/green]")


if __name__ == "__main__":
    with active_run(config={
        "seed": 42,
        "command": "run_20h_production_synthesis",
    }):
        main()
