# Phase Dependencies

Which phases depend on which, what data flows between them, and what the
minimum subset is for specific analyses.

---

## Dependency Graph

```
Phase 1 (Foundation)
  │
  ├──► Phase 2 (Analysis)
  │       │
  │       └──► Phase 3 (Synthesis) ──► Phase 4 (Inference)
  │                                        │
  │                                        ├──► Phase 5 (Mechanism)
  │                                        │       │
  │                                        │       ├──► Phase 6 (Functional)
  │                                        │       │
  │                                        │       └──► Phase 7 (Human Factors)
  │                                        │               │
  │                                        │               └──► Phase 8 (Comparative)
  │                                        │
  │                                        └──► Phase 10 (Admissibility Retest)
  │
  ├──► Phase 11 (Stroke Topology)
  │
  └──► Phase 12 (Mechanical) ──► Phase 13 (Demonstration) ──► Phase 14 (Engine)

Phase 9 (Conjecture) ← reads all prior outputs (narrative only, no computation)
```

All phases require Phase 1 (the database). Phase 11 can run independently
after Phase 1 because it only needs glyph/token data.

---

## Phase-by-Phase Dependencies

| Phase | Requires | Consumes | Produces |
|---|---|---|---|
| **1 Foundation** | External data (IVTFF, scans, corpora) | Raw files | `data/voynich.db` (33 tables), control datasets |
| **2 Analysis** | Phase 1 | Database (structures, hypotheses, metrics) | Admissibility classifications, stress test results |
| **3 Synthesis** | Phase 1, Phase 2 | Segmentation profiles, admissibility outcomes | Synthetic pages, indistinguishability test results |
| **4 Inference** | Phase 1, Phase 3 | Transcriptions, synthetic controls, external corpora | Info clustering, network metrics, language ID, morphology |
| **5 Mechanism** | Phase 1, Phase 4 | Inference results, anchor records, segmentation | Lattice identification, coupling analysis, topology metrics |
| **6 Functional** | Phase 5 | Mechanism features, control datasets | System classification, efficiency metrics, adversarial results |
| **7 Human** | Phase 1, Phase 5 | Page layouts, transcriptions, mechanism results | Scribe coupling, quire structure, ergonomic assessments |
| **8 Comparative** | Phase 7 | Human factors, formal system classification | Proximity scores, artifact similarity |
| **9 Conjecture** | Phases 1-8 | All prior reports (read-only) | Publication narrative (no computation) |
| **10 Retest** | Phases 1-8 | All prior results, external corpora | Method F-K outcomes, closure status |
| **11 Stroke** | Phase 1 | Glyph candidates, transcription tokens | Stroke features, clustering, transition matrices |
| **12 Mechanical** | Phase 5, Phase 11 | Adjacency graph, slip candidates | Grid coordinates, columnar segments, volvelle geometry |
| **13 Demonstration**| Phase 12 | Slip register, context lines | Interactive viz data, evidence gallery |
| **14 Engine** | Phase 12 | Global palette grid, state profiles | Canonical metrics, formal spec, logic export |

---

## Minimum Subsets for Common Tasks

### "I want to check a specific Phase 4 claim"
```
Phase 1 → Phase 3 → Phase 4
```
Phase 2 is needed for admissibility context but Phase 4 scripts can run
with just Phase 1 + 3 data.

### "I want to verify the mechanism identification (Phase 5)"
```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
```

### "I want to run only the stroke topology analysis (Phase 11)"
```
Phase 1 → Phase 11
```
Phase 11 is self-contained after the database is populated.

### "I want to check Phase 10 adversarial retests"
```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 10
```
Phase 10 re-examines conclusions from all prior phases.

### "I want to verify the full mechanical reconstruction (Phase 14)"
```
Phase 1 → Phase 5 → Phase 11 → Phase 12 → Phase 14
```

### "I want to regenerate the publication"
```
Phase 1 through Phase 11 (all)  →  Phase 9
```

---

## Key Data Artifacts Between Phases

| Artifact | Written by | Read by |
|---|---|---|
| `data/voynich.db` | Phase 1 | All phases |
| `results/data/phase3_synthesis/test_a_results.json` | Phase 3 | Phase 4, verification |
| `results/data/phase4_inference/montemurro_results.json` | Phase 4 | Phase 5, Phase 10 |
| `results/data/phase4_inference/network_results.json` | Phase 4 | Phase 5, Phase 10 |
| `results/data/phase5_mechanism/pilot_results.json` | Phase 5 | Phase 6, Phase 10 |
| `results/data/phase5_mechanism/anchor_coupling_confirmatory.json` | Phase 5 | Phase 7, CI checks |
| `results/data/phase7_human/phase_7c_uncertainty.json` | Phase 7 | Phase 8, CI checks |
| `results/data/phase11_stroke/test_a_clustering.json` | Phase 11 | Verification |
| `results/data/phase12_mechanical/slip_detection_results.json` | Phase 12 | Phase 13, Phase 14 |
| `results/data/phase14_machine/full_palette_grid.json` | Phase 14 | Documentation, interactive tools |
| `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Phase 14 | Publication |
| `core_status/` (7+ files) | Various | `ci_check.sh`, `verify_reproduction.sh` |

---

## Execution Time Estimates

| Phase | Approximate Time | Notes |
|---|---|---|
| Phase 1 | 5-15 min | Database population from raw data |
| Phase 2 | 10-20 min | Stress tests with multiple perturbation rounds |
| Phase 3 | 15-30 min | Synthesis + indistinguishability testing |
| Phase 4 | 20-40 min | Multi-method inference (6 analyzers) |
| Phase 5 | 30-60 min | 8 mechanism pilots + anchor coupling |
| Phase 6 | 10-20 min | 3 functional characterization tests |
| Phase 7 | 5-15 min | Codicology and scribe analysis |
| Phase 8 | 5-10 min | Comparative proximity |
| Phase 9 | 2-5 min | Publication generation only |
| Phase 10 | 60-120 min | 7 adversarial stages (most expensive) |
| Phase 11 | 5-15 min | Stroke extraction + clustering |
| Phase 12 | 10-20 min | Columnar solving + slip detection |
| Phase 13 | 5-10 min | Evidence gallery generation |
| Phase 14 | 15-30 min | Global palette solving + formal spec |
| **Total** | **4-8 hours** | Full replication on modern hardware |
