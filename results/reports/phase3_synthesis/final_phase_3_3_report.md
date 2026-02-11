# PHASE 3.3 FINAL REPORT: CONSTRAINT EXHAUSTION AND ROBUSTNESS CLOSURE

**Date:** 2026-02-07
**Status:** Framework-Bounded Closure
**Project:** Voynich Manuscript – Generative Reconstruction

---

## 1. Executive Summary

Phase 3.3 was executed as a focused, framework-bounded phase to test the remaining non-semantic explanatory space and verify robustness of the project's conclusions. Three one-shot tests were performed: **Maximal Mechanical Reuse**, **Transliteration Invariance**, and **Glyph Variant Sensitivity**.

The results confirm that the Voynich Manuscript's most extreme structural anomalies (repetition rate and information density) are **mechanically explainable** and **invariant** under reasonable representational choices. 

---

## 2. Consolidated Test Results

| Test | Objective | Outcome | Key Insight |
|------|-----------|---------|-------------|
| **Test A** | Mechanical Reuse | **H1 SUPPORTED** | Bounded token pools (size 10-30) are sufficient to reach 0.90 repetition. |
| **Test B** | Transliteration Invariance | **INVARIANT** | Repetition and entropy findings hold across Zandbergen-Landini and Currier. |
| **Test C** | Glyph Variant Sensitivity | **STABLE** | Collapsing/expanding glyph variants does not alter structural conclusions. |

---

## 3. Major Conclusions

### 3.1 Mechanical Sufficiency
The "Repetition Anomaly" (0.90 rate) identified in earlier phases does not require a linguistic or semantic explanation. It is a natural emergent property of a **two-stage algorithmic process**:
1.  A rigid, glyph-level grammar (identified in 3.2).
2.  A bounded selection pool (size ~20-30 tokens per page) used by the scribe.

### 3.2 Representational Invariance
The project's findings are macroscopic and robust. They are not artifacts of the Zandbergen-Landini transliteration, nor are they sensitive to fine-grained glyph categorization choices. This increases confidence in the "Linguistic Inadmissibility" determination.

### 3.3 Closing the "Voynich Mechanism"
With these results, the structural phase5_mechanism of the Voynich Manuscript is treated as **provisionally solved in principle under current diagnostics**. We have successfully:
- Shown that natural-language explanations are not supported within tested diagnostics.
- Reverse-engineered the glyph-level grammar.
- Demonstrated mechanical sufficiency for the highest statistical anomalies.

---

## 4. Final Project Determination (Framework-Bounded)

**The structural investigation of the Voynich Manuscript has reached a framework-bounded stopping point under tested diagnostics.**

Further escalation to semantic interpretation or "improvement" of generative models is not currently supported by the tested structural evidence. Within this evidence class, the manuscript behaves as a sophisticated procedural system without demonstrated semantic signal.

This determination is conditionally closed and reopenable under the canonical criteria in `governance/REOPENING_CRITERIA.md`.

---

## 5. What This Does Not Claim

This report does not claim:

- proof of authorial intent,
- proof of semantic impossibility under all future evidence,
- final historical/cultural interpretation of manuscript purpose.

For explicit phase5_mechanism non-claims, see:

- `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md`

---

## 6. Operational Entitlement State

Canonical operational entitlement source:

- `core_status/core_audit/release_gate_health_status.json`

Current gate-health class: `GATE_HEALTH_DEGRADED`.

Accordingly, the closure interpretation in this report is provisional and operationally contingent pending restored release/reproduction gate health.

Current degraded-state dependency is the SK-C1 release sensitivity evidence contract (`core_status/core_audit/sensitivity_sweep_release.json`).

---

## 7. Metadata and Provenance
- **Dataset:** voynich_real (233,646 tokens)
- **Controls:** audit_scrambled, audit_synthetic
- **Runs:** Full provenance recorded in `runs/` directory.
- **Repository State:** Deterministic and verified under current framework checks, with historical provenance qualifiers.
- **Historical provenance confidence:** `PROVENANCE_QUALIFIED` pending full elimination of legacy orphaned run rows.
- **SK-M4.5 provenance lane:** `M4_5_BOUNDED` while legacy orphaned rows remain bounded under current source scope.
- **Canonical provenance source:** `core_status/core_audit/provenance_health_status.json`

---
**End of Framework-Bounded Report**
