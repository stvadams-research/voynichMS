# Audit Log

## 2026-02-10 - Audit 6 Remediation

Source plan: `planning/audit/AUDIT_6_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_6.md`

### Opened

- `RI-1`: Hardcoded/estimated metrics in `run_indistinguishability_test.py`.
- `RI-2`/`RI-3`/`RI-4`/`DOC-1`: Sensitivity artifacts and documentation mismatch.
- `MC-1`/`MC-2`: Stale run status persistence (`running` snapshots).
- `RI-5`/`MC-5`: Reproduction verifier mutates baseline DB and has narrow scope.
- `MC-3`/`MC-4`: Coverage confidence and missing sensitivity end-to-end checks.
- `RI-6`: Strict computed-mode policy needs stronger verification path.
- `INV-2`/`DOC-2`: Missing required `AUDIT_LOG.md`.

### Decisions

- Keep `run_id` immutable and unique; persist final run state via completion callbacks.
- Treat provenance result artifacts as immutable snapshots: omit mutable `status`.
- Preserve `status/` as transient outputs; add documented cleanup path.
- Enforce sensitivity artifact integrity checks in reproducibility verification.

### In Progress

- WS-A through WS-G execution tracked in `reports/audit/FIX_EXECUTION_STATUS_6.md`.

## 2026-02-10 - Audit 7 Remediation

Source plan: `planning/audit/AUDIT_7_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_7.md`

### Opened

- `MC-6`/`DOC-3`: verifier and CI could report success after partial verifier execution.
- `RI-9`: sensitivity artifacts were canonical but bounded and not release-grade evidence.
- `RI-8`/`RI-6`: indistinguishability path still depended on fallback/simulated profile behavior.
- `MC-2`/`ST-1`: historical stale run records and mixed legacy status artifacts.
- `INV-1`/`INV-3`: release baseline and transient artifact lifecycle hygiene gaps.

### Decisions

- Verification scripts must emit an explicit completion token and fail non-zero on partial execution.
- Sensitivity release evidence requires `mode=release` and full scenario execution (`executed == expected`).
- Missing-manifest historical runs are classified as `orphaned` and timestamp-closed for ambiguity reduction.
- Pre-release baseline checks are scriptable and must validate sensitivity release readiness and audit log presence.

### Execution Notes

- `scripts/verify_reproduction.sh` now handles unset `VIRTUAL_ENV` safely and emits `VERIFY_REPRODUCTION_COMPLETED`.
- `scripts/ci_check.sh` now requires verifier sentinel confirmation and defaults to stage-3 (50%) coverage gate.
- Full release-mode sensitivity sweep executed on `voynich_synthetic_grammar` (`17/17` scenarios).
- Strict indistinguishability run (`REQUIRE_COMPUTED=1`) now fails fast with explicit missing-page diagnostics.
- `scripts/audit/repair_run_statuses.py` reconciled stale rows: historical unknowns marked `orphaned`.

### In Progress / Residual

- Strict indistinguishability release execution remains blocked on missing real pharmaceutical page records in `voynich_real`.

## 2026-02-10 - Audit 8 Remediation

Source plan: `planning/audit/AUDIT_8_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_8.md`

### Opened

- `RI-10`: release checks allowed `INCONCLUSIVE` sensitivity artifacts to pass as release-ready.
- `RI-11`/`RI-12`: strict indistinguishability path blocked by missing real pages; fallback remained default outside strict mode.
- `MC-3`: six foundational modules at `0%` coverage.
- `MC-2R`/`ST-1`: historical orphan rows and legacy verify artifact semantics required clearer operational handling.
- `INV-1`: dirty release override had no required rationale.
- `DOC-4`: playbook expected root-level reference docs while repository used `docs/`.

### Decisions

- `release_evidence_ready` now means full release sweep plus conclusive robustness plus quality-gate pass.
- Release gates (`pre_release_check.sh`, `verify_reproduction.sh`) fail closed on `INCONCLUSIVE` sensitivity outcomes.
- Strict indistinguishability preflight is a first-class command path (`--preflight-only`) with explicit blocked artifact output.
- Dirty release overrides require explicit rationale (`DIRTY_RELEASE_REASON`).
- Root-level reference doc aliases are maintained for playbook contract compatibility.

### Execution Notes

- Full release-mode sensitivity sweep rerun completed (`17/17`) with:
  - `release_evidence_ready=false`
  - `robustness_decision=INCONCLUSIVE`
  - `quality_gate_passed=false`
- Pre-release and verification gates now fail as intended against inconclusive sensitivity evidence.
- Added targeted tests for prior 0%-coverage modules:
  - `core/logging`, `core/models`, `qc/anomalies`, `qc/checks`, `storage/filesystem`, `storage/interface`
- Coverage increased to `52.28%`; prior 0% modules now range from `80%` to `100%`.
- Legacy status artifact cleanup script now supports `legacy-report` and accurate zero-match reporting.

### In Progress / Residual

- Strict computed indistinguishability remains blocked by missing `10/18` pharmaceutical pages in `voynich_real`.

## 2026-02-10 - Skeptic SK-C1 Remediation

Source plan: `planning/skeptic/SKEPTIC_C1_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-C1`)

### Opened

- Release sensitivity evidence could be marked conclusive without explicit dataset representativeness policy checks.
- Warning burden and sparse-data fallback behavior were not policy-gated for release evidence.
- Caveat output could appear as `none` despite warning-bearing runs.

### Decisions

- Introduce explicit release-evidence policy configuration:
  - dataset policy (`allowed_dataset_ids`, minimum pages/tokens),
  - warning policy (aggregate and per-scenario thresholds).
