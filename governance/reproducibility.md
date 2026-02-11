# Reproducibility Guide

This guide documents the command path to reproduce Phases 2 through 7 using the
current repository scripts.

## 1. Environment Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you do not activate a venv, the verification scripts still run but print a warning.
Set an explicit interpreter if needed:

```bash
export PYTHON_BIN=python3
```

## 2. Data and Schema Initialization

```bash
python3 scripts/phase1_foundation/acceptance_test.py
```

## 3. Phase 2 (Analysis) Reproduction

```bash
python3 scripts/phase2_analysis/run_phase_2_1.py
python3 scripts/phase2_analysis/run_phase_2_2.py
python3 scripts/phase2_analysis/run_phase_2_3.py
python3 scripts/phase2_analysis/run_phase_2_4.py
```

## 4. Phase 3 (Synthesis) Reproduction

```bash
python3 scripts/phase3_synthesis/extract_grammar.py
python3 scripts/phase3_synthesis/run_phase_3.py
python3 scripts/phase3_synthesis/run_test_a.py --seed 42 --output core_status/phase3_synthesis/TEST_A_RESULTS.json
python3 scripts/phase3_synthesis/run_test_b.py
python3 scripts/phase3_synthesis/run_test_c.py
python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 scripts/phase3_synthesis/run_baseline_assessment.py
```

## 5. Phase 4-6 (Mechanism and Inference) Reproduction

### Mechanism pilots (Phase 5 family)

```bash
python3 scripts/phase5_mechanism/run_5b_pilot.py
python3 scripts/phase5_mechanism/run_5c_pilot.py
python3 scripts/phase5_mechanism/run_5d_pilot.py
python3 scripts/phase5_mechanism/run_5e_pilot.py
python3 scripts/phase5_mechanism/run_5f_pilot.py
python3 scripts/phase5_mechanism/run_5g_pilot.py
python3 scripts/phase5_mechanism/run_5j_pilot.py
python3 scripts/phase5_mechanism/run_5k_pilot.py
python3 scripts/phase5_mechanism/run_pilot.py
```

### Inference runners

```bash
python3 scripts/phase4_inference/build_corpora.py
python3 scripts/phase4_inference/run_lang_id.py
python3 scripts/phase4_inference/run_montemurro.py
python3 scripts/phase4_inference/run_morph.py
python3 scripts/phase4_inference/run_network.py
python3 scripts/phase4_inference/run_topics.py
```

## 6. Phase 7 (Human/Codicological) Reproduction

```bash
python3 scripts/phase7_human/run_7a_human_factors.py
python3 scripts/phase7_human/run_7b_codicology.py
python3 scripts/phase7_human/run_7c_comparative.py
```

## 7. Phase 8 (Visualization and Publication) Reproduction

### Visualization generation

```bash
# Foundation plots
support_visualization phase1_foundation token-frequency voynich_real
support_visualization phase1_foundation repetition-rate voynich_real

# Analysis plots (after running sensitivity sweep)
support_visualization phase2_analysis sensitivity-sweep core_status/core_audit/sensitivity_sweep.json

# Synthesis plots (after baseline assessment)
support_visualization phase3_synthesis gap-phase2_analysis core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json

# Inference plots (after running phase4_inference runners)
support_visualization phase4_inference lang-id results/data/phase4_inference/lang_id_results.json
```

### Publication drafting

```bash
python3 scripts/support_preparation/assemble_draft.py
```

## 8. Seed and Determinism Notes

- Most scripts encode deterministic seed usage internally (commonly `seed=42`
  via `active_run(config=...)` and seeded constructors).
- `run_test_a.py` supports explicit `--seed` and `--output` flags for reproducibility checks.
- Reproduction checks compare canonicalized `results` payloads (excluding volatile
  provenance timestamps/run identifiers).
- `run_indistinguishability_test.py` is strict-by-default and release-evidentiary in default mode.
- Exploratory fallback mode must be explicit:

```bash
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --allow-fallback
```

- Equivalent strict explicit form (also accepted):

```bash
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py
```

