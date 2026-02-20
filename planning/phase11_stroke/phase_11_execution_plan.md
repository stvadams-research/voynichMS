# Phase 11 Execution Plan: Stroke Topology Analysis

**Project:** Voynich Manuscript, Structural Admissibility Program
**Phase:** 11
**Phase Name:** Stroke Topology
**Goal Type:** Sub-glyph structural decomposition and production constraint detection
**Primary Goal:** Determine whether stroke-level decomposition of EVA glyphs carries predictive structure beyond token identity, and whether that structure reflects production constraints in the generative mechanism.

---

## 1. Phase 11 Purpose and Core Question

### 1.1 Core question

Does the sub-glyph stroke composition of EVA characters produce non-random structure — in co-occurrence, transitions, or positional distribution — beyond what token identity alone explains?

### 1.2 Why Phase 11 exists

All prior phases operate at the TOKEN scale or above. The Scale hierarchy (`src/phase1_foundation/core/models.py`) defines GLYPH and STROKE as legitimate analysis scales, but no module operates below the token level.

The ergonomics module (Phase 7A) assigns scalar stroke counts per character but does not model stroke composition, connectivity, or topology. Phase 5's topology collapse analyzes token-sequence topology, not sub-glyph morphology.

If stroke-level features carry predictive information about token behavior — transitions, clustering, positional distribution — then prior phase conclusions may be incomplete. Specifically:

- Phase 5 mechanism findings assume token identity is the finest relevant grain. If stroke features independently predict transitions, the mechanism has sub-token structure.
- Phase 7A production cost estimates use scalar stroke counts. If stroke *composition* (not just count) matters, production constraint models need refinement.

Phase 11 tests whether the STROKE scale contributes signal, or whether it can be formally closed as redundant.

### 1.3 What Phase 11 is not

- Not a linguistic analysis. Stroke features are physical production properties, not phonological or semantic representations.
- Not a computer vision project. All feature assignments derive from the published EVA glyph specification, not from manuscript image analysis.
- Not a claim that stroke structure implies phonology. Even if stroke composition matters, the most parsimonious explanation is production constraint — the hand is constrained by what it just drew.
- Not a decipherment attempt.

### 1.4 Success criteria

Phase 11 is successful if it produces:

1. A complete, validated stroke feature schema covering all EVA characters.
2. A clear determination for each test: structurally significant, null, or indeterminate.
3. A robustness assessment showing whether results are sensitive to specific feature assignments.
4. An updated mechanism characterization if stroke-level structure is found.

### 1.5 Primary outputs

- `src/phase11_stroke/` — analysis modules
- `scripts/phase11_stroke/` — entry point scripts
- `tests/phase11_stroke/` — unit and integration tests
- `results/data/phase11_stroke/` — run-linked JSON artifacts
- `results/reports/phase11_stroke/phase_11_results.md` — findings report
- `planning/phase11_stroke/phase_11_execution_plan.md` — this document

---

## 2. Phase 11 Design Principles

### Principle 1: Fully Automated Feature Assignment

No feature assignment depends on human visual inspection of the manuscript. All stroke features are derived from the **published EVA glyph specification** (Landini & Zandbergen), which defines a fixed mapping from EVA letter to glyph shape. This mapping is encoded as a lookup table in code.

The lookup table is a **model** — a claim about what structural properties each EVA character possesses. Its correctness is tested by sensitivity analysis (Stage 4), not by manual review.

### Principle 2: Token-Identity Baseline Required

Every test must include a control that asks: "Does the observed structure survive after conditioning on token identity?" Since stroke features are deterministic functions of character identity, and characters compose tokens, some correlation with token-level behavior is expected. The question is whether stroke features capture a useful *abstraction* — collapsing distinct characters into behaviorally equivalent classes.

### Principle 3: Permutation Null Over Shuffled Sequences

The primary null hypothesis for all tests is: **Random reassignment of stroke features to characters would produce equal or greater structure.** This tests whether the *specific* glyph-to-feature mapping matters, not whether abstract feature dimensions correlate.

This null is stronger than a shuffled-sequence null, because it preserves all token-level structure and only disrupts the stroke decomposition itself.

### Principle 4: Fast-Kill Gate

If Test A (clustering) and Test B (transitions) both return null results at α = 0.01, Phase 11 terminates without running Test C or the synthesis stage. The STROKE scale is declared redundant and formally closed. This prevents sunk-cost continuation of a dead line of inquiry.

### Principle 5: Production Constraint Framing

Any positive results are interpreted first as production constraints — physical properties of the writing process — not as evidence for phonology, encoding, or linguistic content. Upgrading interpretation beyond production constraint requires independent evidence from outside Phase 11.

### Principle 6: Continuous Console Progress Reporting

Every script must emit structured progress output to the console throughout execution. Long-running operations (permutation loops, corpus-wide extraction, sensitivity sweeps) are indistinguishable from a hung process without progress feedback. Silence is not acceptable.

**Mandatory requirements for all scripts:**

