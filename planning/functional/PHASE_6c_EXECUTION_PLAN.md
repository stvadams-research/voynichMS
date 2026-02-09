# PHASE_6C_EXECUTION_PLAN.md

**Project:** Voynich Manuscript – Functional Characterization Program  
**Phase:** 6C  
**Phase Name:** Adversarial vs Indifferent Structure Test  
**Goal Type:** Functional discrimination under observer and inference pressure  

---

## 1. Phase 6C Purpose and Core Question

### 1.1 Core question
Does the Voynich Manuscript’s formal system merely execute rules indifferently, or does it exhibit **active resistance to inference, reconstruction, or learning**?

Phase 6C tests whether the structure is:
- **Indifferent** to being analyzed, or
- **Adversarially tuned** to frustrate reconstruction by an observer.

---

## 2. Why Phase 6C Exists

Phase 6A established:
- disciplined, exhaustive formal execution.

Phase 6B established:
- explicit rejection of efficiency and optimization.

These results leave a single unresolved functional fork:

- **H6C.1 – Formal Indifference:**  
  The system does not care whether it is understood. Any difficulty of inference is incidental.

- **H6C.2 – Adversarial Formalism:**  
  The system is deliberately structured to resist inference, reconstruction, or compression.

Phase 6C is designed to discriminate between these.

---

## 3. What Phase 6C Is Not

- Not a semantics test  
- Not a psychological intent attribution  
- Not a historical motive analysis  

Phase 6C evaluates **structural hostility to inference**, not meaning or authorial intent.

---

## 4. Competing Hypotheses

### H6C.1 – Indifferent Formal System
- Rules are fixed and local.
- Inference difficulty arises naturally from scale and determinism.
- Additional conditioning does not actively increase ambiguity.

### H6C.2 – Adversarial Formal System
- Rules are structured to:
  - maximize local ambiguity,
  - minimize global learnability,
  - frustrate compression and state recovery,
  - create misleading regularities.

---

## 5. Design Principles

### 5.1 Mechanism frozen
All tests assume:
- Implicit Constraint Lattice
- Deterministic traversal
- Independent entry points
- Position- and history-conditioned rules

No alternative generators introduced.

### 5.2 Observer-model based
Inference is modeled explicitly:
- learning agents,
- reconstruction algorithms,
- partial-information observers.

### 5.3 Adversarial burden of proof
Adversarial tuning must produce **positive evidence**, not just absence of clarity.

---

## 6. Adversarial Signature Tests

### 6.1 Learnability Gradient Test
**Objective:** Measure how quickly structure becomes predictable as data accumulates.

**Metric:**
- Prediction accuracy vs corpus fraction curve

**Expectation:**
- Indifferent systems show monotonic improvement.
- Adversarial systems plateau or oscillate.

**Kill rule (H6C.2):**
If predictability increases smoothly with data, adversarial tuning is falsified.

---

### 6.2 Decoy Regularity Test
**Objective:** Detect local regularities that fail to generalize globally.

**Metric:**
- Local rule confidence vs global failure rate

**Kill rule (H6C.2):**
If locally learned rules generalize proportionally, adversarial misdirection is falsified.

---

### 6.3 Observer Conditioning Sensitivity
**Objective:** Test whether adding observer context (position, history, partial state) paradoxically increases ambiguity.

**Metric:**
- Entropy change under added conditioning

**Kill rule (H6C.2):**
If added conditioning consistently reduces entropy, adversarial structure is falsified.

---

### 6.4 Anti-Compression Trap Test
**Objective:** Evaluate whether compression attempts introduce structural errors.

**Metric:**
- Reconstruction error vs compression strength

**Kill rule (H6C.2):**
If compressed reconstructions preserve structure proportionally, adversarial design is falsified.

---

## 7. Control Corpora

### 7.1 Required controls
- Phase 6A indifferent lattice simulators
- Phase 6B efficiency-neutral baselines
- Explicit adversarial toy systems (designed traps)

### 7.2 Matching constraints
Controls must match:
- vocabulary size,
- line length distribution,
- positional conditioning,
- entry independence.

---

## 8. Execution Order

1. Establish learnability baselines on controls  
2. Run inference agents on Voynich corpus slices  
3. Measure gradients, plateaus, and reversals  
4. Apply adversarial kill rules  

No adaptive agent tuning during execution.

---

## 9. Decision Framework

### Outcome A: Adversarial Tuning Detected
- Learnability plateaus
- Decoy regularities
- Conditioning paradoxes
- Compression-induced failure

**Interpretation:**  
Supports adversarial or obfuscatory functional intent.

---

### Outcome B: No Adversarial Signatures
- Predictability increases monotonically
- Rules generalize cleanly
- Conditioning reduces entropy

**Interpretation:**  
Supports indifferent formal execution. The system is difficult but not hostile.

---

## 10. Phase 6C Deliverables

### Code
- `src/functional/phase_6c/learnability_tests.py`
- `src/functional/phase_6c/adversarial_metrics.py`

### Data
- `results/functional/phase_6c/phase_6c_results.json`

### Report
- `reports/PHASE_6C_RESULTS.md`

---

## 11. Phase 6C Termination Statement

Phase 6C terminates when inference resistance is evaluated against matched indifferent and adversarial controls, and the presence or absence of adversarial tuning is decisively classified. Phase 6C does not infer meaning; it determines whether the formal system is hostile or indifferent to observers.
