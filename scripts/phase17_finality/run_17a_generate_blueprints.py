#!/usr/bin/env python3
"""Phase 17A: Physical Blueprint Generation.

Generates the 10x5 physical layout of the palette sheets, canonical SVG
blueprints (plate + volvelle rings), and the 12 mask stop-settings.
"""

import json
import math
import sys
from html import escape
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_DIR = project_root / "results/visuals/phase17_finality"
console = Console()


def _window_label(words: list[str], max_chars: int = 8) -> str:
    if not words:
        return "EMPTY"
    return words[0][:max_chars]


def _write_palette_plate_svg(window_contents: dict[str, list[str]], out_path: Path) -> None:
    """Render a 10x5 plate layout as a single SVG for publication and print."""
    cols = 10
    rows = 5
    cell_w = 170
    cell_h = 95
    pad = 30
    width = (cols * cell_w) + (2 * pad)
    height = (rows * cell_h) + (2 * pad) + 40

    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{pad}" y="22" font-family="sans-serif" font-size="18" font-weight="bold">'
        "Voynich Engine Canonical Palette Plate (10x5)</text>",
    ]

    for r in range(rows):
        for c in range(cols):
            win_id = (r * cols) + c
            words = window_contents.get(str(win_id), [])
            label = escape(_window_label(words, max_chars=10))
            count = len(words)

            x = pad + (c * cell_w)
            y = pad + (r * cell_h) + 10

            svg.append(
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                'fill="none" stroke="black" stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{x + 8}" y="{y + 20}" font-family="monospace" '
                'font-size="12" font-weight="bold">'
                f"W{win_id:02d}</text>"
            )
            svg.append(
                f'<text x="{x + 8}" y="{y + 42}" font-family="monospace" font-size="12">'
                f"top: {label}</text>"
            )
            svg.append(
                f'<text x="{x + 8}" y="{y + 64}" font-family="monospace" font-size="12">'
                f"size: {count}</text>"
            )

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def _create_ring_svg(
    tokens: list[str],
    ring_name: str,
    inner_r: int,
    outer_r: int,
    *,
    font_size: int = 11,
) -> str:
    """Render a single 10-sector donut ring for physical mockups."""
    sectors = len(tokens)
    size = (outer_r * 2) + 140
    cx = size // 2
    cy = size // 2
    step_deg = 360.0 / sectors
    label_r = inner_r + ((outer_r - inner_r) * 0.52)

    svg = [
        f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="black" stroke-width="2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="black" stroke-width="1"/>',
    ]

    for i, token in enumerate(tokens):
        start_deg = (i * step_deg) - 90.0
        a = math.radians(start_deg)
        x1 = cx + (inner_r * math.cos(a))
        y1 = cy + (inner_r * math.sin(a))
        x2 = cx + (outer_r * math.cos(a))
        y2 = cy + (outer_r * math.sin(a))
        svg.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            'stroke="gray" stroke-width="1"/>'
        )

        mid_deg = start_deg + (step_deg / 2.0)
        mid = math.radians(mid_deg)
        tx = cx + (label_r * math.cos(mid))
        ty = cy + (label_r * math.sin(mid))
        rot = mid_deg + 90.0
        svg.append(
            f'<text x="{tx:.2f}" y="{ty:.2f}" font-family="monospace" font-size="{font_size}" '
            'text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate({rot:.2f},{tx:.2f},{ty:.2f})">{escape(token)}</text>'
        )

    svg.append(
        f'<text x="{cx}" y="{cy + outer_r + 32}" font-family="sans-serif" '
        f'font-size="18" text-anchor="middle">{escape(ring_name)}</text>'
    )
    svg.append("</svg>")
    return "\n".join(svg)


def _write_ring_svgs(window_contents: dict[str, list[str]], out_dir: Path) -> list[Path]:
    """Create five canonical rings from the 10x5 window layout.

    Rings are size-graded so they can be nested physically (outer -> inner).
    """
    generated: list[Path] = []
    # (inner_r, outer_r, label_chars, font_size)
    ring_specs = [
        (270, 340, 9, 11),
        (215, 265, 8, 10),
        (160, 210, 7, 9),
        (105, 155, 6, 8),
        (50, 100, 5, 7),
    ]
    for row_idx in range(5):
        start = row_idx * 10
        stop = start + 10
        inner_r, outer_r, label_chars, font_size = ring_specs[row_idx]
        tokens = [
            _window_label(window_contents.get(str(win_id), []), max_chars=label_chars)
            for win_id in range(start, stop)
        ]
        ring_name = f"Canonical Ring {row_idx + 1} (W{start:02d}-W{stop - 1:02d})"
        svg = _create_ring_svg(
            tokens,
            ring_name,
            inner_r=inner_r,
            outer_r=outer_r,
            font_size=font_size,
        )
        out_path = out_dir / f"volvelle_canonical_ring_{row_idx + 1}.svg"
        out_path.write_text(svg, encoding="utf-8")
        generated.append(out_path)
    return generated


