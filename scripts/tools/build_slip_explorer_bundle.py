#!/usr/bin/env python3
"""Build standalone data bundles for tools/slip_explorer.

Reads canonical JSON artifacts and emits browser-friendly JS files for
file:// execution without fetch().
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SLIPS_PATH = PROJECT_ROOT / "results/data/phase13_demonstration/slip_viz_data.json"
LATTICE_PATH = PROJECT_ROOT / "results/data/phase14_machine/full_palette_grid.json"
OUT_DIR = PROJECT_ROOT / "tools/slip_explorer/data"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_js(path: Path, variable_name: str, payload: dict) -> None:
    serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    content = f"window.{variable_name} = {serialized};\n"
    path.write_text(content, encoding="utf-8")


def main() -> None:
    if not SLIPS_PATH.exists():
        raise FileNotFoundError(f"Missing slips artifact: {SLIPS_PATH}")
    if not LATTICE_PATH.exists():
        raise FileNotFoundError(f"Missing lattice artifact: {LATTICE_PATH}")

    slips_raw = load_json(SLIPS_PATH)
    slips = {"slips": slips_raw.get("slips", [])}
    if not slips["slips"]:
        raise ValueError("Slip dataset is empty.")

    lattice_raw = load_json(LATTICE_PATH)
    lattice_results = lattice_raw.get("results", lattice_raw)

    lattice_map = lattice_results.get("lattice_map")
    window_contents = lattice_results.get("window_contents")
    if not isinstance(lattice_map, dict) or not lattice_map:
        raise ValueError("lattice_map missing or empty in palette artifact.")
    if not isinstance(window_contents, dict) or not window_contents:
        raise ValueError("window_contents missing or empty in palette artifact.")

    lattice = {
        "lattice_map": lattice_map,
        "window_contents": window_contents,
    }

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "slips": str(SLIPS_PATH.relative_to(PROJECT_ROOT)),
            "lattice": str(LATTICE_PATH.relative_to(PROJECT_ROOT)),
        },
        "counts": {
            "slips": len(slips["slips"]),
            "lattice_vocab": len(lattice_map),
            "windows": len(window_contents),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_js(OUT_DIR / "slips_data.js", "SLIP_EXPLORER_SLIPS", slips)
    write_js(OUT_DIR / "lattice_data.js", "SLIP_EXPLORER_LATTICE", lattice)
    write_js(OUT_DIR / "metadata.js", "SLIP_EXPLORER_METADATA", metadata)

    print("Built slip_explorer bundles:")
    print(f"  - {OUT_DIR / 'slips_data.js'}")
    print(f"  - {OUT_DIR / 'lattice_data.js'}")
    print(f"  - {OUT_DIR / 'metadata.js'}")
    print("Counts:")
    print(f"  slips={metadata['counts']['slips']}")
    print(f"  lattice_vocab={metadata['counts']['lattice_vocab']}")
    print(f"  windows={metadata['counts']['windows']}")


if __name__ == "__main__":
    main()
