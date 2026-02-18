# System Architecture

The Voynich Manuscript research framework is organized into three distinct tiers to ensure academic rigor, skeptic-proofing, and operational reproducibility.

## 1. Project Tiers

| Tier | Directory | Meta-Name | Purpose |
| :--- | :--- | :--- | :--- |
| **I. Governance** | `governance/` | **The Constitution** | Methodologies, policies, standards, and manuals (How we work). |
| **II. Evidence** | `results/` | **The Archive** | Final reports, research data, visualizations, and publication drafts (What we found). |
| **III. Operations** | `core_status/` | **The Dashboard** | Machine-readable progress trackers, heartbeats, and CI results (Where we are). |

---

## 2. Research Layers

### Layer 1: Foundation (`src/phase1_foundation/`)
Core infrastructure for data handling and reproducibility.
- **Provenance:** Tracking of RunIDs, environment state, and deterministic seeds.
- **Metrics:** Atomic functions for Repetition Rate, Entropy, and Cluster Tightness.

### Layer 2: Analysis (`src/phase2_analysis/`)
Assumption-Resistant analytical framework.
- **Admissibility:** Formal exclusion of explanation classes (e.g., linguistic models).
- **Stress Tests:** Perturbation analysis measuring structural stability.

### Layer 3: Synthesis (`src/phase3_synthesis/`)
Generative Reconstruction framework.
- **Reconstruction:** Extraction of glyph-level grammars from manuscript sections.
- **Indistinguishability:** "Turing Test" metrics comparing synthetic vs. real output.

### Layer 4: Inference (`src/phase4_inference/`)
Diagnostic evaluation of decipherment methods.
- **Noise Floor:** False-positive testing against non-semantic controls.
- **Method Validation:** Proving whether tools can reliably distinguish noise from meaning.

### Layer 5: Visualization & Publication (`src/support_visualization/` & `scripts/support_preparation/`)
Refining findings for human interpretability.
- **Visualization:** Automatic generation of phase-specific diagnostic plots.
- **Publication:** Automated assembly of substantive research drafts from result records.

### Layer 6: Admissibility Retest (`src/phase10_admissibility/` & `scripts/phase10_admissibility/`)
Adversarial closure retest workflows that operate after the core phase stack.
- **Reverse Search:** Method F parameter-space and null-calibrated reverse mechanism tests.
- **External Grounding:** Method G/I coupling and multilingual positioning checks.
- **Synthesis:** Stage 4 closure update with explicit mixed-result tension handling.

---

## 3. Global Data Flow
1. **Raw Data** -> **Ingestion** (Database).
2. **Database** -> **Profile Extraction** -> **Constraints**.
3. **Constraints** -> **Generator** -> **Synthetic Pages**.
4. **Synthetic + Real Pages** -> **Analysis Pipeline** -> **Metrics**.
5. **Metrics** -> **Comparison/Conclusion**.
6. **Conclusion** -> **Visualization & Drafting** -> **Publication**.
