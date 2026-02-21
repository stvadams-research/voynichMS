import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _load_checker_module():
    module_path = Path("scripts/core_audit/check_provenance_runner_contract.py")
    spec = importlib.util.spec_from_file_location(
        "check_provenance_runner_contract", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_flags_direct_runner_missing_provenance_symbol(tmp_path: Path) -> None:
    checker = _load_checker_module()
    script_path = tmp_path / "scripts/demo/run_demo.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("#!/usr/bin/env python3\nprint('demo')\n", encoding="utf-8")

    policy = {
        "run_glob": "scripts/**/run_*.py",
        "direct_required_symbol": "ProvenanceWriter",
        "display_only_exemptions": [],
        "delegated_provenance": {},
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("missing-direct-provenance" in err for err in errors)


def test_checker_accepts_delegated_runner_with_writer_backing_module(tmp_path: Path) -> None:
    checker = _load_checker_module()
    script_path = tmp_path / "scripts/phase8_comparative/run_uncertainty.py"
    module_path = tmp_path / "src/phase8_comparative/mapping.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.parent.mkdir(parents=True, exist_ok=True)

    script_path.write_text(
        "from phase8_comparative.mapping import run_analysis\n"
        "summary = run_analysis()\n",
        encoding="utf-8",
    )
    module_path.write_text(
        "from phase1_foundation.core.provenance import ProvenanceWriter\n",
        encoding="utf-8",
    )

    policy = {
        "run_glob": "scripts/**/run_*.py",
        "direct_required_symbol": "ProvenanceWriter",
        "display_only_exemptions": [],
        "delegated_provenance": {
            "scripts/phase8_comparative/run_uncertainty.py": {
                "module_path": "src/phase8_comparative/mapping.py",
                "module_required_symbol": "ProvenanceWriter",
                "required_script_markers": [
                    "from phase8_comparative.mapping import run_analysis",
                    "summary = run_analysis(",
                ],
                "modes": ["ci", "release"],
            }
        },
    }

    ci_errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    release_errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert ci_errors == []
    assert release_errors == []


def test_checker_flags_delegated_runner_missing_writer_symbol(tmp_path: Path) -> None:
    checker = _load_checker_module()
    script_path = tmp_path / "scripts/phase8_comparative/run_uncertainty.py"
    module_path = tmp_path / "src/phase8_comparative/mapping.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.parent.mkdir(parents=True, exist_ok=True)

    script_path.write_text(
        "from phase8_comparative.mapping import run_analysis\n"
        "summary = run_analysis()\n",
        encoding="utf-8",
    )
    module_path.write_text("def run_analysis():\n    return {}\n", encoding="utf-8")

    policy = {
        "run_glob": "scripts/**/run_*.py",
        "direct_required_symbol": "ProvenanceWriter",
        "display_only_exemptions": [],
        "delegated_provenance": {
            "scripts/phase8_comparative/run_uncertainty.py": {
                "module_path": "src/phase8_comparative/mapping.py",
                "module_required_symbol": "ProvenanceWriter",
                "required_script_markers": [
                    "from phase8_comparative.mapping import run_analysis",
                    "summary = run_analysis(",
                ],
                "modes": ["ci", "release"],
            }
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("delegated-module-symbol" in err for err in errors)


def test_repo_policy_is_parseable_and_contains_delegated_comparative_runner() -> None:
    policy = json.loads(
        Path("configs/core_audit/provenance_runner_contract.json").read_text(
            encoding="utf-8"
        )
    )
    delegated = policy.get("delegated_provenance", {})
    assert "scripts/phase8_comparative/run_proximity_uncertainty.py" in delegated
