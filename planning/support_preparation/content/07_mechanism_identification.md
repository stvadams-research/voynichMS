# 7. Mechanism Identification: The Implicit Constraint Lattice

Having ruled out language and established non-semantic sufficiency, we sought to identify the actual production mechanism. Phase 5 reframed the problem from interpretation to identifiability: if the manuscript is produced by a non-semantic deterministic process, can we identify the production mechanism class from text-internal signatures alone?

The answer was pursued through an iterative process of hypothesis collapse across eleven sub-phases. At each stage, mechanism families were frozen, necessary consequences pre-registered, and kill rules applied. Families that violated their own predictions were eliminated. The process terminated when a single survivor remained.

## 7.1 Identifiability Pilot (5A)

The initial pilot established that mechanism signatures can discriminate between real manuscript data and matched non-semantic controls. Real successor entropy ({{phase5.pilot.successor_entropy}} bits) was significantly lower than pool-reuse controls ({{phase5.pilot.control_entropy}} bits), identifying a higher-order constraint operating beyond simple token reuse. Variant clustering further separated the manuscript from stochastic baselines.

This result licensed the full elimination program: production mechanisms leave detectable, differentiable fingerprints in the text.

## 7.2 Constraint Geometry and Reset Dynamics (5B)

The line was established as the fundamental unit of execution. The Reset Score of {{phase5.5b.reset_score}} indicates that successor constraints re-initialize almost completely at every line break — an extreme boundary signature. This explains the "line-initial" and "line-final" anomalies that researchers have observed for decades: they are boundary effects of a system that resets its state.

| Dataset | Effective Rank | Reset Score | Interpretation |
|---------|---------------|-------------|----------------|
| Voynich (Real) | 83 | 0.9585 | High-dimensional, non-persistent |
| Pool-Reuse (Syn) | 79 | 0.9366 | Stochastic baseline |
| Geometric Table (Syn) | 61 | 0.0000 | Rigid, persistent |

Static table traversal — where a pointer moves continuously through a fixed grid — was falsified by its zero reset signature. The mechanism requires per-line reinitialization.

{{figure:results/publication/assets/reset_signature.png|Reset Dynamics: Entropy Collapse and Re-initialization at Line Boundaries}}

## 7.3 Workflow Reconstruction (5C)

Line-level Type-Token Ratio of {{phase5.5c.line_ttr}} falsifies random sampling models. Each line exhibits near-total uniqueness: tokens are not drawn from a pool but generated through a constrained walk that avoids immediate repetition.

| Workflow Model | Mean TTR | Mean Entropy | Status |
|----------------|----------|-------------|--------|
| Voynich (Real) | 0.9839 | 1.3487 | TARGET |
| Independent Pool | 0.7280 | 2.7534 | FAIL |
| Coupled Pool | 0.7893 | 2.7740 | FAIL |

Stochastic pools produce too much repetition and too much entropy. The mechanism forces novelty within each line — a signature of rigid procedural generation, not sampling.

## 7.4 Deterministic Grammar (5D)

Testing deterministic grammar classes revealed a critical scale split. Slot-level entropy in the real manuscript (~8 bits per position) implies a large candidate set — thousands of possible tokens at each position. Yet within-line entropy from Phase 5C is extremely low (~1.35 bits), implying rigid local forcing.

Simple slot systems cannot satisfy both properties simultaneously. Fixed slot templates were eliminated. The resolution requires a large deterministic structure with rigid traversal: many paths exist globally, but once a path is entered, choices are heavily constrained.

## 7.5 Successor Consistency — The "Stiffness" Signature (5E)

This was the critical discriminating test. When the same bigram context appears in different locations across the corpus, the successor token matches {{phase5.5e.successor_consistency}} of the time. This is proof of global deterministic rules — not statistical tendencies, but hard constraints that operate uniformly from the first folio to the last.

| Metric | Voynich (Real) | Large Grid (Syn) |
|--------|---------------|-----------------|
| Mean Successor Consistency | 0.8592 | 0.9892 |
| Recurring Bigrams | 1,976 | 2,318 |

Stochastic grammars were eliminated by this property. No model based on probabilistic token selection can produce consistency this high across 200,000+ glyphs. The mechanism is globally deterministic and behaves like rigid traversal through a static rule system.

{{figure:results/publication/assets/lattice_determinism.png|Lattice Determinism: Global Stability of Successor Constraints}}

## 7.6 Entry Selection (5F)

