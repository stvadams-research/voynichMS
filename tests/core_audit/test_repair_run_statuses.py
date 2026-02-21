import importlib.util
import json
from pathlib import Path

import pytest

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, RunRecord

pytestmark = pytest.mark.integration


def _load_script_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts/core_audit/repair_run_statuses.py"
    spec = importlib.util.spec_from_file_location("repair_run_statuses", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repair_run_statuses_updates_stale_running_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "repair_test", "seed": 42}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

    session = store.Session()
    try:
        stale = session.query(RunRecord).filter_by(id=run_id).first()
        assert stale is not None
        stale.status = "running"
        stale.timestamp_end = None
        session.commit()
    finally:
        session.close()

    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "run.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": "success",
                "timestamp_end": "2026-02-10T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    module = _load_script_module()
    summary = module.repair_run_statuses(db_url, report_path=str(tmp_path / "repair_report.json"))
    assert summary["scanned"] >= 1
    assert summary["updated"] >= 1
    assert summary["reconciled"] >= 1
    assert summary["orphaned"] == 0

    session = store.Session()
    try:
        record = session.query(module.RunRecord).filter_by(id=run_id).first()
        assert record is not None
        assert record.status == "success"
        assert record.timestamp_end is not None
    finally:
        session.close()


def test_repair_run_statuses_orphans_rows_without_manifests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "runs").mkdir()
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "repair_test_orphan", "seed": 99}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

    session = store.Session()
    try:
        stale = session.query(RunRecord).filter_by(id=run_id).first()
        assert stale is not None
        stale.status = "running"
        stale.timestamp_end = None
        session.commit()
    finally:
        session.close()

    missing_manifest = tmp_path / "runs" / run_id / "run.json"
    if missing_manifest.exists():
        missing_manifest.unlink()
    assert not missing_manifest.exists()

    module = _load_script_module()
    summary = module.repair_run_statuses(
        db_url,
        orphan_status="orphaned",
        report_path=str(tmp_path / "repair_report.json"),
    )
    assert summary["orphaned"] >= 1
    assert summary["missing_manifests"] >= 1

    session = store.Session()
    try:
        record = session.query(module.RunRecord).filter_by(id=run_id).first()
        assert record is not None
        assert record.status == "orphaned"
        assert record.timestamp_end is not None
    finally:
        session.close()


def test_repair_run_statuses_is_idempotent_after_reconciliation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "repair_test_idempotent", "seed": 7}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

    session = store.Session()
    try:
        stale = session.query(RunRecord).filter_by(id=run_id).first()
        assert stale is not None
        stale.status = "running"
        stale.timestamp_end = None
        session.commit()
    finally:
        session.close()

    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "run.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": "success",
                "timestamp_end": "2026-02-10T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    module = _load_script_module()
    first = module.repair_run_statuses(db_url, report_path=str(tmp_path / "report_first.json"))
    second = module.repair_run_statuses(db_url, report_path=str(tmp_path / "report_second.json"))

    assert first["updated"] >= 1
    assert second["updated"] == 0
    assert second["reconciled"] == 0
    assert second["orphaned"] == 0


def test_repair_run_statuses_can_backfill_missing_manifests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "repair_test_backfill", "seed": 11}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

    session = store.Session()
    try:
        record = session.query(RunRecord).filter_by(id=run_id).first()
        assert record is not None
        record.status = "orphaned"
        if record.timestamp_end is None:
            record.timestamp_end = record.timestamp_start
        session.commit()
    finally:
        session.close()

    run_json = runs_dir / run_id / "run.json"
    if run_json.exists():
        run_json.unlink()

    module = _load_script_module()
    summary = module.repair_run_statuses(
        db_url,
        orphan_status="orphaned",
        report_path=str(tmp_path / "repair_backfill_report.json"),
        backfill_missing_manifests=True,
    )

    assert summary["backfilled_manifests"] >= 1
    assert run_json.exists()
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    assert payload.get("run_id") == run_id
    assert payload.get("manifest_backfilled") is True


def test_repair_run_statuses_dry_run_reports_without_mutation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "runs").mkdir()
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "repair_test_dry_run", "seed": 123}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

    session = store.Session()
    try:
        stale = session.query(RunRecord).filter_by(id=run_id).first()
        assert stale is not None
        stale.status = "running"
        stale.timestamp_end = None
        session.commit()
    finally:
        session.close()

    module = _load_script_module()
    summary = module.repair_run_statuses(
        db_url,
        orphan_status="orphaned",
        report_path=str(tmp_path / "repair_dry_run_report.json"),
        dry_run=True,
    )
    assert summary["dry_run"] is True
    assert summary["updated"] == 0
    assert summary["would_update"] >= 1

    session = store.Session()
    try:
        record = session.query(module.RunRecord).filter_by(id=run_id).first()
        assert record is not None
        assert record.status == "running"
        assert record.timestamp_end is None
    finally:
        session.close()
