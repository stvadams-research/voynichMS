from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = ROOT / "results/data/phase18_generate/folio_state_schedule.json"
PRIORS_PATH = ROOT / "results/data/phase18_generate/page_priors.json"
WORKBENCH_FOLIO_DATA = ROOT / "tools/workbench/data/folio_data.js"
WORKBENCH_SCHEDULE_DATA = ROOT / "tools/workbench/data/page_schedule_data.js"
WORKBENCH_PRIORS_DATA = ROOT / "tools/workbench/data/page_priors_data.js"


def _load_result_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def _load_window_assignment(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    _, rhs = text.split("=", 1)
    return json.loads(rhs.strip().rstrip(";"))


def test_phase18_schedule_schema_and_coverage() -> None:
    assert SCHEDULE_PATH.exists(), f"Missing artifact: {SCHEDULE_PATH}"
    schedule = _load_result_json(SCHEDULE_PATH)

    assert schedule.get("schema_version") == "phase18_folio_schedule_v1"
    assert isinstance(schedule.get("global_mode_offset"), int)
    assert isinstance(schedule.get("section_mode_offsets"), dict)
    assert isinstance(schedule.get("folios"), list)
    assert schedule.get("summary", {}).get("folio_count", 0) > 0
    assert schedule.get("summary", {}).get("line_count", 0) > 0

    first_folio = schedule["folios"][0]
    assert "folio" in first_folio
    assert "lines" in first_folio
    assert first_folio["line_count"] == len(first_folio["lines"])


def test_phase18_priors_schema() -> None:
    assert PRIORS_PATH.exists(), f"Missing artifact: {PRIORS_PATH}"
    priors = _load_result_json(PRIORS_PATH)

    assert priors.get("schema_version") == "phase18_page_priors_v1"
    assert isinstance(priors.get("line_count_priors"), dict)
    assert isinstance(priors.get("marker_priors"), dict)
    assert isinstance(priors.get("observed_folios"), dict)
    assert priors.get("summary", {}).get("folio_count", 0) > 0
    assert priors.get("summary", {}).get("line_count_total", 0) > 0


def test_phase18_schedule_matches_workbench_folios() -> None:
    folio_bundle = _load_window_assignment(WORKBENCH_FOLIO_DATA)
    schedule = _load_result_json(SCHEDULE_PATH)

    workbench_folios = {entry["folio"] for entry in folio_bundle.get("folios", [])}
    schedule_folios = {entry["folio"] for entry in schedule.get("folios", [])}

    assert workbench_folios == schedule_folios


def test_workbench_phase18_data_bundles_present() -> None:
    schedule_bundle = _load_window_assignment(WORKBENCH_SCHEDULE_DATA)
    priors_bundle = _load_window_assignment(WORKBENCH_PRIORS_DATA)

    assert schedule_bundle.get("available") is True
    assert priors_bundle.get("available") is True
    assert len(schedule_bundle.get("folios", [])) > 0
    assert len(priors_bundle.get("observed_folios", {})) > 0
