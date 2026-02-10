import json
import logging
from types import SimpleNamespace

from foundation.core import logging as core_logging


def test_json_formatter_includes_run_id_and_extra_fields(monkeypatch):
    monkeypatch.setattr(
        core_logging.RunManager,
        "get_current_run",
        lambda: SimpleNamespace(run_id="run-123"),
    )
    formatter = core_logging.JsonFormatter()
    record = logging.LogRecord(
        name="audit.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.extra_fields = {"phase": "unit"}

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "hello world"
    assert payload["run_id"] == "run-123"
    assert payload["phase"] == "unit"


def test_json_formatter_sets_run_id_none_without_active_run(monkeypatch):
    def _raise_runtime_error():
        raise RuntimeError("no run")

    monkeypatch.setattr(core_logging.RunManager, "get_current_run", _raise_runtime_error)
    formatter = core_logging.JsonFormatter()
    record = logging.LogRecord(
        name="audit.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=20,
        msg="warning message",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["run_id"] is None
    assert payload["level"] == "WARNING"


def test_setup_logging_creates_json_log_and_run_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        core_logging.RunManager,
        "get_current_run",
        lambda: SimpleNamespace(run_id="run-abc"),
    )
    log_path = tmp_path / "logs" / "app.log"

    core_logging.setup_logging(level=logging.INFO, log_file=log_path, json_format=True)
    logger = core_logging.get_logger("audit.logger")
    logger.info("logging works")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_path.exists()
    log_payload = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log_payload["message"] == "logging works"
    assert log_payload["run_id"] == "run-abc"

    run_log = tmp_path / "runs" / "run-abc" / "execution.jsonl"
    assert run_log.exists()
    run_payload = json.loads(run_log.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert run_payload["logger"] == "audit.logger"
