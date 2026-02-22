from __future__ import annotations

import json
import re
from pathlib import Path

_JS_ASSIGNMENT_RE = re.compile(r"^[^=]+=", re.MULTILINE)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_result_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def load_js_assignment(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    match = _JS_ASSIGNMENT_RE.search(text)
    if not match:
        raise ValueError(f"Unable to parse JS assignment payload at {path}")
    rhs = text[match.end() :].strip()
    rhs = rhs.rstrip(";")
    return json.loads(rhs)


def load_folio_data(root: Path | None = None) -> dict:
    base = root or project_root()
    return load_js_assignment(base / "tools/workbench/data/folio_data.js")


def load_lattice_data(root: Path | None = None) -> dict:
    base = root or project_root()
    payload = load_js_assignment(base / "tools/workbench/data/lattice_data.js")
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def load_page_schedule(root: Path | None = None) -> dict:
    base = root or project_root()
    return load_result_json(base / "results/data/phase18_comparative/folio_state_schedule.json")


def load_page_priors(root: Path | None = None) -> dict:
    base = root or project_root()
    return load_result_json(base / "results/data/phase18_comparative/page_priors.json")


def folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
    match = re.match(r"^f(\d+)([rv])(\d*)$", str(folio_id).strip())
    if not match:
        return (10**9, 1, 10**9, str(folio_id))
    number = int(match.group(1))
    side = 0 if match.group(2) == "r" else 1
    suffix = int(match.group(3) or "0")
    return (number, side, suffix, str(folio_id))


def build_schedule_map(schedule_payload: dict) -> dict[str, dict]:
    return {
        str(entry.get("folio")): entry
        for entry in schedule_payload.get("folios", [])
        if entry.get("folio")
    }


def build_folio_map(folio_payload: dict) -> dict[str, dict]:
    return {
        str(entry.get("folio")): entry
        for entry in folio_payload.get("folios", [])
        if entry.get("folio")
    }


def normalized_window_contents(window_contents: dict) -> dict[int, list[str]]:
    normalized: dict[int, list[str]] = {}
    for key, value in window_contents.items():
        try:
            win = int(key)
        except (TypeError, ValueError):
            continue
        normalized[win] = [str(token) for token in value]
    return normalized
