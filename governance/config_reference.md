# Configuration Reference

This document catalogues all JSON configuration files in the `configs/`
directory, their purpose, which scripts read them, and the key parameters
they control.

---

## Phase 2: Analysis

### `configs/phase2_analysis/thresholds.json`

**Purpose:** Centralized thresholds for Phase 2 stress tests (mapping stability,
locality, compositionality, information preservation) and indistinguishability
separation.

**Read by:**
- `src/phase2_analysis/stress_tests/mapping_stability.py` (via `get_analysis_thresholds()`)
- `src/phase2_analysis/stress_tests/locality_compositionality.py`
- `src/phase3_synthesis/indistinguishability.py`

**Key parameters:**
- `mapping_stability.perturbation_strength` — boundary shift fraction (default 0.05)
- `mapping_stability.constructed_system.ordering_collapse` — ordering collapse threshold (0.5)
- `mapping_stability.constructed_system.min_stable` — minimum stability for constructed systems (0.6)
- `mapping_stability.visual_grammar.segmentation_collapse` — segmentation collapse threshold (0.4)
- `mapping_stability.standard_high_confidence` — high-confidence stability baseline (0.7)
- `indistinguishability.separation_success` — success threshold (0.7)
- `indistinguishability.separation_failure` — failure threshold (0.3)

### `configs/phase2_analysis/anomaly_observed.json`

**Purpose:** Fixed observed values from Phase 1–3 used as constraint inputs in
anomaly characterization modules (stability baselines, capacity bounds).

**Read by:**
- `src/phase1_foundation/config.py` (via `get_anomaly_observed_values()`)
- `src/phase2_analysis/stress_tests/` modules

**Key parameters:** Stability baseline, capacity bounding parameters, constraint
parameters from prior phases. These are treated as fixed inputs, not tunable.

---

## Phase 6: Functional

### `configs/phase6_functional/model_params.json`

**Purpose:** Externalized model sensitivity weights and evaluation dimension
weights for the Phase 6 disconfirmation perturbation battery.

**Read by:**
- `src/phase1_foundation/config.py` (via `get_model_params()`)
- Phase 6 evaluation modules

**Key parameters:**
- Perturbation battery weights (segmentation, ordering, omission, anchor disruption)
- Strength levels and failure thresholds per perturbation type
- Calibration notes in `governance/CALIBRATION_NOTES.md`

### `configs/phase6_functional/synthesis_params.json`

**Purpose:** Continuation generation tolerances and indistinguishability
thresholds for synthesis evaluation.

**Key parameters:**
- Locality/information density/entropy/repetition windows
- Scrambled control indistinguishability threshold (0.7)
- Real data indistinguishability threshold (0.3)
- Equivalence improvement thresholds (0.30/0.10)

### `configs/phase6_functional/baselines.json`

**Purpose:** Observed capacity bounds and comparative baselines for evaluation
against random Markov chains, natural language, and simple ciphers.

**Key parameters:** Memory, entropy, vocabulary, and locality bounds with
comparative reference values.

---

## Phase 10: Admissibility

### `configs/phase10_admissibility/stage1b_upgrade_gate.json`

**Purpose:** Pre-registered upgrade gate configuration for Phase 10 Stage 1b
(J/K confirmatory testing).

**Read by:** `scripts/phase10_admissibility/run_stage1b_jk_replication.py`

### `configs/phase10_admissibility/stage5_high_roi_gate.json`

**Purpose:** Pre-registered confirmatory gate for Phase 10 tension resolution
targeting Method F.

**Key parameters:** Seeds, token windows, perturbation counts, null profile
configuration.

**Read by:** `scripts/phase10_admissibility/run_stage5_high_roi.py`

### `configs/phase10_admissibility/stage5b_k_adjudication_gate.json`

**Purpose:** Targeted adjudication gate for Method K in Phase 10 Stage 5b.

**Read by:** `scripts/phase10_admissibility/run_stage5b_k_adjudication.py`

---

## Core Audit

### `configs/core_audit/release_evidence_policy.json`

