#!/usr/bin/env python3
"""
Generate comparative distance uncertainty artifact and uncertainty-qualified proximity report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from comparative.mapping import run_analysis  # noqa: E402
from foundation.runs.manager import active_run  # noqa: E402

PROVENANCE_CONTRACT_MODE = "delegated"
PROVENANCE_DELEGATED_TO = "src/comparative/mapping.py::run_analysis"
DEFAULT_POLICY_PATH = "configs/skeptic/sk_m2_comparative_uncertainty_policy.json"
PROFILE_ITERATIONS = {
    "smoke": 400,
    "standard": 2000,
    "release-depth": 8000,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SK-M2 comparative uncertainty analysis."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of perturbation/bootstrap iterations (>=100).",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_ITERATIONS.keys()),
        default="standard",
        help="Execution profile used when --iterations is not explicitly provided.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed.",
    )
    parser.add_argument(
        "--target",
        default="Voynich",
        help="Target artifact label in comparative matrix.",
    )
    parser.add_argument(
        "--matrix-path",
        default="reports/comparative/COMPARATIVE_MATRIX.csv",
        help="Comparative matrix CSV path.",
    )
    parser.add_argument(
        "--report-path",
        default="reports/comparative/PROXIMITY_ANALYSIS.md",
        help="Uncertainty-qualified proximity report path.",
    )
    parser.add_argument(
        "--output-path",
        default="results/human/phase_7c_uncertainty.json",
        help="Uncertainty artifact output path.",
    )
    parser.add_argument(
        "--policy-path",
        default=DEFAULT_POLICY_PATH,
        help="SK-M2 comparative uncertainty policy config path.",
    )
    return parser.parse_args()


def _load_status_thresholds(policy_path: str) -> dict:
    path = Path(policy_path)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    thresholds = payload.get("thresholds")
    return thresholds if isinstance(thresholds, dict) else {}


def _assert_provenance_envelope(output_path: str) -> None:
    path = Path(output_path)
    if not path.exists():
        raise RuntimeError(
            f"Comparative uncertainty output not created: {path}"
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("provenance"), dict):
        raise RuntimeError(
            "Comparative uncertainty output missing provenance envelope."
        )
    if not isinstance(payload.get("results"), dict):
        raise RuntimeError(
            "Comparative uncertainty output missing results envelope."
        )


def main() -> int:
    args = _parse_args()
    iterations = int(args.iterations) if args.iterations is not None else PROFILE_ITERATIONS[args.profile]
    thresholds = _load_status_thresholds(args.policy_path)
    # Provenance writing is delegated to `run_analysis`, which writes via
    # ProvenanceWriter in src/comparative/mapping.py.
    with active_run(
        config={
            "command": "run_proximity_uncertainty",
            "seed": args.seed,
            "iterations": iterations,
            "profile": args.profile,
            "target": args.target,
            "matrix_path": args.matrix_path,
            "report_path": args.report_path,
            "output_path": args.output_path,
            "policy_path": args.policy_path,
        },
        capture_env=False,
    ):
        summary = run_analysis(
            matrix_path=args.matrix_path,
            report_path=args.report_path,
            uncertainty_output_path=args.output_path,
            seed=args.seed,
            iterations=iterations,
            run_profile=args.profile,
            target=args.target,
            status_thresholds=thresholds,
        )
    _assert_provenance_envelope(args.output_path)
    summary["provenance_contract_mode"] = PROVENANCE_CONTRACT_MODE
    summary["provenance_delegated_to"] = PROVENANCE_DELEGATED_TO
    summary["policy_path"] = args.policy_path
    summary["profile"] = args.profile
    summary["iterations"] = iterations
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
