from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(*parts: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *parts],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_unreferenced_module_tiers_contract_check_passes() -> None:
    result = _run("scripts/core_audit/check_unreferenced_module_tiers.py")
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "critical_open=0" in result.stdout


def test_script_interface_contract_check_passes() -> None:
    result = _run("scripts/core_audit/check_script_interface_contract.py")
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "tier1_checked=" in result.stdout


def test_ci_check_wires_p4_contract_checks() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert "check_unreferenced_module_tiers.py" in script
    assert "check_script_interface_contract.py" in script
