# Replicating Results: External Reviewer Guide

**Target Publication:** `Voynich_Structural_Identification_Final_021526` (February 15, 2026)
**Repository:** Zenodo DOI v1.0.1 (archived)
**Last Verified:** 2026-02-21

---

## Overview

This document provides a step-by-step path for an external party to reproduce
every quantitative claim in the publication from source code and raw data. The
project spans 18 release-canonical research phases (Phases 1-17 and 20).
Phase 11 Stroke Topology reached fast-kill termination; Phase 13 Demonstration
is a visualization-only phase.

Exploratory/post-publication phases (18-19) are tracked separately and are not
part of the default release-canonical replication path. See
[governance/RELEASE_SCOPE.md](governance/RELEASE_SCOPE.md).

**Estimated wall-clock time:** 4-8 hours (single machine, Phase 10 permutation
tests dominate).

---

## Prerequisites

### 1. System Requirements

| Requirement | Tested Value | Minimum |
|---|---|---|
| Python | 3.11.13 (CPython, arm64) | 3.11+ |
| RAM | 16 GB | 8 GB |
| Disk | 15 GB (including external data) | 15 GB |
| OS | macOS Darwin 25.3.0 (arm64) | macOS or Linux |

### 2. Clone and Environment Setup

```bash
git clone <repository-url> voynichMS
cd voynichMS
python3.11 -m venv .venv
source .venv/bin/activate

# Option A: Exact reproduction (recommended — pinned versions matching publication)
pip install -r requirements-lock.txt

# Option B: Compatible reproduction (minimum-version constraints, may diverge on edge cases)
pip install -r requirements.txt
```

**Note on Python version:** The publication results were generated with Python
3.11.13. Different minor versions (3.12, 3.13) may produce subtly different
floating-point results or hash orderings. For exact reproduction, use 3.11.x.

### 3. External Data Acquisition

The following data must be obtained before running any pipeline scripts.
See [DATA_SOURCES.md](DATA_SOURCES.md) for download links and checksums.

**Automated download:** Run `python3 scripts/phase0_data/download_external_data.py`
to fetch IVTFF transliterations and Gutenberg corpora automatically. Yale scans
must be downloaded manually (see `--include-scans` for instructions).

| Dataset | Size | Destination | Required By |
|---|---|---|---|
| IVTFF 2.0 transliterations | ~2 MB | `data/raw/transliterations/ivtff2.0/` | Phase 1+ |
| Yale Beinecke JPEG scans | ~550 MB | `data/raw/scans/jpg/folios_full/` | Phase 5 (anchoring), Phase 7 |
| Latin corpus (Caesar) | ~1 MB | `data/external_corpora/latin/` | Phase 4 |
| English corpus (Carroll) | ~200 KB | `data/external_corpora/english/` | Phase 4 |
| German corpus (Kafka) | ~200 KB | `data/external_corpora/german/` | Phase 4 |
| Phase 10 multilingual corpora | ~5 MB | `data/external_corpora/multilingual/` | Phase 10 Method H |

**Critical:** The primary transliteration file is `ZL3b-n.txt` (Zandbergen-Landini).
All tokenization flows through the canonical `EVAParser` from this file.

### 4. Environment Variables

```bash
export REQUIRE_COMPUTED=1   # Enforces strict mode (no fallback placeholders)
# Optional:
export PYTHON_BIN=python3   # Override Python interpreter
```

---

## Reproduction Path

### Phase 1: Foundation (Digital Ledgering)

Populates the SQLite database from raw IVTFF transliterations.

```bash
python3 scripts/phase1_foundation/acceptance_test.py
python3 scripts/phase1_foundation/populate_database.py
python3 scripts/phase1_foundation/populate_glyphs.py
python3 scripts/phase1_foundation/run_destructive_audit.py
```

**Verifies:** Database schema integrity, glyph identity fragility (37.5%
collapse at 5% perturbation), word boundary stability (75% agreement).

**Key outputs:**
- `data/voynich.db` (SQLite database, ~400 MB — regenerated, not distributed.
  The `.gitignore` excludes `*.db` files. Always regenerate from raw IVTFF data.)
