---
name: "Phase 2.1 Admissibility Mapping"
overview: "Systematically map allowed explanations against Phase 1 constraints"
todos: []
isProject: false
status: COMPLETE
executed: 2026-02-06
---

# Phase 2.1 Execution Plan: Admissibility Mapping

## Objective

Systematically map the space of allowed explanations by evaluating major explanation classes against the structural constraints established in Phase 1. This phase does not choose a winner; it filters out the impossible and constrains the possible.

---

## Execution Summary

| Phase | Status | Artifacts |
|-------|--------|-----------|
| 1. Database Schema | **COMPLETE** | `src/foundation/storage/metadata.py` |
| 2. Admissibility Engine | **COMPLETE** | `src/analysis/admissibility/manager.py` |
| 3. CLI & Reporting | **COMPLETE** | `src/foundation/cli/main.py` |
| 4. Execution Script | **COMPLETE** | `scripts/analysis/run_phase_2_1.py` |
| 5. Acceptance Demo | **COMPLETE** | `scripts/analysis/demo_phase_2_1.py` |

---

## Results: Admissibility Matrix

| Explanation Class | Status | Key Evidence |
|-------------------|--------|--------------|
| Natural Language | **INADMISSIBLE** | Glyph identity unstable (37.5% collapse); word boundaries inconsistent (75% agreement) |
| Enciphered Language | **INADMISSIBLE** | Glyph identity unstable (cannot support consistent substitution) |
| Constructed System | **ADMISSIBLE** | Surface regularity confirmed; no semantic content detected |
| Visual Grammar | **ADMISSIBLE** | Spatial relationships confirmed (anchors degrade >80% on scrambled); text-diagram linkage present |
| Hybrid System | **UNDERCONSTRAINED** | Needs evidence of different statistical profiles across sections |

### Key Finding

The Phase 1 Destructive Audit finding that **glyph identity is segmentation-dependent** directly ruled out both natural language and enciphered language explanations. This demonstrates the value of the rigorous negative control framework.

---

## Phase 1: Database Schema Expansion

**Status**: COMPLETE

**Goal**: Persist explanation classes, admissibility criteria, and final status decisions.

**Implementation**: Updated `src/foundation/storage/metadata.py`:
  - Added `ExplanationClassRecord`:
    - `id` (String) - e.g., "natural_language", "enciphered_language"
    - `name` (String)
    - `description` (Text)
    - `status` (Enum: ADMISSIBLE, INADMISSIBLE, UNDERCONSTRAINED)
  - Added `AdmissibilityConstraintRecord`:
    - `id` (Integer, Auto)
    - `explanation_class_id` (ForeignKey)
    - `constraint_type` (Enum: REQUIRED, FORBIDDEN, OPTIONAL)
    - `description` (Text) - e.g., "Must exhibit bounded vocabulary growth"
  - Added `AdmissibilityEvidenceRecord`:
    - `id` (Integer, Auto)
    - `explanation_class_id` (ForeignKey)
    - `constraint_id` (ForeignKey)
    - `structure_id` (ForeignKey) - Link to Phase 1 StructureRecord
    - `hypothesis_id` (ForeignKey) - Link to Phase 1 HypothesisRecord
    - `support_level` (Enum: SUPPORTS, CONTRADICTS, IRRELEVANT)
    - `reasoning` (Text)

---

## Phase 2: Admissibility Engine

**Status**: COMPLETE

**Goal**: Logic for registering classes, defining constraints, and mapping evidence.

**Implementation**: Created `src/analysis/admissibility/manager.py`:
  - `AdmissibilityManager` class with methods:
    - `register_class(id, name, description)`
    - `add_constraint(class_id, type, description)`
    - `map_evidence(class_id, constraint_id, structure_id, support_level, reasoning)`
    - `evaluate_status(class_id)` - Returns `EvaluationResult` with violations, unmet requirements, and reversal conditions
    - `evaluate_all()` - Evaluates all registered classes
    - `generate_report()` - Creates the Admissibility Matrix
  - Evaluation Logic:
    - If any FORBIDDEN constraint is supported by evidence -> INADMISSIBLE
    - If any REQUIRED constraint is contradicted by evidence -> INADMISSIBLE
    - If no violations, but insufficient evidence for requirements -> UNDERCONSTRAINED
    - If no violations and requirements met -> ADMISSIBLE

---

## Phase 3: CLI & Reporting

**Status**: COMPLETE

**Goal**: User-facing commands for the admissibility workflow.

**Implementation**: Updated `src/foundation/cli/main.py`:
  - `voynich admissibility register-class --id <id> --name <name> --description <desc>`
  - `voynich admissibility add-constraint --class <id> --type <type> --desc <text>`
  - `voynich admissibility map-evidence --class <id> --constraint <id> --support <level>`
  - `voynich admissibility evaluate --class <id>`
  - `voynich admissibility report` - Generates the Admissibility Matrix
  - `voynich admissibility list` - Lists all registered classes

