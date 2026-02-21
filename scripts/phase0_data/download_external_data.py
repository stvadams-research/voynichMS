#!/usr/bin/env python3
"""
Download external data files required by the analysis pipeline.

Downloads:
  1. IVTFF 2.0 transliteration files from voynich.nu
  2. Project Gutenberg corpora (Latin, English, German)

Skipped by default (use --include-scans to enable):
  - Yale Beinecke MS 408 scans (7+ GB)

Usage:
    python3 scripts/phase0_data/download_external_data.py
    python3 scripts/phase0_data/download_external_data.py --skip-corpora
    python3 scripts/phase0_data/download_external_data.py --skip-scans  # default
    python3 scripts/phase0_data/download_external_data.py --include-scans

See DATA_SOURCES.md for full documentation of each data source.
"""

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- IVTFF transliteration files ---
# voynich.nu hosts EVA-format transliterations. The canonical download page is
# https://www.voynich.nu/transcr/ — individual files are linked as .txt downloads.
IVTFF_DIR = PROJECT_ROOT / "data" / "raw" / "transliterations" / "ivtff2.0"
IVTFF_BASE_URL = "https://www.voynich.nu/data"
IVTFF_FILES = [
    ("ZL3b-n.txt", "PRIMARY — Zandbergen / Landini"),
    ("CD2a-n.txt", "Currier / D'Imperio"),
    ("FG2a-n.txt", "Friedman Group"),
    ("GC2a-n.txt", "Glen Claston"),
    ("IT2a-n.txt", "Interim"),
    ("RF1b-er.txt", "Rene / Friedman"),
    ("VT0e-n.txt", "Voynich Transcription"),
]

# --- Project Gutenberg corpora ---
CORPORA_DIR = PROJECT_ROOT / "data" / "external_corpora"
GUTENBERG_BASE = "https://www.gutenberg.org/cache/epub"
GUTENBERG_FILES = [
    # (ebook_id, local_filename, description)
    (218, "latin_part1.txt", "De Bello Gallico I-IV (Caesar)"),
    (18837, "latin_part2.txt", "De Bello Gallico V-VIII (Caesar)"),
    (11, "english.txt", "Alice's Adventures in Wonderland (Carroll)"),
    (22367, "german.txt", "Die Verwandlung (Kafka)"),
]

# Post-download: latin_part1.txt + latin_part2.txt -> latin_corpus.txt