1. **Phase banner on startup.** Print the script name, phase, stage, seed, and timestamp before any computation begins.
2. **Stage-level progress.** Before each logical stage (e.g., "computing similarity matrix", "running permutation null"), print a labeled status line.
3. **Permutation loop progress.** All permutation loops (10,000 iterations) must emit a progress update at least every 500 iterations, reporting: current iteration, elapsed time, estimated time remaining, and the running statistic value. Use `rich.progress.Progress` with a live-updating bar, or at minimum a periodic `console.print` line. The update interval should be configurable but default to every 5% of total iterations.
4. **Corpus iteration progress.** Feature extraction across the full corpus must report progress per page or per 100 lines, whichever produces updates at least every few seconds.
5. **Completion summary.** After each test completes, print: test ID, observed statistic, p-value, determination (significant/null/indeterminate), and wall-clock duration.
6. **Heartbeat for any operation exceeding 30 seconds.** If a single computation step (e.g., building a large matrix) takes longer than 30 seconds, it must emit at least one intermediate status line indicating it is still running.

**Implementation pattern (using Rich):**

```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TimeRemainingColumn
import time

console = Console()

# Startup banner
console.print(Panel.fit(
    f"[bold blue]Phase 11B: Stroke-Feature Clustering[/bold blue]\n"
    f"Seed: 42 | Permutations: 10,000 | {datetime.now().isoformat()}"
))

# Permutation loop with live progress bar
with Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn(),
    TimeRemainingColumn(),
    console=console,
) as progress:
    task = progress.add_task("Permutation null", total=n_permutations)
    for i in range(n_permutations):
        # ... permutation work ...
        progress.advance(task)

# Completion summary
console.print(f"[green]Test A complete[/green] | ρ={rho:.4f} | p={p_value:.4f} "
              f"| {determination} | {elapsed:.1f}s")
```

Scripts that do not produce console output during long-running operations will be rejected during code review regardless of correctness.

---

## 3. Stroke Feature Schema

### 3.1 EVA glyph inventory

Phase 11 operates on the 20 core EVA alphabetic characters, matching the inventory in `src/phase7_human/ergonomics.py`:

```
a c d e f g h i k l m n o p r s t v x y
```

Non-alphabetic markers (numerals, uncertainty symbols, ligature notations) are excluded from stroke analysis. Characters not in this set are silently skipped during feature extraction, with a per-run count of skipped characters logged for audit.

### 3.2 Feature dimensions

Six structural features per character, derived from the published EVA glyph forms:

| Feature | Type | Definition | Source criterion |
|---------|------|------------|------------------|
| `gallows` | binary | Tall vertical stem extending well above x-height | EVA class: t, k, p, f |
| `loop` | binary | Contains a closed or near-closed curved enclosure | Glyph form has enclosed region |
| `bench` | binary | Horizontal connecting stroke at or near baseline | EVA class: c, h |
| `descender` | binary | Stroke extends below baseline | Glyph form dips below writing line |
| `minimal` | binary | Character is a single simple stroke or dot | No compound structure |
| `stroke_count` | integer | Estimated number of distinct pen strokes | Refined from ergonomics.py estimates |

### 3.3 Primary feature table

This is the definitional lookup table, derived from the canonical EVA glyph descriptions. It is a code constant, not a runtime computation.

| Char | gallows | loop | bench | descender | minimal | stroke_count |
|------|---------|------|-------|-----------|---------|--------------|
| a    | 0       | 1    | 0     | 0         | 0       | 2            |
| c    | 0       | 0    | 1     | 0         | 0       | 1            |
| d    | 0       | 1    | 0     | 0         | 0       | 2            |
| e    | 0       | 1    | 0     | 0         | 0       | 1            |
| f    | 1       | 1    | 0     | 0         | 0       | 4            |
| g    | 0       | 1    | 0     | 1         | 0       | 2            |
| h    | 0       | 0    | 1     | 0         | 0       | 2            |
| i    | 0       | 0    | 0     | 0         | 1       | 1            |
| k    | 1       | 0    | 0     | 0         | 0       | 3            |
| l    | 0       | 0    | 0     | 0         | 1       | 2            |
| m    | 0       | 0    | 0     | 1         | 0       | 3            |
| n    | 0       | 0    | 0     | 0         | 0       | 2            |
| o    | 0       | 1    | 0     | 0         | 0       | 1            |
| p    | 1       | 1    | 0     | 0         | 0       | 4            |
| r    | 0       | 0    | 0     | 0         | 1       | 1            |
| s    | 0       | 0    | 0     | 1         | 0       | 1            |
| t    | 1       | 1    | 0     | 0         | 0       | 3            |
| v    | 0       | 0    | 0     | 0         | 0       | 3            |
| x    | 0       | 0    | 0     | 0         | 0       | 2            |
| y    | 0       | 0    | 0     | 1         | 0       | 2            |

**Assignment rationale:**

