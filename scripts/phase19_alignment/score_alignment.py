#!/usr/bin/env python3
"""Phase 19 scoring package for generated-vs-actual alignment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phase19_alignment.data import build_folio_map, load_folio_data  # noqa: E402
from phase19_alignment.metrics import score_alignment  # noqa: E402


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _folio_actual_text(folio_id: str, fmt: str) -> str:
    folio_payload = load_folio_data(PROJECT_ROOT)
    folio_map = build_folio_map(folio_payload)
    folio = folio_map.get(folio_id)
    if not folio:
        raise KeyError(f"Unknown folio id: {folio_id}")

    rows = []
    for line in folio.get("lines", []):
        location = str(line.get("location", "")).strip()
        content = str(line.get("content", "")).strip()
        if not content:
            continue
        if fmt == "ivtff" and location:
            rows.append(f"<{location}>      {content}")
        else:
            rows.append(content)
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score generated-vs-actual folio alignment")
    parser.add_argument("--generated-file", type=Path, required=True)
    parser.add_argument("--actual-file", type=Path)
    parser.add_argument("--folio-id", type=str)
    parser.add_argument("--format", choices=["content", "ivtff"], default="content")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_text = _load_text(args.generated_file)

    if args.actual_file is not None:
        actual_text = _load_text(args.actual_file)
    elif args.folio_id:
        actual_text = _folio_actual_text(args.folio_id, args.format)
    else:
        raise ValueError("Provide either --actual-file or --folio-id")

    result = score_alignment(generated_text, actual_text)
    payload = {
        "schema_version": "phase19_alignment_score_v1",
        "generated_file": str(args.generated_file),
        "actual_file": str(args.actual_file) if args.actual_file else None,
        "folio_id": args.folio_id,
        "format": args.format,
        "scores": result,
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