- Quick strict prerequisite check (no phase3_synthesis run, preflight only):
  - Preflight now canonicalizes split folio ids (for example `f89r1`/`f89r2` are matched as `f89r`).

```bash
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
```

- For strict fallback enforcement during reruns:

```bash
export REQUIRE_COMPUTED=1
```

## 9. Provenance and Outputs

- Runner outputs include a `provenance` block (`run_id`, timestamps, commit).
- Outputs are written to both:
  - run-scoped immutable snapshots under `.../by_run/*.json`
  - backward-compatible latest pointer paths (the historical static filenames)
- See `governance/PROVENANCE.md` for full policy.
- `core_status/` is transient execution output and is not treated as release evidence.
- Release evidence should come from `reports/` plus provenance-managed `results/.../by_run/`.

## 10. Automated Verification

Use both checks after a clean reproduction run:

```bash
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
```

Verifier contract notes:

- `scripts/verify_reproduction.sh` must emit `VERIFY_REPRODUCTION_COMPLETED` on success.
- Any missing prerequisite or failed check must exit non-zero.
- `scripts/ci_check.sh` requires verifier completion sentinel; it must not report pass on partial verifier execution.
- Release sensitivity evidence is valid only when `release_evidence_ready=true` and robustness is conclusive (`PASS` or `FAIL`) with quality gates passing.
- Release sensitivity checks read:
  - `core_status/core_audit/sensitivity_sweep_release.json`
  - `reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md`
- Release sensitivity preflight status is recorded at:
  - `core_status/core_audit/sensitivity_release_preflight.json`
- Scenario-level resume state is recorded at:
  - `core_status/core_audit/sensitivity_checkpoint.json`
- CI/latest iterative checks read:
  - `core_status/core_audit/sensitivity_sweep.json`
  - `reports/core_audit/SENSITIVITY_RESULTS.md`
- Release sensitivity evidence also requires:
  - `dataset_policy_pass=true`
  - `warning_policy_pass=true`
  - `warning_density_per_scenario` present in summary
  - non-empty caveats when `total_warning_count > 0`
- Sensitivity artifact/report coherence is checked by:

```bash
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode ci
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
```

- Release preflight can be run independently (no sweep execution):

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
```

- Runner-level provenance contract is checked by:

```bash
python3 scripts/core_audit/check_provenance_runner_contract.py --mode ci
python3 scripts/core_audit/check_provenance_runner_contract.py --mode release
```
- Release-path strict preflight is always enforced. `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` must be generated with `strict_computed=true`.
- If strict preflight is blocked only because source pages are unavailable/lost, results must record `status=BLOCKED` and `reason_code=DATA_AVAILABILITY`.
- A `BLOCKED` strict preflight with `reason_code=DATA_AVAILABILITY` is treated as a scoped data-availability constraint, not as proof of code malfunction.
- SK-H3 closure metadata must include `h3_5_closure_lane`, `h3_5_residual_reason`, and `h3_5_reopen_conditions`.

Optional strict verification mode:

```bash
VERIFY_STRICT=1 bash scripts/verify_reproduction.sh
```

This enables additional `REQUIRE_COMPUTED=1` enforcement checks.

## 11. Sensitivity Sweep Iteration Modes

`scripts/phase2_analysis/run_sensitivity_sweep.py` supports lower-cost iteration modes for frequent local checks.

Quick iterative defaults (recommended for development loops):

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke --quick
```

Explicit iterative mode (reduced scenario profile):

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode iterative
```

Authoritative release evidence mode (full required run):

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
```

Fail-fast release preflight:

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
```

Progress visibility during long runs:

```bash
cat core_status/core_audit/sensitivity_progress.json
```

Checkpoint/resume behavior:

- `core_status/core_audit/sensitivity_checkpoint.json` is updated after each completed scenario.
- Release runs resume from checkpoint automatically when signature matches mode/dataset/scenarios.
- To force a full rerun without resume:

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --no-resume
```

## 12. SK-H1 Multimodal Coupling Reproduction

Run this sequence to reproduce confirmatory image/layout coupling evidence:

```bash
python3 scripts/phase5_mechanism/generate_all_anchors.py --dataset-id voynich_real --method-name geometric_v1 --threshold 0.10
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
```

Coverage core_audit artifact:

- `core_status/phase5_mechanism/anchor_coverage_audit.json`

Confirmatory coupling artifact:

- `results/phase5_mechanism/anchor_coupling_confirmatory.json`

Conclusive claim status must be read from:

- `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.status`
- `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.allowed_claim`
- `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.h1_4_closure_lane`
- `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.robustness.robustness_class`

H1.4 interpretation rule:

- `H1_4_ALIGNED` permits robust conclusive multimodal language within policy scope.
- `H1_4_QUALIFIED` requires explicit qualifier language: robustness remains qualified across registered lanes.

Policy source:

```bash
cat configs/core_skeptic/sk_h1_multimodal_policy.json
cat configs/core_skeptic/sk_h1_multimodal_status_policy.json
```

Status/claim coherence checks:

```bash
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release
python3 -m pytest -q tests/core_skeptic/test_multimodal_coupling_checker.py
```

## 13. SK-H2 Claim Boundary Verification

Run claim-boundary checks for public-facing conclusion language:

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_skeptic/check_claim_boundaries.py --mode ci
python3 scripts/core_skeptic/check_claim_boundaries.py --mode release
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode ci
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode release
python3 -m pytest -q tests/core_skeptic/test_claim_boundary_checker.py
```

Claim-boundary policy sources:

- `governance/CLAIM_BOUNDARY_POLICY.md`
- `configs/core_skeptic/sk_h2_claim_language_policy.json`

## 14. SK-H3 Control Comparability Verification

Run SK-H3 comparability artifacts and policy checks:

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

Primary SK-H3 policy sources:

- `governance/CONTROL_COMPARABILITY_POLICY.md`
- `configs/core_skeptic/sk_h3_control_comparability_policy.json`
- `configs/core_skeptic/sk_h3_data_availability_policy.json`

Primary artifacts:

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`

Interpretation rule:

- `evidence_scope=available_subset` indicates bounded subset evidence only.
- `full_data_closure_eligible=false` means full-dataset comparability remains blocked.
- `available_subset_reason_code=AVAILABLE_SUBSET_UNDERPOWERED` indicates subset diagnostics failed thresholds and cannot support closure language.
- `approved_lost_pages_policy_version` and `approved_lost_pages_source_note_path` must match the active data-availability policy.
- `irrecoverability.classification` must be present in both SK-H3 status artifacts.

Quick SK-H3.4 semantic parity check:

```bash
python3 - <<'PY'
import json
s=json.load(open('core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json'))['results']
a=json.load(open('core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json'))['results']
print('status', s['status'], s['reason_code'], s['available_subset_reason_code'])
print('scope', s['evidence_scope'], 'full_closure', s['full_data_closure_eligible'])
print('policy_version', s['approved_lost_pages_policy_version'])
print('source_note', s['approved_lost_pages_source_note_path'])
print('feasibility', s['full_data_feasibility'])
print('terminal_reason', s['full_data_closure_terminal_reason'])
print('reopen_conditions', s['full_data_closure_reopen_conditions'])
print('lane', s['h3_4_closure_lane'])
print('irrecoverability', s['irrecoverability'])
print('parity', s['irrecoverability'] == a['irrecoverability'])
print('lane_parity', s['h3_4_closure_lane'] == a['h3_4_closure_lane'])
PY
```

## 15. SK-M1 Closure Conditionality Verification

