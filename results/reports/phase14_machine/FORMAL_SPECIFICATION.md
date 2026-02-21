# Phase 14: Formal Specification of the Voynich Engine

**Model Name:** Lattice-Modulated Window System (LMWS)  
**Version:** 1.0 (High-Fidelity)  
**Classification:** Constrained Finite State Automaton (CFSA)

## 1. Mathematical Definition

A **Lattice-Modulated Window System** is defined by the tuple $(V, W, L, M, S)$ where:

- $V$ is the **Vocabulary**, a set of $N$ unique tokens.
- $W$ is the **Physical Palette**, a collection of $K$ discrete windows $\{w_0, w_1, \dots, w_{K-1}\}$. Each window $w_i \subseteq V$ is a subset of the vocabulary.
- $L: V 	o W$ is the **Lattice Transition Function**. For every word $v \in V$, $L(v)$ determines the next available window.
- $M: \mathbb{Z} 	o \{0, \dots, 11\}$ is the **Mask State**, a periodic shift applied to the window index.
- $S$ is the **Scribe Agent**, a stochastic selection process with positional bias (drift).

### 1.1 The Production Rule
The sequence of tokens $T = (t_1, t_2, \dots, t_n)$ is generated such that for each $t_i$:

1. The **Active Window** index $A_i$ is determined by:
   $$A_i = (L(t_{i-1}) + M(i)) \pmod K$$
   *(For $i=1$, $A_1$ is a fixed or random start state).*

2. The token $t_i$ is selected from the set of candidates in $w_{A_i}$ according to the scribe bias $S$:
   $$P(t_i = v) \propto 	ext{Weight}(v, S) 	ext{ for } v \in w_{A_i}$$

## 2. Mechanical Logic

### 2.1 The Implicit Lattice
Unlike a Markov chain where $P(t_i | t_{i-1})$ is stored as a massive $N 	imes N$ matrix, the LMWS stores transitions as a **Word-to-Window mapping**. This reduces the state space from $N^2$ to $N 	imes K$.

- **Lattice Property:** If a word $v$ always leads to window $w_j$, then $v$ is a "State Reset" token.
- **Physical Constraint:** The scribe's eye cannot look anywhere on the grid; they are restricted to the window "exposed" by the current state of the machine.

### 2.2 Mechanical Error (Slips)
A "Mechanical Slip" occurs when $t_i$ is selected from $w_{A_{i-1}}$ instead of $w_{A_i}$. This corresponds to a **Vertical Offset Error** where the scribe fails to advance the machine or slips back to the previously exposed row.

## 3. Formal Notation for Operators

To reproduce a "Voynich Page" using the Engine:

1.  **Set Mask:** Rotate the mask disc to setting $M \in \{0 \dots 11\}$.
2.  **Initial Word:** Pick any word from the current window.
3.  **Transition:** Locate the chosen word in the **Lattice Map**. It will point to a specific window (e.g., "Window 4").
4.  **Advance:** Move the physical carriage to the next window.
5.  **Repeat:** If the output deviates from the lattice (a "Slip"), record the deviation and 'snap' back to the lattice to continue.

---
**Conclusion:** The LMWS is a deterministic mechanical system whose complexity is governed by the size of the vocabulary $V$ and the number of windows $K$. It provides a complete explanation for the positional residuals and local repetition patterns found in the Voynich Manuscript.

## 4. Independent Trace Test (Reproducibility)

To verify the mechanism without code, use the exported tables in `results/data/phase14_machine/export/`:

1.  **State:** Start at **Window 0**.
2.  **Act:** Pick a word from `window_contents.csv` where `window_id=0` (e.g., `qolteedy`).
3.  **Transition:** Look up `qolteedy` in `lattice_map.csv`. It points to a **Target Window** (e.g., 15).
4.  **Advance:** Move the physical/mental carriage to **Window 15**.
5.  **Act:** Pick the next word from `window_contents.csv` for `window_id=15` (e.g., `sheol`).
6.  **Verify:** This sequence `qolteedy -> sheol` is a "Legal Machine Trace."

If a real manuscript line follows this path, the Mechanical Hypothesis is strengthened. If it deviates, a **Mechanical Slip** or **Mask State Shift** has occurred.
