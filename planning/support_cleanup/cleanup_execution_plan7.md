# Cleanup Execution Plan: Transition to Publication-Ready Architecture

**Date:** 2026-02-21
**Objective:** Transition the VoynichMS project from an "Experiment-Active" structure to a "Publication-Ready" architecture.
**Focus:** Correctness, reproducibility, credibility, and maintainability.

## 1. High-Level Goals

1.  **Structural Integrity:** Enforce a strict 1:1 mapping between `src/`, `scripts/`, `tests/`, and `results/` for all active phases.
2.  **Code Maturity:** Promote logic from "script-heavy" implementations in `scripts/` to reusable, tested modules in `src/`.
3.  **Documentation Consistency:** Ensure `ARCHITECTURE.md`, `STATUS.md`, and phase-level READMEs reflect the current state of the project (Phases 1-19).
4.  **Reproducibility:** Verify that `replicate_all.py` and individual phase scripts meet Tier 1/2 standards and function correctly.

## 2. Execution Phases

### Phase 1: Structural Regularization & Naming (Immediate)

**Goal:** Resolve naming inconsistencies and missing directories.

*   **Action 1.1: Standardize Phase 15 (Rule Extraction)**
    *   **Decision:** Canonical name will be `phase15_rule_extraction`.
    *   **Tasks:**
        *   Create `src/phase15_rule_extraction/`.
        *   Rename `tests/phase15_selection/` -> `tests/phase15_rule_extraction/`.
        *   Rename `results/data/phase15_selection/` -> `results/data/phase15_rule_extraction/`.
        *   Update `scripts/phase15_rule_extraction/` to import from `src/`.

*   **Action 1.2: Standardize Phase 16 (Physical Grounding)**
    *   **Decision:** Canonical name will be `phase16_physical_grounding`.
    *   **Tasks:**
        *   Create `src/phase16_physical_grounding/`.
        *   Rename `tests/phase16_physical/` -> `tests/phase16_physical_grounding/`.
        *   Rename `results/data/phase16_physical/` -> `results/data/phase16_physical_grounding/`.
        *   Update `scripts/phase16_physical_grounding/` to import from `src/`.

*   **Action 1.3: Standardize Phase 18 (Comparative/Generate)**
    *   **Decision:** Clarify if `phase18_comparative` and `phase18_generate` are distinct or merged. Likely `phase18_synthesis` or similar if they are combined, or keep distinct if they serve different roles.
    *   **Investigation:** Check if `phase18_generate` is a utility for `phase18_comparative`.
    *   **Tasks:**
        *   Create `src/phase18_comparative/` (and `src/phase18_generate/` if distinct).
        *   Ensure `tests/` exist for both.
        *   Resolve `scripts/` duality.

*   **Action 1.4: Address Missing/Orphaned Phases**
    *   **Phase 13 (Demonstration):** Create `src/phase13_demonstration/` and `tests/phase13_demonstration/`.
    *   **Phase 17 (Finality):** Create `src/phase17_finality/` and `tests/phase17_finality/`.
    *   **Phase 19 (Alignment):** Ensure `tests/phase19_alignment/` exists (currently missing).

### Phase 2: Code Migration & Refactoring (High ROI)

**Goal:** Move logic from `scripts/` to `src/` to enable testing and reuse.

*   **Action 2.1: Migrate Phase 15 Logic**
    *   Move `Trace Instrumentation` logic to `src/phase15_rule_extraction/instrumentation.py`.
    *   Move `Rule Extraction` logic to `src/phase15_rule_extraction/extraction.py`.
    *   Refactor `scripts/phase15_rule_extraction/*.py` to use these modules.

*   **Action 2.2: Migrate Phase 16 Logic**
    *   Move physical grounding logic (ergonomics, etc.) to `src/phase16_physical_grounding/`.
    *   Refactor scripts.

*   **Action 2.3: Audit & Cleanup Scripts**
    *   Ensure all scripts in `scripts/` handle arguments via `argparse`/`click` (Tier 1/2).
    *   Remove hardcoded paths where possible (use `configs/`).

### Phase 3: Documentation Synchronization

**Goal:** Ensure documentation reflects the codebase.

*   **Action 3.1: Update ARCHITECTURE.md**
    *   Add sections for Phases 18 and 19.
    *   Update diagrams/descriptions for Refactored Phases 15/16.

*   **Action 3.2: Update STATUS.md**
    *   Reflect the "Publication-Ready" status of Phases 15-19.
    *   Mark older phases as "Complete/Frozen".

*   **Action 3.3: Phase READMEs**
    *   Ensure every `src/phase*` directory has a `README.md` explaining its purpose, inputs, and outputs.

### Phase 4: Verification & Coverage

**Goal:** Ensure the system works and is tested.

*   **Action 4.1: Add Missing Tests**
    *   Create tests for new `src/` modules (Phases 15, 16, 18, 19).
    *   Target >50% coverage for new modules.

*   **Action 4.2: Full Replication Run**
    *   Run `replicate_all.py` (or equivalent chain) to verify end-to-end integrity.
    *   Validate artifacts against `claim_artifact_map.md`.

## 3. Immediate Next Steps

1.  Execute **Action 1.1** (Phase 15 Standardization).
2.  Execute **Action 1.2** (Phase 16 Standardization).
3.  Investigate Phase 18 duality.