- `gallows`: Strictly {t, k, p, f}. Universally agreed classification in Voynich studies.
- `loop`: Characters with visually enclosed or near-enclosed curved regions. Includes the loop atop gallows letters t, p, f. Excludes k (angular top, no enclosure).
- `bench`: Characters that form horizontal connecting strokes. Strictly {c, h}.
- `descender`: Characters whose forms extend below baseline. {y, s, g, m}.
- `minimal`: Single-stroke or near-single-stroke characters with no compound structure. {i, r, l}. Note: l is borderline (has a hook); included because it is structurally simple. Tested in sensitivity analysis.
- `stroke_count`: Refined from `src/phase7_human/ergonomics.py` estimates with adjustment for compound forms.

### 3.4 Feature vector representation

Each character maps to a 6-element vector: `[gallows, loop, bench, descender, minimal, stroke_count]`.

For analyses requiring homogeneous feature scales, `stroke_count` is normalized to [0, 1] by dividing by the maximum value (4). The five binary features remain as-is. This gives a 6-dimensional vector in [0, 1]^6.

### 3.5 Token-level stroke profiles

For a token of length L with characters c_1, ..., c_L, three representations are computed:

- **Mean profile**: Element-wise mean of character feature vectors. Represents the "average stroke character" of the token. Dimensionality: 6.
- **Boundary profile**: Concatenation of first-character features and last-character features. Captures the morphological entry and exit of the token. Dimensionality: 12.
- **Aggregate counts**: Sum of each binary feature across characters, plus total stroke count. Represents cumulative production effort. Dimensionality: 6.

All three representations are computed and stored. Tests use whichever representation is most appropriate for the hypothesis being tested.

---

## 4. Test Specifications

### 4.1 Test A: Non-Random Stroke-Feature Clustering

**Question:** Do tokens with similar stroke profiles co-occur in the same lines more than expected by chance?

**Hypothesis:** If stroke composition reflects production constraints, tokens with similar morphological profiles may cluster — either because the scribe falls into motor patterns, or because the generative mechanism groups morphologically similar tokens.

**Method:**

1. Compute the mean stroke profile for each token type in the vocabulary.
2. Compute pairwise cosine similarity between all token-type stroke profiles.
3. For each pair of token types (above a minimum occurrence threshold of 5), compute co-occurrence rate: the fraction of lines containing both types.
4. Compute Spearman correlation ρ between stroke-profile similarity and co-occurrence rate.
5. **Frequency control:** High-frequency tokens co-occur more often regardless of stroke features. Compute the partial Spearman correlation after regressing out log-frequency-product (log(freq_i) + log(freq_j)) from both similarity and co-occurrence. Report both raw ρ and partial ρ.
6. **Null:** Randomly reassign stroke feature vectors to the 20 EVA characters (permuting the lookup table). Recompute token-type profiles, similarities, and co-occurrence correlation. Repeat 10,000 times.
7. **p-value:** Fraction of null partial-ρ values ≥ observed partial-ρ.

**Decision rules:**

- **Significant:** p < 0.01 and partial ρ > 0.05. Stroke composition influences token co-occurrence beyond frequency.
- **Null:** p ≥ 0.01 or partial ρ ≤ 0.05. No evidence that stroke features predict co-occurrence.
- **Indeterminate:** p < 0.01 but partial ρ ≤ 0.05, or result reverses under sensitivity analysis.

Deliverables:
- `results/data/phase11_stroke/test_a_clustering.json`

---

### 4.2 Test B: Stroke Features Predict Token Transitions

**Question:** At inter-token character boundaries, do the stroke features of the outgoing character (last character of token N) predict the incoming character (first character of token N+1)?

**Hypothesis:** If the scribe's hand is physically constrained by the last stroke it made, the morphological ending of one token constrains the morphological beginning of the next. This would manifest as mutual information between outgoing and incoming stroke features above what random feature assignments produce.

**Method:**

**B1 — Boundary mutual information:**

1. For every consecutive token pair (t_N, t_{N+1}) within the same line, extract:
   - `f_out` = stroke feature vector of last character of t_N
   - `f_in` = stroke feature vector of first character of t_{N+1}
2. Discretize: Each unique feature vector maps to a categorical label. Compute mutual information MI(f_out, f_in).
3. **Null:** Permute the character-to-feature-vector mapping across the 20 EVA characters. Recompute MI. Repeat 10,000 times.
4. **p-value:** Fraction of null MI ≥ observed MI.

**B2 — Intra-token mutual information:**

5. For consecutive characters c_i, c_{i+1} within the same token, compute MI(features(c_i), features(c_{i+1})).
6. Same null (permute feature assignments across characters). Same p-value computation.
7. Compare: If intra-token MI > inter-token MI, production constraints are stronger within the production unit (the token) than across boundaries.

**B3 — Information ratio:**

8. Compute MI(last_char_identity, first_char_identity) at token boundaries — the raw character-level bigram MI.
9. Report the ratio: stroke_MI / character_MI. This measures how much of the character-level transition structure is captured by the lossy stroke-feature projection.
   - Ratio near 1.0: Stroke features capture nearly all transition information. The feature abstraction is nearly complete.
   - Ratio near 0.0: Character identity carries substantial information beyond stroke features. The decomposition is too coarse.