- `core_status/phase1_foundation/FINDINGS_PHASE_1_FOUNDATION.md`

---

### Phase 2: Analysis (Admissibility Stress Tests)

Tests which explanation classes survive structural constraints.

```bash
python3 scripts/phase2_analysis/run_phase_2_1.py
python3 scripts/phase2_analysis/run_phase_2_2.py
python3 scripts/phase2_analysis/run_phase_2_3.py
python3 scripts/phase2_analysis/run_phase_2_4.py
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke
```

**Verifies:** Natural language and enciphered language ruled inadmissible;
visual grammar and constructed system remain admissible.

**Key outputs:**
- `core_status/core_audit/sensitivity_sweep.json`

---

### Phase 3: Synthesis (Generative Reconstruction)

Tests whether non-semantic generators can reproduce manuscript metrics.

```bash
python3 scripts/phase3_synthesis/extract_grammar.py
python3 scripts/phase3_synthesis/run_phase_3.py
python3 scripts/phase3_synthesis/run_baseline_assessment.py
python3 scripts/phase3_synthesis/run_test_a.py --seed 42
python3 scripts/phase3_synthesis/run_test_b.py
python3 scripts/phase3_synthesis/run_test_c.py
python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 scripts/phase3_synthesis/run_control_matching_audit.py
```

**Verifies:** Mechanical generators achieve indistinguishability on core
metrics. Repetition rate 0.9003, mapping stability 0.02.

**Key outputs:**
- `data/derived/voynich_grammar.json` (grammar used by later phases)
- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`

---

### Phase 4: Inference (Noise Floor Mapping)

Evaluates whether standard decipherment methods distinguish signal from noise.

```bash
python3 scripts/phase4_inference/build_corpora.py
python3 scripts/phase4_inference/run_lang_id.py
python3 scripts/phase4_inference/run_montemurro.py
python3 scripts/phase4_inference/run_morph.py
python3 scripts/phase4_inference/run_network.py
python3 scripts/phase4_inference/run_topics.py
```

**Verifies:** Information clustering false positive (self-citation scores 3.58-3.62
vs manuscript 2.20). Language ID produces false positives on random noise. No
method reliably separates manuscript from mechanical generators.

**Key outputs:**
- `results/data/phase4_inference/lang_id_results.json`
- `results/reports/phase4_inference/phase_4_5_closure_statement.md`

---

### Phase 5: Mechanism Identification (Constraint Lattice)

Identifies the specific mechanical process class.

```bash
python3 scripts/phase5_mechanism/run_pilot.py
python3 scripts/phase5_mechanism/run_5b_pilot.py
python3 scripts/phase5_mechanism/run_5c_pilot.py
python3 scripts/phase5_mechanism/run_5d_pilot.py
python3 scripts/phase5_mechanism/run_5e_pilot.py
python3 scripts/phase5_mechanism/run_5f_pilot.py
python3 scripts/phase5_mechanism/run_5g_pilot.py
python3 scripts/phase5_mechanism/run_5j_pilot.py
python3 scripts/phase5_mechanism/run_5k_pilot.py
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
```

**Verifies:** Mechanism class = Globally Stable Deterministic Rule-Evaluated
Constraint Lattice. Reset score 0.9585, successor entropy 3.4358, successor
consistency 0.8592, line TTR 0.9839.

**Key outputs:**
- `results/data/phase5_mechanism/` (per-pilot JSON results)
- `results/reports/phase5_mechanism/phase_5_final_findings_summary.md`

---

### Phase 6: Functional Analysis

Characterizes the system's functional class.

```bash
python3 scripts/phase6_functional/run_6a_exhaustion.py
python3 scripts/phase6_functional/run_6b_efficiency.py
python3 scripts/phase6_functional/run_6c_adversarial.py
```

**Verifies:** Formal-system execution confirmed (coverage 0.9168, hapax 0.9638,
deviation 0.0000). Efficiency-indifferent (reuse suppression 0.9896).
Indifferent formal system (prediction accuracy 0.0019).

---

### Phase 7: Human Factors and Codicology

Analyzes scribe behavior and physical manuscript structure.

```bash
python3 scripts/phase7_human/run_7a_human_factors.py
python3 scripts/phase7_human/run_7b_codicology.py
python3 scripts/phase7_human/run_7c_comparative.py
```

---

### Phase 8: Comparative Analysis

Measures proximity to known historical artifacts.

```bash
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
```

**Verifies:** Nearest neighbor = combinatorial systems (Lullian-style); moderate
proximity, not decisive. Manuscript remains structurally isolated.

---

### Phase 9: Conjecture (Narrative Synthesis)

Read-only synthesis phase. No new computation.

```bash
python3 scripts/phase9_conjecture/replicate.py
```

---

### Phase 10: Adversarial Admissibility Retest (Methods F-K)

Tests six methods designed to defeat the Phase 4.5 closure.

```bash
# Stage 1: Methods H, J, K
python3 scripts/phase10_admissibility/run_stage1_hjk.py --seed 42

