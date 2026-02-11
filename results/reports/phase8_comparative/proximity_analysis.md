# PROXIMITY_ANALYSIS.md
## Phase B: Comparative and Contextual Classification

### Euclidean Distances from Voynich Manuscript (Uncertainty-Qualified)

| Artifact | Distance (Point) | 95% CI | Proximity | Nearest P |
| :--- | :---: | :---: | :--- | :---: |
| Lullian Wheels | 5.0990 | [2.4352, 8.0182] | Moderate | 0.457 |
| Magic Squares | 5.5678 | [2.4804, 8.1730] | Moderate | 0.390 |
| Lingua Ignota | 7.1414 | [3.0753, 10.6085] | Moderate | 0.087 |
| Codex Seraph. | 7.9373 | [5.5987, 9.9086] | Moderate | 0.003 |
| Table-Grille | 8.4261 | [5.3228, 11.4727] | Distant | 0.001 |
| Vedic Chanting | 8.4261 | [5.7418, 11.3175] | Distant | 0.025 |
| Latin | 8.4853 | [6.2127, 10.6648] | Distant | 0.019 |
| Trithemius | 8.6603 | [5.6527, 11.6402] | Distant | 0.020 |
| Enochian | 8.9443 | [5.5691, 12.0502] | Distant | 0.000 |
| Penmanship | 11.9583 | [8.7525, 14.6707] | Distant | 0.000 |

### Clustering Insights

- **Nearest Neighbor (Point Estimate):** Lullian Wheels
- **Nearest-Neighbor Stability:** 0.457 (bootstrap perturbation)
- **Jackknife Stability:** 0.833 (leave-one-dimension-out)
- **Rank Stability:** 0.457 (top-3 set stability)
- **Nearest-Neighbor Margin (P1-P2):** 0.067
- **Top-2 Gap Robustness (CI Lower):** 0.0263
- **M2.5 Closure Lane:** `M2_5_BOUNDED`
- **M2.5 Residual Reason:** `top2_identity_flip_rate_remains_dominant`
- **M2.4 Closure Lane (Compatibility):** `M2_4_BOUNDED`
- **Top-2 Identity Flip Rate:** 0.442
- **Top-2 Order Flip Rate:** 0.722
- **Nearest Rank Entropy:** 1.747
- **Runner-up Rank Entropy:** 2.082
- **Dominant Fragility Signal:** `TOP2_IDENTITY_FLIP_DOMINANT`
- **Comparative Uncertainty Status:** `INCONCLUSIVE_UNCERTAINTY`
- **Reason Code:** `TOP2_IDENTITY_FLIP_DOMINANT`
- **Allowed Claim:** Comparative claim remains provisional; nearest-neighbor identity is unstable across perturbation lanes.
- **Missing-Folio Blocking Claimed:** `False`
- **Objective Comparative Validity Failure:** `False`
- **Uncertainty Artifact:** `results/phase7_human/phase_7c_uncertainty.json`
