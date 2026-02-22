#!/usr/bin/env python3
"""Phase 20, Sprint 4: Non-Circular Device Forms.

4.1: Sliding strip (dual-strip linear device)
4.2: Folding tabula (accordion-fold card)
4.3: Cipher grille / mask (aperture card over master grid)
4.4: Tabula + codebook baseline (formalize Sprint 1 result)
4.5: Comparative ranking and historical plausibility

Dimensions the production tool as linear/flat device forms that avoid
the angular sector bottleneck inherent in disc-based (volvelle) designs.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402

console = Console()

NUM_WINDOWS = 50
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
CODEBOOK_PATH = project_root / "results/data/phase20_state_machine/codebook_architecture.json"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase20_state_machine/linear_devices.json"

# Physical constants (same as Sprint 1)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
LINE_SPACING_MM = 2.0
WORD_SPACING_MM = 3.0
MARGIN_MM = 5.0

# Per-position footprint (from Sprint 1)
LABEL_WIDTH_MM = 2 * GLYPH_WIDTH_MM      # "18" = 2 chars
CORR_WIDTH_MM = 3 * GLYPH_WIDTH_MM       # "+13" = 3 chars
SEP_MM = 2.0
POSITION_WIDTH_MM = LABEL_WIDTH_MM + CORR_WIDTH_MM + SEP_MM + 2 * MARGIN_MM  # 32mm
POSITION_HEIGHT_MM = GLYPH_HEIGHT_MM + 2 * MARGIN_MM  # 15mm

# Average word width for vocabulary display
AVG_WORD_CHARS = 5  # typical Voynichese word length
AVG_WORD_WIDTH_MM = AVG_WORD_CHARS * GLYPH_WIDTH_MM + WORD_SPACING_MM  # 23mm

# Size thresholds
MAX_PORTABLE_MM = 200
MAX_HANDHELD_MM = 300
MAX_DESKTOP_MM = 500

# Historical devices (extended for linear forms)
HISTORICAL_DEVICES = {
    "Alberti cipher disc (1467)": {
        "type": "volvelle", "max_dim_mm": 120,
    },
    "Llull Ars Magna (c.1305)": {
        "type": "volvelle", "max_dim_mm": 200,
    },
    "Apian Astronomicum (1540)": {
        "type": "volvelle", "max_dim_mm": 350,
    },
    "Trithemius tabula recta (1508)": {
        "type": "tabula", "max_dim_mm": 250,
    },
    "Rebatello cipher strip (c.1470)": {
        "type": "strip", "max_dim_mm": 300,
    },
    "Logarithmic slide rule (17c)": {
        "type": "strip", "max_dim_mm": 300,
    },
    "Portolan chart foldout (15c)": {
        "type": "fold", "max_dim_mm": 500, "folded_mm": 125,
    },
    "Cardano grille (1550)": {
        "type": "grille", "max_dim_mm": 200,
    },
    "Typical playing card (15c)": {
        "type": "card", "max_dim_mm": 120,
    },
    "Vigenere table (1586)": {
        "type": "tabula", "max_dim_mm": 200,
    },
}


# ── Helpers ───────────────────────────────────────────────────────────

def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def load_codebook_results(path):
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data)


def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    wc_key = ("reordered_window_contents" if "reordered_window_contents" in results
              else "window_contents")
    return {int(k): v for k, v in results[wc_key].items()}


def size_category(max_dim_mm):
    if max_dim_mm <= MAX_PORTABLE_MM:
        return "PORTABLE"
    if max_dim_mm <= MAX_HANDHELD_MM:
        return "HANDHELD"
    if max_dim_mm <= MAX_DESKTOP_MM:
        return "DESKTOP"
    return "OVERSIZED"


# ── 4.1: Sliding Strip ───────────────────────────────────────────────

def sprint_4_1(corrections):
    """Dimension a dual-strip sliding device."""
    console.rule("[bold blue]4.1: Sliding Strip Device")

    # Fixed strip: 50 positions in a line
    total_length = NUM_WINDOWS * POSITION_WIDTH_MM
    strip_height = POSITION_HEIGHT_MM

    # Sliding cursor strip: narrow pointer
    cursor_width = POSITION_WIDTH_MM + 2 * MARGIN_MM
    cursor_height = strip_height + 2 * MARGIN_MM

    # Total assembled device
    device_width = total_length
    device_height = strip_height + cursor_height + MARGIN_MM

    console.print(f"  Fixed strip: {total_length:.0f} × {strip_height:.0f} mm")
    console.print(f"  Cursor: {cursor_width:.0f} × {cursor_height:.0f} mm")
    console.print(f"  Assembled: {device_width:.0f} × {device_height:.0f} mm")
    console.print(f"  Category: {size_category(device_width)} (unfolded)")

    # Fold variants
    fold_configs = []
    for n_folds in [2, 4, 5, 8, 10]:
        folded_length = math.ceil(total_length / n_folds)
        # Each fold doubles the stack height; the cursor slides along one panel
        folded_height = device_height  # height stays the same; width reduces
        # But panels stack, so effective thickness increases (not modeled)
        panels = n_folds

        config = {
            "folds": n_folds,
            "panels": panels,
            "folded_length_mm": folded_length,
            "folded_width_mm": round(device_height),
            "max_dim_mm": max(folded_length, round(device_height)),
            "category": size_category(max(folded_length, round(device_height))),
        }
        fold_configs.append(config)

    table = Table(title="Sliding Strip Fold Variants")
    table.add_column("Folds", justify="right")
    table.add_column("Folded Size", justify="right")
    table.add_column("Max Dim", justify="right")
    table.add_column("Category", style="bold")

    for fc in fold_configs:
        color = "green" if fc["category"] in ("PORTABLE", "HANDHELD") else "yellow"
        table.add_row(
            str(fc["folds"]),
            f"{fc['folded_length_mm']} × {fc['folded_width_mm']} mm",
            f"{fc['max_dim_mm']}mm",
            f"[{color}]{fc['category']}[/{color}]",
        )
    console.print(table)

    # Best fold: smallest max dimension
    best_fold = min(fold_configs, key=lambda c: c["max_dim_mm"])

    # Historical comparison
    console.print(f"\n  Best fold: {best_fold['folds']}-fold → "
                  f"{best_fold['folded_length_mm']} × {best_fold['folded_width_mm']} mm")
    console.print(f"  vs Rebatello cipher strip (300mm): "
                  f"{best_fold['max_dim_mm'] / 300:.2f}×")

    verdict = "PLAUSIBLE" if best_fold["max_dim_mm"] <= MAX_HANDHELD_MM else "MARGINAL"
    console.print(f"  Verdict: [bold]{verdict}[/bold]")

    return {
        "unfolded_length_mm": round(total_length),
        "unfolded_height_mm": round(device_height),
        "strip_height_mm": round(strip_height),
        "cursor_dims_mm": {"width": round(cursor_width), "height": round(cursor_height)},
        "fold_variants": fold_configs,
        "best_fold": best_fold,
        "historical_parallel": "Rebatello cipher strip (c.1470), slide rules",
        "verdict": verdict,
    }


# ── 4.2: Folding Tabula ──────────────────────────────────────────────

def sprint_4_2(window_contents, corrections):
    """Dimension an accordion-fold card device."""
    console.rule("[bold blue]4.2: Folding Tabula")

    panel_counts = [2, 4, 5, 6, 8, 10]
    configs = []

    for n_panels in panel_counts:
        windows_per_panel = math.ceil(NUM_WINDOWS / n_panels)
        # Each panel: a grid of windows
        # Layout: windows arranged in rows within each panel
        panel_cols = min(windows_per_panel, 5)  # max 5 columns per panel
        panel_rows = math.ceil(windows_per_panel / panel_cols)

        # State-only: just window label + correction per cell
        state_panel_width = panel_cols * POSITION_WIDTH_MM + 2 * MARGIN_MM
        state_panel_height = panel_rows * POSITION_HEIGHT_MM + 2 * MARGIN_MM

        # Annotated: label + correction + top-3 words per cell
        word_line_height = GLYPH_HEIGHT_MM + LINE_SPACING_MM
        annotated_cell_height = POSITION_HEIGHT_MM + 3 * word_line_height
        ann_panel_height = panel_rows * annotated_cell_height + 2 * MARGIN_MM

        # Folded: one panel visible at a time
        # Unfolded: all panels side by side
        state_unfolded_width = n_panels * state_panel_width
        ann_unfolded_width = n_panels * state_panel_width  # same width, taller

        config = {
            "panels": n_panels,
            "windows_per_panel": windows_per_panel,
            "panel_grid": f"{panel_rows}x{panel_cols}",
            "state_only": {
                "panel_width_mm": round(state_panel_width),
                "panel_height_mm": round(state_panel_height),
                "folded_max_dim_mm": max(round(state_panel_width),
                                         round(state_panel_height)),
                "unfolded_width_mm": round(state_unfolded_width),
                "category": size_category(
                    max(round(state_panel_width), round(state_panel_height))),
            },
            "annotated": {
                "panel_width_mm": round(state_panel_width),
                "panel_height_mm": round(ann_panel_height),
                "folded_max_dim_mm": max(round(state_panel_width),
                                         round(ann_panel_height)),
                "unfolded_width_mm": round(ann_unfolded_width),
                "category": size_category(
                    max(round(state_panel_width), round(ann_panel_height))),
            },
        }
        configs.append(config)

    # Display state-only variants
    table = Table(title="Folding Tabula: State-Only")
    table.add_column("Panels", justify="right")
    table.add_column("Win/Panel", justify="right")
    table.add_column("Grid", justify="right")
    table.add_column("Panel Size", justify="right")
    table.add_column("Max Dim", justify="right")
    table.add_column("Category", style="bold")

    for c in configs:
        s = c["state_only"]
        color = "green" if s["category"] in ("PORTABLE", "HANDHELD") else "yellow"
        table.add_row(
            str(c["panels"]),
            str(c["windows_per_panel"]),
            c["panel_grid"],
            f"{s['panel_width_mm']} × {s['panel_height_mm']} mm",
            f"{s['folded_max_dim_mm']}mm",
            f"[{color}]{s['category']}[/{color}]",
        )
    console.print(table)

    # Display annotated variants
    table2 = Table(title="Folding Tabula: Annotated (+3 words)")
    table2.add_column("Panels", justify="right")
    table2.add_column("Panel Size", justify="right")
    table2.add_column("Max Dim", justify="right")
    table2.add_column("Category", style="bold")

    for c in configs:
        a = c["annotated"]
        color = "green" if a["category"] in ("PORTABLE", "HANDHELD") else "yellow"
        table2.add_row(
            str(c["panels"]),
            f"{a['panel_width_mm']} × {a['panel_height_mm']} mm",
            f"{a['folded_max_dim_mm']}mm",
            f"[{color}]{a['category']}[/{color}]",
        )
    console.print(table2)

    # Best: smallest folded max dimension for state-only
    best_state = min(configs, key=lambda c: c["state_only"]["folded_max_dim_mm"])
    best_ann = min(configs, key=lambda c: c["annotated"]["folded_max_dim_mm"])

    console.print(f"\n  Best state-only: {best_state['panels']}-panel → "
                  f"{best_state['state_only']['panel_width_mm']} × "
                  f"{best_state['state_only']['panel_height_mm']} mm folded")
    console.print(f"  Best annotated: {best_ann['panels']}-panel → "
                  f"{best_ann['annotated']['panel_width_mm']} × "
                  f"{best_ann['annotated']['panel_height_mm']} mm folded")

    verdict = ("PLAUSIBLE"
               if best_state["state_only"]["folded_max_dim_mm"] <= MAX_HANDHELD_MM
               else "MARGINAL")
    console.print(f"  Verdict: [bold]{verdict}[/bold]")

    return {
        "configurations": configs,
        "best_state_only": {
            "panels": best_state["panels"],
            "folded_dims_mm": {
                "width": best_state["state_only"]["panel_width_mm"],
                "height": best_state["state_only"]["panel_height_mm"],
            },
            "max_dim_mm": best_state["state_only"]["folded_max_dim_mm"],
        },
        "best_annotated": {
            "panels": best_ann["panels"],
            "folded_dims_mm": {
                "width": best_ann["annotated"]["panel_width_mm"],
                "height": best_ann["annotated"]["panel_height_mm"],
            },
            "max_dim_mm": best_ann["annotated"]["folded_max_dim_mm"],
        },
        "historical_parallel": "Portolan chart foldouts, astronomical tables",
        "verdict": verdict,
    }


# ── 4.3: Cipher Grille ───────────────────────────────────────────────

def sprint_4_3():
    """Dimension a cipher grille / mask system."""
    console.rule("[bold blue]4.3: Cipher Grille / Mask")

    # Master grid: 10 rows × 5 cols = 50 cells (one per window)
    grid_rows, grid_cols = 10, 5
    grid_width = grid_cols * POSITION_WIDTH_MM + 2 * MARGIN_MM
    grid_height = grid_rows * POSITION_HEIGHT_MM + 2 * MARGIN_MM

    console.print(f"  Master grid: {grid_rows}×{grid_cols} = "
                  f"{grid_rows * grid_cols} cells")
    console.print(f"  Grid size: {grid_width:.0f} × {grid_height:.0f} mm")

    # Grille card: same outer dimensions, with apertures
    # With 4 rotational positions (0/90/180/270), each reveals ~12-13 cells
    # But 10×5 is not square — rotation doesn't map cleanly
    # Alternative: 4 separate grille cards, each showing ~12-13 windows
    # Or: sliding grille (shift horizontally/vertically)

    # For a non-square grid, use shift positions instead of rotation
    # Shift by (row_offset, col_offset) to select different subsets
    # With a 5×5 aperture pattern on a 10×5 grid:
    #   2 vertical positions × 1 horizontal = 2 positions (25 windows each)
    # With a 5×3 aperture on 10×5:
    #   2 vertical × 2 horizontal = 4 positions (15 cells each, 60 total, 50 used)

    aperture_configs = [
        {
            "name": "2-position (5×5 aperture)",
            "aperture_rows": 5, "aperture_cols": 5,
            "positions": 2,
            "windows_per_position": 25,
            "total_addressable": 50,
        },
        {
            "name": "4-position (5×3 aperture)",
            "aperture_rows": 5, "aperture_cols": 3,
            "positions": 4,
            "windows_per_position": 15,
            "total_addressable": 60,  # 10 cells unused
        },
    ]

    table = Table(title="Cipher Grille Configurations")
    table.add_column("Config")
    table.add_column("Positions", justify="right")
    table.add_column("Win/Position", justify="right")
    table.add_column("Total", justify="right")

    for ac in aperture_configs:
        table.add_row(
            ac["name"],
            str(ac["positions"]),
            str(ac["windows_per_position"]),
            str(ac["total_addressable"]),
        )
    console.print(table)

    max_dim = max(grid_width, grid_height)
    console.print("\n  Components: 2 (master grid + grille card)")
    console.print(f"  Max dimension: {max_dim:.0f}mm")
    console.print(f"  Category: {size_category(max_dim)}")
    console.print(f"  vs Cardano grille (200mm): {max_dim / 200:.2f}×")

    # Assessment
    console.print("\n  Note: Grille adds mechanical complexity (alignment, "
                  "rotation/shifting)")
    console.print("  without reducing information content vs a simple tabula.")
    console.print("  The grille concept is historically authentic but "
                  "over-engineered for state tracking.")

    verdict = "MARGINAL"
    console.print(f"  Verdict: [bold]{verdict}[/bold]")

    return {
        "master_grid": {
            "rows": grid_rows,
            "cols": grid_cols,
            "width_mm": round(grid_width),
            "height_mm": round(grid_height),
        },
        "aperture_configs": aperture_configs,
        "max_dim_mm": round(max_dim),
        "components": 2,
        "category": size_category(max_dim),
        "historical_parallel": "Cardano grille (1550)",
        "verdict": verdict,
        "note": "Over-engineered for state tracking; adds complexity "
                "without benefit vs simple tabula",
    }


# ── 4.4: Tabula + Codebook Baseline ──────────────────────────────────

def sprint_4_4(codebook_data):
    """Formalize Sprint 1 tabula + codebook as baseline."""
    console.rule("[bold blue]4.4: Tabula + Codebook Baseline")

    state_dev = codebook_data["state_indicator_device"]
    codebook = codebook_data["codebook_estimation"]

    tabula = state_dev["tabula"]
    tab_max = max(tabula["width_mm"], tabula["height_mm"])

    console.print(f"  Tabula (state indicator): {tabula['width_mm']} × "
                  f"{tabula['height_mm']} mm ({tabula['grid']} grid)")
    console.print(f"  Codebook: {codebook['total_pages']} pages, "
                  f"{codebook['total_folios']} folios, "
                  f"{codebook.get('n_quires', '?')} quires")
    console.print("  Components: 2 (tabula card + codebook booklet)")
    console.print(f"  Tabula max dimension: {tab_max}mm → "
                  f"{size_category(tab_max)}")

    # Workflow: read tabula for current window state → open codebook
    # to that window's page → select word → write
    console.print("\n  Workflow: read state from card → consult codebook → "
                  "select word → write")
    console.print("  Consultation rate: 100% (all words require codebook)")
    console.print(f"  Codebook vs Voynich MS: "
                  f"{codebook['total_pages'] / 232:.2f}× "
                  "(smaller than the manuscript itself)")

    verdict = "PLAUSIBLE"
    console.print(f"  Verdict: [bold green]{verdict}[/bold green]")

    return {
        "tabula_dims_mm": {"width": tabula["width_mm"], "height": tabula["height_mm"]},
        "tabula_grid": tabula["grid"],
        "tabula_max_dim_mm": tab_max,
        "codebook_pages": codebook["total_pages"],
        "codebook_folios": codebook["total_folios"],
        "components": 2,
        "consultation_rate": 1.0,
        "category": size_category(tab_max),
        "historical_parallel": "Alberti disc + external alphabet, "
                               "Trithemius key table + word codebook",
        "verdict": verdict,
    }


# ── 4.5: Comparative Ranking ─────────────────────────────────────────

def sprint_4_5(strip, fold, grille, tabula_cb):
    """Rank all four device forms."""
    console.rule("[bold blue]4.5: Comparative Ranking")

    devices = [
        {
            "name": "Sliding strip",
            "form": "strip",
            "max_dim_mm": strip["best_fold"]["max_dim_mm"],
            "components": 2,
            "verdict": strip["verdict"],
            "size_score": _size_score(strip["best_fold"]["max_dim_mm"]),
            "size_note": (f"Best fold: {strip['best_fold']['folds']}-fold, "
                          f"{strip['best_fold']['max_dim_mm']}mm"),
            "practicality_score": 0.5,
            "practicality_note": ("Requires sliding action; cursor can slip; "
                                  "fold adds bulk but stays compact"),
            "precedent_score": 0.75,
            "precedent_note": "Direct parallel: Rebatello cipher strip (c.1470)",
            "durability_score": 0.50,
            "durability_note": "Moving cursor part; folds wear over time",
        },
        {
            "name": "Folding tabula (state-only)",
            "form": "fold",
            "max_dim_mm": fold["best_state_only"]["max_dim_mm"],
            "components": 1,
            "verdict": fold["verdict"],
            "size_score": _size_score(fold["best_state_only"]["max_dim_mm"]),
            "size_note": (f"Best: {fold['best_state_only']['panels']}-panel, "
                          f"{fold['best_state_only']['max_dim_mm']}mm folded"),
            "practicality_score": 0.80,
            "practicality_note": ("Single object; unfold to locate window; "
                                  "direct read; no moving parts except folds"),
            "precedent_score": 0.75,
            "precedent_note": "Portolan chart foldouts, astronomical tables (15c)",
            "durability_score": 0.70,
            "durability_note": "Folds wear but no loose parts; single sheet",
        },
        {
            "name": "Folding tabula (annotated)",
            "form": "fold",
            "max_dim_mm": fold["best_annotated"]["max_dim_mm"],
            "components": 1,
            "verdict": fold["verdict"],
            "size_score": _size_score(fold["best_annotated"]["max_dim_mm"]),
            "size_note": (f"Best: {fold['best_annotated']['panels']}-panel, "
                          f"{fold['best_annotated']['max_dim_mm']}mm folded"),
            "practicality_score": 0.85,
            "practicality_note": ("Top-3 words on device reduces codebook "
                                  "consultations; direct read for common words"),
            "precedent_score": 0.75,
            "precedent_note": "Annotated reference tables common in period",
            "durability_score": 0.65,
            "durability_note": "Taller panels; more fold wear",
        },
        {
            "name": "Cipher grille",
            "form": "grille",
            "max_dim_mm": grille["max_dim_mm"],
            "components": grille["components"],
            "verdict": grille["verdict"],
            "size_score": _size_score(grille["max_dim_mm"]),
            "size_note": f"Grid: {grille['max_dim_mm']}mm",
            "practicality_score": 0.30,
            "practicality_note": ("Two-piece system; alignment critical; "
                                  "no advantage over simple tabula for state tracking"),
            "precedent_score": 0.50,
            "precedent_note": "Cardano grille (1550); slightly post-Voynich date",
            "durability_score": 0.50,
            "durability_note": "Two loose pieces; aperture alignment wears",
        },
        {
            "name": "Tabula + codebook",
            "form": "tabula",
            "max_dim_mm": tabula_cb["tabula_max_dim_mm"],
            "components": tabula_cb["components"],
            "verdict": tabula_cb["verdict"],
            "size_score": _size_score(tabula_cb["tabula_max_dim_mm"]),
            "size_note": (f"Tabula: {tabula_cb['tabula_max_dim_mm']}mm; "
                          f"codebook: {tabula_cb['codebook_pages']}pp separate"),
            "practicality_score": 0.65,
            "practicality_note": ("Two objects but workflow is natural: "
                                  "read card, consult book. 100% consultation rate."),
            "precedent_score": 1.0,
            "precedent_note": ("Direct parallel: Alberti disc + external alphabet "
                               "(1467), Trithemius key + codebook (1499)"),
            "durability_score": 0.80,
            "durability_note": "Rigid card + bound booklet; highly durable",
        },
    ]

    # Compute combined scores
    w_size, w_prac, w_prec, w_dur = 0.30, 0.30, 0.25, 0.15
    for d in devices:
        d["combined_score"] = round(
            d["size_score"] * w_size
            + d["practicality_score"] * w_prac
            + d["precedent_score"] * w_prec
            + d["durability_score"] * w_dur,
            4,
        )

    # Sort by combined score
    devices.sort(key=lambda d: d["combined_score"], reverse=True)

    # Display ranking
    table = Table(title="Device Form Ranking")
    table.add_column("Rank", justify="right", style="bold")
    table.add_column("Device")
    table.add_column("Max Dim", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Pract.", justify="right")
    table.add_column("Preced.", justify="right")
    table.add_column("Durab.", justify="right")
    table.add_column("Combined", justify="right", style="bold")
    table.add_column("Verdict")

    for i, d in enumerate(devices):
        v_color = {"PLAUSIBLE": "green", "MARGINAL": "yellow",
                   "IMPLAUSIBLE": "red"}.get(d["verdict"], "white")
        table.add_row(
            str(i + 1),
            d["name"],
            f"{d['max_dim_mm']}mm",
            f"{d['size_score']:.2f}",
            f"{d['practicality_score']:.2f}",
            f"{d['precedent_score']:.2f}",
            f"{d['durability_score']:.2f}",
            f"{d['combined_score']:.4f}",
            f"[{v_color}]{d['verdict']}[/{v_color}]",
        )
    console.print(table)

    recommended = devices[0]
    console.print(f"\n  [bold green]Recommended:[/bold green] "
                  f"{recommended['name']} (score: {recommended['combined_score']:.4f})")
    console.print(f"  {recommended['size_note']}")
    console.print(f"  {recommended['practicality_note']}")

    # Count plausible
    n_plausible = sum(1 for d in devices if d["verdict"] == "PLAUSIBLE")
    console.print(f"\n  PLAUSIBLE devices: {n_plausible}/{len(devices)}")

    return {
        "scores": [
            {
                "device": d["name"],
                "form": d["form"],
                "max_dim_mm": d["max_dim_mm"],
                "components": d["components"],
                "size_score": d["size_score"],
                "practicality_score": d["practicality_score"],
                "precedent_score": d["precedent_score"],
                "durability_score": d["durability_score"],
                "combined_score": d["combined_score"],
                "verdict": d["verdict"],
                "size_note": d["size_note"],
                "practicality_note": d["practicality_note"],
                "precedent_note": d["precedent_note"],
                "durability_note": d["durability_note"],
            }
            for d in devices
        ],
        "recommended": recommended["name"],
        "recommended_score": recommended["combined_score"],
        "n_plausible": n_plausible,
        "weights": {
            "size": w_size,
            "practicality": w_prac,
            "precedent": w_prec,
            "durability": w_dur,
        },
    }


def _size_score(max_dim_mm):
    """Score a device by max dimension."""
    if max_dim_mm <= MAX_PORTABLE_MM:
        return 1.0
    if max_dim_mm <= MAX_HANDHELD_MM:
        return 0.5
    if max_dim_mm <= MAX_DESKTOP_MM:
        return 0.25
    return 0.0


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 20, Sprint 4: Non-Circular Device Forms")

    # Load data
    console.print("Loading data...")
    corrections = load_corrections(OFFSETS_PATH)
    codebook_data = load_codebook_results(CODEBOOK_PATH)
    window_contents = load_palette(PALETTE_PATH)
    console.print(f"  Corrections: {len(corrections)} windows")
    console.print("  Codebook data loaded from Sprint 1")

    # 4.1: Sliding strip
    s4_1 = sprint_4_1(corrections)

    # 4.2: Folding tabula
    s4_2 = sprint_4_2(window_contents, corrections)

    # 4.3: Cipher grille
    s4_3 = sprint_4_3()

    # 4.4: Tabula + codebook baseline
    s4_4 = sprint_4_4(codebook_data)

    # 4.5: Comparative ranking
    s4_5 = sprint_4_5(s4_1, s4_2, s4_3, s4_4)

    # Assemble results
    results = {
        "sliding_strip": s4_1,
        "folding_tabula": s4_2,
        "cipher_grille": s4_3,
        "tabula_codebook": s4_4,
        "ranking": s4_5,
    }

    # Sanitize numpy types
    def _sanitize(obj):
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

    results = _sanitize(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_20c_linear_devices"}):
        main()