- Require `dataset_policy_pass=true` and `warning_policy_pass=true` for `release_evidence_ready=true`.
- Require explicit caveats when warnings are present.
- Extend release and verifier gates to fail closed when new policy fields are missing or failing.

### Execution Notes

- Added `configs/audit/release_evidence_policy.json`.
- Hardened `scripts/analysis/run_sensitivity_sweep.py` with:
  - dataset policy evaluation,
  - expanded warning taxonomy (`insufficient`, `sparse`, `nan`, `fallback`),
  - warning-density and fallback-heavy policy checks,
  - quality diagnostics sidecar output:
    - `status/audit/sensitivity_quality_diagnostics.json`.
- Updated release gate consumers:
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
  to enforce new sensitivity policy fields fail-closed.
- Updated sensitivity and reproducibility docs to reflect the new release evidence contract.
- Added/updated tests in `tests/analysis` and `tests/audit` for policy and contract behavior.

## 2026-02-10 - Skeptic SK-H1 Remediation

Source plan: `planning/skeptic/SKEPTIC_H1_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-H1`)

### Opened

- Illustration coupling claims were mixed across phases: pilot limitations existed while downstream wording could read as conclusive.
- Prior anchor-coupling outputs lacked explicit adequacy thresholds, uncertainty reporting, and fail-closed status classes.
- Phase 7 summaries could overstate illustration/layout independence when multimodal evidence was exploratory.

### Decisions

- Introduce SK-H1 multimodal policy with explicit adequacy and inference thresholds.
- Make coupling outcomes status-gated:
  - `CONCLUSIVE_NO_COUPLING`
  - `CONCLUSIVE_COUPLING_PRESENT`
  - `INCONCLUSIVE_UNDERPOWERED`
  - `BLOCKED_DATA_GEOMETRY`
- Require allowed-claim text in the coupling artifact so downstream reports cannot exceed evidence class.
- Add pre-coupling coverage audit and Phase 7 evidence-grade ingestion.

### Execution Notes

- Added policy/config and contract docs:
  - `configs/skeptic/sk_h1_multimodal_policy.json`
  - `docs/MULTIMODAL_COUPLING_POLICY.md`
- Added SK-H1 analysis utilities:
  - `src/mechanism/anchor_coupling.py`
- Added scripts:
  - `scripts/mechanism/audit_anchor_coverage.py`
  - rewritten `scripts/mechanism/run_5i_anchor_coupling.py` with adequacy gates, bootstrap CI, permutation p-value, and status mapping.
- Updated `scripts/mechanism/generate_all_anchors.py` with dataset/method configurability for reproducible method variants.
- Updated `scripts/human/run_7b_codicology.py` to ingest multimodal status and emit illustration evidence grade in report outputs.
- Calibrated report language to prevent categorical claims under non-conclusive multimodal status:
  - `results/reports/PHASE_5H_RESULTS.md`
  - `results/reports/PHASE_5I_RESULTS.md`
  - `results/reports/PHASE_5_FINAL_FINDINGS_SUMMARY.md`
  - `reports/human/PHASE_7_FINDINGS_SUMMARY.md`
- Added tests:
  - `tests/mechanism/test_anchor_coupling.py`
  - `tests/mechanism/test_anchor_coupling_contract.py`
  - `tests/human/test_phase7_claim_guardrails.py`

### Current Evidence State

- Confirmatory coupling artifact now reports:
  - `results/mechanism/anchor_coupling_confirmatory.json` -> `INCONCLUSIVE_UNDERPOWERED`
- This blocks categorical illustration-coupling conclusions and forces evidence-bounded reporting.

## 2026-02-10 - Skeptic SK-H2 Remediation

Source plan: `planning/skeptic/SKEPTIC_H2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-H2`)

### Opened

- Public-facing conclusions included categorical phrasing stronger than bounded non-claims.
- Key risks were concentrated in:
  - `README.md`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md`

### Decisions

- Define explicit claim-boundary taxonomy and wording policy.
- Require non-claim/scope blocks in public summary docs.
- Enforce banned phrase checks plus required marker checks via automated script.
- Integrate claim-boundary checks into CI.

### Execution Notes

- Added policy and governance artifacts:
  - `docs/CLAIM_BOUNDARY_POLICY.md`
  - `configs/skeptic/sk_h2_claim_language_policy.json`
- Added automated checker:
  - `scripts/skeptic/check_claim_boundaries.py`
- Added tests:
  - `tests/skeptic/test_claim_boundary_checker.py`
- Integrated checker into CI:
  - `scripts/ci_check.sh`
- Calibrated public language and added explicit non-claim boundaries:
  - `README.md`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md`
- Added traceability register and execution report:
  - `reports/skeptic/SK_H2_CLAIM_REGISTER.md`
  - `reports/skeptic/SKEPTIC_H2_EXECUTION_STATUS.md`

### Current Evidence State

- SK-H2 targeted public files now use framework-bounded language and explicit non-claim references.
- CI now includes automated claim-boundary policy enforcement for tracked docs.

## 2026-02-10 - Skeptic SK-H3 Remediation

Source plan: `planning/skeptic/SKEPTIC_H3_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-H3`)

### Opened

- Control comparability remained vulnerable to a target-leakage critique:
  - matching objectives and inferential conclusions were not explicitly partitioned.
- Methods documentation acknowledged normalization asymmetry without enforceable runtime guardrails.
- Release/CI gates did not enforce SK-H3-specific comparability policy artifacts.

### Decisions

- Define SK-H3 policy with explicit `matching_metrics` vs `holdout_evaluation_metrics`.
- Treat metric overlap as leakage and enforce fail-closed behavior.
- Add explicit normalization mode contract for controls:
  - `parser`
  - `pre_normalized_with_assertions`