**Decision rules:**

- **Significant (B1):** p < 0.01. The specific stroke features of boundary characters carry transition structure that random feature assignments do not.
- **Null (B1):** p ≥ 0.01. No evidence of stroke-mediated transition constraints.
- **Production constraint evidence:** B2 (intra-token) MI > B1 (inter-token) MI, both significant. Motor constraint is stronger within the production unit.
- **Abstraction quality:** B3 ratio > 0.3 indicates the stroke decomposition captures a non-trivial fraction of character-level transition structure.

Deliverables:
- `results/data/phase11_stroke/test_b_transitions.json`

---

### 4.3 Test C: Stroke Features Correlate with Lattice Position

**Gating condition:** Test C runs only if Test A or Test B produces a significant result. See Principle 4 (fast-kill gate).

**Question:** Do tokens in different positional contexts — word position within a line, line position within a page — have systematically different stroke profiles?

**Hypothesis:** If stroke composition reflects the generative mechanism's structure (e.g., lattice position determines which characters are available), then positional features should correlate with stroke profiles in non-monotonic ways. If stroke composition reflects only production fatigue or drift, correlation should be monotonic with sequential position.

**Method:**

**C1 — Word position effect:**

1. For each token occurrence, record its index within its line (position 1, 2, 3, ...).
2. Bin positions into: first, second, penultimate, last, and middle (all others). Lines with fewer than 4 tokens are excluded.
3. Compute mean stroke profile per position bin.
4. Test: Kruskal-Wallis test for each feature dimension across position bins.
5. **Null:** Permute position labels within each line (preserving line lengths and token identities). Recompute. 10,000 permutations.
6. Report per-feature p-values with Bonferroni correction (6 features = threshold p < 0.0017).

**C2 — Page position effect:**

7. For each line, record its index within its page.
8. Compute mean stroke profile per line-position tertile (first third, middle third, last third of page).
9. Same statistical test and correction as C1.

**C3 — Cross-reference with Phase 5:**

10. From Phase 5 dependency-scope features (`src/phase5_mechanism/dependency_scope/features.py`), obtain per-token feature vectors (prefix, suffix, vowel_like_count, char_entropy).
11. Compute Spearman correlation between Phase 5 features and Phase 11 stroke profiles.
12. Report whether stroke features add predictive power for positional behavior beyond what Phase 5 features already capture. Specifically: regress position bin on Phase 5 features alone, then on Phase 5 features + stroke features, and compare R^2.

**Decision rules:**

- **Significant:** At least 2 feature dimensions show p < 0.0017 (Bonferroni-corrected) for position effect, and the effect survives the permutation null.
- **Null:** No feature dimension passes corrected threshold.
- **Production drift pattern:** Significant effects are monotonic with position (e.g., stroke count decreases later in page). Consistent with fatigue, not mechanism structure.
- **Mechanism structure pattern:** Significant effects are non-monotonic or position-specific (e.g., first-word tokens have more gallows, mid-line tokens have more bench). Consistent with entry-point selection constraints or positional glyph rules.

Deliverables:
- `results/data/phase11_stroke/test_c_position.json`

---

## 5. Sensitivity and Robustness

### 5.1 Feature table perturbation

**Gating condition:** At least one test (A, B, or C) produced a significant result.

For each significant test:

1. Generate 100 perturbed feature tables. Each perturbation randomly flips exactly one binary feature assignment for one randomly chosen character.
2. Rerun the significant test with each perturbed table (using the same seed and corpus).
3. Report:
   - What fraction of perturbations preserve significance (p < 0.01)?
   - Which character-feature assignments are load-bearing (flipping them causes significance to drop)?
   - Is there a single character whose assignments dominate the result?

A result is considered **robust** if ≥ 80% of perturbations preserve significance. A result that depends on a single character's assignment is flagged as **fragile**.

### 5.2 Minimal feature set

Rerun all significant tests using only the two most unambiguous features:

- `gallows` (unambiguous: exactly {t, k, p, f}, universally agreed)
- `stroke_count` (numeric, from established estimates)

If results hold with this 2-dimensional feature set, the conclusions are robust to debatable assignments of loop, bench, descender, and minimal.

### 5.3 Extended feature set (optional)

If primary results are significant and robust under Sections 5.1 and 5.2, optionally extend the feature table with additional dimensions:

- `symmetry`: Bilateral symmetry of glyph form (0/1)
- `ascender`: Stroke extends above x-height but below gallows height (0/1) — captures {d, l}
- `openness`: Topologically open (no enclosed region) vs. closed (0/1)

This is exploratory. It does not affect the primary determinations and is reported separately.

Deliverables:
- `results/data/phase11_stroke/sensitivity_results.json`

---

## 6. Code Structure

### 6.1 Source modules

```
src/phase11_stroke/
  __init__.py
  schema.py              # Feature definitions, lookup table, normalization
  extractor.py           # Extract stroke profiles from EVA tokens
  clustering.py          # Test A: co-occurrence clustering analysis
  transitions.py         # Test B: boundary transition analysis
  position.py            # Test C: positional correlation analysis
  sensitivity.py         # Feature table perturbation and robustness checks
```