# Stage 1B: J/K replication across seeds
python3 scripts/phase10_admissibility/run_stage1b_jk_replication.py --seeds 42,77,101

# Stage 2: Methods G, I
python3 scripts/phase10_admissibility/run_stage2_gi.py

# Stage 3: Method F
python3 scripts/phase10_admissibility/run_stage3_f.py

# Stage 4: Synthesis
python3 scripts/phase10_admissibility/run_stage4_synthesis.py

# Stage 5: High-ROI confirmatory runs
python3 scripts/phase10_admissibility/run_stage5_high_roi.py

# Stage 5B: Method K adjudication
python3 scripts/phase10_admissibility/run_stage5b_k_adjudication.py
```

**Verifies:**
- Methods H/I: `closure_strengthened`
- Methods J/K: `closure_weakened`
- Methods F/G: `indeterminate`
- Aggregate: `mixed_results_tension` / `in_tension`

**Key outputs:**
- `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
- `results/data/phase10_admissibility/` (per-stage JSON with run IDs)

---

### Phase 11: Stroke Topology (Fast-Kill)

Sub-glyph structural analysis. Terminated via fast-kill gate.

```bash
python3 scripts/phase11_stroke/run_11a_extract.py
python3 scripts/phase11_stroke/run_11b_cluster.py
python3 scripts/phase11_stroke/run_11c_transitions.py
```

**Verifies:** Both gate tests null at alpha=0.01. Stroke scale formally closed
as redundant. Outcome class: `STROKE_NULL`.

---

### Phase 12: Mechanical Slip Detection

Detects vertical slip artefacts in the manuscript, clusters them, and infers
the columnar grid geometry of the physical production tool.

```bash
python3 scripts/phase12_mechanical/run_12a_slip_detection.py
python3 scripts/phase12_mechanical/run_12b_cluster_analysis.py
python3 scripts/phase12_mechanical/run_12c_geometry_inference.py
python3 scripts/phase12_mechanical/run_12e_prototype_validation.py
python3 scripts/phase12_mechanical/run_12i_blueprint_synthesis.py
```

**Verifies:** 202 mechanical slips detected (ZL canonical data), permutation
z-score 9.47 sigma (10K permutations, p < 0.0001), section structural
correlation 0.721 (Herbal vs Biological).

**Key outputs:**
- `results/data/phase12_mechanical/slip_detection_results.json`
- `results/data/phase12_mechanical/slip_permutation_test.json`
- `results/data/phase12_mechanical/matrix_alignment.json`

---

### Phase 13: Demonstration (Evidence Gallery)

Visualization-only phase. Generates the evidence gallery and interactive
slip visualizations for external review. No new quantitative claims.

```bash
python3 scripts/phase13_demonstration/generate_evidence_gallery.py
python3 scripts/phase13_demonstration/run_final_fit_check.py
python3 scripts/phase13_demonstration/export_slip_viz.py
```

**Key outputs:**
- Evidence gallery HTML/images in `results/reports/phase13_demonstration/`

---

### Phase 14: Voynich Engine (Mechanical Reconstruction)