**Purpose:** Release gating policy for CI and release modes, defining minimum
data requirements and warning limits.

**Key parameters:**
- Minimum pages (200), minimum tokens (200k)
- Maximum total warnings (400)
- Dataset policy requirements

**Read by:** `scripts/core_audit/pre_release_check.sh`,
`scripts/core_audit/check_sensitivity_artifact_contract.py`

### `configs/core_audit/sensitivity_artifact_contract.json`

**Purpose:** SK-C1.5 contract defining artifact/report paths and required
summary fields for sensitivity sweep execution.

**Read by:** `scripts/core_audit/check_sensitivity_artifact_contract.py`

### `configs/core_audit/provenance_runner_contract.json`

**Purpose:** SK-C2.2 runner-level provenance contract specifying which scripts
require `ProvenanceWriter` and delegated provenance paths.

**Read by:** `scripts/core_audit/check_provenance_runner_contract.py`

---

## Core Skeptic

### `configs/core_skeptic/sk_h1_multimodal_policy.json`

**Purpose:** Multimodal coupling policy for Phase B boundary assertions and
H1.4/H1.5 closure semantics.

**Read by:** `scripts/core_skeptic/check_multimodal_coupling.py`

### `configs/core_skeptic/sk_h1_multimodal_status_policy.json`

**Purpose:** Multimodal status tracking and robustness class entitlements.

**Read by:** `scripts/core_skeptic/check_multimodal_coupling.py`

### `configs/core_skeptic/sk_h2_claim_language_policy.json`

**Purpose:** Claim language validation for H2 closure governance.

**Read by:** `scripts/core_skeptic/check_claim_boundaries.py`

### `configs/core_skeptic/sk_h3_control_comparability_policy.json`

**Purpose:** SK-H3.5 control comparability policy enforcing anti-circularity,
terminal-qualified closure, and bounded available-subset diagnostics.

**Read by:** `scripts/core_skeptic/check_control_comparability.py`

### `configs/core_skeptic/sk_h3_data_availability_policy.json`

**Purpose:** SK-H3.5 data-availability policy specifying expected Voynich pages
(f88r–f96v), approved lost pages (f91r/v, f92r/v), and terminal-qualified
closure classification.

**Read by:** `scripts/core_skeptic/check_control_data_availability.py`

### `configs/core_skeptic/sk_m1_closure_policy.json`

**Purpose:** SK-M1 closure conditionality policy for contradictory
terminal-closure language with gate-dependent entitlement controls.

**Read by:** `scripts/core_skeptic/check_closure_conditionality.py`

### `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json`

**Purpose:** Comparative uncertainty policy tracking measurement, assumption,
and sensitivity sources.

**Read by:** `scripts/core_skeptic/check_comparative_uncertainty.py`

### `configs/core_skeptic/sk_m3_report_coherence_policy.json`

**Purpose:** Report coherence constraints for Phase B.

**Read by:** `scripts/core_skeptic/check_report_coherence.py`

### `configs/core_skeptic/sk_m4_provenance_policy.json`

**Purpose:** Provenance validation policy for Phase B.

**Read by:** `scripts/core_skeptic/check_provenance_uncertainty.py`

---

## Phases 11-20: No External Configs

Phases 11-20 (stroke topology, mechanical reconstruction, high-fidelity emulation,
rule extraction, physical grounding, finality, state machine) do not use external
JSON configuration files. Their parameters are passed inline via `active_run(config={...})`
and recorded in per-run provenance envelopes. This design decision was made because
these phases have few tunable parameters (primarily `seed` and script-specific flags)
and the inline approach ensures parameter values are always co-located with the
run provenance record.

---

## Environment Variables

For environment variables that control runtime behavior, see `.env.example`.

---

## Transcription Source

The canonical transcription source is set in
`src/phase1_foundation/core/data_loading.py`:

- `DEFAULT_SOURCE_ID = "zandbergen_landini"`

This is not configurable via environment variable by design — changing the
transcription source would invalidate all downstream results. The ZL
transcription uses EVA lowercase encoding; see `governance/methods_reference.md`
Section 0 for full details.
