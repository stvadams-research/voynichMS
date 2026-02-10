from pathlib import Path

import pytest
from pydantic import BaseModel

from foundation.configs.loader import load_config


class DemoConfig(BaseModel):
    alpha: int
    name: str = "demo"


def test_load_config_returns_model_and_hash(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("alpha: 7\nname: test\n", encoding="utf-8")

    config, config_hash = load_config(config_path, DemoConfig)

    assert config.alpha == 7
    assert config.name == "test"
    assert len(config_hash) == 64


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_config(missing, DemoConfig)

