import json
from pathlib import Path

from phase1_foundation.core.ids import PageID, RunID
from phase1_foundation.qc.reporting import generate_overlays, generate_run_summary


def test_generate_run_summary_writes_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = RunID(seed=123)
    run_dir = Path("runs") / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "status": "success",
                "timestamp_start": "2026-02-10T00:00:00Z",
                "timestamp_end": "2026-02-10T00:10:00Z",
                "git_commit": "abc123",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "inputs.json").write_text(json.dumps({"inputs": [1, 2]}), encoding="utf-8")
    (run_dir / "outputs.json").write_text(json.dumps({"outputs": [1]}), encoding="utf-8")

    summary_path = generate_run_summary(run_id)
    summary_text = Path(summary_path).read_text(encoding="utf-8")

    assert Path(summary_path).exists()
    assert f"# Run Summary: {run_id}" in summary_text
    assert "- Status: success" in summary_text
    assert "- Inputs: 2" in summary_text
    assert "- Outputs: 1" in summary_text


def test_generate_overlays_writes_placeholder_payload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    page_id = PageID(folio="f1r")

    output_path = generate_overlays(page_id)
    payload = json.loads(Path(output_path).read_text(encoding="utf-8"))

    assert Path(output_path).exists()
    assert payload["page_id"] == "f1r"
    assert payload["status"] == "not_rendered"
    assert "backend is not part of this repository build" in payload["reason"]
