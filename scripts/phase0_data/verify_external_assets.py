#!/usr/bin/env python3
"""
Automated External Asset Validator

Performs a non-destructive check (presence + file size) of the external data 
files required by the VoynichMS analysis pipeline.

Required Assets (Data Sources):
  1. IVTFF 2.0 Transliterations (ZL3b-n.txt)
  2. Project Gutenberg Corpora (latin_corpus.txt, english.txt, german.txt)
  3. Yale Beinecke MS 408 PDF

Optional Assets (Recommended for Full Depth):
  - High-res TIFF/JPEG scans (7+ GB)

Usage:
    python3 scripts/phase0_data/verify_external_assets.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- Required Asset Definitions ---

# IVTFF Directory and primary file
IVTFF_DIR = PROJECT_ROOT / "data" / "raw" / "transliterations" / "ivtff2.0"
REQUIRED_IVTFF = [
    "ZL3b-n.txt",  # Primary Zandbergen/Landini
]

# Gutenberg Corpora
CORPORA_DIR = PROJECT_ROOT / "data" / "external_corpora"
REQUIRED_CORPORA = [
    "latin_corpus.txt",
    "english.txt",
    "german.txt",
]

# Yale Scan PDF
YALE_PDF = PROJECT_ROOT / "data" / "raw" / "VoynichMS_Yale-2002046.pdf"

# --- Optional Asset Definitions ---
SCANS_DIR = PROJECT_ROOT / "data" / "raw" / "scans"
TIFF_DIR = SCANS_DIR / "tiff"


def verify_assets() -> bool:
    """Verify presence and non-empty status of all required assets."""
    print("VoynichMS External Asset Verification")
    print("=" * 40)
    
    missing_required = []
    
    # 1. Check IVTFF
    print("\n[IVTFF Transliterations]")
    if not IVTFF_DIR.exists():
        print(f"  [MISSING] Directory: {IVTFF_DIR}")
        missing_required.append("data/raw/transliterations/ivtff2.0/")
    else:
        for filename in REQUIRED_IVTFF:
            path = IVTFF_DIR / filename
            if path.exists() and path.stat().st_size > 0:
                print(f"  [OK]    {filename} ({path.stat().st_size:,} bytes)")
            else:
                print(f"  [FAIL]  {filename} (missing or empty)")
                missing_required.append(f"IVTFF: {filename}")

    # 2. Check Gutenberg Corpora
    print("\n[Project Gutenberg Corpora]")
    if not CORPORA_DIR.exists():
        print(f"  [MISSING] Directory: {CORPORA_DIR}")
        missing_required.append("data/external_corpora/")
    else:
        for filename in REQUIRED_CORPORA:
            path = CORPORA_DIR / filename
            if path.exists() and path.stat().st_size > 0:
                print(f"  [OK]    {filename} ({path.stat().st_size:,} bytes)")
            else:
                # Check for components if it's the latin_corpus
                if filename == "latin_corpus.txt":
                    p1 = CORPORA_DIR / "latin_part1.txt"
                    p2 = CORPORA_DIR / "latin_part2.txt"
                    if p1.exists() and p2.exists():
                        print("  [OK]    latin_part1.txt + latin_part2.txt found (concatenation pending)")
                        continue
                
                print(f"  [FAIL]  {filename} (missing or empty)")
                missing_required.append(f"Corpus: {filename}")

    # 3. Check Yale PDF
    print("\n[Yale Beinecke MS 408 PDF]")
    if YALE_PDF.exists() and YALE_PDF.stat().st_size > 100_000_000: # ~115 MB
        print(f"  [OK]    {YALE_PDF.name} ({YALE_PDF.stat().st_size:,} bytes)")
    else:
        # Check if jpg or tiff scans exist as alternative
        has_scans = any(SCANS_DIR.glob("**/*.jpg")) or any(SCANS_DIR.glob("**/*.tif"))
        if has_scans:
            print("  [OK]    PDF missing but scan images detected.")
        else:
            print(f"  [FAIL]  {YALE_PDF.name} (missing or too small)")
            missing_required.append("Yale PDF or Scans")

    # 4. Check Optional TIFF Scans
    print("\n[High-Resolution TIFF Scans (Optional)]")
    if TIFF_DIR.exists() and any(TIFF_DIR.iterdir()):
        count = len(list(TIFF_DIR.glob("*.tif")))
        print(f"  [INFO]  {count} TIFF scans detected.")
    else:
        print("  [INFO]  No TIFF scans found (optional, recommended for full segmentation depth).")

    print("\n" + "=" * 40)
    if missing_required:
        print(f"VERIFICATION FAILED: {len(missing_required)} required asset(s) missing.")
        for item in missing_required:
            print(f"  - {item}")
        print("\nPlease run: python3 scripts/phase0_data/download_external_data.py")
        print("See DATA_SOURCES.md for manual download instructions.")
        return False
    else:
        print("VERIFICATION SUCCESSFUL: All required assets detected.")
        return True


if __name__ == "__main__":
    success = verify_assets()
    sys.exit(0 if success else 1)
