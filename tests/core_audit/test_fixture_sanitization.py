import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _load_fixture_module():
    module_path = Path("scripts/core_audit/generate_fixtures.py")
    spec = importlib.util.spec_from_file_location("generate_fixtures", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sanitize_for_json_replaces_non_finite_floats():
    fixtures = _load_fixture_module()
    assert fixtures.sanitize_for_json(float("nan")) is None
    assert fixtures.sanitize_for_json(float("inf")) is None
    assert fixtures.sanitize_for_json(float("-inf")) is None
