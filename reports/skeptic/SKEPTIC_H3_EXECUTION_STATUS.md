# SK-H3 Execution Status

**Date:** 2026-02-10  
**Plan:** `planning/skeptic/SKEPTIC_H3_EXECUTION_PLAN.md`  
**Scope:** SK-H3 control comparability hardening (metric leakage and normalization symmetry)

---

## Summary

SK-H3 remediation was implemented across policy, control-generation normalization, synthesis artifact contracts, release/CI guardrails, and governance docs.

Implemented outcomes:

- Added SK-H3 comparability policy doc and machine-readable config.
- Added SK-H3 policy checker with CI/release modes.
- Added deterministic control matching audit runner and comparability status artifact.
- Added explicit matching vs holdout metric partition fields to Turing artifact outputs.
- Added control normalization modes (`parser`, `pre_normalized_with_assertions`) with provenance.
- Added tests for normalization behavior and SK-H3 checker enforcement.
- Integrated SK-H3 checks into `ci_check`, `pre_release_check`, and `verify_reproduction` paths.

---

## Files Added

- `docs/CONTROL_COMPARABILITY_POLICY.md`
- `configs/skeptic/sk_h3_control_comparability_policy.json`
- `scripts/skeptic/check_control_comparability.py`
- `scripts/synthesis/run_control_matching_audit.py`
- `tests/skeptic/test_control_comparability_checker.py`
- `reports/skeptic/SKEPTIC_H3_EXECUTION_STATUS.md`

## Files Modified

- `src/foundation/controls/interface.py`
- `src/foundation/controls/self_citation.py`
- `src/foundation/controls/table_grille.py`
- `src/foundation/controls/mechanical_reuse.py`
- `src/foundation/controls/synthetic.py`
- `tests/foundation/test_controls.py`
- `scripts/synthesis/run_indistinguishability_test.py`
- `src/synthesis/indistinguishability.py`
- `tests/synthesis/test_run_indistinguishability_runner.py`
- `scripts/ci_check.sh`
- `scripts/audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`
- `tests/audit/test_pre_release_contract.py`
- `tests/audit/test_verify_reproduction_contract.py`
- `docs/GENERATOR_MATCHING.md`
- `docs/METHODS_REFERENCE.md`
- `docs/REPRODUCIBILITY.md`
- `docs/RUNBOOK.md`
- `docs/CLAIM_BOUNDARY_POLICY.md`
- `planning/skeptic/SKEPTIC_H3_EXECUTION_PLAN.md`
- `AUDIT_LOG.md`

---

## Verification Commands

- `python3 scripts/synthesis/run_control_matching_audit.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only` (allowed to block on `DATA_AVAILABILITY`)
- `python3 scripts/skeptic/check_control_comparability.py --mode ci`
- `python3 scripts/skeptic/check_control_comparability.py --mode release`
- `python3 scripts/skeptic/check_claim_boundaries.py`
- `python3 -m pytest -q tests/skeptic/test_control_comparability_checker.py`
- `python3 -m pytest -q tests/skeptic/test_claim_boundary_checker.py`
- `python3 -m pytest -q tests/foundation/test_controls.py tests/synthesis/test_run_indistinguishability_runner.py`
- `python3 -m pytest -q tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py`

---

## Residual

- SK-H3 guardrails now fail closed on leakage and missing comparability artifacts.
- Current comparability status may remain `INCONCLUSIVE_DATA_LIMITED` in preflight-only mode; conclusive closure requires full evidence reruns under policy gates.
