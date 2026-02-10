from pathlib import Path

import typer

import foundation.cli.main as cli_main
from foundation.storage.metadata import MetadataStore


def test_get_metadata_store_raises_when_db_missing(monkeypatch, tmp_path):
    missing_db = tmp_path / "missing.db"
    monkeypatch.setattr(cli_main, "DB_PATH", f"sqlite:///{missing_db}")

    try:
        cli_main.get_metadata_store()
        assert False, "Expected typer.Exit"
    except typer.Exit as exc:
        assert exc.exit_code == 1


def test_get_metadata_store_returns_store_when_db_exists(monkeypatch, tmp_path):
    db_file = tmp_path / "exists.db"
    db_file.touch()
    monkeypatch.setattr(cli_main, "DB_PATH", f"sqlite:///{db_file}")

    store = cli_main.get_metadata_store()
    assert isinstance(store, MetadataStore)
    assert Path(str(store.engine.url).replace("sqlite:///", "")).name == "exists.db"


def test_main_callback_sets_expected_logging_level(monkeypatch):
    captured = []

    def _capture(level: str):
        captured.append(level)

    monkeypatch.setattr(cli_main, "setup_logging", _capture)
    cli_main.main(verbose=True)
    cli_main.main(verbose=False)

    assert captured == ["DEBUG", "INFO"]
