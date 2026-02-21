"""Tests for RunContext and RunManager — run lifecycle and provenance.

Covers: context creation, active_run() usage, artifact writing, callback
execution, nesting prevention, thread isolation, and REQUIRE_COMPUTED guard.
"""

import json
import os
import threading

import pytest

from phase1_foundation.runs.context import RunContext, get_git_revision_hash
from phase1_foundation.runs.manager import RunManager, active_run


# ---------------------------------------------------------------------------
# RunContext model
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunContextModel:
    def test_run_context_requires_run_id(self):
        from phase1_foundation.core.ids import RunID
        ctx = RunContext(run_id=RunID(seed=42))
        assert ctx.run_id is not None
        assert ctx.status == "running"

    def test_default_fields(self):
        from phase1_foundation.core.ids import RunID
        ctx = RunContext(run_id=RunID(seed=42))
        assert ctx.timestamp_start is not None
        assert ctx.timestamp_end is None
        assert ctx.status == "running"
        assert ctx.input_assets == []
        assert ctx.output_assets == []

    def test_add_input_asset(self):
        from phase1_foundation.core.ids import RunID
        ctx = RunContext(run_id=RunID(seed=42))
        ctx.add_input_asset("/data/test.txt", "sha256abc")
        assert len(ctx.input_assets) == 1
        assert ctx.input_assets[0]["path"] == "/data/test.txt"
        assert ctx.input_assets[0]["checksum"] == "sha256abc"

    def test_add_output_asset(self):
        from phase1_foundation.core.ids import RunID
        ctx = RunContext(run_id=RunID(seed=42))
        ctx.add_output_asset("/results/out.json", "sha256def", "json")
        assert len(ctx.output_assets) == 1
        assert ctx.output_assets[0]["type"] == "json"


