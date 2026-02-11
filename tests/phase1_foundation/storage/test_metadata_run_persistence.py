import pytest

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, RunRecord


def _fetch_run_record(store: MetadataStore, run_id: str) -> RunRecord:
    session = store.Session()
    try:
        record = session.query(RunRecord).filter_by(id=run_id).first()
        assert record is not None
        return record
    finally:
        session.close()


def test_save_run_updates_to_success_after_context_completes(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path}/runs.db"
    store = MetadataStore(db_url)

    with active_run(config={"command": "metadata_persistence_success", "seed": 101}, capture_env=False) as run:
        run_id = str(run.run_id)
        store.save_run(run)

        # Mid-run persistence is expected to be running.
        record = _fetch_run_record(store, run_id)
        assert record.status == "running"
        assert record.timestamp_end is None

    # Completion callback should update core_status/timestamp_end.
    record = _fetch_run_record(store, run_id)
    assert record.status == "success"
    assert record.timestamp_end is not None


def test_save_run_updates_to_failed_when_context_errors(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path}/runs_fail.db"
    store = MetadataStore(db_url)

    run_id = ""
    with pytest.raises(RuntimeError, match="forced failure"):
        with active_run(config={"command": "metadata_persistence_failure", "seed": 202}, capture_env=False) as run:
            run_id = str(run.run_id)
            store.save_run(run)
            raise RuntimeError("forced failure")

    record = _fetch_run_record(store, run_id)
    assert record.status == "failed"
    assert record.timestamp_end is not None
