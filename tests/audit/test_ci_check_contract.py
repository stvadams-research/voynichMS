from pathlib import Path


def test_ci_check_uses_stage_3_default_and_50_percent_floor() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert 'COVERAGE_STAGE="${COVERAGE_STAGE:-3}"' in script
    assert "3) COVERAGE_MIN=50" in script


def test_ci_check_enforces_critical_module_and_verifier_completion() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert 'CRITICAL_MODULE_ENFORCE", "1"' in script
    assert "VERIFY_SENTINEL_PATH" in script
    assert "VERIFY_REPRODUCTION_COMPLETED" in script