# ---------------------------------------------------------------------------
# Completion callbacks
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCallbacks:
    def test_callback_executes_on_complete(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        called = []
        ctx = RunContext(run_id=RunID(seed=42))
        ctx.add_completion_callback("logger", lambda run: called.append(run.status))
        ctx.complete(status="success")

        assert called == ["success"]

    def test_duplicate_callback_key_ignored(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        count = []
        ctx = RunContext(run_id=RunID(seed=42))
        ctx.add_completion_callback("once", lambda run: count.append(1))
        ctx.add_completion_callback("once", lambda run: count.append(1))
        ctx.complete()

        assert len(count) == 1

    def test_callback_exception_does_not_block_others(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        second_called = []
        ctx = RunContext(run_id=RunID(seed=42))
        ctx.add_completion_callback("bad", lambda run: 1 / 0)
        ctx.add_completion_callback("good", lambda run: second_called.append(True))
        ctx.complete()

        assert second_called == [True]


# ---------------------------------------------------------------------------
# Artifact writing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestArtifactWriting:
    def test_complete_writes_run_json(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        rid = RunID(seed=42)
        ctx = RunContext(run_id=rid, config={"seed": 42})
        ctx.complete(status="success")

        run_dir = tmp_path / "runs" / str(rid)
        assert (run_dir / "run.json").exists()
        assert (run_dir / "config.json").exists()
        assert (run_dir / "inputs.json").exists()
        assert (run_dir / "outputs.json").exists()
        assert (run_dir / "manifest.json").exists()

    def test_run_json_contents(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        rid = RunID(seed=42)
        ctx = RunContext(run_id=rid, config={"seed": 42})
        ctx.complete(status="success")

        data = json.loads((tmp_path / "runs" / str(rid) / "run.json").read_text())
        assert data["run_id"] == str(rid)
        assert data["status"] == "success"
        assert "timestamp_start" in data
        assert data["timestamp_end"] is not None

    def test_config_json_contents(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        rid = RunID(seed=42)
        ctx = RunContext(run_id=rid, config={"seed": 42, "phase": "test"})
        ctx.complete()

        data = json.loads((tmp_path / "runs" / str(rid) / "config.json").read_text())
        assert data["seed"] == 42
        assert data["phase"] == "test"

    def test_complete_sets_timestamp_end(self, tmp_path, monkeypatch):
        from phase1_foundation.core.ids import RunID
        monkeypatch.chdir(tmp_path)

        ctx = RunContext(run_id=RunID(seed=42))
        assert ctx.timestamp_end is None
        ctx.complete()
        assert ctx.timestamp_end is not None


# ---------------------------------------------------------------------------
# RunManager lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunManager:
    def test_start_and_end_run(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)
        RM = clean_run_manager

        run = RM.start_run(config={"seed": 42}, capture_env=False)
        assert RM.has_active_run()
        assert RM.get_current_run() is run

        RM.end_run(status="success")
        assert not RM.has_active_run()

    def test_nested_start_raises(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)
        RM = clean_run_manager

        RM.start_run(config={"seed": 1}, capture_env=False)
        with pytest.raises(RuntimeError, match="already active"):
            RM.start_run(config={"seed": 2}, capture_env=False)
        RM.end_run()

    def test_get_current_run_raises_when_none(self, clean_run_manager):
        RM = clean_run_manager
        with pytest.raises(RuntimeError, match="No active run"):
            RM.get_current_run()

    def test_end_run_without_active_is_silent(self, clean_run_manager):
        RM = clean_run_manager
        RM.end_run()  # should not raise

    def test_run_has_deterministic_experiment_id(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)
        RM = clean_run_manager

        run = RM.start_run(config={"seed": 42}, capture_env=False)
        assert "experiment_id" in run.config
        RM.end_run()

    def test_unseeded_run_gets_timestamp_seed(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)
        # Ensure REQUIRE_COMPUTED is not set
        monkeypatch.delenv("REQUIRE_COMPUTED", raising=False)
        RM = clean_run_manager

        run = RM.start_run(config={}, capture_env=False)
        assert run.config.get("unseeded_run") is True
        assert "seed" in run.config
        RM.end_run()


# ---------------------------------------------------------------------------
# active_run() context manager
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestActiveRun:
    def test_active_run_basic(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)

        with active_run(config={"seed": 42}, capture_env=False) as run:
            assert RunManager.has_active_run()
            assert run.status == "running"
        assert not RunManager.has_active_run()

    def test_active_run_sets_success_on_normal_exit(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)

        with active_run(config={"seed": 42}, capture_env=False) as run:
            pass
        assert run.status == "success"

    def test_active_run_sets_failed_on_exception(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError):
            with active_run(config={"seed": 42}, capture_env=False) as run:
                raise ValueError("boom")
        assert run.status == "failed"
        assert not RunManager.has_active_run()


# ---------------------------------------------------------------------------
# REQUIRE_COMPUTED enforcement
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRequireComputed:
    def test_require_computed_rejects_unseeded(self, monkeypatch, clean_run_manager):
        monkeypatch.setenv("REQUIRE_COMPUTED", "1")
        RM = clean_run_manager

        with pytest.raises(RuntimeError, match="No seed provided"):
            RM.start_run(config={}, capture_env=False)

    def test_require_computed_allows_seeded(self, tmp_path, monkeypatch, clean_run_manager):
        monkeypatch.setenv("REQUIRE_COMPUTED", "1")
        monkeypatch.chdir(tmp_path)
        RM = clean_run_manager

        run = RM.start_run(config={"seed": 42}, capture_env=False)
        assert run is not None
        RM.end_run()


# ---------------------------------------------------------------------------
# Thread isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_thread_isolation(tmp_path, monkeypatch, clean_run_manager):
    """Each thread has its own run context."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REQUIRE_COMPUTED", raising=False)
    results = {}

    def thread_fn(name, seed):
        run = RunManager.start_run(config={"seed": seed}, capture_env=False)
        results[name] = str(run.run_id)
        RunManager.end_run()

    t1 = threading.Thread(target=thread_fn, args=("a", 1))
    t2 = threading.Thread(target=thread_fn, args=("b", 2))
    t1.start()
    t1.join()
    t2.start()
    t2.join()

    assert results["a"] != results["b"]


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_git_revision_returns_string():
    """get_git_revision_hash returns a string even outside a git repo."""
    result = get_git_revision_hash()
    assert isinstance(result, str)