- Require comparability artifact checks in release path and policy checks in CI.

### Execution Notes

- Added SK-H3 policy artifacts:
  - `docs/CONTROL_COMPARABILITY_POLICY.md`
  - `configs/skeptic/sk_h3_control_comparability_policy.json`
- Added SK-H3 checker and tests:
  - `scripts/skeptic/check_control_comparability.py`
  - `tests/skeptic/test_control_comparability_checker.py`
- Added deterministic control-matching audit runner:
  - `scripts/synthesis/run_control_matching_audit.py`
- Extended Turing artifact flow with comparability block:
  - `scripts/synthesis/run_indistinguishability_test.py`
  - now emits matching/holdout partition, overlap, leakage, normalization mode, and comparability status.
- Added control normalization symmetry hooks and provenance:
  - `src/foundation/controls/interface.py`
  - `src/foundation/controls/self_citation.py`
  - `src/foundation/controls/table_grille.py`
  - `src/foundation/controls/mechanical_reuse.py`
  - `src/foundation/controls/synthetic.py`
- Added normalization tests:
  - `tests/foundation/test_controls.py`
- Integrated SK-H3 checks into gate scripts:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Updated docs and governance references:
  - `docs/GENERATOR_MATCHING.md`
  - `docs/METHODS_REFERENCE.md`
  - `docs/REPRODUCIBILITY.md`
  - `docs/RUNBOOK.md`
  - `docs/CLAIM_BOUNDARY_POLICY.md`

### Current Evidence State

- SK-H3 now has explicit policy, checker, and release-path enforcement.
- Comparability claims are bounded by `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`.
- Leakage and missing-artifact regressions now fail closed through automated checks.

## 2026-02-10 - Skeptic SK-M1 Remediation

Source plan: `planning/skeptic/SKEPTIC_M1_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-M1`)

### Opened

- Closure language in comparative/final reports contained terminal phrasing while reopening criteria existed elsewhere.
- Comparative Phase B closure statements were not consistently linked to reopening criteria.
- CI and pre-release paths had no SK-M1-specific contradiction guardrails.

### Decisions

- Define SK-M1 closure-conditionality taxonomy and prohibited terminal wording patterns.
- Establish canonical reopening criteria as a single source of truth.
- Calibrate closure statements to framework-bounded and explicitly reopenable language.
- Enforce SK-M1 checks in both CI and pre-release paths.

### Execution Notes

- Added SK-M1 policy and canonical criteria artifacts:
  - `docs/CLOSURE_CONDITIONALITY_POLICY.md`
  - `docs/REOPENING_CRITERIA.md`
  - `configs/skeptic/sk_m1_closure_policy.json`
- Added SK-M1 checker and tests:
  - `scripts/skeptic/check_closure_conditionality.py`
  - `tests/skeptic/test_closure_conditionality_checker.py`
- Added closure contradiction register and execution status:
  - `reports/skeptic/SK_M1_CLOSURE_REGISTER.md`
  - `reports/skeptic/SKEPTIC_M1_EXECUTION_STATUS.md`
- Calibrated closure wording in:
  - `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`
  - `reports/comparative/PHASE_B_SYNTHESIS.md`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md`
- Integrated SK-M1 guardrails into:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
- Updated reproducibility guidance:
  - `docs/REPRODUCIBILITY.md`

### Current Evidence State

- Tracked closure-bearing docs now use framework-bounded reopening-linked language.
- SK-M1 checker passes in both `ci` and `release` modes.
- Regression to known contradictory terminal patterns is now blocked by automated guardrails.

## 2026-02-10 - Skeptic SK-M2 Remediation

Source plan: `planning/skeptic/SKEPTIC_M2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-M2`)

### Opened

- Comparative distance claims were presented as point estimates with limited uncertainty disclosure.
- Public comparative docs lacked explicit confidence intervals and perturbation-stability framing.
- CI and pre-release paths had no SK-M2-specific policy gate for uncertainty-qualified comparative claims.

### Decisions

- Introduce SK-M2 comparative uncertainty policy and status taxonomy.
- Generate canonical comparative uncertainty artifact with bootstrap and jackknife diagnostics.
- Calibrate comparative narrative language to uncertainty-qualified claim classes.
- Enforce SK-M2 checks in both CI and pre-release paths.

### Execution Notes

- Added SK-M2 policy artifacts:
  - `docs/COMPARATIVE_UNCERTAINTY_POLICY.md`
  - `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`
- Added comparative uncertainty computation and runner:
  - `src/comparative/mapping.py`
  - `scripts/comparative/run_proximity_uncertainty.py`
- Added SK-M2 checker and tests:
  - `scripts/skeptic/check_comparative_uncertainty.py`
  - `tests/skeptic/test_comparative_uncertainty_checker.py`
  - `tests/comparative/test_mapping_uncertainty.py`
- Updated comparative reports to uncertainty-qualified phrasing:
  - `reports/comparative/PROXIMITY_ANALYSIS.md`
  - `reports/comparative/PHASE_B_SYNTHESIS.md`
  - `reports/comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md`
  - `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`
- Integrated SK-M2 checks into gate scripts:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
- Updated reproducibility and skeptic trace artifacts:
  - `docs/REPRODUCIBILITY.md`
  - `reports/skeptic/SK_M2_COMPARATIVE_REGISTER.md`
  - `reports/skeptic/SKEPTIC_M2_EXECUTION_STATUS.md`

### Current Evidence State

- Canonical uncertainty artifact now exists at `results/human/phase_7c_uncertainty.json`.
- Current SK-M2 comparative status is `INCONCLUSIVE_UNCERTAINTY` with `reason_code=RANK_UNSTABLE_UNDER_PERTURBATION`.
- Comparative claims are now policy-bounded to directional/caveated language until stability thresholds improve.

## 2026-02-10 - Skeptic SK-M4 Remediation

Source plan: `planning/skeptic/SKEPTIC_M4_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-M4`)

### Opened

- Historical provenance uncertainty remained externally attackable despite explicit disclosure.
- Closure-facing docs did not consistently surface provenance confidence class and canonical source.
- CI and pre-release paths had no SK-M4-specific policy gate for provenance-overstated claims.

### Decisions

- Introduce SK-M4 historical provenance policy taxonomy and threshold contract.
- Canonicalize provenance confidence in machine-readable artifact:
  - `status/audit/provenance_health_status.json`
- Extend run-status repair operations with dry-run reporting and explicit backfill metadata fields.
- Enforce SK-M4 checks in both CI and pre-release paths.

### Execution Notes

- Added SK-M4 policy artifacts:
  - `docs/HISTORICAL_PROVENANCE_POLICY.md`
  - `configs/skeptic/sk_m4_provenance_policy.json`
- Added canonical provenance-health builder and artifact path:
  - `scripts/audit/build_provenance_health_status.py`
  - `status/audit/provenance_health_status.json`
- Hardened repair/backfill contract:
  - `scripts/audit/repair_run_statuses.py` now supports `--dry-run`
  - backfilled manifests include:
    - `manifest_backfilled=true`
    - `backfill_generated_utc`
    - `backfill_source`
- Added SK-M4 checker and tests:
  - `scripts/skeptic/check_provenance_uncertainty.py`
  - `tests/skeptic/test_provenance_uncertainty_checker.py`
- Updated closure-facing provenance qualifiers in:
  - `README.md`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md`
  - `docs/PROVENANCE.md`