Run closure-conditionality policy checks:

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_skeptic/check_closure_conditionality.py --mode ci
python3 scripts/core_skeptic/check_closure_conditionality.py --mode release
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode ci
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode release
python3 -m pytest -q tests/core_skeptic/test_closure_conditionality_checker.py
```

Primary SK-M1 policy sources:

- `governance/CLOSURE_CONDITIONALITY_POLICY.md`
- `governance/REOPENING_CRITERIA.md`
- `configs/core_skeptic/sk_m1_closure_policy.json`

Primary trace artifact:

- `reports/core_skeptic/SK_M1_CLOSURE_REGISTER.md`

## 16. SK-M2 Comparative Uncertainty Verification

Run phase8_comparative uncertainty artifact and policy checks:

```bash
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --profile smoke --seed 42
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --profile release-depth --seed 42
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release
python3 -m pytest -q tests/core_skeptic/test_comparative_uncertainty_checker.py
```

Inspect SK-M2.4 confidence and lane diagnostics:

```bash
python3 - <<'PY'
import json
r=json.load(open('results/phase7_human/phase_7c_uncertainty.json'))['results']
print(r['status'], r['reason_code'])
print('lane', r['m2_4_closure_lane'])
print('nearest', r['nearest_neighbor_stability'])
print('jackknife', r['jackknife_nearest_neighbor_stability'])
print('rank', r['rank_stability'])
print('margin', r['nearest_neighbor_probability_margin'])
print('top2_ci_low', r['top2_gap']['ci95_lower'])
print('flip_rate', r['fragility_diagnostics']['top2_identity_flip_rate'])
print('dominant_signal', r['fragility_diagnostics']['dominant_fragility_signal'])
PY
```

Primary SK-M2 policy sources:

- `governance/COMPARATIVE_UNCERTAINTY_POLICY.md`
- `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json`

Primary artifact:

- `results/phase7_human/phase_7c_uncertainty.json`

## 17. SK-M3 Report Coherence Verification

Run report-coherence policy checks:

```bash
python3 scripts/core_skeptic/check_report_coherence.py --mode ci
python3 scripts/core_skeptic/check_report_coherence.py --mode release
python3 -m pytest -q tests/core_skeptic/test_report_coherence_checker.py
```

Primary SK-M3 policy sources:

- `governance/REPORT_COHERENCE_POLICY.md`
- `configs/core_skeptic/sk_m3_report_coherence_policy.json`

Primary SK-M3 artifact:

- `results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json`

## 18. SK-M4 Historical Provenance Verification

Run canonical provenance-health generation and policy checks:

```bash
python3 scripts/core_audit/repair_run_statuses.py --dry-run --report-path core_status/core_audit/run_status_repair_report.json
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_audit/sync_provenance_register.py
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
python3 -m pytest -q tests/core_skeptic/test_provenance_uncertainty_checker.py
```

Primary SK-M4 policy sources:

- `governance/HISTORICAL_PROVENANCE_POLICY.md`
- `governance/PROVENANCE.md`
- `configs/core_skeptic/sk_m4_provenance_policy.json`

Primary SK-M4 artifact:

- `core_status/core_audit/provenance_health_status.json`
- `core_status/core_audit/provenance_register_sync_status.json`

## 19. Release Baseline Checklist

Before declaring a reproducible release baseline:

1. Run verification commands in Section 10.
2. Confirm sensitivity report caveats are present in `reports/core_audit/SENSITIVITY_RESULTS.md`.
3. Confirm no unintended transient artifacts are staged:

```bash
git status --short
```

4. Confirm artifact policy alignment:

```bash
rg -n "^core_status/?$|^core_status/" .gitignore
```

5. Confirm required core_audit log is present and updated:

```bash
test -f AUDIT_LOG.md
```

6. Validate release-evidence sensitivity artifact and baseline gate:

```bash
bash scripts/core_audit/pre_release_check.sh
```

Sensitivity policy source:

```bash
cat configs/core_audit/release_evidence_policy.json
cat configs/core_audit/sensitivity_artifact_contract.json
```

If a non-clean tree is intentional for a controlled release cut, you may override:

```bash
ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='AUDIT-10: controlled release-candidate validation' bash scripts/core_audit/pre_release_check.sh
```

`DIRTY_RELEASE_REASON` must include `:` and be at least 12 characters.

7. Optionally clean transient verification artifacts before release packaging:

```bash
bash scripts/core_audit/cleanup_status_artifacts.sh dry-run
bash scripts/core_audit/cleanup_status_artifacts.sh legacy-report
bash scripts/core_audit/cleanup_status_artifacts.sh clean
```