**Progress reporting contract (Principle 6):**

All analyzer classes in `src/phase11_stroke/` accept an optional `console: rich.console.Console` parameter. When provided, analyzers emit progress updates directly. When `None`, analyzers run silently (for unit testing). This keeps progress reporting in the library layer — scripts do not need to wrap every loop manually.

Analyzers that run permutation loops must also accept an optional `progress: rich.progress.Progress` instance and `task_id` so the calling script can provide a shared progress bar. If not provided, the analyzer creates its own. This allows scripts to compose multiple analyzers under a single progress display.

**Module responsibilities:**

- `schema.py`: Defines `STROKE_FEATURES` dict constant (the lookup table from Section 3.3). Provides `StrokeSchema` class with methods:
  - `get_char_features(char: str) -> np.ndarray` — Returns the 6-element feature vector for a single EVA character. Returns None for characters outside the inventory.
  - `get_token_profile(token: str, mode: str) -> np.ndarray` — Computes token-level profile. `mode` is one of `"mean"`, `"boundary"`, `"aggregate"`.
  - `normalize(features: np.ndarray) -> np.ndarray` — Normalizes stroke_count to [0, 1].
  - `char_inventory() -> List[str]` — Returns the 20 recognized characters.
  - `feature_names() -> List[str]` — Returns the 6 feature names in order.
  - `permuted_table(rng: np.random.Generator) -> dict` — Returns a copy of the feature table with feature vectors randomly permuted across characters.

- `extractor.py`: Operates on the full corpus. Takes parsed lines from EVAParser, produces per-token stroke profiles with positional metadata. Provides `StrokeExtractor` class with:
  - `extract_corpus(parsed_lines, console=None) -> dict` — Returns structured dict with per-token profiles (mean, boundary, aggregate), per-line summaries, per-page summaries, and corpus-level statistics. Also records skipped-character counts. When `console` is provided, emits progress every 100 lines or per page.

- `clustering.py`: Implements Test A. Provides `ClusteringAnalyzer` class with:
  - `run(extracted_data: dict, n_permutations: int, rng: np.random.Generator, console=None, progress=None, task_id=None) -> dict` — Computes similarity, co-occurrence, correlation, frequency control, and permutation null. Returns results dict. Emits permutation progress via `progress` bar or console fallback.

- `transitions.py`: Implements Tests B1, B2, B3. Provides `TransitionAnalyzer` class with:
  - `run(parsed_lines, schema: StrokeSchema, n_permutations: int, rng: np.random.Generator, console=None, progress=None, task_id=None) -> dict` — Computes boundary MI, intra-token MI, information ratio, and permutation nulls. Returns results dict.

- `position.py`: Implements Tests C1, C2, C3. Provides `PositionAnalyzer` class with:
  - `run(extracted_data: dict, n_permutations: int, rng: np.random.Generator, console=None, progress=None, task_id=None) -> dict` — Computes positional effects, Kruskal-Wallis tests, and Phase 5 cross-reference. Returns results dict.

- `sensitivity.py`: Provides `SensitivityAnalyzer` class with:
  - `run_perturbation(test_fn, schema: StrokeSchema, n_perturbations: int, rng: np.random.Generator, console=None) -> dict` — Generates perturbed tables, reruns tests, reports stability. Emits progress per perturbation.
  - `run_minimal(test_fn, rng: np.random.Generator, console=None) -> dict` — Reruns with gallows + stroke_count only.

### 6.2 Scripts

```
scripts/phase11_stroke/
  README.md
  run_11a_extract.py          # Stage 1: Extract features for full corpus
  run_11b_cluster.py          # Stage 2: Test A
  run_11c_transitions.py      # Stage 2: Test B
  run_11d_position.py         # Stage 3: Test C (gated)
  run_11e_sensitivity.py      # Stage 4: Robustness checks (gated)
  run_11f_synthesis.py        # Stage 5: Generate final report
```

Each script follows the established pattern, incorporating the progress reporting mandate (Principle 6):

```python
#!/usr/bin/env python3
"""Phase 11X: [Description]"""
import sys
import time
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TimeRemainingColumn

from phase1_foundation.runs.manager import active_run
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.randomness import RandomnessController

console = Console()
SEED = 42
N_PERMUTATIONS = 10_000

def main():
    # --- Startup banner (Principle 6.1) ---
    console.print(Panel.fit(
        f"[bold blue]Phase 11X: [Description][/bold blue]\n"
        f"Seed: {SEED} | Permutations: {N_PERMUTATIONS:,} | {datetime.now().isoformat()}"
    ))
    t_start = time.time()

    with active_run(config={"command": "run_11x_...", "seed": SEED}) as run:
        # --- Stage-level progress (Principle 6.2) ---
        console.print("[cyan]Stage:[/cyan] Computing observed statistic...")

        # ... observed statistic computation ...

        # --- Permutation loop with live progress bar (Principle 6.3) ---
        console.print(f"[cyan]Stage:[/cyan] Running {N_PERMUTATIONS:,} permutations...")
        null_values = []
        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Permutation null", total=N_PERMUTATIONS)
            for i in range(N_PERMUTATIONS):
                # ... permutation work ...
                progress.advance(task)

        # --- Completion summary (Principle 6.5) ---
        elapsed = time.time() - t_start
        console.print(
            f"[green]Test complete[/green] | stat={observed:.4f} | "
            f"p={p_value:.4f} | {determination} | {elapsed:.1f}s"
        )

        ProvenanceWriter.save_results(results, output_path)

if __name__ == "__main__":
    main()
```