- Integrated SK-M4 gate enforcement into:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`

### Current Evidence State

- Canonical SK-M4 provenance status:
  - `status/audit/provenance_health_status.json` -> `status=PROVENANCE_QUALIFIED`
- Current historical run distribution:
  - `success=133`
  - `orphaned=63`
  - `running=0`
  - `missing_manifests=0`
- SK-M4 contradiction class (strong closure framing without explicit provenance qualification) is now guarded by automated policy checks.

## 2026-02-10 - Skeptic SK-M3 Remediation

Source plan: `planning/skeptic/SKEPTIC_M3_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-M3`)

### Opened

- Phase 4 reporting contained an internal contradiction class:
  - final determination wording coexisting with unresolved `PENDING` method rows.
- Phase 4 status-bearing artifacts lacked a single canonical machine-readable status source.
- CI and pre-release paths had no SK-M3-specific policy gate for report coherence.

### Decisions

- Introduce SK-M3 report-coherence policy taxonomy and contradiction patterns.
- Canonicalize Phase 4 method status in a single index artifact.
- Normalize status framing across Phase 4 result/conclusion/mapping artifacts.
- Enforce SK-M3 coherence checks in both CI and pre-release paths.

### Execution Notes

- Added SK-M3 policy artifacts:
  - `docs/REPORT_COHERENCE_POLICY.md`
  - `configs/skeptic/sk_m3_report_coherence_policy.json`
- Added canonical method-status artifact:
  - `results/reports/PHASE_4_STATUS_INDEX.json`
- Added SK-M3 checker and tests:
  - `scripts/skeptic/check_report_coherence.py`
  - `tests/skeptic/test_report_coherence_checker.py`
- Normalized Phase 4 status-bearing docs:
  - `results/reports/PHASE_4_RESULTS.md`
  - `results/reports/PHASE_4_CONCLUSIONS.md`
  - `results/reports/PHASE_4_5_METHOD_CONDITION_MAP.md`
  - `results/reports/PHASE_4_METHOD_MAP.md`
- Added contradiction register and execution trace:
  - `reports/skeptic/SK_M3_COHERENCE_REGISTER.md`
  - `reports/skeptic/SKEPTIC_M3_EXECUTION_STATUS.md`
- Integrated SK-M3 checks into gate scripts:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
- Updated governance/test trace:
  - `docs/REPRODUCIBILITY.md`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`

### Current Evidence State

- Phase 4 canonical coherence status:
  - `results/reports/PHASE_4_STATUS_INDEX.json` -> `status=COHERENCE_ALIGNED`
- Methods A-E are all canonicalized as:
  - `execution_status=COMPLETE`
  - `determination=NOT_DIAGNOSTIC`
- SK-M3 contradiction class is now blocked by automated CI and pre-release guardrails.

## 2026-02-10 - Skeptic SK-C1.2 Contract Remediation

Source plan: `planning/skeptic/SKEPTIC_C1_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-C1` pass-2)

### Opened

- Sensitivity artifact/report state was contract-incoherent with release/repro gate expectations.
- No single machine-checkable contract existed for sensitivity JSON/report coherence.
- Release readiness needed explicit failure reasons to prevent ambiguous PASS framing.

### Decisions

- Introduce a dedicated SK-C1.2 sensitivity artifact contract policy + checker.
- Add schema/policy provenance metadata and explicit `release_readiness_failures` in sensitivity summary.
- Wire contract checks into CI, pre-release, and reproduction verification paths.
- Refresh canonical sensitivity artifact/report in quick iterative mode for immediate coherence.

### Execution Notes

- Added contract policy/config:
  - `configs/audit/sensitivity_artifact_contract.json`
- Added contract checker:
  - `scripts/audit/check_sensitivity_artifact_contract.py`
- Updated sensitivity runner:
  - `scripts/analysis/run_sensitivity_sweep.py`
  - summary metadata fields added (`schema_version`, `policy_version`, `generated_utc`, `generated_by`)
  - `release_readiness_failures` added and enforced fail-closed
  - caveat output deduplicated and warning-consistent
