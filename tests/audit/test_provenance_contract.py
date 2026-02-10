from pathlib import Path


EXEMPT_DISPLAY_ONLY = {
    "scripts/analysis/run_phase_2_1.py",
    "scripts/analysis/run_phase_2_3.py",
    "scripts/analysis/run_phase_2_4.py",
    "scripts/synthesis/run_phase_3.py",
    "scripts/synthesis/run_phase_3_1.py",
}


def test_runner_provenance_contract_enforced():
    run_files = sorted(Path("scripts").rglob("run_*.py"))
    missing = []
    for path in run_files:
        text = path.read_text(encoding="utf-8")
        rel = path.as_posix()
        if "ProvenanceWriter" not in text and rel not in EXEMPT_DISPLAY_ONLY:
            missing.append(rel)

    assert missing == []
