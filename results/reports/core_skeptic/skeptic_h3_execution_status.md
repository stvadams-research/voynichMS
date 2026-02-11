# SK-H3 Execution Status

**Date:** 2026-02-10  
**Plan:** `planning/core_skeptic/SKEPTIC_H3_EXECUTION_PLAN.md`  
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

- `governance/CONTROL_COMPARABILITY_POLICY.md`
- `configs/core_skeptic/sk_h3_control_comparability_policy.json`
- `scripts/core_skeptic/check_control_comparability.py`
- `scripts/phase3_synthesis/run_control_matching_audit.py`
- `tests/core_skeptic/test_control_comparability_checker.py`
- `reports/core_skeptic/SKEPTIC_H3_EXECUTION_STATUS.md`

## Files Modified

- `src/phase1_foundation/controls/interface.py`
- `src/phase1_foundation/controls/self_citation.py`
- `src/phase1_foundation/controls/table_grille.py`
- `src/phase1_foundation/controls/mechanical_reuse.py`
- `src/phase1_foundation/controls/synthetic.py`
- `tests/phase1_foundation/test_controls.py`
- `scripts/phase3_synthesis/run_indistinguishability_test.py`
- `src/phase3_synthesis/indistinguishability.py`
- `tests/phase3_synthesis/test_run_indistinguishability_runner.py`
- `scripts/ci_check.sh`
- `scripts/core_audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`
- `tests/core_audit/test_pre_release_contract.py`
- `tests/core_audit/test_verify_reproduction_contract.py`
- `governance/GENERATOR_MATCHING.md`
- `governance/governance/METHODS_REFERENCE.md`
- `governance/governance/REPRODUCIBILITY.md`
- `governance/RUNBOOK.md`
- `governance/CLAIM_BOUNDARY_POLICY.md`
- `planning/core_skeptic/SKEPTIC_H3_EXECUTION_PLAN.md`
- `AUDIT_LOG.md`

---

## Verification Commands

- `python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only` (allowed to block on `DATA_AVAILABILITY`)
- `python3 scripts/core_skeptic/check_control_comparability.py --mode ci`
- `python3 scripts/core_skeptic/check_control_comparability.py --mode release`
- `python3 scripts/core_skeptic/check_claim_boundaries.py`
- `python3 -m pytest -q tests/core_skeptic/test_control_comparability_checker.py`
- `python3 -m pytest -q tests/core_skeptic/test_claim_boundary_checker.py`
- `python3 -m pytest -q tests/phase1_foundation/test_controls.py tests/phase3_synthesis/test_run_indistinguishability_runner.py`
- `python3 -m pytest -q tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py`

---

## Residual

- SK-H3 guardrails now fail closed on leakage and missing comparability artifacts.
- Current comparability status may remain `INCONCLUSIVE_DATA_LIMITED` in preflight-only mode; conclusive closure requires full evidence reruns under policy gates.