---

## Phase 4: Execution & Verification (The "Work")

**Status**: COMPLETE

**Goal**: Actually perform the mapping for the core classes.

**Implementation**: Created `scripts/analysis/run_phase_2_1.py`:
  - **Step 1**: Registered 5 Core Classes (Natural Language, Enciphered, Constructed, Visual, Hybrid)
  - **Step 2**: Defined 18 total constraints across all classes
  - **Step 3**: Mapped 8 Phase 1 evidence items to constraints:
    - `glyph_position_entropy` (SUPPORTED) -> Natural Language positional constraints
    - `fixed_glyph_identity` (FALSIFIED) -> Contradicts Natural Language & Enciphered stable glyph requirements
    - `word_boundary_stability` (WEAKLY_SUPPORTED) -> Contradicts Natural Language word boundary requirement
    - `geometric_anchors` (ACCEPTED) -> Supports Visual Grammar spatial dependency
    - `diagram_text_alignment` -> Supports Visual Grammar text-diagram linkage
  - **Step 4**: Ran evaluation on all classes
  - **Step 5**: Generated Admissibility Matrix report

---

## Phase 5: Acceptance Demo

**Status**: COMPLETE (ALL CRITERIA PASSED)

**Goal**: Verify the process against the "Simple Acceptance Demo" criteria.

**Implementation**: Created `scripts/analysis/demo_phase_2_1.py`:

| Acceptance Criterion | Result |
|---------------------|--------|
| At least one explanation class evaluated | PASS |
| Multiple status types present (discrimination) | PASS |
| INADMISSIBLE classes have documented violations | PASS |
| ADMISSIBLE classes have reversal conditions | PASS |
| Evidence links to Phase 1 artifacts | PASS |

---

## Detailed Findings

### INADMISSIBLE: Natural Language

**Violations**:
1. **REQUIRED: Glyph identity must be stable** - CONTRADICTED
   - Evidence: Phase 1 `fixed_glyph_identity` hypothesis was FALSIFIED
   - Detail: Identity collapse rate at 5% boundary perturbation was 37.5% (threshold: 20%)

2. **REQUIRED: Word boundaries must be objective** - CONTRADICTED
   - Evidence: Phase 1 `word_boundary_stability` was WEAKLY_SUPPORTED
   - Detail: Cross-source agreement was only 75% (threshold: 80%)

### INADMISSIBLE: Enciphered Language

**Violations**:
1. **REQUIRED: Glyph identity must be stable for substitution** - CONTRADICTED
   - Evidence: Phase 1 `fixed_glyph_identity` was FALSIFIED
   - Detail: If glyph identity is unstable, consistent substitution is impossible

### ADMISSIBLE: Constructed System

**Supporting Evidence**:
- Surface regularity confirmed via `glyph_position_entropy` (text exhibits language-like patterns)

**Reversal Conditions**:
- Would become INADMISSIBLE if genuine semantic content is detected under any decoding

### ADMISSIBLE: Visual Grammar

**Supporting Evidence**:
- Spatial relationships confirmed via `geometric_anchors` (degrade >80% on scrambled data)
- Text-diagram linkage present via `diagram_text_alignment`

**Reversal Conditions**:
- Would become INADMISSIBLE if text is fully interpretable independent of visual context

### UNDERCONSTRAINED: Hybrid System

**Unmet Requirements**:
- Needs evidence that different sections/components exhibit different statistical profiles

---

## Implications for Phase 2 Tracks B & C

### Track B: Constrained Translation Stress Tests
- Translation feasibility testing should focus on **constructed system** and **visual grammar** explanations
- Pure linguistic translation attempts are **not warranted** given glyph identity instability

### Track C: Alternative System Modeling
- **Visual grammar models** have strongest evidential support
- **Constructed system models** (procedural generation, structured nonsense) remain viable
- Hybrid models need additional profiling work before evaluation

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `src/foundation/storage/metadata.py` | Added Phase 2 tables |
| `src/analysis/__init__.py` | Phase 2 package init |
| `src/analysis/admissibility/__init__.py` | Admissibility module init |
| `src/analysis/admissibility/manager.py` | AdmissibilityManager class |
| `src/foundation/cli/main.py` | Added admissibility CLI commands |
| `scripts/analysis/run_phase_2_1.py` | Execution script |
| `scripts/analysis/demo_phase_2_1.py` | Acceptance demo |

---

## Next Steps

1. **Track B**: Design translation stress tests for admissible classes (constructed, visual)
2. **Track C**: Develop specific models for visual grammar and constructed system hypotheses
3. **Hybrid Investigation**: Profile different manuscript sections to gather evidence for hybrid hypothesis
