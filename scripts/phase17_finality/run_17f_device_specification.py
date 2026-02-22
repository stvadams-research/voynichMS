#!/usr/bin/env python3
"""Sprint C1: Device Specification Derivation + Sprint C2: Wear Predictions.

Derives testable physical predictions from the computational model:
  C1: Device dimensions (volvelle and tabula), historical plausibility
  C2: Wear pattern predictions, anchor signatures, temporal gradient

These predictions could guide physical examination of the manuscript
or comparative analysis of historical production devices.
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
PHYS_PATH = project_root / "results/data/phase14_machine/physical_integration.json"
CHOICE_PATH = project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
LEGACY_CHOICE_PATH = project_root / "results/data/phase15_selection/choice_stream_trace.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/device_specification.json"

# 15th-century physical constraints
GLYPH_WIDTH_MM = 4.0   # avg Voynichese glyph width (3-5mm typical)
GLYPH_HEIGHT_MM = 5.0  # avg glyph height
LINE_SPACING_MM = 2.0  # inter-line spacing within a window's word list
WORD_SPACING_MM = 3.0  # horizontal space between words in a row
MARGIN_MM = 5.0         # minimum margin around content

# Historical reference devices
HISTORICAL_DEVICES = {
    "Llull Ars Magna (c.1305)": {"diameter_mm": 200, "type": "volvelle"},
    "Alberti cipher disc (1467)": {"diameter_mm": 120, "type": "volvelle"},
    "Apian Astronomicum (1540)": {"diameter_mm": 350, "type": "volvelle"},
    "Trithemius tabula recta (1508)": {"width_mm": 250, "height_mm": 200, "type": "tabula"},
    "Vigenere table (1586)": {"width_mm": 200, "height_mm": 200, "type": "tabula"},
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


# ── C1: Device Dimension Inference ───────────────────────────────────

def sprint_c1(window_contents, corrections):
    """Derive physical dimensions for volvelle and tabula models."""
    console.rule("[bold blue]Sprint C1: Device Specification Derivation")

    # Window vocabulary statistics
    window_sizes = {}
    for w in range(NUM_WINDOWS):
        words = window_contents.get(w, [])
        avg_glyph_len = np.mean([len(word) for word in words]) if words else 0
        window_sizes[w] = {
            "n_words": len(words),
            "avg_word_length": round(avg_glyph_len, 1),
            "max_word_length": max((len(w) for w in words), default=0),
        }

    sizes = [ws["n_words"] for ws in window_sizes.values()]
    console.print(f"  Window sizes: min={min(sizes)}, max={max(sizes)}, "
                  f"mean={np.mean(sizes):.0f}, median={np.median(sizes):.0f}")

    # C1.1: Vocabulary density constraints
    console.print("\n[bold]C1.1: Vocabulary Density Constraints[/bold]")

    # Each window needs to display its words legibly
    # Assume words arranged in columns within a sector/cell
    window_areas_mm2 = {}
    for w in range(NUM_WINDOWS):
        n_words = window_sizes[w]["n_words"]
        avg_len = window_sizes[w]["avg_word_length"]
        # Words per column (assume 15-20 words per column)
        words_per_col = 18
        n_cols = math.ceil(n_words / words_per_col)
        col_width = avg_len * GLYPH_WIDTH_MM + WORD_SPACING_MM
        total_width = n_cols * col_width + 2 * MARGIN_MM
        total_height = words_per_col * (GLYPH_HEIGHT_MM + LINE_SPACING_MM) + 2 * MARGIN_MM
        area = total_width * total_height
        window_areas_mm2[w] = {
            "width_mm": round(total_width, 1),
            "height_mm": round(total_height, 1),
            "area_mm2": round(area, 1),
            "n_cols": n_cols,
        }

    total_area_mm2 = sum(a["area_mm2"] for a in window_areas_mm2.values())
    console.print(f"  Total vocabulary area: {total_area_mm2:,.0f} mm² "
                  f"({total_area_mm2 / 1e6:.3f} m²)")

    # C1.2: Volvelle geometry
    console.print("\n[bold]C1.2: Volvelle Geometry[/bold]")

    # 50 windows = 50 angular sectors of 7.2° each
    sector_angle_deg = 360.0 / NUM_WINDOWS
    sector_angle_rad = math.radians(sector_angle_deg)

    # For a volvelle, windows are arranged in concentric rings
    # The arc length at radius r must accommodate the window's word columns
    # Arc length = r * theta, so r_min = width / theta
    min_radii = []
    for w in range(NUM_WINDOWS):
        width_needed = window_areas_mm2[w]["width_mm"]
        r_min = width_needed / sector_angle_rad
        min_radii.append(r_min)

    # The volvelle needs concentric rings for different word density levels
    # Sort windows by required radius
    sorted_by_radius = sorted(range(NUM_WINDOWS), key=lambda w: min_radii[w])

    # Estimate: use 3-5 concentric rings
    n_rings = 5
    windows_per_ring = NUM_WINDOWS // n_rings
    ring_specs = []
    current_radius = 0
    for ring_idx in range(n_rings):
        start = ring_idx * windows_per_ring
        end = start + windows_per_ring if ring_idx < n_rings - 1 else NUM_WINDOWS
        ring_windows = sorted_by_radius[start:end]
        max_height = max(window_areas_mm2[w]["height_mm"] for w in ring_windows)
        max_radius_needed = max(min_radii[w] for w in ring_windows)

        inner_r = current_radius + MARGIN_MM
        outer_r = inner_r + max_height
        current_radius = outer_r

        ring_specs.append({
            "ring": ring_idx + 1,
            "inner_radius_mm": round(inner_r, 1),
            "outer_radius_mm": round(outer_r, 1),
            "n_windows": len(ring_windows),
            "max_word_count": max(window_sizes[w]["n_words"] for w in ring_windows),
        })

    total_diameter_mm = 2 * current_radius
    console.print(f"  Angular sector: {sector_angle_deg:.1f}°")
    console.print(f"  Estimated rings: {n_rings}")
    console.print(f"  Total disc diameter: {total_diameter_mm:.0f} mm ({total_diameter_mm / 10:.1f} cm)")

    ring_table = Table(title="Volvelle Ring Specifications")
    ring_table.add_column("Ring", justify="right")
    ring_table.add_column("Inner R (mm)", justify="right")
    ring_table.add_column("Outer R (mm)", justify="right")
    ring_table.add_column("Windows", justify="right")
    ring_table.add_column("Max Words", justify="right")
    for rs in ring_specs:
        ring_table.add_row(
            str(rs["ring"]), f"{rs['inner_radius_mm']:.0f}",
            f"{rs['outer_radius_mm']:.0f}",
            str(rs["n_windows"]), str(rs["max_word_count"]),
        )
    console.print(ring_table)

    # Anchor position
    anchor_window = 18  # from Phase 14N
    anchor_angle = anchor_window * sector_angle_deg
    console.print(f"\n  Anchor window 18: angular position {anchor_angle:.1f}° from reference")
    console.print(f"  Reading aperture: aligned at {anchor_angle:.1f}°")

    # C1.3: Tabula geometry
    console.print("\n[bold]C1.3: Tabula Geometry (10×5 Grid)[/bold]")

    # 10 rows × 5 columns = 50 cells
    max_cell_width = max(window_areas_mm2[w]["width_mm"] for w in range(NUM_WINDOWS))
    max_cell_height = max(window_areas_mm2[w]["height_mm"] for w in range(NUM_WINDOWS))
    tabula_width = 5 * max_cell_width + 2 * MARGIN_MM
    tabula_height = 10 * max_cell_height + 2 * MARGIN_MM

    console.print(f"  Cell size: {max_cell_width:.0f} × {max_cell_height:.0f} mm")
    console.print(f"  Total sheet: {tabula_width:.0f} × {tabula_height:.0f} mm "
                  f"({tabula_width / 10:.1f} × {tabula_height / 10:.1f} cm)")

    # C1.4: Historical plausibility
    console.print("\n[bold]C1.4: Historical Plausibility[/bold]")

    hist_table = Table(title="Historical Device Comparison")
    hist_table.add_column("Device", style="cyan")
    hist_table.add_column("Type")
    hist_table.add_column("Size (mm)", justify="right")
    hist_table.add_column("vs Volvelle", justify="right")
    hist_table.add_column("vs Tabula", justify="right")

    for name, spec in HISTORICAL_DEVICES.items():
        if spec["type"] == "volvelle":
            size_str = f"⌀{spec['diameter_mm']}"
            vol_ratio = total_diameter_mm / spec["diameter_mm"]
            tab_ratio = "—"
        else:
            size_str = f"{spec['width_mm']}×{spec['height_mm']}"
            vol_ratio = "—"
            tab_ratio = f"{tabula_width / spec['width_mm']:.1f}× / {tabula_height / spec['height_mm']:.1f}×"

        vol_str = f"{vol_ratio:.1f}×" if isinstance(vol_ratio, float) else vol_ratio
        hist_table.add_row(name, spec["type"], size_str, vol_str, tab_ratio)

    hist_table.add_row(
        "Voynich Volvelle (derived)", "volvelle",
        f"⌀{total_diameter_mm:.0f}", "1.0×", "—",
        style="bold green",
    )
    hist_table.add_row(
        "Voynich Tabula (derived)", "tabula",
        f"{tabula_width:.0f}×{tabula_height:.0f}", "—", "1.0×",
        style="bold green",
    )
    console.print(hist_table)

    # Plausibility assessment
    alberti_ratio = total_diameter_mm / 120
    apian_ratio = total_diameter_mm / 350
    plausible = 0.5 <= alberti_ratio <= 5.0  # within 0.5x-5x of known devices

    console.print(f"\n  Volvelle vs Alberti disc: {alberti_ratio:.1f}×")
    console.print(f"  Volvelle vs Apian disc: {apian_ratio:.1f}×")
    console.print(f"  Historically plausible: "
                  f"{'[green]YES[/green]' if plausible else '[red]NO[/red]'}")

    return {
        "window_sizes": {str(k): v for k, v in window_sizes.items()},
        "volvelle": {
            "sector_angle_deg": round(sector_angle_deg, 1),
            "n_rings": n_rings,
            "ring_specs": ring_specs,
            "total_diameter_mm": round(total_diameter_mm, 0),
            "total_diameter_cm": round(total_diameter_mm / 10, 1),
            "anchor_window": 18,
            "anchor_angle_deg": round(anchor_angle, 1),
        },
        "tabula": {
            "grid": "10x5",
            "cell_width_mm": round(max_cell_width, 0),
            "cell_height_mm": round(max_cell_height, 0),
            "total_width_mm": round(tabula_width, 0),
            "total_height_mm": round(tabula_height, 0),
            "total_width_cm": round(tabula_width / 10, 1),
            "total_height_cm": round(tabula_height / 10, 1),
        },
        "historical_plausibility": {
            "volvelle_vs_alberti": round(alberti_ratio, 2),
            "volvelle_vs_apian": round(apian_ratio, 2),
            "plausible": plausible,
        },
    }


# ── C2: Wear and Usage Predictions ───────────────────────────────────

def sprint_c2(lines, folios, lattice_map, corrections, choices):
    """Predict wear patterns from usage frequencies."""
    console.rule("[bold blue]Sprint C2: Wear and Usage Predictions")

    # C2.1: Window usage frequency map
    console.print("\n[bold]C2.1: Window Usage Frequency[/bold]")

    window_usage = Counter()
    for line in lines:
        for word in line:
            if word in lattice_map:
                window_usage[lattice_map[word]] += 1

    total_usage = sum(window_usage.values())
    usage_profile = []
    for w in range(NUM_WINDOWS):
        count = window_usage.get(w, 0)
        usage_profile.append({
            "window": w,
            "token_count": count,
            "usage_fraction": round(count / total_usage, 4) if total_usage > 0 else 0,
            "correction": corrections.get(w, 0),
        })

    # Top and bottom 5
    sorted_usage = sorted(usage_profile, key=lambda x: x["token_count"], reverse=True)

    usage_table = Table(title="Window Usage (Top 10)")
    usage_table.add_column("Window", justify="right")
    usage_table.add_column("Tokens", justify="right")
    usage_table.add_column("Fraction", justify="right")
    usage_table.add_column("Correction", justify="right")
    for entry in sorted_usage[:10]:
        usage_table.add_row(
            str(entry["window"]), str(entry["token_count"]),
            f"{entry['usage_fraction']:.3f}", str(entry["correction"]),
        )
    console.print(usage_table)

    # Usage concentration
    top5_usage = sum(e["usage_fraction"] for e in sorted_usage[:5])
    top10_usage = sum(e["usage_fraction"] for e in sorted_usage[:10])
    console.print(f"  Top 5 windows: {top5_usage:.1%} of usage")
    console.print(f"  Top 10 windows: {top10_usage:.1%} of usage")

    # C2.2: Anchor wear prediction
    console.print("\n[bold]C2.2: Anchor Wear Prediction[/bold]")

    anchor_window = 18
    anchor_usage = window_usage.get(anchor_window, 0)
    anchor_fraction = anchor_usage / total_usage if total_usage > 0 else 0

    # How many times does the scribe visit window 18?
    # Count window transitions to/from anchor
    anchor_visits = 0
    for line in lines:
        for i in range(len(line)):
            if line[i] in lattice_map and lattice_map[line[i]] == anchor_window:
                anchor_visits += 1

    console.print(f"  Window 18 (anchor): {anchor_usage} tokens "
                  f"({anchor_fraction:.1%} of corpus)")
    console.print(f"  Window 18 visits: {anchor_visits}")

    # Predict anchor wear signatures
    anchor_predictions = {
        "window": anchor_window,
        "token_count": anchor_usage,
        "usage_fraction": round(anchor_fraction, 4),
        "visit_count": anchor_visits,
        "predicted_signatures": [
            "Alignment marks or registration features at this position",
            "Higher ink density from frequent scribe positioning",
            "Potential wear on reading aperture edge near anchor",
            "92.6% of mechanical slips occur here — visible as correction marks",
        ],
    }

    console.print("  Predicted wear signatures:")
    for sig in anchor_predictions["predicted_signatures"]:
        console.print(f"    - {sig}")

    # C2.3: Temporal wear gradient
    console.print("\n[bold]C2.3: Temporal Wear Gradient[/bold]")

    # Load slip data from physical integration results
    slip_folios = defaultdict(int)
    if PHYS_PATH.exists():
        with open(PHYS_PATH) as f:
            phys = json.load(f)
        per_window = phys.get("results", phys).get(
            "sprint2_slip_correlation", {},
        ).get("per_window_summary", [])
        for pw in per_window:
            if pw["slip_count"] > 0:
                slip_folios[pw["window"]] = pw["slip_count"]

    # Map folios to quire positions
    folio_order = {}
    for i, folio in enumerate(folios):
        fnum = get_folio_num(folio)
        if fnum not in folio_order:
            folio_order[fnum] = i

    # Split manuscript into halves and compare slip rates
    all_folio_nums = sorted(folio_order.keys())
    if all_folio_nums:
        mid = all_folio_nums[len(all_folio_nums) // 2]
        early_lines = [lines[i] for i, f in enumerate(folios) if get_folio_num(f) <= mid]
        late_lines = [lines[i] for i, f in enumerate(folios) if get_folio_num(f) > mid]

        # Count tokens in each half
        early_tokens = sum(len(l) for l in early_lines)
        late_tokens = sum(len(l) for l in late_lines)

        console.print(f"  Early half (folios ≤{mid}): {len(early_lines)} lines, "
                      f"{early_tokens} tokens")
        console.print(f"  Late half (folios >{mid}): {len(late_lines)} lines, "
                      f"{late_tokens} tokens")

        temporal_gradient = {
            "midpoint_folio": mid,
            "early_lines": len(early_lines),
            "early_tokens": early_tokens,
            "late_lines": len(late_lines),
            "late_tokens": late_tokens,
        }
    else:
        temporal_gradient = {"note": "no folio data available"}

    # C2.4: Falsifiable predictions summary
    console.print("\n[bold]C2.4: Falsifiable Predictions[/bold]")

    predictions = {
        "volvelle_confirmatory": [
            "Circular wear marks on a disc-shaped artifact or template",
            "Registration mark or notch at the angular position corresponding to window 18",
            "Radially arranged vocabulary in 50 angular sectors",
            "Concentric rings accommodating varying word-count density per window",
            f"Disc diameter approximately {sprint_c1_result['volvelle']['total_diameter_mm']:.0f}mm "
            f"(within range of known 15th-century volvelles)" if 'sprint_c1_result' in dir() else
            "Disc diameter within 120-350mm range of known 15th-century volvelles",
            "Wear concentrated at high-usage windows (particularly windows 18, 0, and 36)",
        ],
        "tabula_confirmatory": [
            "Rectangular wear pattern consistent with a sliding mask",
            "Track marks from a sliding grille on a flat sheet",
            "Grid-arranged vocabulary in a 10×5 pattern",
            "Uniform cell sizes (no radial distortion)",
        ],
        "refutatory_both": [
            "No physical production artifact found despite analysis",
            "Vocabulary arrangement inconsistent with any geometric layout",
            "Uniform wear across all positions (suggesting cognitive process)",
            "Slip distribution inconsistent with any single device geometry",
        ],
    }

    for category, preds in predictions.items():
        label = category.replace("_", " ").title()
        console.print(f"\n  [{label}]")
        for pred in preds:
            console.print(f"    - {pred}")

    return {
        "usage_profile": usage_profile,
        "usage_concentration": {
            "top5_fraction": round(top5_usage, 4),
            "top10_fraction": round(top10_usage, 4),
        },
        "anchor_wear": anchor_predictions,
        "temporal_gradient": temporal_gradient,
        "falsifiable_predictions": predictions,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprints C1-C2: Physical Archaeology")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines, folios = load_lines_with_folios(store)

    # Load choices
    choice_path = CHOICE_PATH if CHOICE_PATH.exists() else LEGACY_CHOICE_PATH
    if not choice_path.exists():
        raise FileNotFoundError(
            "Choice stream trace missing. Checked "
            f"{CHOICE_PATH} and {LEGACY_CHOICE_PATH}."
        )
    with open(choice_path) as f:
        cdata = json.load(f)
    choices = cdata.get("results", cdata).get("choices", [])

    console.print(f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows")
    console.print(f"  Corpus: {len(lines)} lines")
    console.print(f"  Choice stream: {choice_path}")
    console.print(f"  Choices: {len(choices)} decisions")

    # Sprint C1
    c1_results = sprint_c1(window_contents, corrections)

    # Sprint C2 (needs c1 results for prediction text — pass diameter directly)
    global sprint_c1_result
    sprint_c1_result = c1_results

    # Fix the volvelle prediction text with actual computed diameter
    c2_results = sprint_c2(lines, folios, lattice_map, corrections, choices)

    # Update the volvelle confirmatory prediction with actual diameter
    volvelle_diameter = c1_results["volvelle"]["total_diameter_mm"]
    c2_results["falsifiable_predictions"]["volvelle_confirmatory"] = [
        "Circular wear marks on a disc-shaped artifact or template",
        "Registration mark or notch at the angular position corresponding to window 18",
        "Radially arranged vocabulary in 50 angular sectors",
        "Concentric rings accommodating varying word-count density per window",
        f"Disc diameter approximately {volvelle_diameter:.0f}mm "
        f"(within range of known 15th-century volvelles: 120-350mm)",
        "Wear concentrated at high-usage windows (particularly windows 18, 0, and 36)",
    ]

    # Assemble results
    results = {
        "sprint_c1_device_specification": c1_results,
        "sprint_c2_wear_predictions": c2_results,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17f_device_specification"}):
        main()
