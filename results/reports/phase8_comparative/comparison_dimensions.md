# COMPARISON_DIMENSIONS.md
## Phase B: Comparative and Contextual Classification

This document defines the non-semantic dimensions used to compare the Voynich Manuscript to other formal artifacts.

---

### 1. Determinism (Successor Predictability)
- **Definition:** The degree to which the next element is fixed by the current state.
- **Indicators:** Successor entropy, predictive accuracy under optimal conditioning.
- **Exclusions:** Semantic predictability (context-based meaning).
- **Confounds:** Small sample sizes making things look more deterministic than they are.

### 2. State-Space Sparsity
- **Definition:** The extent to which the theoretically reachable state space is actually sampled.
- **Indicators:** Hapax state ratio, visitation distribution skew (Gini coefficient).
- **Exclusions:** Vocabulary size (absolute count).
- **Confounds:** Sampling bias in shorter artifacts.

### 3. Novelty Convergence
- **Definition:** The rate at which the introduction of new patterns decreases over the corpus.
- **Indicators:** Slope of the novelty curve, asymptote of state discovery.
- **Exclusions:** Subject matter shifts.
- **Confounds:** Intentional section breaks or changes in production mode.

### 4. Path Efficiency
- **Definition:** The amount of unique structural information produced per unit of effort/text.
- **Indicators:** TTR (Type-Token Ratio) at specific scales, information density (Z-score).
- **Exclusions:** Communicative efficiency (brevity for meaning).
- **Confounds:** Repetitive ritual structures.

### 5. Reuse Suppression
- **Definition:** The degree to which the system actively avoids repeating states or paths.
- **Indicators:** Observed vs. expected repetition under random walk, suppression index.
- **Exclusions:** Avoidance of redundancy for clarity.
- **Confounds:** Large state spaces naturally making repetition rare.

### 6. Reset Dynamics
- **Definition:** The strength and frequency of state resets at structural boundaries (e.g., lines, paragraphs).
- **Indicators:** Reset score, inter-line independence.
- **Exclusions:** Semantic topic changes.
- **Confounds:** Visual layout formatting.

### 7. Human Effort Proxy
- **Definition:** The mechanical and cognitive complexity required to produce the artifact.
- **Indicators:** Stroke count per character, execution speed proxies, cognitive load estimates.
- **Exclusions:** Artistic or aesthetic value.
- **Confounds:** Scribe skill level.

### 8. Correction Density
- **Definition:** The frequency of overt errors, deletions, and corrections.
- **Indicators:** Correction count per 1000 units, error typology (mechanical vs. structural).
- **Exclusions:** Erasures for layout adjustment.
- **Confounds:** Differing standards of "cleanliness" in different traditions.

### 9. Layout Coupling
- **Definition:** The sensitivity of the production phase5_mechanism to the physical geometry of the page.
- **Indicators:** Line length correlation with position, text wrapping behavior, obstruction avoidance.
- **Exclusions:** Decorative integration.
- **Confounds:** Pre-ruled margins or grids.

### 10. Global Stability
- **Definition:** The consistency of structural signatures across different sections or time periods.
- **Indicators:** Cross-sectional variance in entropy, rank, and determinism.
- **Exclusions:** Stylistic shifts.
- **Confounds:** Changes in scribe or production tool.

### 11. Positional Conditioning
- **Definition:** The extent to which rules are sensitive to the absolute or relative position within a block.
- **Indicators:** Positional entropy reduction, slot-logic signatures.
- **Exclusions:** Grammatical positioning (e.g., subject-verb).
- **Confounds:** Simple start/end markers.

### 12. History Dependence
- **Definition:** The depth of memory required to determine the current rule (Markov order).
- **Indicators:** Context length vs. entropy reduction, long-range dependency scores.
- **Exclusions:** Narrative coherence.
- **Confounds:** Repetitive "mantra" structures.