### 6.3 Tests

```
tests/phase11_stroke/
  __init__.py
  test_schema.py              # Feature table completeness, normalization, permutation
  test_extractor.py           # Extraction correctness on known tokens
  test_clustering.py          # Test A logic on synthetic data
  test_transitions.py         # Test B logic on synthetic data
  test_position.py            # Test C logic on synthetic data
```

**Test conventions (matching project patterns):**

- Pytest functions, no classes
- Type-hinted `-> None`
- Synthetic test data with known ground truth
- At least one positive case (structure should be detected) and one null case (no structure) per test module
- Tests must not depend on the real Voynich corpus (use synthetic EVA-like sequences)

**Key tests per module:**

`test_schema.py`:
- All 20 characters have feature vectors of length 6
- Feature vectors contain only valid values (0/1 for binary, 1-4 for stroke_count)
- No character is missing from the inventory
- Normalization maps stroke_count to [0, 1]
- Permuted table has the same set of feature vectors, just reassigned
- `get_token_profile` handles edge cases: empty string, single character, unknown characters

`test_extractor.py`:
- Known token "daiin" produces expected mean/boundary/aggregate profiles
- Tokens with only unknown characters produce empty/zero profiles
- Skipped character counting is accurate

`test_clustering.py`:
- Synthetic corpus where tokens with similar stroke profiles always co-occur → ρ > 0
- Synthetic corpus where token placement is random → ρ ≈ 0
- Frequency control removes spurious correlation from high-frequency tokens

`test_transitions.py`:
- Synthetic corpus with deterministic stroke-boundary transitions → MI > 0
- Synthetic corpus with random character placement → MI ≈ 0
- B3 ratio computation is correct for known MI values

`test_position.py`:
- Synthetic corpus where first-position tokens have all-gallows characters → Kruskal-Wallis significant
- Synthetic corpus with no positional pattern → Kruskal-Wallis not significant

### 6.4 Results

```
results/data/phase11_stroke/
  stroke_features.json            # Full corpus extraction (Stage 1)
  test_a_clustering.json          # Test A results
  test_b_transitions.json         # Test B results
  test_c_position.json            # Test C results (if gated in)
  sensitivity_results.json        # Robustness analysis (if gated in)
  by_run/                         # Immutable run-scoped snapshots

results/reports/phase11_stroke/
  phase_11_results.md             # Complete findings report
```

**JSON structure (all result files):**

```json
{
  "provenance": {
    "run_id": "...",
    "git_commit": "...",
    "timestamp": "...",
    "seed": 42,
    "command": "run_11x_..."
  },
  "results": {
    "test_id": "A|B1|B2|B3|C1|C2|C3",
    "observed_statistic": 0.0,
    "null_distribution_summary": {
      "mean": 0.0,
      "std": 0.0,
      "percentile_95": 0.0,
      "percentile_99": 0.0
    },
    "p_value": 0.0,
    "n_permutations": 10000,
    "determination": "significant|null|indeterminate",
    "details": {}
  }
}
```

---

## 7. Execution Stages

### Stage 0: Schema Definition and Validation

**Tasks:**

1. Implement `src/phase11_stroke/__init__.py` (empty, module marker).
2. Implement `src/phase11_stroke/schema.py` with the feature table from Section 3.3.
3. Implement `src/phase11_stroke/extractor.py` for corpus-wide feature extraction.
4. Write `tests/phase11_stroke/__init__.py`, `test_schema.py`, and `test_extractor.py`.
5. Run tests. Validate:
   - Every character in the 20-character inventory has a feature vector.
   - Every feature vector has dimensionality 6.
   - Normalization produces values in [0, 1].
   - Edge cases (empty tokens, unknown characters) are handled.

**Dependencies:** None.

**Provenance:** Not applicable (no corpus data processed).

Deliverables:
- `src/phase11_stroke/__init__.py`
- `src/phase11_stroke/schema.py`
- `src/phase11_stroke/extractor.py`
- `tests/phase11_stroke/__init__.py`
- `tests/phase11_stroke/test_schema.py`
- `tests/phase11_stroke/test_extractor.py`

---

### Stage 1: Feature Extraction

**Tasks:**

