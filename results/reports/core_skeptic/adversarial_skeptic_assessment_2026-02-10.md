# Adversarial Skeptic Assessment Report

**Date:** 2026-02-10  
**Playbook Executed:** `planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md`  
**Assessment Type:** Documentation and methodological stress test only (no code fixes)

---

## 1. Execution Evidence (This Run)

The following checks were executed during this assessment:

- `bash scripts/core_audit/pre_release_check.sh` -> **PASSED**
  - Release sensitivity gate passed.
  - Strict indistinguishability preflight policy artifact passed with `status=BLOCKED`, `reason_code=DATA_AVAILABILITY`, `missing_count=4`.
  - Working tree gate passed (`dirty_count=0`).
- `bash scripts/verify_reproduction.sh` -> **PASSED**
  - Determinism check passed.
  - Sensitivity integrity check passed.
  - Strict preflight policy validation passed with approved data-availability block.
- `bash scripts/ci_check.sh` -> **PASSED**
  - Test suite passed.
  - Coverage passed (`58.07%`).
- Runtime provenance spot-check: `data/voynich.db` `runs` table currently reports `63 orphaned`, `129 success` rows.

---

## 2. Overall Skeptic Verdict

The project is stronger operationally (fail-closed gates, strict preflight policy, deterministic checks), but it is **not yet fully hardened against a hostile expert core_skeptic**.

Primary reason: the strongest remaining challenges are methodological framing and evidence scope, not CI reliability.

---

## 3. Attack Vector Scorecard

| Attack Vector | Status | Risk |
|---|---|---|
| AV1. "You defined language out of existence" | Partially Defended | Medium |
| AV2. "Your controls are not comparable" | Exposed | High |
| AV3. "Statistics cannot detect meaning" | Partially Defended | High |
| AV4. "You ignored the images" | Exposed | High |
| AV5. "You stopped too early" | Exposed | High |
| AV6. "Comparative phase2_analysis is subjective" | Partially Defended | Medium |
| AV7. "You are really saying it is a hoax" | Partially Defended | Medium |
| Meta: Motivated reasoning | Exposed | High |
| Meta: Overreach | Exposed | High |

---

## 4. Detailed Findings (Prioritized)

### SK-C1 (Critical): Release-robustness evidence is labeled conclusive but is currently narrow and warning-heavy.

- Sensitivity release evidence is now marked ready and conclusive (`release_evidence_ready=true`, `robustness_decision=PASS`) in `core_status/core_audit/sensitivity_sweep.json:22`, `core_status/core_audit/sensitivity_sweep.json:26`, `core_status/core_audit/sensitivity_sweep.json:35`.
- The same artifact is based on a very small dataset profile (`dataset_pages=18`, `dataset_tokens=216`) in `core_status/core_audit/sensitivity_sweep.json:30`, `core_status/core_audit/sensitivity_sweep.json:31`, echoed in `reports/core_audit/SENSITIVITY_RESULTS.md:5`, `reports/core_audit/SENSITIVITY_RESULTS.md:6`.
- The sweep also reports very high warning volume (`918`) in `core_status/core_audit/sensitivity_sweep.json:24` and `reports/core_audit/SENSITIVITY_RESULTS.md:23`, with sparse-data fallback messages in `core_status/core_audit/sensitivity_sweep.json:57`.
- Reported caveat remains `none` in `reports/core_audit/SENSITIVITY_RESULTS.md:26`.

**Skeptic leverage:** "You called robustness conclusive while relying on sparse-data fallback behavior and a tiny evaluation profile."

---

### SK-H1 (High): Multimodal/image challenge is still not decisively closed.

- Phase 5H illustration coupling had near-total anchoring imbalance (`Unanchored` sample size `2`) and explicitly states geometry refinement is required in `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md:36`, `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md:38`.
- Phase 5I marks layout independence as exploratory/preliminary in `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md:50`, `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md:51`.
- Phase 7 summary concludes no significant adaptation to illustration proximity in `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md:72`.

**Skeptic leverage:** "You tested image coupling weakly, then generalized strongly."

---

### SK-H2 (High): Public conclusions still overstate falsification compared with bounded non-claims.

- Bounded non-claims are present: no claim of semantics/intent/language reconstruction in `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md:379` through `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md:384`.
- But public-facing language remains absolute:
  - "Language Hypothesis Falsified" in `README.md:26`.
  - "PROJECT TERMINATED (Exhaustive)" and "scientifically unjustified" closure language in `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md:4`, `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md:28`.
  - "semantically empty procedural system" in `results/reports/FINAL_PHASE_3_3_REPORT.md:49`.

**Skeptic leverage:** "Your boundary statements are cautious, but your headline claims are categorical."

---

### SK-H3 (High): Control comparability attack remains strong due metric-targeted tuning and known asymmetries.

