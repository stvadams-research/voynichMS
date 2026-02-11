import importlib.util
import json
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/core_audit/check_provenance_runner_contract.py")
    spec = importlib.util.spec_from_file_location(
        "check_provenance_runner_contract", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_provenance_contract_enforced_ci_and_release():
    checker = _load_checker_module()
    policy = json.loads(
        Path("configs/core_audit/provenance_runner_contract.json").read_text(
            encoding="utf-8"
        )
    )

    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []
