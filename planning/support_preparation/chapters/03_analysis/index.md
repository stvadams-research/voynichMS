# Layer 2: Analysis & Admissibility

## Headline
**Traditional linguistic models are structurally inadmissible; the manuscript behaves as a unified procedural machine rather than a language.**

## The Concept (Layman's Summary)
If you see a cloud that looks like a face, you don't assume the cloud is trying to tell you something. You know that wind and water vapor just happen to form that shape sometimes. We did the same thing with the Voynich Manuscript. We tested it to see if it "breaks" in the same way a language would.

When you garble a sentence in English, you can usually still guess some of the words. But when we slightly shifted the "alphabet" or "word boundaries" of the Voynich, the whole structure collapsed instantly. This tells us the patterns are extremely rigid and fragile—like a computer program's code—rather than flexible and redundant like a human language.

## Technical Deep-Dive
We utilized an **Admissibility Mapping** protocol to test the manuscript against 6 distinct explanation classes.

### The Failure of Redundancy
Natural languages are redundant; they can survive noise. We measured **Mapping Stability**—the ability of structural patterns to persist under 5% character perturbation.

- **Natural Language Baseline**: 0.80 - 0.90 (Stable)
- **Voynich Manuscript**: 0.02 (Collapsed)

This collapse proves that the "words" in the manuscript are not carriers of semantic meaning, but are instead "terminal strings" of a rigid procedural process.

### Structural Anomalies
Using a battery of **Stress Tests**, we identified two primary signatures that exclude simple "gibberish" while also excluding "language":

1.  **Information Density (Z-Score: 5.68)**: The manuscript is far more "orderly" than random noise.
2.  **Locality Radius (2-4 units)**: Statistical dependencies exist only between immediate neighbors, lacking the "long-range correlations" found in all human thought and communication.

## Skeptic's Corner
Some researchers point to the "word-like" statistics (Zipf's Law) as proof of language.

### Counter-Point Analysis
Our **Semantic Necessity Assessment** proved that 4 out of 6 tested non-semantic machines (such as High-order Markov chains) can reproduce Zipfian curves *and* high information density simultaneously. Therefore, Zipf's Law is a "weak signal" that does not require a language to explain it.

## Reproducibility
The Admissibility results are captured in `core_status/core_audit/sensitivity_sweep.json`.
Run the sweep yourself:
```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke
```
**Reference RunID**: `fa6a368d-bf6e-93f4-bd1a-cf85a08b5551`
