#!/usr/bin/env python3
"""Phase 15B: Rule Extraction (Implicit to Declarative).

Extracts the implicit state-transition rules from the lattice model 
into a human-readable declarative table.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase15_rule_extraction.extraction import RuleExtractor  # noqa: E402

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
REPORT_PATH = project_root / "results/reports/phase15_rule_extraction/DECLARATIVE_RULES.md"
STATUS_PATH = project_root / "results/data/phase15_rule_extraction/rule_extraction_status.json"
console = Console()

def main():
    console.print("[bold yellow]Phase 15B: Rule Extraction (The Declarative Table)[/bold yellow]")

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: Palette grid not found at {PALETTE_PATH}[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = data["window_contents"]

    # 2. Extract Implicit Grammar
    extractor = RuleExtractor(lattice_map, window_contents)
    rules = extractor.extract_rules()

    # 3. Generate Report
    extractor.generate_markdown_report(rules, REPORT_PATH, limit=100)
    console.print(f"\n[green]Success! Declarative rules extracted to:[/green] {REPORT_PATH}")

    # 4. Save Status
    ProvenanceWriter.save_results(
        {"num_rules_extracted": len(rules)},
        STATUS_PATH,
    )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_15b_extract_rules"}):
        main()
