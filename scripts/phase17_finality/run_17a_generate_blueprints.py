#!/usr/bin/env python3
"""Phase 17A: Physical Blueprint Generation.

Generates the 10x5 physical layout of the palette sheets and
the 12 mask stop-settings.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_DIR = project_root / "results/visuals/phase17_finality"
console = Console()

def main():
    console.print("[bold yellow]Phase 17A: Physical Blueprint Generation[/bold yellow]")

    if not PALETTE_PATH.exists():
        console.print("[red]Error: Palette grid not found.[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH, "r") as f:
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
    avg_words = sum(w["word_count"] for w in window_stats) / len(window_stats) if window_stats else 0

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

    # 5. Save provenance
    results = {
        "num_windows": len(window_contents),
        "total_words": sum(w["word_count"] for w in window_stats),
        "avg_words_per_window": avg_words,
        "window_sizes": window_stats,
        "artifacts": [
            str(OUTPUT_DIR / "palette_layout.txt"),
            str(OUTPUT_DIR / "mask_settings.txt")
        ]
    }
    ProvenanceWriter.save_results(
        results,
        project_root / "results/data/phase17_finality/blueprint_metadata.json"
    )

    console.print(f"\n[green]Success! Physical blueprints generated in:[/green] {OUTPUT_DIR}")
    console.print(f"  Windows: {len(window_contents)}, Total Words: {results['total_words']}, Avg/Window: {avg_words:.0f}")

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17a_generate_blueprints"}):
        main()