Full-scale reconstruction of the physical production tool: palette solver,
spectral reordering, MDL baseline comparison, mirror corpus generation,
and mask inference.

```bash
# Reconstruction
python3 scripts/phase14_machine/run_14a_palette_solver.py --full
python3 scripts/phase14_machine/run_14b_state_discovery.py

# Validation
python3 scripts/phase14_machine/run_14c_mirror_corpus.py
python3 scripts/phase14_machine/run_14d_overgeneration_audit.py
python3 scripts/phase14_machine/run_14e_mdl_analysis.py
python3 scripts/phase14_machine/run_14f_noise_register.py
python3 scripts/phase14_machine/run_14g_holdout_validation.py
python3 scripts/phase14_machine/run_14h_baseline_showdown.py
python3 scripts/phase14_machine/run_14i_ablation_study.py
python3 scripts/phase14_machine/run_14j_sequence_audit.py
python3 scripts/phase14_machine/run_14k_failure_viz.py

# Canonical Evaluation
python3 scripts/phase14_machine/run_14l_canonical_metrics.py
python3 scripts/phase14_machine/run_14m_refined_mdl.py
python3 scripts/phase14_machine/run_14n_chance_calibration.py

# Logic Export
python3 scripts/phase14_machine/run_14o_export_logic.py
```

**Verifies:** Palette size 7,717 tokens, mirror corpus entropy fit 87.60%,
holdout admissibility 10.81% (16.2 sigma above chance), MDL Lattice 15.73 BPT
vs Copy-Reset 10.90 BPT, optimal window count 50.

**Key outputs:**
- `results/data/phase14_machine/full_palette_grid.json`
- `results/data/phase14_machine/mirror_corpus_validation.json`
- `results/data/phase14_machine/baseline_comparison.json`
- `results/data/phase14_machine/holdout_performance.json`
- `results/data/phase14_machine/residual_analysis.json`

---

### Phase 15: Selection & Rule Extraction

Traces within-window selection decisions and extracts scribal bias rules,
including positional preference, suffix affinity, and compressibility analysis.

```bash
python3 scripts/phase15_rule_extraction/run_15a_trace_instrumentation.py
python3 scripts/phase15_rule_extraction/run_15b_extract_rules.py
python3 scripts/phase15_rule_extraction/run_15c_bias_and_compressibility.py
python3 scripts/phase15_rule_extraction/run_15d_selection_drivers.py
```

**Verifies:** 12,519 scribal decisions logged, average selection skew 21.49%,
compressibility improvement 7.93%, top selection driver = bigram context
(2.432 bits information gain).

**Key outputs:**
- `results/data/phase15_selection/choice_stream_trace.json`
- `results/data/phase15_selection/bias_modeling.json`
- `results/data/phase15_selection/selection_drivers.json`

Alias note: execution slug is `phase15_rule_extraction`; historical output
directory alias is `phase15_selection`.

---

### Phase 16: Physical Grounding

Tests ergonomic coupling between production tool layout and scribal effort,
and evaluates geometric layout optimization.

```bash
python3 scripts/phase16_physical_grounding/run_16a_ergonomic_costing.py
python3 scripts/phase16_physical_grounding/run_16b_effort_correlation.py
python3 scripts/phase16_physical_grounding/run_16c_layout_projection.py
```

**Verifies:** Effort correlation rho = -0.0003 (p=0.99, NULL result — no
ergonomic optimization detected), grid layout efficiency 81.50%.

**Key outputs:**
- `results/data/phase16_physical/effort_correlation.json`
- `results/data/phase16_physical/layout_projection.json`

Alias note: execution slug is `phase16_physical_grounding`; historical output
directory alias is `phase16_physical`.

---

### Phase 17: Physical Synthesis & Bandwidth Audit

Final synthesis phase. Generates physical blueprints of the reconstructed tool
and performs a steganographic bandwidth audit.

```bash
python3 scripts/phase17_finality/run_17a_generate_blueprints.py
python3 scripts/phase17_finality/run_17b_bandwidth_audit.py
```

