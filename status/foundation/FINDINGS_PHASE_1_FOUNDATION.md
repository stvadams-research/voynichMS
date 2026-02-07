# FINDINGS: Phase 1 (Foundation)

**Status**: FROZEN
**Date**: 2026-02-06
**Scope**: Levels 0–6 (Infrastructure & Capability Build)

This document audits the findings of Phase 1. It serves as the immutable input for Phase 2.1.

---

## 1. Hypothesis Audit

Which hypotheses were tested, and what was the outcome?

| Hypothesis ID | Description | Outcome | Controls Applied | Notes |
|---|---|---|---|---|
| `glyph_position_entropy` | Certain glyphs are positionally constrained (start/mid/end). | **SUPPORTED** (Demo) | Scrambled, Synthetic | Entropy in "Real" data (0.40) was significantly lower than Scrambled (0.95). |

**Conclusion**: The hypothesis testing machinery correctly discriminates between structured and unstructured data.

---

## 2. Structure Audit

Which structures survived Level 5 decision gates?

| Structure ID | Name | Status | Sensitivity | Controls Impact |
|---|---|---|---|---|
| `geometric_anchors` | Geometric Anchors | **ACCEPTED** | Robust to threshold changes (0.1–0.4) | **Degrades**: Anchor counts drop >80% on scrambled data. |

**Conclusion**: We have at least one class of structure (Geometric Anchors) that is demonstrably non-random and robust.

---

## 3. Unresolved Uncertainties

What ambiguity must be preserved entering Phase 2?

1.  **Glyph Identity**: We still do not know if "glyph candidates" map 1:1 to semantic units. Level 2A preserves this ambiguity.
2.  **Region Semantics**: We do not know if regions represent physical objects, abstract concepts, or decorative elements. Level 2B preserves this ambiguity.
3.  **Alignment Granularity**: Word-to-image alignment is probabilistic. We cannot force 1:1 mapping without losing data.

---

## 4. Failed or Collapsed Structures

The following assumptions were tested by the Phase 1 Destructive Audit and **failed**:

### Fixed Glyph Identity

| Aspect | Value |
|--------|-------|
| **Hypothesis** | Glyph identity is stable under segmentation perturbation |
| **Status** | **FALSIFIED** |
| **Test** | Perturb word boundaries by 5%, re-segment, measure identity stability |
| **Finding** | Identity collapse rate at 5% perturbation: ~35% (threshold: 20%) |
| **Conclusion** | Glyph identity is segmentation-dependent. Shifting word boundaries even slightly causes glyphs to merge, split, or become ambiguous. Any analysis assuming stable glyph identity is **inadmissible** without explicit segmentation controls. |

### Word Boundary Stability

| Aspect | Value |
|--------|-------|
| **Hypothesis** | Word boundaries are consistent across transcription sources |
| **Status** | **WEAKLY_SUPPORTED** (Fragile) |
| **Test** | Compare word boundary positions across EVA, Currier, Bennett |
| **Finding** | Cross-source agreement rate: ~75% (threshold: 80%) |
| **Conclusion** | Word boundaries show significant inter-source disagreement. EVA treats ligatures as single tokens while Currier often splits them. Subtle spacing is interpreted inconsistently. Any analysis assuming objective word boundaries is **fragile** and must declare which transcription source it depends on. |

### Diagram-Text Alignment

| Aspect | Value |
|--------|-------|
| **Hypothesis** | Text near diagrams is semantically related to those diagrams |
| **Status** | **WEAKLY_SUPPORTED** to **FALSIFIED** |
| **Test** | Compare alignment scores between real data and scrambled controls |
| **Finding** | Alignment scores show only modest degradation under scrambling (z-score < 2.0) |
| **Conclusion** | Text-diagram proximity may be a geometric artifact of page layout density rather than intentional labeling. Claims of "label" relationships are **inadmissible** without statistical controls demonstrating significance above chance.

---

**Audit Significance**: These failures are intentional and expected. They demonstrate that the negative control framework correctly identifies fragile assumptions. The Phase 1 infrastructure successfully distinguishes between robust structures (e.g., geometric anchors which degrade >80% under scrambling) and fragile assumptions (e.g., fixed glyph identity which collapses under minor perturbation).

**Implication for Phase 2**: Any Phase 2 analysis that depends on glyph identity, word boundaries, or diagram-text relationships must:
1. Explicitly declare its assumptions
2. Include sensitivity analysis for boundary perturbation
3. Test against scrambled controls
4. Report significance above chance

---

## 5. Decision for Phase 2.1

The Foundation (Phase 1) is **COMPLETE**.
The system is capable of:
1.  Ingesting and segmenting data without bias.
2.  Generating rigorous negative controls.
3.  Testing hypotheses categorically.

**Recommendation**: Proceed to Phase 2.1 (Admissibility Mapping).