1. Implement and run `scripts/phase11_stroke/run_11a_extract.py`.
2. Parse the full Voynich corpus via EVAParser (canonical transcription path).
3. For each token occurrence, compute mean profile, boundary profile, and aggregate counts.
4. Store per-token, per-line, and per-page aggregated features.
5. Log and save the count of skipped (non-EVA) characters.
6. Save to `results/data/phase11_stroke/stroke_features.json`.

**Dependencies:** Stage 0 (schema and extractor must be implemented and tested).

**Provenance requirements:**
- RunID registered via `active_run`
- RandomnessController mode: **FORBIDDEN** (extraction is fully deterministic)
- Corpus hash recorded in provenance

Deliverables:
- `results/data/phase11_stroke/stroke_features.json`
- `scripts/phase11_stroke/run_11a_extract.py`

---

### Stage 2: Core Statistical Tests (A and B)

**Tasks:**

1. Implement `src/phase11_stroke/clustering.py` and `src/phase11_stroke/transitions.py`.
2. Write `tests/phase11_stroke/test_clustering.py` and `test_transitions.py`.
3. Implement and run `scripts/phase11_stroke/run_11b_cluster.py` — Test A.
4. Implement and run `scripts/phase11_stroke/run_11c_transitions.py` — Test B.
5. Tests A and B are independent and may run in parallel.

**Dependencies:** Stage 1 (extracted features required).

**Provenance requirements:**
- RunID registered via `active_run`
- RandomnessController mode: **SEEDED** (seed=42)
- 10,000 permutations per null distribution
- `numpy.random.Generator` seeded from RandomnessController, not `random.random()`

**Fast-kill gate evaluation:**

After Stage 2 completes, evaluate:
- If Test A p ≥ 0.01 **AND** Test B1 p ≥ 0.01: **TERMINATE.** Skip Stages 3–5. Write a brief termination report documenting the null results and formally closing the STROKE scale.
- If either Test A p < 0.01 **OR** Test B1 p < 0.01: Proceed to Stage 3.

Deliverables:
- `src/phase11_stroke/clustering.py`
- `src/phase11_stroke/transitions.py`
- `tests/phase11_stroke/test_clustering.py`
- `tests/phase11_stroke/test_transitions.py`
- `results/data/phase11_stroke/test_a_clustering.json`
- `results/data/phase11_stroke/test_b_transitions.json`
- `scripts/phase11_stroke/run_11b_cluster.py`
- `scripts/phase11_stroke/run_11c_transitions.py`

---

### Stage 3: Positional Analysis (Gated)

**Gating condition:** At least one of Test A or Test B1 produced p < 0.01.

**Tasks:**

1. Implement `src/phase11_stroke/position.py`.
2. Write `tests/phase11_stroke/test_position.py`.
3. Implement and run `scripts/phase11_stroke/run_11d_position.py` — Test C.
4. Cross-reference with Phase 5 dependency-scope features.

**Dependencies:** Stage 2 (must pass fast-kill gate).

**Provenance requirements:**
- RunID registered via `active_run`
- RandomnessController mode: **SEEDED** (seed=42)
- 10,000 permutations

Deliverables:
- `src/phase11_stroke/position.py`
- `tests/phase11_stroke/test_position.py`
- `results/data/phase11_stroke/test_c_position.json`
- `scripts/phase11_stroke/run_11d_position.py`

---

### Stage 4: Sensitivity Analysis (Gated)

**Gating condition:** At least one test (A, B, or C) produced p < 0.01.

**Tasks:**

1. Implement `src/phase11_stroke/sensitivity.py`.
2. Implement and run `scripts/phase11_stroke/run_11e_sensitivity.py`.
3. Perturbation analysis: 100 perturbed tables per significant test.
4. Minimal feature set replication: gallows + stroke_count only.
5. Classify each significant result as **robust** (≥80% perturbations preserve significance) or **fragile** (<80%).

**Dependencies:** Stages 2 and/or 3 (significant results required).

**Provenance requirements:**
- RunID registered via `active_run`
- RandomnessController mode: **SEEDED** (seed=42)
- Each perturbation uses a deterministic sub-seed derived from the main seed

Deliverables:
- `src/phase11_stroke/sensitivity.py`
- `results/data/phase11_stroke/sensitivity_results.json`
- `scripts/phase11_stroke/run_11e_sensitivity.py`

---

### Stage 5: Synthesis

**Tasks:**

1. Implement and run `scripts/phase11_stroke/run_11f_synthesis.py`.
2. Compile all test results, sensitivity analysis, and interpretive classification into `results/reports/phase11_stroke/phase_11_results.md`.
3. Classify overall outcome into one of the four classes defined in Section 8.1.
4. Update mechanism characterization if warranted.
5. Write `scripts/phase11_stroke/README.md`.

**Dependencies:** All prior stages.

Deliverables:
- `results/reports/phase11_stroke/phase_11_results.md`
- `scripts/phase11_stroke/run_11f_synthesis.py`
- `scripts/phase11_stroke/README.md`

---

## 8. Interpretation Framework

### 8.1 Outcome classes