**Verifies:** Realized steganographic bandwidth 7.53 bpw, total capacity
11.5 KB (~23K Latin chars equivalent), bandwidth judgment SUBSTANTIAL.

**Key outputs:**
- `results/data/phase17_finality/bandwidth_audit.json`

---

## Exploratory Phases (18-19, Optional)

Phases 18-19 are outside the release-canonical claim surface, but their
claim-bearing outputs are reproducible through documented entrypoints.

```bash
# Full exploratory extension path (after release phases)
python3 scripts/support_preparation/replicate_all.py --include-exploratory

# Per-phase exploratory entrypoints
python3 scripts/phase18_comparative/replicate.py
python3 scripts/phase19_alignment/replicate.py
```

Manifest source of truth: `configs/project/phase_manifest.json`

---

## Verification

After running all phases, execute the verification suite:

```bash
# Unit tests
python3 -m pytest tests/ -v

# CI checks (linting, type checking, policy coherence)
bash scripts/ci_check.sh

# Full reproduction verification (determinism, artifact integrity, policy alignment)
bash scripts/verify_reproduction.sh

# Optional: strict enforcement mode
VERIFY_STRICT=1 bash scripts/verify_reproduction.sh
```

### Prerequisite: `core_status/` directory

Both `ci_check.sh` and `verify_reproduction.sh` read from `core_status/`, a
directory of transient status artifacts populated during the pipeline run. This
directory is **not** checked into the repository and does not exist after a
fresh clone. You must run the full pipeline (or at minimum Phases 2, 3, 5, and
8) before verification will pass.

Key files the verification scripts require:

| File | Populated by |
|---|---|
| `core_status/core_audit/sensitivity_release_preflight.json` | `run_sensitivity_sweep.py --mode release --preflight-only` |
| `core_status/core_audit/provenance_health_status.json` | `build_provenance_health_status.py` |
| `core_status/core_audit/provenance_register_sync_status.json` | `sync_provenance_register.py` |
| `core_status/core_audit/release_gate_health_status.json` | `build_release_gate_health_status.py` |
| `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` | `run_indistinguishability_test.py` |
| `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` | `run_control_matching_audit.py` |
| `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` | `run_control_matching_audit.py` |

Additionally, `verify_reproduction.sh` reads result artifacts from
`results/data/phase5_mechanism/` and `results/data/phase7_human/` for SK-H1 and
SK-M2 policy checks.

**If verification fails with "Missing artifact" errors**, the most likely cause
is that the required phase scripts have not been run yet. Run
`python3 scripts/support_preparation/replicate_all.py` to populate all
artifacts, then retry verification. To include exploratory phases (18-19), run
`python3 scripts/support_preparation/replicate_all.py --include-exploratory`.

---

## Publication Generation

Regenerate the publication document from computed results:

```bash
# Generate individual phase Word documents
for phase in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17; do
  python3 scripts/support_preparation/generate_publication.py --phase $phase
done

# Generate the master composite document
python3 scripts/support_preparation/generate_publication.py
```

**Output:** `results/publication/`

---

## Claim-to-Script Traceability

For the complete mapping (**154 tracked claims**, including **154 fully
verifiable JSON-key claims**), see
[governance/claim_artifact_map.md](governance/claim_artifact_map.md).

Summary:

| Publication Claim | Source Phase | Script(s) | Output Artifact |
|---|---|---|---|
| Repetition rate 0.9003 | Phase 3 | `run_baseline_assessment.py` | baseline assessment JSON |
| Mapping stability 0.02 | Phase 2-3 | `run_phase_2_*.py` | phase 2 results |
| Info clustering false positive | Phase 4 | `run_montemurro.py` | lang_id_results.json |
| Reset score 0.9585 | Phase 5 | `run_pilot.py` | phase 5 mechanism JSON |
| Successor entropy 3.4358 | Phase 5 | `run_pilot.py` | phase 5 mechanism JSON |
| Successor consistency 0.8592 | Phase 5 | `run_pilot.py` | phase 5 mechanism JSON |
| Coverage ratio 0.9168 | Phase 6 | `run_6a_exhaustion.py` | phase 6 results |
| Hapax ratio 0.9638 | Phase 6 | `run_6a_exhaustion.py` | phase 6 results |
| Prediction accuracy 0.0019 | Phase 6 | `run_6c_adversarial.py` | phase 6 results |
| Phase 5K entropy reduction 88.11% | Phase 5 | `run_5k_pilot.py` | 5k pilot JSON |
| Phase 10 method outcomes | Phase 10 | Stage 1-5b scripts | PHASE_10_RESULTS.md |
| Stroke null determination | Phase 11 | `run_11a/b/c*.py` | fast_kill_termination.md |
| Mechanical slips detected (202) | Phase 12 | `run_12a_slip_detection.py` | slip_detection_results.json |
| Slip permutation z-score 9.47 sigma | Phase 12 | `run_12g_slip_permutation.py` | slip_permutation_test.json |
| Section structural correlation 0.721 | Phase 12 | `run_12d_matrix_alignment.py` | matrix_alignment.json |
| Palette size 7,717 | Phase 14 | `run_14a_palette_solver.py --full` | full_palette_grid.json |
| Mirror corpus entropy fit 87.60% | Phase 14 | `run_14c_mirror_corpus.py` | mirror_corpus_validation.json |
| Holdout admissibility 10.81% (16.2 sigma) | Phase 14 | `run_14g_holdout_validation.py` | holdout_performance.json |
| MDL: Lattice 15.73 / Copy-Reset 10.90 BPT | Phase 14 | `run_14h_baseline_showdown.py` | baseline_comparison.json |
| Scribal decisions logged (12,519) | Phase 15 | `run_15a_trace_instrumentation.py` | choice_stream_trace.json |
| Average selection skew 21.49% | Phase 15 | `run_15c_bias_and_compressibility.py` | bias_modeling.json |
| Top selection driver: bigram context | Phase 15 | `run_15d_selection_drivers.py` | selection_drivers.json |
| Effort correlation rho = -0.0003 (NULL) | Phase 16 | `run_16b_effort_correlation.py` | effort_correlation.json |
| Grid layout efficiency 81.50% | Phase 16 | `run_16c_layout_projection.py` | layout_projection.json |
| Steganographic bandwidth 7.53 bpw | Phase 17 | `run_17b_bandwidth_audit.py` | bandwidth_audit.json |
| Bandwidth judgment SUBSTANTIAL | Phase 17 | `run_17b_bandwidth_audit.py` | bandwidth_audit.json |

---

## Known Reproducibility Caveats

1. **Use `requirements-lock.txt` for exact reproduction.** The unpinned
   `requirements.txt` uses `>=` constraints and may resolve to newer versions.
   The lock file pins every dependency to the exact versions used to generate
   the publication results (Python 3.11.13, numpy 2.3.5, etc.).

2. **Python version matters for exact bit-for-bit results.** Publication
   results were generated with Python 3.11.13 (CPython) on Darwin arm64.
   Python 3.12+ may produce subtly different floating-point rounding or hash
   orderings. Use 3.11.x for exact reproduction.

3. **Some scripts have optional seed parameters.** When running manually,
   always pass `--seed 42` where the flag is available. The `replicate.py`
   wrappers use internal defaults but do not always pass explicit seeds.

4. **External data is not in the repository.** Follow DATA_SOURCES.md
   exactly. The IVTFF transliteration `ZL3b-n.txt` is the canonical input;
   using a different transliteration file will produce different results.

5. **`umap-learn` is inherently stochastic across environments.** Even with
   the same seed and pinned version, UMAP embeddings may differ across CPU
   architectures due to underlying C++ library differences. UMAP is used
   only in `src/phase4_inference/projection_diagnostics/analyzer.py` for
   visualization of token-frequency projections. No publication claims
   depend on exact UMAP coordinates — all quantitative claims use the
   underlying distance/similarity metrics computed before projection.

6. **Run provenance includes timestamps and run IDs.** When comparing outputs,
   strip provenance metadata and compare only the `results` payload. The
   `verify_reproduction.sh` script does this canonicalization automatically.