- Control matching explicitly tunes to Voynich targets (tokens, z-score, repetition, locality, grammar) in `governance/GENERATOR_MATCHING.md:9` through `governance/GENERATOR_MATCHING.md:17`, with class tuning steps in `governance/GENERATOR_MATCHING.md:25`, `governance/GENERATOR_MATCHING.md:29`, `governance/GENERATOR_MATCHING.md:33`.
- Methods doc discloses control normalization asymmetry (controls bypass EVA parser) and flags this as a known confound in `governance/governance/METHODS_REFERENCE.md:75` through `governance/governance/METHODS_REFERENCE.md:83`.

**Skeptic leverage:** "Controls are tuned to look like Voynich, then used to argue Voynich is non-semantic."

---

### SK-M1 (Medium): "Stopped too early" attack remains viable because closure language is absolute.

- Comparative boundary says no further text-internal comparison will help in `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md:15`.
- Reopening criteria exist (irreducible signal / external grounding / framework shift) in `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md:34` through `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md:38`.

**Skeptic leverage:** "You assert exhaustion and also admit reopening criteria; the closure claim should be conditional, not terminal."

---

### SK-M2 (Medium): Comparative-subjectivity challenge is only partially neutralized.

- Comparative distances and nearest-neighbor claims are explicit in `reports/phase8_comparative/PHASE_B_SYNTHESIS.md:8` through `reports/phase8_comparative/PHASE_B_SYNTHESIS.md:15`.
- However, public phase8_comparative documents do not present confidence intervals or perturbation-stability sensitivity for those distance claims.

**Skeptic leverage:** "Distance geometry appears deterministic in prose but uncertainty reporting is thin."

---

### SK-M3 (Medium): Documentation coherence issues create avoidable credibility attacks.

- `results/reports/phase4_inference/PHASE_4_RESULTS.md` gives a full final determination but still includes a residual "PENDING" status table for methods B-E in `results/reports/phase4_inference/PHASE_4_RESULTS.md:160` through `results/reports/phase4_inference/PHASE_4_RESULTS.md:163`.

**Skeptic leverage:** "If your own report contradicts itself, why trust stronger claims?"

---

### SK-M4 (Medium): Historical provenance uncertainty is disclosed but still externally attackable.

- Provenance policy explicitly documents orphaned historical rows and uncertainty handling in `governance/PROVENANCE.md:98` through `governance/PROVENANCE.md:107`.
- Runtime check confirms orphaned rows are still present (`63`).

**Skeptic leverage:** "You retain acknowledged historical uncertainty while asserting strong closure in conclusions."

---

## 5. What Held Up Well Under Skeptic Pressure

1. **Fail-closed release and reproduction gates are materially improved.**  
   Evidence: strict and sensitivity gate enforcement in `scripts/core_audit/pre_release_check.sh:33` through `scripts/core_audit/pre_release_check.sh:56`, `scripts/core_audit/pre_release_check.sh:80` through `scripts/core_audit/pre_release_check.sh:101`, `scripts/verify_reproduction.sh:140` through `scripts/verify_reproduction.sh:165`, `scripts/verify_reproduction.sh:221` through `scripts/verify_reproduction.sh:252`.

2. **Strict data-availability blocking is explicit and policy-compliant (not silent fallback).**  
   Evidence: strict preflight error path in `scripts/phase3_synthesis/run_indistinguishability_test.py:159` through `scripts/phase3_synthesis/run_indistinguishability_test.py:164`; current blocked artifact in `core_status/phase3_synthesis/TURING_TEST_RESULTS.json:12` through `core_status/phase3_synthesis/TURING_TEST_RESULTS.json:15`, `core_status/phase3_synthesis/TURING_TEST_RESULTS.json:488` through `core_status/phase3_synthesis/TURING_TEST_RESULTS.json:494`.

3. **Semantic boundary framework is explicit and testable.**  
   Evidence: operational semantics definition and C1-C4 requirements in `results/reports/phase4_inference/PHASE_4_5_SEMANTIC_ADMISSIBILITY.md:10` through `results/reports/phase4_inference/PHASE_4_5_SEMANTIC_ADMISSIBILITY.md:33`; pre-registered method decision rules in `results/reports/phase4_inference/PHASE_4_METHOD_MAP.md:3`, `results/reports/phase4_inference/PHASE_4_METHOD_MAP.md:15` through `results/reports/phase4_inference/PHASE_4_METHOD_MAP.md:17`.

---

## 6. Skeptic Success Criteria Check

Against the playbook's own success criteria, a competent core_skeptic can still plausibly claim:

- A meaningful but non-recoverable semantic system could remain consistent with current structural findings.
- Image-text constraints are not conclusively exhausted.
- Some closure claims are broader than the strongest evidence currently supports.

**Result:** Skeptic cannot easily demonstrate operational sloppiness anymore, but can still demonstrate **claim-scope overreach and unresolved methodological vulnerability**.

---

## 7. Final Assessment Statement

This pass shows clear progress in reproducibility discipline and gate integrity. The remaining risk is mostly epistemic presentation: several conclusions are written as terminal/falsificatory while the underlying evidence is stronger as bounded structural phase4_inference.

If the goal is to be resilient to a hostile external critic, the next hardening step is claim-scope calibration and multimodal evidence tightening, not additional CI mechanics.

