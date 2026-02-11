# Layer 3: Structural Mechanism

## Headline
**The manuscript is the output of an "Implicit Constraint Lattice"—a deterministic rule-system that generates text line-by-line with no memory of the past.**

## The Concept (Layman's Summary)
Imagine a giant wall of switches and gears. Every time you pull a lever, a word is printed. The gear you turn *now* depends exactly on which gear you turned *last* and where you are on the page. But as soon as you finish a line and move to the next, all the gears reset. 

This is how the Voynich Manuscript works. It isn't a person writing a story; it's a person (or a process) following a very strict set of instructions that tells them exactly which symbol comes next based on the one they just wrote. This explains why the book looks so consistent but says absolutely nothing.

## Technical Deep-Dive
Phase 5 of our research focused on **Mechanism Identifiability**. We eliminated competing families of generative processes (e.g., simple copying, static tables, or random sampling) until only one class remained.

### The Survival of the Lattice
We tested the "Entropy Reduction" of words based on their context. In a language, knowing the previous word helps a little. In the Voynich, knowing the `(Prev Word, Current Word, Position)` removes almost **88.11%** of all uncertainty.

| Predictor State | Entropy Remaining (bits) | Predictive Lift |
|-----------------|--------------------------|-----------------|
| Node Only       | 2.27                     | -               |
| Node + Position | 0.78                     | 65.6%           |
| Node + Pos + History | 0.09                | 88.1%           |

This "Entropy Collapse" is the signature of a **Deterministic Rule System**. 

### Line Reset Dynamics
We measured the **Reset Score** across line boundaries.
- **Voynich Score**: 0.95 (Near-total reset)
This proves that the "state" of the machine does not cross from one line to the next, which is physically consistent with mechanical aids like grilles or wheels that are moved per-line.

## Skeptic's Corner
Could this "lattice" just be the grammar of a real language?

### Counter-Point Analysis
No. Natural language grammar is "lossy" and "stochastic"—it allows for creativity and variation. The Voynich Lattice is "rigid"—it forces successors with near-mathematical certainty. If it were a language, the author would have been a prisoner to their own grammar, unable to express a single original thought.

## Reproducibility
Mechanism results are consolidated in `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md`.
Specific topology tests can be rerun via:
```bash
python3 scripts/phase5_mechanism/run_pilot.py
```
**Reference RunID**: `f18b9a7c-a852-89d1-58ba-359007d8c038`
