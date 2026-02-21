import logging
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.qc import anomalies as anomaly_module
from phase1_foundation.qc.anomalies import AnomalyLogger


class _DummyStore:
    def __init__(self):
        self.calls = []

    def add_anomaly(self, **kwargs):
        self.calls.append(kwargs)


def test_anomaly_logger_persists_with_active_run(monkeypatch):
    store = _DummyStore()
    logger = AnomalyLogger(store)
    monkeypatch.setattr(
        anomaly_module.RunManager,
        "get_current_run",
        lambda: SimpleNamespace(run_id="run-xyz"),
    )

    logger.log(
        severity="high",
        category="integrity",
        message="test anomaly",
        details={"k": "v"},
    )

    assert len(store.calls) == 1
    call = store.calls[0]
    assert call["run_id"] == "run-xyz"
    assert call["severity"] == "high"
    assert call["category"] == "integrity"
    assert call["message"] == "test anomaly"
    assert call["details"] == {"k": "v"}


def test_anomaly_logger_warns_when_no_active_run(monkeypatch, caplog):
    def _raise_runtime_error():
        raise RuntimeError("no active run")

    store = _DummyStore()
    logger = AnomalyLogger(store)
    monkeypatch.setattr(anomaly_module.RunManager, "get_current_run", _raise_runtime_error)

    caplog.set_level(logging.WARNING, logger="phase1_foundation.qc.anomalies")
    logger.log(severity="low", category="qc", message="outside run")

    assert store.calls == []
    assert "Anomaly occurred outside active run" in caplog.text