def download_file(url: str, dest: Path, description: str) -> bool:
    """Download a single file. Returns True on success."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [SKIP] {dest.name} — already exists ({dest.stat().st_size:,} bytes)")
        return True

    print(f"  [GET]  {description}")
    print(f"         {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VoynichMS-Pipeline/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        print(f"         -> {dest} ({len(data):,} bytes)")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"  [FAIL] {description}: {exc}")
        return False


def download_ivtff() -> int:
    """Download IVTFF transliteration files. Returns count of failures."""
    print("\n=== IVTFF 2.0 Transliterations ===")
    print(f"Target: {IVTFF_DIR}/")
    IVTFF_DIR.mkdir(parents=True, exist_ok=True)

    failures = 0
    for filename, description in IVTFF_FILES:
        url = f"{IVTFF_BASE_URL}/{filename}"
        dest = IVTFF_DIR / filename
        if not download_file(url, dest, description):
            failures += 1

    if failures:
        print(f"\n  {failures} IVTFF file(s) failed to download.")
        print("  Manual download: https://www.voynich.nu/transcr/")
    return failures


def download_gutenberg() -> int:
    """Download Project Gutenberg corpora. Returns count of failures."""
    print("\n=== Project Gutenberg Corpora ===")
    print(f"Target: {CORPORA_DIR}/")
    CORPORA_DIR.mkdir(parents=True, exist_ok=True)

    failures = 0
    for ebook_id, filename, description in GUTENBERG_FILES:
        url = f"{GUTENBERG_BASE}/{ebook_id}/pg{ebook_id}.txt"
        dest = CORPORA_DIR / filename
        if not download_file(url, dest, description):
            failures += 1

    # Concatenate Latin parts into latin_corpus.txt
    latin_corpus = CORPORA_DIR / "latin_corpus.txt"
    part1 = CORPORA_DIR / "latin_part1.txt"
    part2 = CORPORA_DIR / "latin_part2.txt"

    if part1.exists() and part2.exists():
        if latin_corpus.exists() and latin_corpus.stat().st_size > 0:
            print("  [SKIP] latin_corpus.txt — already exists")
        else:
            content = part1.read_text(encoding="utf-8") + "\n" + part2.read_text(encoding="utf-8")
            latin_corpus.write_text(content, encoding="utf-8")
            print("  [OK]   Concatenated latin_part1.txt + latin_part2.txt -> latin_corpus.txt")

    if failures:
        print(f"\n  {failures} Gutenberg file(s) failed to download.")
    return failures


def print_scan_instructions() -> None:
    """Print instructions for downloading Yale scans."""
    print("\n=== Yale Beinecke MS 408 Scans ===")
    print("  Scans are NOT downloaded automatically (7+ GB).")
    print("  To obtain them manually:")
    print("  1. PDF (~115 MB): https://collections.library.yale.edu/pdfs/2002046.pdf")
    print("     -> data/raw/VoynichMS_Yale-2002046.pdf")
    print("  2. IIIF manifest: https://collections.library.yale.edu/manifests/2002046")
    print("     Use an IIIF-compatible downloader to fetch TIFF/JPEG scans.")
    print("  See DATA_SOURCES.md for full instructions.")


def verify_checksums() -> None:
    """Print SHA-256 checksums for verification."""
    print("\n=== Checksums (SHA-256) ===")
    primary = IVTFF_DIR / "ZL3b-n.txt"
    if primary.exists():
        sha = hashlib.sha256(primary.read_bytes()).hexdigest()
        print(f"  ZL3b-n.txt: {sha}")
    else:
        print("  ZL3b-n.txt: not found")

    latin = CORPORA_DIR / "latin_corpus.txt"
    if latin.exists():
        sha = hashlib.sha256(latin.read_bytes()).hexdigest()
        print(f"  latin_corpus.txt: {sha}")
    else:
        print("  latin_corpus.txt: not found")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download external data for the VoynichMS pipeline."
    )
    parser.add_argument(
        "--skip-ivtff", action="store_true",
        help="Skip IVTFF transliteration downloads.",
    )
    parser.add_argument(
        "--skip-corpora", action="store_true",
        help="Skip Project Gutenberg corpus downloads.",
    )
    parser.add_argument(
        "--skip-scans", action="store_true", default=True,
        help="Skip Yale scan download instructions (default: True).",
    )
    parser.add_argument(
        "--include-scans", action="store_true",
        help="Show Yale scan download instructions.",
    )
    parser.add_argument(
        "--checksums", action="store_true",
        help="Print SHA-256 checksums after download.",
    )
    args = parser.parse_args()

    print("VoynichMS External Data Downloader")
    print("=" * 40)

    total_failures = 0

    if not args.skip_ivtff:
        total_failures += download_ivtff()

    if not args.skip_corpora:
        total_failures += download_gutenberg()

    if args.include_scans:
        print_scan_instructions()
    else:
        print("\n  (Yale scans skipped. Use --include-scans to see instructions.)")

    if args.checksums:
        verify_checksums()

    print("\n" + "=" * 40)
    if total_failures:
        print(f"Completed with {total_failures} failure(s).")
        print("See DATA_SOURCES.md for manual download instructions.")
        sys.exit(1)
    else:
        print("All downloads completed successfully.")
        print("Next: python3 scripts/phase1_foundation/populate_database.py")


if __name__ == "__main__":
    main()
