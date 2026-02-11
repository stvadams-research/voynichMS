# CASEFILE_02_TABLE_GRILLE.md
## Artifact: Table-Grille Generator (Baseline)

---

### 1. Artifact Identity
- **Name:** Table-Grille (Rugg Style)
- **Category:** Non-Semantic Structured Generation
- **Approximate Date/Origin:** Modern reconstruction of possible 16th-century methods.
- **Primary Source(s):** Rugg (2004), Phase 5 simulation results.

### 2. Physical Description (Non-Interpretive)
- **Format:** Grid-based lookup tables + physical aperture grilles.
- **Scale:** Matched to Voynich (~230,000 tokens).
- **Layout:** Columnar or block-wise generation.

### 3. Production Workflow
- **Constraints:** Rigid mechanical selection from a finite pool.
- **Human Factors:** High discipline required to follow lookup paths; error-prone if attention flags.
- **Tool Reliance:** Physical grille or coordinate sheet.

### 4. Structural Signatures (Scored 0–5)
| Dimension | Score | Evidence / Rationale |
| :--- | :---: | :--- |
| 1. Determinism | 5 | Total; rule + state = fixed successor. |
| 2. Sparsity | 3 | Bounded by table size; often repetitive in long runs. |
| 3. Novelty Conv. | 5 | Absolute; once table is exhausted, no new tokens occur. |
| 4. Path Efficiency | 1 | Low; repetition is a natural consequence of the grille. |
| 5. Reuse Suppress. | 0 | None; same cells are reused frequently. |
| 6. Reset Dynamics | 5 | Total; each line/cell starts fresh. |
| 7. Effort Proxy | 4 | High cognitive load for lookup; slow execution. |
| 8. Correction Dens. | 4 | High; mechanical slips in lookup are frequent. |
| 9. Layout Coupling | 5 | Absolute; text form is dictated by the grille dimensions. |
| 10. Global Stab. | 5 | Invariant as long as table/grille pair is used. |
| 11. Positional Cond. | 5 | Absolute; position in block = cell in table. |
| 12. History Depend. | 1 | Low; usually memoryless (next depends on position only). |

### 5. Semantic Leakage Audit
- [x] No Content Assumption
- [x] No Efficiency Assumption
- [x] Structural Grounding Verified

### 6. Summary and VM Distance
- **Key Alignment:** Determinism, Reset Dynamics, Positional Conditioning.
- **Key Deviation:** Reuse Suppression (Table-Grille repeats, VM does not).
- **Estimated Proximity:** **Moderate**
