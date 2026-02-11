#!/usr/bin/env python3
"""
Assemble Draft: Publication Framework

Aggregates individual chapter files into a single master Markdown document
for further editing or conversion to MS Word.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "planning/preparation/chapters"
OUTPUT_DIR = PROJECT_ROOT / "results/reports/publication"
OUTPUT_PATH = OUTPUT_DIR / "DRAFT_MASTER.md"

def get_latest_results(json_path: Path) -> dict:
    """Helper to load latest result data."""
    if not json_path.exists():
        return {}
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return data.get("results", data)
    except Exception as e:
        logger.warning(f"Failed to load {json_path}: {e}")
        return {}

def assemble_chapters():
    """Combines all chapter folders in order."""
    chapters = sorted([d for d in CHAPTERS_DIR.iterdir() if d.is_dir()])
    
    master_content = []
    timestamp = datetime.now().strftime('%Y-%m-%d')
    master_content.append(f"# Voynich Manuscript Research Draft: {timestamp}\n")
    master_content.append("> This document is an automated assembly of the current project findings.\n\n---\n")

    for chapter_dir in chapters:
        chapter_name = chapter_dir.name
        logger.info(f"Assembling chapter: {chapter_name}")
        
        # Look for a master file in each chapter, or create one if missing from template
        master_file = chapter_dir / "index.md"
        if not master_file.exists():
            # Create from template if not exists
            template_path = PROJECT_ROOT / "planning/preparation/templates/CHAPTER_TEMPLATE.md"
            with open(template_path, "r") as f:
                content = f.read()
            
            # Basic replacement
            pretty_name = chapter_name.split("_", 1)[1].replace("_", " ").title()
            content = content.replace("CHAPTER_TITLE_PLACEHOLDER", pretty_name)
            
            with open(master_file, "w") as f:
                f.write(content)
            
        with open(master_file, "r") as f:
            master_content.append(f.read())
            master_content.append("\n\n---\n")

    # Final assembly
    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(master_content))
    
    logger.info(f"Draft assembled successfully at: {OUTPUT_PATH}")

if __name__ == "__main__":
    assemble_chapters()
