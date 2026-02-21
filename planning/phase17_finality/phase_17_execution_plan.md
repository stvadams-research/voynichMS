# Phase 17: Physical Synthesis & The "Meaning" Boundary

**Objective:** To achieve absolute closure by producing the physical blueprints for the 10x5 sliding grille and calculating the maximum theoretical information bandwidth (steganographic capacity) of the manuscript.

**Updated:** 2026-02-21

---

## 1. Task 1: Physical Blueprint Generation
**Goal:** Translate the digital lattice into 15th-century "Hardware."

- [ ] **1.1: 10x5 Palette Sheet Export**
    - **Implementation:** Create `scripts/phase17_finality/run_17a_generate_blueprints.py`.
    - **Task:** Generate printable 10x5 "Word Sheets" (50 windows) containing the 7,755-token vocabulary.
- [ ] **1.2: 12-Setting Mask Grilles**
    - **Task:** Generate the 12 physical mask templates (Cut-out patterns) that, when slid over the Word Sheets, expose the active vocabulary for each state.
    - **Note:** Phase 14G Sprint 3 found global mode offset = 17 (44.2% oracle capture). 48 of 50 mask offsets are used empirically.
- [ ] **1.3: Artifact:** `results/visuals/phase17_finality/grille_blueprints.pdf`.

## 2. Task 2: Steganographic Bandwidth Audit
**Goal:** Conclusively bound the "Head" (Meaning) vs. the "Hand" (Ergonomics).

- [x] **2.1: Information Capacity Calculation**
    - **Implementation:** `scripts/phase17_finality/run_17b_bandwidth_audit.py` (exists).
    - **Result:** 7.53 bits/word realized bandwidth; total capacity 11.5 KB (~23K Latin chars).
- [ ] **2.2: The "Latin Test"**
    - **Task:** Determine if a common Latin text (e.g., the Vulgate) could be encoded into the 12,519 admissible decisions without violating the physical lattice constraints.
    - **Metric:** `Residual Steganographic Bandwidth` (RSB) in bits-per-token.
    - **Note:** Capacity bound: 7.53 bpw x 12,519 choices = 94,268 bits. At ~4.1 bits/char (frequency-weighted Latin), capacity ~ 22,992 chars ~ 4-5 Vulgate chapters.
- [x] **2.3: Artifact:** `results/data/phase17_finality/bandwidth_audit.json` (exists).

## 3. Task 3: The 15th-Century Operator Protocol
**Goal:** Document the "Manual" for the Voynich Engine.

- [ ] **3.1: Protocol Definition**
    - **Implementation:** Create `results/reports/phase17_finality/OPERATOR_MANUAL.md`.
    - **Content:** Step-by-step instructions for a medieval scribe: "How to generate a page of herbal text using the sliding grille."
- [ ] **3.2: Error Handling:** Formalize the "Mechanical Slip" correction procedure.

## 4. Task 4: Final Research Monograph
**Goal:** Consolidate 17 phases of research into a single academic-grade summary.

- [ ] **4.1: Monograph Synthesis**
    - **Implementation:** Update `scripts/support_preparation/generate_publication.py`.
    - **Task:** Finalize the 17-phase structure and generate the "Voynich Engine: A Functional Solution" monograph.

---

## Success Criteria for Phase 17

1. **Physicality:** A printable PDF allows any researcher to physically reproduce "Voynichese" using 15th-century technology.
2. **Exclusion:** The bandwidth audit proves that the "Meaning" bandwidth is below the threshold required for natural language (Target: < 1.0 bit/token).
    - **Status:** SUBSTANTIAL — realized bandwidth is 7.53 bpw, well above the 3.0 bpw stego threshold. The mechanical model does NOT rule out hidden content.
3. **Closure:** The Project moves to **STATUS: SOLVED**.
