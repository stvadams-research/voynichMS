import sys
from pathlib import Path

import pytest

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


# ---------------------------------------------------------------------------
# Shared fixtures available to all test files
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a fresh SQLite database URL rooted in a temp directory."""
    db_path = tmp_path / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture
def store(tmp_db):
    """MetadataStore backed by a temporary SQLite database."""
    from phase1_foundation.storage.metadata import MetadataStore

    return MetadataStore(tmp_db)


@pytest.fixture
def populated_store(store):
    """MetadataStore pre-loaded with a minimal dataset, page, line, and tokens.

    Provides a realistic baseline for tests that need existing records.
    """
    store.add_dataset("test_ds", "/test/path", checksum="abc123")
    store.add_page("f1r", "test_ds", "/images/f1r.jpg", "img_hash", 800, 600)
    store.add_line("f1r_L1", "f1r", 1, {"x": 0, "y": 0, "w": 800, "h": 30})
    store.add_word("f1r_W1", "f1r_L1", 0, {"x": 0, "y": 0, "w": 100, "h": 30})
    store.add_transcription_source("eva_test", "EVA Test Source")
    store.add_transcription_line("f1r_TL1", "eva_test", "f1r", 1, "daiin.qokeey.dal")
    store.add_transcription_token("f1r_T1", "f1r_TL1", 0, "daiin")
    store.add_transcription_token("f1r_T2", "f1r_TL1", 1, "qokeey")
    store.add_transcription_token("f1r_T3", "f1r_TL1", 2, "dal")
    return store


@pytest.fixture
def sample_ivtff_file(tmp_path):
    """Create a minimal IVTFF-format transliteration file for parser tests."""
    content = (
        "# Comment line\n"
        "<f1r.P.1;H> fachys.ykal.ar.ataiin.shol.shory\n"
        "<f1r.P.2;H> qokal.okeey.dal.qokain\n"
        "\n"
        "<f2v.P.1;H> daiin.chedy.qokey\n"
    )
    path = tmp_path / "test_transcription.txt"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def clean_randomness():
    """Ensure RandomnessController is unpatched and in a clean state.

    Yields the controller, then restores state after the test.
    """
    from phase1_foundation.core.randomness import get_randomness_controller

    ctrl = get_randomness_controller()
    ctrl.unpatch_random_module()
    ctrl.clear_seed_log()
    yield ctrl
    ctrl.unpatch_random_module()
    ctrl.clear_seed_log()


@pytest.fixture
def clean_run_manager():
    """Ensure no active run exists before and after a test."""
    from phase1_foundation.runs.manager import RunManager

    if RunManager.has_active_run():
        RunManager.end_run(status="aborted_by_test")
    yield RunManager
    if RunManager.has_active_run():
        RunManager.end_run(status="aborted_by_test")