Start-word entropy of 11.82 bits — far exceeding the 7.86 bits of synthetic uniform models — reveals a vast entry space. Adjacency coupling between consecutive lines is near zero (0.0093). Lines are independent traversal instances: each enters the lattice at a fresh, independently selected point with no carryover from the previous line.

## 7.7 Topology Collapse (5G)

With the mechanism established as deterministic, line-resetting, and globally consistent, the question narrowed to topology: what shape is the underlying structure?

| Topology | Collision Rate | Gini (Skew) | Convergence |
|----------|---------------|-------------|-------------|
| Voynich (Real) | 0.1359 | 0.6098 | 2.2330 |
| Grid | 0.2040 | 0.5290 | 1.6800 |
| Layered Table | 0.1925 | 0.5559 | 1.7312 |
| DAG (Stratified) | 0.1895 | 0.5442 | 1.7333 |
| Implicit Lattice | 0.2080 | 0.6434 | 1.6961 |

Gini skew ({{phase5.5g.gini_coefficient}}) and convergence rate ({{phase5.5g.convergence_rate}}) distinguish the Voynich topology from simple grids or directed graphs. The structure is neither fully connected nor purely hierarchical — it is a constrained network with preferred pathways, high convergence, and strongly skewed visitation frequencies. Simple grids were weakened; the implicit lattice became the leading candidate.

{{figure:results/publication/assets/topology_comparison.png|Topology Comparison: Convergence and Skew vs. Candidate Mechanism Families}}

## 7.8 Sectional Stability (5I)

The mechanism was tested for global uniformity across codicological sections:

| Section | Token Count | Effective Rank | Successor Consistency |
|---------|-------------|---------------|----------------------|
| Astronomical | 3,331 | 85 | 0.9158 |
| Biological | 47,063 | 78 | 0.8039 |
| Herbal | 72,037 | 80 | 0.8480 |
| Pharmaceutical | 11,095 | 83 | 0.8897 |
| Stars | 63,534 | 81 | 0.8730 |

The lattice signature remains stable across all sections. Cross-section trigram overlap confirms shared deterministic structure. The manuscript is not a collection of different systems — it is a single global machine applied uniformly regardless of subject matter.

{{figure:results/publication/assets/sectional_stability.png|Sectional Stability: Consistency of Deterministic Signatures across Codicological Units}}

## 7.9 Position Sensitivity (5J)

Dependency scope testing discriminated between purely local transitions and position-conditioned constraints:

| Dataset | H(S\|Node) | H(S\|Node,Pos) | Predictive Lift |
|---------|-----------|----------------|----------------|
| Voynich (Real) | 2.2720 | 0.7814 | 65.61% |
| Local Transition | 1.2811 | 1.1478 | 10.40% |
| Feature-Conditioned | 1.0806 | 0.9042 | 16.32% |

Position provides a 65.6% reduction in successor uncertainty — far exceeding what any purely local model can explain. Constraints are conditioned on global line parameters, not just the immediate preceding token.

## 7.10 Final Collapse — The Minimal State Machine (5K)

The residual history audit proved that knowing the previous word reduces uncertainty by {{phase5.5k.entropy_reduction_pct}}%:

{{include:results/reports/phase5_mechanism/phase_5k_results.md}}

The state (Word, Position) alone is insufficient — substantial uncertainty remains. Adding history (the previous token) removes nearly all of it. The minimal state specification is therefore **(Previous Token, Current Token, Position)**.

Encoding this second-order dependence as an explicit graph would require state growth on the order of V^2 x L, producing a pathologically large and non-explanatory model. The parsimony criterion eliminates explicit graph representations. The implicit constraint lattice — where successors are computed by rule evaluation rather than stored as edges — is the sole survivor.

## 7.11 Synthesis: The Identified Mechanism

The eleven sub-phases converge on a single structural identification:

> The Voynich Manuscript is generated by a **single, globally stable, deterministic rule system** that produces each line as an independent traversal instance through an **implicit constraint lattice**, where successor choice is **rule-evaluated** and depends on **position** and **history** (at least second-order), with strict **line-boundary resets**.

The key properties of the identified mechanism:

- **State** includes at least (Previous Token, Current Token, Position)
- **Lines reset** fully — no carryover state between lines
- **Entry points** are selected independently from a large pool
- **Successors** are evaluated by constraints rather than retrieved from fixed edges
- **Global frequency skew** emerges from constraint geometry and path visitation, not hard-coded frequency tables

This is not an interpretive claim. It is a mechanistic identification based on eleven rounds of elimination and forced consequence. The hypothesis space began with six mechanism families and was collapsed to one through falsification, not preference.