- Integrated checker into gates:
  - `scripts/ci_check.sh` (`--mode ci`)
  - `scripts/audit/pre_release_check.sh` (`--mode release`)
  - `scripts/verify_reproduction.sh` (`--mode release`)
- Expanded test coverage:
  - `tests/audit/test_sensitivity_artifact_contract.py`
  - `tests/analysis/test_sensitivity_sweep_guardrails.py`
  - `tests/analysis/test_sensitivity_sweep_end_to_end.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
  - `tests/audit/test_ci_check_contract.py`
- Updated docs:
  - `docs/SENSITIVITY_ANALYSIS.md`
  - `docs/REPRODUCIBILITY.md`
- Added SK-C1.2 trace artifacts:
  - `reports/skeptic/SK_C1_2_CONTRACT_REGISTER.md`
  - `reports/skeptic/SKEPTIC_C1_2_EXECUTION_STATUS.md`

### Verification

- `python3 scripts/analysis/run_sensitivity_sweep.py --mode smoke --quick`
- `python3 scripts/audit/check_sensitivity_artifact_contract.py --mode ci` -> PASS
- `python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release` -> expected FAIL (non-release evidence)
- `python3 -m pytest -q tests/analysis/test_sensitivity_sweep_guardrails.py tests/analysis/test_sensitivity_sweep_end_to_end.py tests/audit/test_sensitivity_artifact_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py tests/audit/test_ci_check_contract.py` -> PASS (`26 passed`)

### Current Evidence State

- Contract coherence is restored for sensitivity artifact/report + gate integration.
- Current canonical artifact is policy-qualified but non-release:
  - `execution_mode=iterative`
  - `release_evidence_ready=false`
  - explicit `release_readiness_failures` present
- SK-C1 pass-2 is reduced from contradiction risk to qualified non-release evidence pending full release-mode sweep.

## 2026-02-10 - Skeptic SK-C2.2 Provenance Runner Contract Remediation

Source plan: `planning/skeptic/SKEPTIC_C2_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-C2`)

### Opened

- CI provenance contract failed on `scripts/comparative/run_proximity_uncertainty.py`.
- Existing contract test was string-fragile (required literal `ProvenanceWriter` in runner script body).
- Delegated provenance behavior (runner -> module writer) was not centrally policy-modeled.

### Decisions

- Introduce policy-backed runner provenance contract with explicit mode taxonomy:
  - direct provenance,
  - delegated provenance,
  - display-only exemption.
- Keep comparative uncertainty runner as delegated provenance, but make delegation explicit and runtime-asserted.
- Integrate runner contract checks into CI, pre-release, and reproduction verification paths.

### Execution Notes

- Added runner contract policy:
  - `configs/audit/provenance_runner_contract.json`
- Added runner contract checker:
  - `scripts/audit/check_provenance_runner_contract.py`
- Updated comparative runner:
  - `scripts/comparative/run_proximity_uncertainty.py`
  - adds delegated provenance metadata in summary output
  - validates output provenance envelope after run
- Updated provenance contract tests:
  - `tests/audit/test_provenance_contract.py` (policy/checker-based)
  - `tests/audit/test_provenance_runner_contract_checker.py` (new)
- Integrated checks into gate scripts:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Updated gate contract tests:
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
- Updated docs:
  - `docs/PROVENANCE.md`
  - `docs/REPRODUCIBILITY.md`
- Added SK-C2.2 trace artifacts:
  - `reports/skeptic/SK_C2_2_PROVENANCE_REGISTER.md`
  - `reports/skeptic/SKEPTIC_C2_2_EXECUTION_STATUS.md`

### Verification

- `python3 -m pytest -q tests/audit/test_provenance_contract.py` -> PASS
- `python3 scripts/audit/check_provenance_runner_contract.py --mode ci` -> PASS
- `python3 scripts/audit/check_provenance_runner_contract.py --mode release` -> PASS
- `python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42` -> PASS
- `python3 -m pytest -q tests/audit/test_provenance_contract.py tests/audit/test_provenance_runner_contract_checker.py tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`15 passed`)

### Current Evidence State

- SK-C2 critical provenance contract mismatch is now closed in this scope.
- Comparative runner is explicitly compliant under delegated provenance policy and checker enforcement.


## 2026-02-10 - Skeptic SK-H3.2 Data-Availability Governance Closure

Source plan: `planning/skeptic/SKEPTIC_H3_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-H3` pass-2 residual)

### Opened

- SK-H3 anti-leakage controls were in place, but full-data comparability remained blocked by missing source pages.
- Blocked-state semantics were not yet centralized as a dedicated SK-H3.2 data-availability contract.
- Gate/report wording risked drift between full-closure and available-subset evidence posture.

### Decisions