def _write_concentric_assembly_svg(window_contents: dict[str, list[str]], out_path: Path) -> None:
    """Render all five rings in one concentric SVG for assembly reference."""
    size = 980
    cx = size // 2
    cy = size // 2
    # (row_idx, inner_r, outer_r, label_chars, font_size)
    specs = [
        (0, 360, 430, 9, 10),
        (1, 290, 350, 8, 9),
        (2, 220, 280, 7, 8),
        (3, 150, 210, 6, 7),
        (4, 80, 140, 5, 7),
    ]

    svg = [
        f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="28" font-family="sans-serif" font-size="20" font-weight="bold">'
        "Voynich Engine Concentric Volvelle (Assembly Reference)</text>",
    ]

    for row_idx, inner_r, outer_r, label_chars, font_size in specs:
        start = row_idx * 10
        stop = start + 10
        tokens = [
            _window_label(window_contents.get(str(win_id), []), max_chars=label_chars)
            for win_id in range(start, stop)
        ]
        step_deg = 36.0
        label_r = inner_r + ((outer_r - inner_r) * 0.52)

        svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="black" stroke-width="1.5"/>'
        )
        svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="black" stroke-width="1"/>'
        )

        for i, token in enumerate(tokens):
            start_deg = (i * step_deg) - 90.0
            a = math.radians(start_deg)
            x1 = cx + (inner_r * math.cos(a))
            y1 = cy + (inner_r * math.sin(a))
            x2 = cx + (outer_r * math.cos(a))
            y2 = cy + (outer_r * math.sin(a))
            svg.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                'stroke="gray" stroke-width="0.8"/>'
            )

            mid_deg = start_deg + (step_deg / 2.0)
            mid = math.radians(mid_deg)
            tx = cx + (label_r * math.cos(mid))
            ty = cy + (label_r * math.sin(mid))
            rot = mid_deg + 90.0
            svg.append(
                f'<text x="{tx:.2f}" y="{ty:.2f}" font-family="monospace" font-size="{font_size}" '
                'text-anchor="middle" dominant-baseline="middle" '
                f'transform="rotate({rot:.2f},{tx:.2f},{ty:.2f})">{escape(token)}</text>'
            )

        tag_r = outer_r + 14
        tag_x = cx
        tag_y = cy - tag_r
        svg.append(
            f'<text x="{tag_x}" y="{tag_y}" font-family="sans-serif" font-size="11" '
            f'text-anchor="middle">R{row_idx + 1} (W{start:02d}-W{stop - 1:02d})</text>'
        )

    # Center axle reference hole
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="black" stroke-width="1.2"/>')
    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def main():
    console.print("[bold yellow]Phase 17A: Physical Blueprint Generation[/bold yellow]")

    if not PALETTE_PATH.exists():
        console.print("[red]Error: Palette grid not found.[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    window_contents = data["window_contents"]

    # 2. Generate 10x5 Palette Sheet (The physical arrangement of windows)
    sheet = []
    window_stats = []
    for r in range(5):
        row = []
        for c in range(10):
            win_id = str(r * 10 + c)
            words = window_contents.get(win_id, [])
            label = words[0] if words else "EMPTY"
            row.append(f"Win {win_id:2} [{label[:8]:8}]")
            window_stats.append({"window_id": int(win_id), "word_count": len(words)})
        sheet.append(" | ".join(row))

    palette_grid = "\n".join(sheet)
    avg_words = (
        sum(w["word_count"] for w in window_stats) / len(window_stats)
        if window_stats else 0
    )

    # 3. Save Blueprint Artifacts
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "palette_layout.txt", "w") as f:
        f.write("VOYNICH ENGINE: 10x5 PALETTE SHEET LAYOUT\n")
        f.write("=" * 80 + "\n\n")
        f.write(palette_grid)
        f.write(f"\n\n{'=' * 80}\n")
        f.write(f"Each cell contains a stack of word-strips (avg {avg_words:.0f} per window).\n")

    # 4. Generate Mask Stop-Settings
    mask_report = ["VOYNICH ENGINE: 12-SETTING MASK CONFIGURATIONS", "=" * 50, ""]
    for m in range(12):
        mask_report.append(f"Setting {m:2}: Index Shift +{m} windows clockwise/down.")

    with open(OUTPUT_DIR / "mask_settings.txt", "w") as f:
        f.write("\n".join(mask_report))

    # 5. Canonical SVG blueprints (publication-safe visual artifacts)
    plate_svg = OUTPUT_DIR / "palette_plate.svg"
    _write_palette_plate_svg(window_contents, plate_svg)
    ring_svgs = _write_ring_svgs(window_contents, OUTPUT_DIR)
    assembly_svg = OUTPUT_DIR / "volvelle_canonical_assembly.svg"
    _write_concentric_assembly_svg(window_contents, assembly_svg)

    # 6. Save provenance
    artifacts = [
        str(OUTPUT_DIR / "palette_layout.txt"),
        str(OUTPUT_DIR / "mask_settings.txt"),
        str(plate_svg),
        str(assembly_svg),
    ] + [str(path) for path in ring_svgs]
    results = {
        "num_windows": len(window_contents),
        "total_words": sum(w["word_count"] for w in window_stats),
        "avg_words_per_window": avg_words,
        "window_sizes": window_stats,
        "artifacts": artifacts,
    }
    ProvenanceWriter.save_results(
        results,
        project_root / "results/data/phase17_finality/blueprint_metadata.json"
    )

    console.print(f"\n[green]Success! Physical blueprints generated in:[/green] {OUTPUT_DIR}")
    console.print(
        f"  Windows: {len(window_contents)}, "
        f"Total Words: {results['total_words']}, "
        f"Avg/Window: {avg_words:.0f}"
    )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17a_generate_blueprints"}):
        main()
