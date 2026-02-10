import json
from pathlib import Path

from foundation.core.provenance import ProvenanceWriter
from foundation.runs.manager import active_run


def test_provenance_writer_writes_latest_and_snapshot_without_run(tmp_path):
    output = tmp_path / "results.json"
    paths = ProvenanceWriter.save_results({"ok": True}, output)

    latest_path = Path(paths["latest_path"])
    snapshot_path = Path(paths["snapshot_path"])
    assert latest_path.exists()
    assert snapshot_path.exists()

    data = json.loads(latest_path.read_text())
    assert data["results"]["ok"] is True
    assert data["provenance"]["run_id"] == "none"
    assert "status" not in data["provenance"]


def test_provenance_writer_uses_active_run_id_for_snapshot(tmp_path):
    output = tmp_path / "phase" / "result.json"
    with active_run(config={"command": "test_provenance", "seed": 99}):
        paths = ProvenanceWriter.save_results({"value": 1}, output)

    snapshot_path = Path(paths["snapshot_path"])
    data = json.loads(Path(paths["latest_path"]).read_text())

    assert snapshot_path.exists()
    assert data["provenance"]["run_id"] != "none"
    assert data["provenance"]["seed"] == 99
    assert data["provenance"]["experiment_id"]
    assert "status" not in data["provenance"]
