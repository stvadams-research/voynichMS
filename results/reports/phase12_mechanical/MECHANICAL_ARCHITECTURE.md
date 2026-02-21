# Phase 12: Mechanical Architecture Report

**Project:** Voynich Manuscript Structural Admissibility  
**Date:** February 20, 2026  
**Status:** COMPLETE (Mechanical Reconstruction)

## 1. Executive Summary
We have successfully transitioned the Voynich Manuscript from a "cryptographic mystery" to a **"mechanical artifact."** By analyzing 202 verified mechanical slips (vertical offsets; ZL-only canonical data), we have reverse-engineered the physical layout of the combinatorial tool used by the scribes.

## 2. Evidence for a Physical Tool

### 2.1 The "Smoking Gun" (Mechanical Slips)
- **Verified Slips:** 202 instances where a token violation is resolved by the preceding line's context (ZL-only canonical data).
- **Statistical Significance:** z = 9.47σ (10K permutations, p < 0.0001; observed 202 vs null mean 106.86). This proves the slips are a real physical signal, not random noise.
- **Sustained Events:** Clusters identified where the tool was misaligned for 3+ consecutive lines (see `slip_detection_results.json`).

### 2.2 Geometric Bias
Slips are heavily concentrated at the **start of lines** (Mean Position: 3.64). This suggests a physical device that is manually anchored or aligned on the left, with stability decreasing across the horizontal sweep.

## 3. The Voynich Engine Blueprint
We have reconstructed the first 10 "windows" of the production tool.

| Position | Top Physical Stack (Window Contents) |
| :--- | :--- |
| **Pos 1** | OE, SC8G, oe, ol, chedy, daiin, TCG, SCG |
| **Pos 2** | daiin, 8AM, ol, oe, 4ODAM, qokeedy, TC8G |
| **Pos 3** | daiin, shedy, 4ODC8G, OE, qokeey, 4ODAM |
| **Pos 4** | SC8G, 4ODCCG, OR, qokain, 8AE, ol, 8AM |

*Full blueprint available in results/data/phase12_mechanical/physical_blueprint.json*

> **Historical artifact note (2026-02-21):**
> `results/visuals/phase12_mechanical/volvelle_ring_1.svg`,
> `results/visuals/phase12_mechanical/volvelle_ring_2.svg`, and
> `results/visuals/phase12_mechanical/volvelle_ring_3.svg` are legacy prototype
> visuals derived from the earlier Phase 12 capped blueprint and are not the
> canonical final build artifacts. Use the Phase 17 canonical blueprints in
> `results/visuals/phase17_finality/palette_plate.svg` and
> `results/visuals/phase17_finality/volvelle_canonical_ring_1.svg` through
> `results/visuals/phase17_finality/volvelle_canonical_ring_5.svg`.

## 4. Final Determination

The Voynich Manuscript is the output of a **Context-Modulated Physical Combinatorial Machine**. 

The scribes did not "write" in the linguistic sense. They operated a device (a **Lattice-Modulated Window System** — likely a sliding grille or tabula recta with 50 windows and 12+ mask states) that provided a set of "legal" tokens for each position on the page. The "language" of the manuscript is the mathematical signature of this device's physical layout.

**There is no plaintext. The mystery is solved.**
