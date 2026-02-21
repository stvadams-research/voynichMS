# Phase 16: Ergonomic Grounding and Physical Layout

**Subject:** Physical Verification of the Voynich Engine
**Data source:** Phase 15 choice stream (12,519 admissible decisions) + Phase 11 stroke topology

## 1. Ergonomic Coupling (NULL Result)

We correlated within-window selection frequency with physical effort (stroke
complexity) for 1,220 word-window pairs that had both stroke-cost data and
sufficient selection observations.

| Metric | Value |
| :--- | :--- |
| **Spearman Rho (Cost vs Selection Rank)** | **-0.0003** |
| **p-value** | 0.9926 (not significant) |
| **Variance explained (rho²)** | 0.00% |
| **Average effort gradient** | 0.611 strokes |
| **Is ergonomically coupled** | **No** |

**Interpretation:** There is no correlation between a word's physical effort
(stroke complexity) and its selection frequency within a window. The 21.49%
selection skew identified in Phase 15 is real but is **not driven by physical
effort**. The scribe's within-window preferences operate on a dimension other
than stroke complexity — possibly positional bias, suffix affinity, bigram
context, or frequency effects (investigated in Phase 15D).

**Artifact:** `results/data/phase16_physical/effort_correlation.json`
(`results.correlation_rho`, `results.p_value`, `results.is_ergonomically_coupled`)

## 2. Geometric Layout Optimization

We projected the 50-window engine into two physical geometries to test which
layout minimizes scribe transition distance.

| Layout Type | Avg. Travel Distance | Efficiency vs. Random |
| :--- | ---: | ---: |
| **2D Sliding Grille (10×5)** | **0.723 units** | **81.50% improvement** |
| Circular Volvelle | 2.330 units | — |
| Random baseline (grid) | 3.906 units | — |

**Interpretation:** The 2D grid layout is highly optimized for the manuscript's
transition patterns. Sequential window-to-window transitions follow
geometrically short paths, consistent with a physical tool designed for
efficient operation. The grid efficiency measures **layout quality for
transitions**, not ergonomic selection preference.

**Artifact:** `results/data/phase16_physical/layout_projection.json`
(`results.grid_efficiency`, `results.avg_grid_dist`, `results.random_baseline_grid`)

## 3. Conclusion

The Voynich Engine's physical layout is **geometrically optimized** (81.50%
transition efficiency over random placement), confirming that the 50-window
structure maps naturally onto a 10×5 rectangular grid — consistent with a
sliding grille or tabula recta design.

However, within-window word selection is **ergonomically neutral** (rho ≈ 0).
The scribe does not preferentially select words that are easier to write. This
means:

1. The **Lattice** (Phase 14) provides the mathematical grammar (43.4% admissibility).
2. The **Instrumented Choice** (Phase 15) captures real scribal bias (21.49% skew).
3. The **Physical Layout** (Phase 16) confirms geometric optimization of the tool.
4. The **Selection Driver** remains open — the bias exists but its source is not physical effort.

The geometric optimization result is strong evidence for a physical production
tool. The null ergonomic result means that selection within windows is driven
by visual, contextual, or frequency-based factors rather than stroke economy.

---
**Data verified:** 2026-02-21. All values sourced from `effort_correlation.json`
and `layout_projection.json` (provenance-wrapped, reproducible).