- Introduce a canonical SK-H3.2 data-availability policy and checker.
- Emit a dedicated machine-readable availability artifact:
  - `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- Encode explicit bounded-subset semantics in comparability outputs:
  - `evidence_scope`
  - `full_data_closure_eligible`
  - `available_subset_status`
  - `available_subset_reason_code`
- Enforce blocked-state consistency in CI/pre-release/reproduction paths.

### Execution Notes

- Added SK-H3.2 policy/config:
  - `configs/skeptic/sk_h3_data_availability_policy.json`
- Added SK-H3.2 checker:
  - `scripts/skeptic/check_control_data_availability.py`
- Updated SK-H3 audit runner:
  - `scripts/synthesis/run_control_matching_audit.py`
  - now writes `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
  - now writes bounded subset fields to `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- Extended SK-H3 policy/checker contract:
  - `configs/skeptic/sk_h3_control_comparability_policy.json`
  - `scripts/skeptic/check_control_comparability.py`
- Integrated SK-H3.2 checks in gates:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Added/updated tests:
  - `tests/skeptic/test_control_data_availability_checker.py`
  - `tests/skeptic/test_control_comparability_checker.py`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
- Updated SK-H3 docs:
  - `docs/CONTROL_COMPARABILITY_POLICY.md`
  - `docs/GENERATOR_MATCHING.md`
  - `docs/METHODS_REFERENCE.md`
  - `docs/REPRODUCIBILITY.md`
  - `docs/RUNBOOK.md`
- Added SK-H3.2 execution trace artifacts:
  - `reports/skeptic/SK_H3_2_DATA_AVAILABILITY_REGISTER.md`
  - `reports/skeptic/SKEPTIC_H3_2_EXECUTION_STATUS.md`

### Verification

- `python3 scripts/synthesis/run_control_matching_audit.py --preflight-only` -> `status=NON_COMPARABLE_BLOCKED`, `reason_code=DATA_AVAILABILITY`, `evidence_scope=available_subset`
- `python3 scripts/skeptic/check_control_comparability.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_control_comparability.py --mode release` -> PASS
- `python3 scripts/skeptic/check_control_data_availability.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_control_data_availability.py --mode release` -> PASS
- `python3 -m pytest -q tests/skeptic/test_control_comparability_checker.py tests/skeptic/test_control_data_availability_checker.py tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`20 passed`)

### Current Evidence State

- Full-data control comparability remains blocked by approved data-availability constraints (`f91r`, `f91v`, `f92r`, `f92v`).
- Available-subset comparability is now explicitly bounded and non-conclusive under SK-H3.2 policy.
- SK-H3.2 execution outcome is `H3_2_QUALIFIED`.


## 2026-02-10 - Skeptic SK-H1.2 Multimodal Residual Closure

Source plan: `planning/skeptic/SKEPTIC_H1_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-H1` pass-2 residual)

### Opened

- Pass-2 SK-H1 residual remained non-conclusive (`INCONCLUSIVE_UNDERPOWERED`).
- Baseline inadequacy was recurring-context limited in small matched cohorts.
- Status/report coherence existed but lacked dedicated SK-H1.2 gate enforcement.

### Decisions

- Use adequacy-first method selection and cohort recovery, not outcome-tuned selection.
- Promote `geometric_v1_t001` as selected lane with larger default matched cohorts.
- Keep fail-closed stance when stability envelope is inferentially ambiguous.
- Add a dedicated multimodal status checker to CI/pre-release/reproduction gates.

### Execution Notes

- Added adequacy and method-selection registers:
  - `reports/skeptic/SK_H1_2_ADEQUACY_REGISTER.md`
  - `reports/skeptic/SK_H1_2_METHOD_SELECTION.md`
- Added SK-H1.2 execution report:
  - `reports/skeptic/SKEPTIC_H1_2_EXECUTION_STATUS.md`
- Updated SK-H1 default policy lane:
  - `configs/skeptic/sk_h1_multimodal_policy.json`
    - `anchor_method_name=geometric_v1_t001`
    - `sampling.max_lines_per_cohort=1600`
- Added SK-H1.2 multimodal status policy/checker:
  - `configs/skeptic/sk_h1_multimodal_status_policy.json`
  - `scripts/skeptic/check_multimodal_coupling.py`
- Integrated checker into gates:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Added/updated tests:
  - `tests/skeptic/test_multimodal_coupling_checker.py`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
  - plus SK-H1 regression suite (`tests/mechanism/test_anchor_coupling.py`, `tests/mechanism/test_anchor_coupling_contract.py`, `tests/human/test_phase7_claim_guardrails.py`, `tests/mechanism/test_anchor_engine_ids.py`)
- Updated report coherence language:
  - `results/reports/PHASE_5H_RESULTS.md`
  - `results/reports/PHASE_5I_RESULTS.md`
  - `reports/human/PHASE_7_FINDINGS_SUMMARY.md`
- Updated SK-H1 docs/runbook:
  - `docs/MULTIMODAL_COUPLING_POLICY.md`
  - `docs/REPRODUCIBILITY.md`
  - `docs/RUNBOOK.md`

### Verification

