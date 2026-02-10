import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_run_test_a_reproducible_for_same_seed(tmp_path: Path) -> None:
    grammar_path = Path("data/derived/voynich_grammar.json")
    db_path = Path("data/voynich.db")
    if not grammar_path.exists() or not db_path.exists():
        pytest.skip("Requires local grammar and database assets.")

    out_1 = tmp_path / "test_a_1.json"
    out_2 = tmp_path / "test_a_2.json"
    seed = "777"

    cmd_1 = [
        sys.executable,
        "scripts/synthesis/run_test_a.py",
        "--seed",
        seed,
        "--output",
        str(out_1),
    ]
    cmd_2 = [
        sys.executable,
        "scripts/synthesis/run_test_a.py",
        "--seed",
        seed,
        "--output",
        str(out_2),
    ]
    subprocess.run(cmd_1, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(cmd_2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    results_1 = json.loads(out_1.read_text(encoding="utf-8"))["results"]
    results_2 = json.loads(out_2.read_text(encoding="utf-8"))["results"]
    assert results_1 == results_2

