#!/usr/bin/env python3
"""Phase 17A: Physical Blueprint Generation (Tabula + Codebook Model).

Generates the canonical blueprint artifacts for the Voynich production tool
as established by Phase 20: a flat tabula (state tracker card) paired with
a vocabulary codebook organized by window number.

Artifacts generated:
  1. tabula_card.svg       — 170x160mm state tracker with 50 windows + correction offsets
  2. palette_plate.svg     — 10x5 palette plate with vocabulary labels and offsets
  3. codebook_index.svg    — Codebook section index (W0-W49 with word counts and page spans)
  4. palette_layout.txt    — Text reference for the palette layout
  5. correction_offsets.txt — Per-window correction offset table

Historical volvelle ring artifacts are preserved in historical/ subdirectory.
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
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
OUTPUT_DIR = project_root / "results/visuals/phase17_finality"
HISTORICAL_DIR = OUTPUT_DIR / "historical"
console = Console()


def _load_corrections() -> dict[int, int]:
    """Load per-window correction offsets from Phase 14 canonical offsets."""
    with open(OFFSETS_PATH) as f:
        data = json.load(f)
    raw = data["results"]["corrections"]
    return {int(k): int(v) for k, v in raw.items()}


def _window_label(words: list[str], max_chars: int = 8) -> str:
    if not words:
        return "EMPTY"
    return words[0][:max_chars]


# ---------------------------------------------------------------------------
# 1. Tabula Card SVG (the physical state-tracker card)
# ---------------------------------------------------------------------------

def _write_tabula_card_svg(
    corrections: dict[int, int],
    window_sizes: dict[str, int],
    out_path: Path,
) -> None:
    """Render the 170x160mm tabula as a 10x5 card with window IDs and offsets.

    This is the physical card a scribe would consult to track state transitions.
    Each cell shows: window number, correction offset, and vocabulary size.
    """
    cols = 10
    rows = 5
    cell_w = 100
    cell_h = 80
    pad = 30
    width = (cols * cell_w) + (2 * pad)
    height = (rows * cell_h) + (2 * pad) + 60

    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="#faf8f0"/>',
        f'<text x="{width // 2}" y="24" font-family="sans-serif" font-size="16" '
        'font-weight="bold" text-anchor="middle">'
        'Voynich Tabula Card (170 x 160mm) — State Tracker</text>',
        f'<text x="{width // 2}" y="44" font-family="sans-serif" font-size="11" '
        'text-anchor="middle" fill="#666">'
        '50 Windows | Per-window correction offsets | Phase 20 canonical model</text>',
    ]

    for r in range(rows):
        for c in range(cols):
            win_id = (r * cols) + c
            offset = corrections.get(win_id, 0)
            n_words = window_sizes.get(str(win_id), 0)

            x = pad + (c * cell_w)
            y = pad + (r * cell_h) + 30

            # Cell background: highlight hub window (W18) and zero-offset windows
            if win_id == 18:
                fill = "#e8d8b8"  # hub window
            elif offset == 0:
                fill = "#f0ece0"  # zero offset
            else:
                fill = "none"

            svg.append(
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                f'fill="{fill}" stroke="black" stroke-width="1"/>'
            )
            # Window ID
            svg.append(
                f'<text x="{x + 50}" y="{y + 20}" font-family="monospace" '
                'font-size="14" font-weight="bold" text-anchor="middle">'
                f'W{win_id:02d}</text>'
            )
            # Correction offset
            offset_color = "#c00" if offset < 0 else ("#060" if offset > 0 else "#888")
            offset_label = f"+{offset}" if offset > 0 else str(offset)
            svg.append(
                f'<text x="{x + 50}" y="{y + 42}" font-family="monospace" '
                f'font-size="13" text-anchor="middle" fill="{offset_color}">'
                f'{offset_label}</text>'
            )
            # Word count
            svg.append(
                f'<text x="{x + 50}" y="{y + 60}" font-family="monospace" '
                'font-size="10" text-anchor="middle" fill="#666">'
                f'{n_words} words</text>'
            )

    # Legend
    ly = height - 18
    svg.append(
        f'<text x="{pad}" y="{ly}" font-family="sans-serif" font-size="10" fill="#666">'
        'Legend: shaded = hub window (W18) | green = positive drift | '
        'red = negative drift | gray = zero offset</text>'
    )

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


# ---------------------------------------------------------------------------
# 2. Palette Plate SVG (10x5 vocabulary grid with offsets)
# ---------------------------------------------------------------------------

def _write_palette_plate_svg(
    window_contents: dict[str, list[str]],
    corrections: dict[int, int],
    out_path: Path,
) -> None:
    """Render a 10x5 plate layout with vocabulary labels and correction offsets."""
    cols = 10
    rows = 5
    cell_w = 180
    cell_h = 105
    pad = 30
    width = (cols * cell_w) + (2 * pad)
    height = (rows * cell_h) + (2 * pad) + 50

    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{pad}" y="22" font-family="sans-serif" font-size="18" font-weight="bold">'
        'Voynich Engine Canonical Palette Plate (10x5)</text>',
        f'<text x="{pad}" y="40" font-family="sans-serif" font-size="11" fill="#666">'
        'Tabula + Codebook Architecture | Per-window correction offsets shown</text>',
    ]

    for r in range(rows):
        for c in range(cols):
            win_id = (r * cols) + c
            words = window_contents.get(str(win_id), [])
            label = escape(_window_label(words, max_chars=12))
            count = len(words)
            offset = corrections.get(win_id, 0)

            x = pad + (c * cell_w)
            y = pad + (r * cell_h) + 20

            svg.append(
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                'fill="none" stroke="black" stroke-width="1"/>'
            )
            # Window ID + offset
            offset_label = f"+{offset}" if offset > 0 else str(offset)
            svg.append(
                f'<text x="{x + 8}" y="{y + 18}" font-family="monospace" '
                'font-size="12" font-weight="bold">'
                f'W{win_id:02d} (offset {offset_label})</text>'
            )
            # Top word
            svg.append(
                f'<text x="{x + 8}" y="{y + 40}" font-family="monospace" font-size="11">'
                f'top: {label}</text>'
            )
            # Word count
            svg.append(
                f'<text x="{x + 8}" y="{y + 58}" font-family="monospace" font-size="11">'
                f'size: {count}</text>'
            )
            # Codebook pages estimate (~60 words per page)
            pages = max(1, (count + 59) // 60)
            svg.append(
                f'<text x="{x + 8}" y="{y + 76}" font-family="monospace" font-size="10" fill="#666">'
                f'~{pages} codebook pg</text>'
            )

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


# ---------------------------------------------------------------------------
# 3. Codebook Index SVG
# ---------------------------------------------------------------------------

def _write_codebook_index_svg(
    window_contents: dict[str, list[str]],
    corrections: dict[int, int],
    out_path: Path,
) -> None:
    """Render a codebook section index showing cumulative page spans."""
    row_h = 22
    header_h = 60
    cols_w = 800
    n_windows = 50
    height = header_h + (n_windows * row_h) + 40

    svg = [
        f'<svg width="{cols_w}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="24" font-family="sans-serif" font-size="16" font-weight="bold">'
        'Voynich Codebook Index (154 pages, 10 quires)</text>',
        '<text x="20" y="42" font-family="sans-serif" font-size="11" fill="#666">'
        'Organized by window number (W0-W49) | ~60 words per page (2 cols x 30 rows)</text>',
    ]

    # Header row
    hy = header_h
    headers = ["Window", "Words", "Pages", "Page Span", "Offset", "Top Word"]
    col_x = [20, 100, 170, 240, 380, 460]
    for hdr, cx in zip(headers, col_x):
        svg.append(
            f'<text x="{cx}" y="{hy}" font-family="monospace" font-size="11" '
            f'font-weight="bold">{hdr}</text>'
        )
    svg.append(
        f'<line x1="20" y1="{hy + 4}" x2="{cols_w - 20}" y2="{hy + 4}" '
        'stroke="black" stroke-width="0.5"/>'
    )

    cumulative_page = 1
    total_words = 0
    for win_id in range(n_windows):
        words = window_contents.get(str(win_id), [])
        count = len(words)
        total_words += count
        pages = max(1, (count + 59) // 60)
        offset = corrections.get(win_id, 0)
        offset_label = f"+{offset}" if offset > 0 else str(offset)
        top_word = escape(words[0][:12]) if words else "EMPTY"
        page_span = f"pp. {cumulative_page}-{cumulative_page + pages - 1}"

        ry = hy + 16 + (win_id * row_h)
        # Alternate row shading
        if win_id % 2 == 0:
            svg.append(
                f'<rect x="15" y="{ry - 13}" width="{cols_w - 30}" height="{row_h}" '
                'fill="#f8f8f8"/>'
            )
        # Highlight W18
        if win_id == 18:
            svg.append(
                f'<rect x="15" y="{ry - 13}" width="{cols_w - 30}" height="{row_h}" '
                'fill="#e8d8b8"/>'
            )

        values = [
            f"W{win_id:02d}",
            str(count),
            str(pages),
            page_span,
            offset_label,
            top_word,
        ]
        for val, cx in zip(values, col_x):
            svg.append(
                f'<text x="{cx}" y="{ry}" font-family="monospace" font-size="10">'
                f'{val}</text>'
            )
        cumulative_page += pages

    # Summary
    sy = hy + 20 + (n_windows * row_h)
    svg.append(
        f'<text x="20" y="{sy}" font-family="sans-serif" font-size="11" font-weight="bold">'
        f'Total: {total_words} words across {cumulative_page - 1} pages '
        f'({math.ceil((cumulative_page - 1) / 16)} quires of 8 leaves)</text>'
    )

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


# ---------------------------------------------------------------------------
# Historical volvelle ring generation (preserved for reference)
# ---------------------------------------------------------------------------

def _create_ring_svg(
    tokens: list[str],
    ring_name: str,
    inner_r: int,
    outer_r: int,
    *,
    font_size: int = 11,
) -> str:
    """Render a single 10-sector donut ring (historical volvelle model)."""
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


def _write_historical_ring_svgs(
    window_contents: dict[str, list[str]], out_dir: Path
) -> list[Path]:
    """Create five historical volvelle rings (deprecated — see Phase 20 findings)."""
    generated: list[Path] = []
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
        ring_name = f"Historical Ring {row_idx + 1} (W{start:02d}-W{stop - 1:02d})"
        svg = _create_ring_svg(
            tokens, ring_name, inner_r=inner_r, outer_r=outer_r, font_size=font_size
        )
        out_path = out_dir / f"volvelle_canonical_ring_{row_idx + 1}.svg"
        out_path.write_text(svg, encoding="utf-8")
        generated.append(out_path)
    return generated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    console.print("[bold yellow]Phase 17A: Physical Blueprint Generation "
                  "(Tabula + Codebook Model)[/bold yellow]")

    if not PALETTE_PATH.exists():
        console.print("[red]Error: Palette grid not found.[/red]")
        return
    if not OFFSETS_PATH.exists():
        console.print("[red]Error: Canonical offsets not found.[/red]")
        return

    # 1. Load model data
    with open(PALETTE_PATH) as f:
        palette_data = json.load(f)["results"]
    window_contents = palette_data["window_contents"]
    corrections = _load_corrections()

    window_sizes = {
        str(win_id): len(window_contents.get(str(win_id), []))
        for win_id in range(50)
    }

    # 2. Generate text layout reference
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet = []
    window_stats = []
    for r in range(5):
        row = []
        for c in range(10):
            win_id = r * 10 + c
            words = window_contents.get(str(win_id), [])
            label = words[0] if words else "EMPTY"
            offset = corrections.get(win_id, 0)
            offset_s = f"+{offset}" if offset > 0 else str(offset)
            row.append(f"W{win_id:02d}[{label[:6]:6}|{offset_s:>4}]")
            window_stats.append({"window_id": win_id, "word_count": len(words)})
        sheet.append("  ".join(row))

    avg_words = (
        sum(w["word_count"] for w in window_stats) / len(window_stats)
        if window_stats else 0
    )

    with open(OUTPUT_DIR / "palette_layout.txt", "w") as f:
        f.write("VOYNICH ENGINE: 10x5 TABULA LAYOUT (Window[TopWord|Offset])\n")
        f.write("=" * 100 + "\n\n")
        f.write("\n".join(sheet))
        f.write(f"\n\n{'=' * 100}\n")
        f.write(f"50 windows | {sum(w['word_count'] for w in window_stats)} total words "
                f"| avg {avg_words:.0f} per window\n")
        f.write("43 non-zero corrections | range: -20 to +13\n")
        f.write("Architecture: flat tabula (170x160mm) + codebook (154pp)\n")

    # 3. Generate correction offsets reference
    offset_lines = [
        "VOYNICH TABULA: PER-WINDOW CORRECTION OFFSETS",
        "=" * 60,
        "",
        "The correction offset is added to the raw next-window number (mod 50)",
        "to account for systematic drift in the production device.",
        "",
        f"{'Window':>8}  {'Offset':>8}  {'Words':>8}  {'Note':<20}",
        "-" * 50,
    ]
    for win_id in range(50):
        offset = corrections.get(win_id, 0)
        n_words = len(window_contents.get(str(win_id), []))
        offset_s = f"+{offset}" if offset > 0 else str(offset)
        note = ""
        if win_id == 18:
            note = "HUB (production center)"
        elif offset == 0:
            note = "zero drift"
        offset_lines.append(f"  W{win_id:02d}     {offset_s:>5}     {n_words:>5}  {note}")

    nonzero = sum(1 for v in corrections.values() if v != 0)
    offset_lines.extend([
        "",
        f"Non-zero corrections: {nonzero} of {len(corrections)}",
        f"Range: {min(corrections.values())} to {max(corrections.values())}",
    ])

    with open(OUTPUT_DIR / "correction_offsets.txt", "w") as f:
        f.write("\n".join(offset_lines))

    # 4. Generate canonical SVG blueprints
    tabula_svg = OUTPUT_DIR / "tabula_card.svg"
    _write_tabula_card_svg(corrections, window_sizes, tabula_svg)

    plate_svg = OUTPUT_DIR / "palette_plate.svg"
    _write_palette_plate_svg(window_contents, corrections, plate_svg)

    codebook_svg = OUTPUT_DIR / "codebook_index.svg"
    _write_codebook_index_svg(window_contents, corrections, codebook_svg)

    # 5. Preserve historical volvelle rings in historical/ subdirectory
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    historical_svgs = _write_historical_ring_svgs(window_contents, HISTORICAL_DIR)

    # 6. Save provenance
    artifacts = [
        str(OUTPUT_DIR / "palette_layout.txt"),
        str(OUTPUT_DIR / "correction_offsets.txt"),
        str(tabula_svg),
        str(plate_svg),
        str(codebook_svg),
    ] + [str(p) for p in historical_svgs]

    results = {
        "model": "tabula_codebook",
        "num_windows": len(window_contents),
        "total_words": sum(w["word_count"] for w in window_stats),
        "avg_words_per_window": avg_words,
        "nonzero_corrections": nonzero,
        "correction_range": [min(corrections.values()), max(corrections.values())],
        "window_sizes": window_stats,
        "corrections": {str(k): v for k, v in corrections.items()},
        "artifacts": artifacts,
    }
    ProvenanceWriter.save_results(
        results,
        project_root / "results/data/phase17_finality/blueprint_metadata.json",
    )

    console.print(f"\n[green]Success! Tabula + codebook blueprints generated in:[/green] {OUTPUT_DIR}")
    console.print("  [cyan]tabula_card.svg[/cyan]     — physical state-tracker card (170x160mm)")
    console.print("  [cyan]palette_plate.svg[/cyan]   — 10x5 vocabulary plate with offsets")
    console.print("  [cyan]codebook_index.svg[/cyan]  — codebook section index (154 pages)")
    console.print("  [cyan]correction_offsets.txt[/cyan] — per-window offset table")
    console.print("  [dim]historical/[/dim]           — deprecated volvelle ring SVGs")
    console.print(
        f"  Windows: {len(window_contents)}, "
        f"Total Words: {results['total_words']}, "
        f"Non-zero Offsets: {nonzero}"
    )


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17a_generate_blueprints"}):
        main()