- `python3 scripts/mechanism/audit_anchor_coverage.py --method-name geometric_v1_t001` -> PASS
- `python3 scripts/skeptic/check_multimodal_coupling.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_multimodal_coupling.py --mode release` -> PASS
- `python3 -m pytest tests/skeptic/test_multimodal_coupling_checker.py tests/mechanism/test_anchor_coupling.py tests/mechanism/test_anchor_coupling_contract.py tests/human/test_phase7_claim_guardrails.py tests/mechanism/test_anchor_engine_ids.py tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`25 passed`)

### Current Evidence State

- Adequacy recovery is complete for SK-H1.2 (cohort adequacy passes in tracked lanes).
- Residual uncertainty is inferential/stability-based (mixed-seed envelope), not adequacy failure.
- SK-H1.2 closure outcome is `H1_2_QUALIFIED` with explicit non-conclusive claim boundaries and automated gate enforcement.


## 2026-02-10 - Skeptic SK-M2.2 Comparative Confidence Residual Closure

Source plan: `planning/skeptic/SKEPTIC_M2_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-M2` pass-2 residual)

### Opened

- Pass-2 SK-M2 remained `INCONCLUSIVE_UNCERTAINTY`.
- Nearest-neighbor confidence was uncertainty-qualified but not confidence-complete for closure.
- Artifact semantics lacked explicit rank-stability and margin diagnostics required for finer residual classification.

### Decisions

- Add SK-M2.2 confidence diagnostics to the uncertainty artifact (rank stability, probability margin, top-2 fragility).
- Apply policy-backed threshold logic and reason-code discipline in comparative status evaluation.
- Execute pre-registered seed/iteration confidence matrix and select publication lane via anti-tuning rule.
- Extend reproduction-path checks to include SK-M2 uncertainty contract validation.

### Execution Notes

- Updated comparative uncertainty engine:
  - `src/comparative/mapping.py`
  - added `rank_stability`, `rank_stability_components`, `nearest_neighbor_probability_margin`, `top2_gap_fragile`, `metric_validity`, and threshold-driven status logic.
- Updated comparative runner:
  - `scripts/comparative/run_proximity_uncertainty.py`
  - now loads policy thresholds and runs under `active_run` so uncertainty artifacts carry full provenance run IDs.
- Updated SK-M2 policy/checker:
  - `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`
  - `scripts/skeptic/check_comparative_uncertainty.py`
  - added nested key requirements, status/reason compatibility checks, and threshold checks for strengthened statuses.
- Updated comparative reports:
  - `reports/comparative/PROXIMITY_ANALYSIS.md`
  - `reports/comparative/PHASE_B_SYNTHESIS.md`
  - `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`
  - `reports/comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md`
- Added SK-M2.2 governance artifacts:
  - `reports/skeptic/SK_M2_2_CONFIDENCE_REGISTER.md`
  - `reports/skeptic/SK_M2_2_METHOD_SELECTION.md`
  - `reports/skeptic/SKEPTIC_M2_2_EXECUTION_STATUS.md`
- Updated docs/repro guidance:
  - `docs/COMPARATIVE_UNCERTAINTY_POLICY.md`
  - `docs/REPRODUCIBILITY.md`
- Added verify-path SK-M2 checks:
  - `scripts/verify_reproduction.sh`
  - `tests/audit/test_verify_reproduction_contract.py`

### Verification

- `python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42` -> PASS
- Registered 9-lane confidence matrix executed (`seeds: 42/314/2718`, `iterations: 2000/4000/8000`) -> all lanes produced valid artifacts and consistent residual class.
- `python3 scripts/skeptic/check_comparative_uncertainty.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_comparative_uncertainty.py --mode release` -> PASS
- `python3 -m pytest tests/comparative/test_mapping_uncertainty.py tests/skeptic/test_comparative_uncertainty_checker.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`14 passed`)
- `python3 -m pytest tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`11 passed`)

### Current Evidence State

- Canonical SK-M2 artifact remains `INCONCLUSIVE_UNCERTAINTY`, now with richer diagnostics:
  - `reason_code=TOP2_GAP_FRAGILE`
  - `nearest_neighbor_stability=0.4565`
  - `jackknife_nearest_neighbor_stability=0.8333`
  - `rank_stability=0.4565`
  - `nearest_neighbor_probability_margin=0.0670`
  - `top2_gap.ci95_lower=0.0263`
- Matrix-wide behavior was homogeneous across registered lanes (no lane reached qualified/confirmed thresholds).
- SK-M2.2 closure outcome is `M2_2_QUALIFIED` with bounded directional claims and strengthened contract governance.


## 2026-02-10 - Skeptic SK-H2.2 / SK-M1.2 Operational Claim-Entitlement Hardening

Source plan: `planning/skeptic/SKEPTIC_H2_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-H2 / SK-M1` pass-2 residual)

### Opened

- Pass-2 skeptic assessment showed closure/non-claim language was materially improved but still vulnerable when operational gates fail.
- Existing H2/M1 checks were static text-policy checks and did not enforce gate-dependent entitlement downgrade.
- No canonical artifact existed to map current gate-health posture to allowed claim/closure class.

### Decisions

- Introduce a canonical release gate-health artifact for entitlement control.
- Extend SK-H2/SK-M1 policies and checkers so degraded gate state enforces stronger contingency language.
- Add explicit operational entitlement markers in public closure/summary documents.
- Integrate gate-health generation and entitlement checks into CI/pre-release/reproduction paths.

### Execution Notes

- Added gate-health builder and canonical artifact path:
  - `scripts/audit/build_release_gate_health_status.py`
  - `status/audit/release_gate_health_status.json`
  - `status/audit/by_run/release_gate_health_status.<run_id>.json`
- Extended H2/M1 policies for gate-dependent enforcement:
  - `configs/skeptic/sk_h2_claim_language_policy.json`
  - `configs/skeptic/sk_m1_closure_policy.json`
- Extended checker logic:
  - `scripts/skeptic/check_claim_boundaries.py`
  - `scripts/skeptic/check_closure_conditionality.py`
- Extended coherence policy coverage for operational entitlement markers/artifact:
  - `configs/skeptic/sk_m3_report_coherence_policy.json`
  - `docs/REPORT_COHERENCE_POLICY.md`
- Calibrated target docs with explicit operational entitlement sections:
  - `README.md`
  - `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`
  - `reports/comparative/PHASE_B_SYNTHESIS.md`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md`
- Updated policy docs and reproducibility guidance:
  - `docs/CLAIM_BOUNDARY_POLICY.md`
  - `docs/CLOSURE_CONDITIONALITY_POLICY.md`
  - `docs/REOPENING_CRITERIA.md`
  - `docs/REPRODUCIBILITY.md`
- Updated registers and added H2.2 status artifacts:
  - `reports/skeptic/SK_H2_CLAIM_REGISTER.md`
  - `reports/skeptic/SK_M1_CLOSURE_REGISTER.md`
  - `reports/skeptic/SK_H2_M1_2_ASSERTION_REGISTER.md`
  - `reports/skeptic/SKEPTIC_H2_2_EXECUTION_STATUS.md`
