#!/usr/bin/env python3
"""
Task 2.1: SVG Ring Generator

Generates concentric rings for a physical paper volvelle 
based on the reconstructed blueprint.
"""

import json
import math
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = project_root / "results/data/phase12_mechanical/physical_blueprint.json"
OUTPUT_DIR = project_root / "results/visuals/phase12_mechanical"

def create_svg_ring(tokens: list, radius_inner: int, radius_outer: int, name: str) -> str:
    size = (radius_outer * 2) + 100
    center = size // 2

    num_sectors = len(tokens)
    angle_step = 360 / num_sectors

    svg = [
        f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">',
        f'<circle cx="{center}" cy="{center}" r="{radius_outer}" fill="none" stroke="black" stroke-width="2" />',
        f'<circle cx="{center}" cy="{center}" r="{radius_inner}" fill="none" stroke="black" stroke-width="1" />'
    ]

    for i, token in enumerate(tokens):
        angle_deg = i * angle_step
        angle_rad = math.radians(angle_deg)

        # Sector Line
        x1 = center + radius_inner * math.cos(angle_rad)
        y1 = center + radius_inner * math.sin(angle_rad)
        x2 = center + radius_outer * math.cos(angle_rad)
        y2 = center + radius_outer * math.sin(angle_rad)
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="gray" />')

        # Text Label (mid-sector)
        label_angle = math.radians(angle_deg + angle_step / 2)
        tx = center + (radius_inner + (radius_outer - radius_inner)/2) * math.cos(label_angle)
        ty = center + (radius_inner + (radius_outer - radius_inner)/2) * math.sin(label_angle)

        # Rotate text to align with sector
        rotation = angle_deg + angle_step / 2
        svg.append(f'<text x="{tx}" y="{ty}" font-family="monospace" font-size="12" text-anchor="middle" transform="rotate({rotation}, {tx}, {ty})">{token}</text>')

    svg.append(f'<text x="{center}" y="{center + radius_outer + 30}" font-family="sans-serif" font-size="20" text-anchor="middle">{name}</text>')
    svg.append('</svg>')
    return "\n".join(svg)

def main():
    if not INPUT_PATH.exists():
        print(f"Error: {INPUT_PATH} not found.")
        return

    with open(INPUT_PATH) as f:
        data = json.load(f)
    blueprint = data.get("results", data).get("blueprint", [])

    # We take the vertical stacks for Pos 1, 2, and 3 as our 3 rings
    # Transpose to get columns
    cols = list(zip(*blueprint))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ring 1: Position 1 tokens
    ring1 = create_svg_ring(cols[0], 100, 200, "Ring 1 (Pos 1)")
    (OUTPUT_DIR / "volvelle_ring_1.svg").write_text(ring1)

    # Ring 2: Position 2 tokens
    ring2 = create_svg_ring(cols[1], 200, 300, "Ring 2 (Pos 2)")
    (OUTPUT_DIR / "volvelle_ring_2.svg").write_text(ring2)

    # Ring 3: Position 3 tokens
    ring3 = create_svg_ring(cols[2], 300, 400, "Ring 3 (Pos 3)")
    (OUTPUT_DIR / "volvelle_ring_3.svg").write_text(ring3)

    print(f"Volvelle SVGs generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