| Outcome | Condition | Interpretation |
|---------|-----------|----------------|
| **STROKE_NULL** | Tests A and B both null (fast-kill) | Stroke-level features carry no predictive structure. STROKE scale is formally redundant. Prior phase conclusions at TOKEN scale are complete. |
| **PRODUCTION_CONSTRAINT** | Test B significant, Test C null or shows monotonic drift | Stroke features predict transitions. Consistent with motor/production constraints. The mechanism has sub-token structure but it reflects the writing process, not the generative logic. |
| **MECHANISM_STRUCTURE** | Test B significant, Test C shows non-monotonic positional effects | Stroke features interact with positional structure. The generative mechanism may operate partly at sub-token level. Phase 5 findings require refinement. |
| **CLUSTERING_ONLY** | Test A significant, Test B null | Tokens with similar morphology co-occur, but not because of boundary constraints. May reflect scribe motor habits or visual grouping. Low-impact finding. |

### 8.2 Implications for prior phases

- **STROKE_NULL:** No revision needed. STROKE scale can be formally excluded from future work.
- **PRODUCTION_CONSTRAINT:** Phase 7A production cost model should be upgraded from scalar stroke counts to feature-weighted profiles. Phase 5 mechanism characterization gains a sub-token refinement but does not change at the structural level.
- **MECHANISM_STRUCTURE:** Phase 5 topology conclusions should be re-examined for sub-token sensitivity. The generative mechanism may have a glyph-composition rule in addition to a token-selection rule. This does not imply linguistic content — it implies the mechanism has structure at a finer grain than previously tested.
- **CLUSTERING_ONLY:** No revision to mechanism phases. Minor note for Phase 7 human factors.

### 8.3 What Phase 11 cannot conclude

- That stroke features encode phonological units.
- That glyph morphology implies a specific writing system type (Phase 10 Method H addresses this independently).
- That any production constraint implies intentional encoding or a constructed language.
- That the stroke feature schema is the "correct" decomposition — it is a model whose utility is measured by predictive power, not by correspondence to historical authorial intent.

---

## 9. Run Structure and Provenance

### 9.1 Run requirements

Every script execution must record:
- Run ID via `active_run()`
- Git commit hash (automatic via RunContext)
- RandomnessController mode (FORBIDDEN for Stage 1, SEEDED for Stages 2–4)
- Seed value (42 unless explicitly varied for robustness)
- Permutation count (10,000 for all null distributions)
- Input corpus hash (from EVAParser canonical path)
- Phase 11 schema version (hash of the feature table dict)

### 9.2 Reproducibility

All results must be exactly reproducible given:
- The same git commit
- The same seed
- The same corpus file

No floating-point non-determinism is permitted in statistical tests. Use `numpy.random.Generator` seeded from `RandomnessController`, not `random.random()` or unseeded `numpy.random`. Permutation loops must use deterministic iteration order (sorted keys, fixed indices).

### 9.3 Complete file structure

```
planning/phase11_stroke/
  phase_11_execution_plan.md              # This document

src/phase11_stroke/
  __init__.py
  schema.py
  extractor.py
  clustering.py
  transitions.py
  position.py
  sensitivity.py

scripts/phase11_stroke/
  README.md
  run_11a_extract.py
  run_11b_cluster.py
  run_11c_transitions.py
  run_11d_position.py
  run_11e_sensitivity.py
  run_11f_synthesis.py

tests/phase11_stroke/
  __init__.py
  test_schema.py
  test_extractor.py
  test_clustering.py
  test_transitions.py
  test_position.py

results/data/phase11_stroke/
  stroke_features.json
  test_a_clustering.json
  test_b_transitions.json
  test_c_position.json
  sensitivity_results.json
  by_run/

results/reports/phase11_stroke/
  phase_11_results.md
```

---

## 10. Phase 11 Termination Statement

Phase 11 tests whether sub-glyph stroke composition of EVA characters carries predictive structure beyond token identity. Using a fully automated stroke feature schema derived from the published EVA glyph specification, three tests evaluate co-occurrence clustering, transition prediction at character boundaries, and positional correlation at the stroke level. A fast-kill gate terminates the phase early if the two primary tests (clustering and transitions) both return null, preventing investment in a non-productive analysis scale.

If all tests return null results, the STROKE scale is formally closed as redundant, confirming that prior phases operating at the TOKEN scale are complete. If significant structure is found, it is interpreted first as production constraint evidence — the hand constrained by what it just drew — unless positional analysis indicates non-monotonic interaction with mechanism structure, in which case Phase 5 conclusions require sub-token refinement.

Even if stroke structure matters, that does not imply phonology. It would more likely imply production constraints. This distinction is maintained throughout Phase 11 interpretation.

This determination would change if:

- An alternative stroke decomposition (e.g., based on high-resolution image analysis or a different transcription system) yields substantially different feature assignments that reverse the test outcomes.
- Additional EVA characters are identified in the transcription corpus that were not included in the 20-character inventory.
- External evidence links specific stroke features to a known writing system's structural units, warranting reinterpretation of Phase 11 results under a linguistic rather than production-constraint framework.