- Integrated gate-health/entitlement checks into gate scripts:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Added/updated tests:
  - `tests/skeptic/test_claim_boundary_checker.py`
  - `tests/skeptic/test_closure_conditionality_checker.py`
  - `tests/skeptic/test_report_coherence_checker.py`
  - `tests/audit/test_release_gate_health_status_builder.py`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`

### Verification

- `python3 scripts/audit/build_release_gate_health_status.py` -> PASS (artifact emitted)
- `python3 scripts/skeptic/check_claim_boundaries.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_claim_boundaries.py --mode release` -> PASS
- `python3 scripts/skeptic/check_closure_conditionality.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_closure_conditionality.py --mode release` -> PASS
- `python3 scripts/skeptic/check_report_coherence.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_report_coherence.py --mode release` -> PASS
- `python3 -m py_compile scripts/audit/build_release_gate_health_status.py scripts/skeptic/check_claim_boundaries.py scripts/skeptic/check_closure_conditionality.py scripts/skeptic/check_report_coherence.py` -> PASS
- `python3 -m pytest -q tests/skeptic/test_claim_boundary_checker.py tests/skeptic/test_closure_conditionality_checker.py tests/skeptic/test_report_coherence_checker.py tests/audit/test_release_gate_health_status_builder.py tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`28 passed`)

### Current Evidence State

- Canonical gate-health artifact currently reports:
  - `status=GATE_HEALTH_DEGRADED`
  - `reason_code=GATE_CONTRACT_BLOCKED`
  - `allowed_claim_class=QUALIFIED`
  - `allowed_closure_class=CONDITIONAL_CLOSURE_QUALIFIED`
- Current degraded posture is driven by unresolved sensitivity release contract conditions (`dataset_policy_pass=false`, `warning_policy_pass=false`, release readiness not yet satisfied).
- SK-H2.2/SK-M1.2 closure outcome is `H2_2_M1_2_QUALIFIED`: claim-scope enforcement is now operationally coupled and fail-closed.


## 2026-02-10 - Skeptic SK-M4.2 Provenance Confidence Closure

Source plan: `planning/skeptic/SKEPTIC_M4_2_EXECUTION_PLAN.md`  
Source finding: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-M4` pass-2 residual)

### Opened

- Pass-2 SK-M4 residual remained `PROVENANCE_QUALIFIED` and required stronger closure discipline.
- Provenance register/report drift had to be eliminated via canonical synchronization.
- Provenance confidence language required explicit coupling to gate-health/contract posture.

### Decisions

- Add a deterministic register sync contract with machine-checkable drift status.
- Couple provenance confidence class and reason codes to operational gate-health outcomes.
- Fail closed when coupling is broken or register drift is detected.
- Keep closure qualified unless historical orphan constraints are actually resolved.

### Execution Notes

- Added canonical sync tool and status artifact:
  - `scripts/audit/sync_provenance_register.py`
  - `status/audit/provenance_register_sync_status.json`
- Extended provenance health builder for contract coupling:
  - `scripts/audit/build_provenance_health_status.py`
- Extended SK-M4 checker for coupling/drift enforcement:
  - `scripts/skeptic/check_provenance_uncertainty.py`
- Updated SK-M4.2 policy contract:
  - `configs/skeptic/sk_m4_provenance_policy.json`
- Integrated SK-M4.2 sync/checks into gates:
  - `scripts/ci_check.sh`
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- Added/updated tests:
  - `tests/audit/test_sync_provenance_register.py`
  - `tests/skeptic/test_provenance_uncertainty_checker.py`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
- Updated provenance docs and skeptic registers:
  - `docs/HISTORICAL_PROVENANCE_POLICY.md`
  - `docs/PROVENANCE.md`
  - `docs/REPRODUCIBILITY.md`
  - `reports/skeptic/SK_M4_PROVENANCE_REGISTER.md`
  - `reports/skeptic/SK_M4_2_GAP_REGISTER.md`
  - `reports/skeptic/SKEPTIC_M4_2_EXECUTION_STATUS.md`

### Verification

- `python3 scripts/audit/repair_run_statuses.py --dry-run --report-path status/audit/run_status_repair_report.json` -> PASS
- `python3 scripts/audit/build_release_gate_health_status.py` -> PASS
- `python3 scripts/audit/build_provenance_health_status.py` -> PASS
- `python3 scripts/audit/sync_provenance_register.py` -> PASS
- `python3 scripts/skeptic/check_provenance_uncertainty.py --mode ci` -> PASS
- `python3 scripts/skeptic/check_provenance_uncertainty.py --mode release` -> PASS
- `python3 -m pytest tests/skeptic/test_provenance_uncertainty_checker.py tests/audit/test_sync_provenance_register.py tests/audit/test_ci_check_contract.py tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py` -> PASS (`19 passed`)

### Current Evidence State

- Canonical provenance artifact (`status/audit/provenance_health_status.json`) currently reports:
  - `status=PROVENANCE_QUALIFIED`
  - `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
  - `run_status_counts.success=156`
  - `orphaned_rows=63`
  - `threshold_policy_pass=true`
  - `contract_health_status=GATE_HEALTH_DEGRADED`
  - `contract_health_reason_code=GATE_CONTRACT_BLOCKED`
  - `contract_reason_codes=[PROVENANCE_CONTRACT_BLOCKED]`
  - `contract_coupling_pass=true`
- Canonical sync artifact (`status/audit/provenance_register_sync_status.json`) currently reports:
  - `status=IN_SYNC`
  - `drift_detected=false`
  - `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
  - `contract_coupling_state=COUPLED_DEGRADED`
- SK-M4.2 closure outcome is `M4_2_QUALIFIED`: drift is remediated and policy-coupled, while historical uncertainty remains explicitly bounded.
