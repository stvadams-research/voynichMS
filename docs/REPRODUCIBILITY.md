# Reproducibility Guide

This guide documents the command path to reproduce Phases 2 through 7 using the
current repository scripts.

## 1. Environment Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you do not activate a venv, the verification scripts still run but print a warning.
Set an explicit interpreter if needed:

```bash
export PYTHON_BIN=python3
```

## 2. Data and Schema Initialization

```bash
python3 scripts/foundation/acceptance_test.py
```

## 3. Phase 2 (Analysis) Reproduction

```bash
python3 scripts/analysis/run_phase_2_1.py
python3 scripts/analysis/run_phase_2_2.py
python3 scripts/analysis/run_phase_2_3.py
python3 scripts/analysis/run_phase_2_4.py
```

## 4. Phase 3 (Synthesis) Reproduction

```bash
python3 scripts/synthesis/extract_grammar.py
python3 scripts/synthesis/run_phase_3.py
python3 scripts/synthesis/run_test_a.py --seed 42 --output status/synthesis/TEST_A_RESULTS.json
python3 scripts/synthesis/run_test_b.py
python3 scripts/synthesis/run_test_c.py
python3 scripts/synthesis/run_indistinguishability_test.py
python3 scripts/synthesis/run_baseline_assessment.py
```

## 5. Phase 4-6 (Mechanism and Inference) Reproduction

### Mechanism pilots (Phase 5 family)

```bash
python3 scripts/mechanism/run_5b_pilot.py
python3 scripts/mechanism/run_5c_pilot.py
python3 scripts/mechanism/run_5d_pilot.py
python3 scripts/mechanism/run_5e_pilot.py
python3 scripts/mechanism/run_5f_pilot.py
python3 scripts/mechanism/run_5g_pilot.py
python3 scripts/mechanism/run_5j_pilot.py
python3 scripts/mechanism/run_5k_pilot.py
python3 scripts/mechanism/run_pilot.py
```

### Inference runners

```bash
python3 scripts/inference/build_corpora.py
python3 scripts/inference/run_lang_id.py
python3 scripts/inference/run_montemurro.py
python3 scripts/inference/run_morph.py
python3 scripts/inference/run_network.py
python3 scripts/inference/run_topics.py
```

## 6. Phase 7 (Human/Codicological) Reproduction

```bash
python3 scripts/human/run_7a_human_factors.py
python3 scripts/human/run_7b_codicology.py
python3 scripts/human/run_7c_comparative.py
```

## 7. Seed and Determinism Notes

- Most scripts encode deterministic seed usage internally (commonly `seed=42`
  via `active_run(config=...)` and seeded constructors).
- `run_test_a.py` supports explicit `--seed` and `--output` flags for reproducibility checks.
- Reproduction checks compare canonicalized `results` payloads (excluding volatile
  provenance timestamps/run identifiers).
- `run_indistinguishability_test.py` is strict-by-default and release-evidentiary in default mode.
- Exploratory fallback mode must be explicit:

```bash
python3 scripts/synthesis/run_indistinguishability_test.py --allow-fallback
```

- Equivalent strict explicit form (also accepted):

```bash
REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py
```

- Quick strict prerequisite check (no synthesis run, preflight only):
  - Preflight now canonicalizes split folio ids (for example `f89r1`/`f89r2` are matched as `f89r`).

```bash
REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
```

- For strict fallback enforcement during reruns:

```bash
export REQUIRE_COMPUTED=1
```

## 8. Provenance and Outputs

- Runner outputs include a `provenance` block (`run_id`, timestamps, commit).
- Outputs are written to both:
  - run-scoped immutable snapshots under `.../by_run/*.json`
  - backward-compatible latest pointer paths (the historical static filenames)
- See `docs/PROVENANCE.md` for full policy.
- `status/` is transient execution output and is not treated as release evidence.
- Release evidence should come from `reports/` plus provenance-managed `results/.../by_run/`.

## 9. Automated Verification

Use both checks after a clean reproduction run:

```bash
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
```

Verifier contract notes:

- `scripts/verify_reproduction.sh` must emit `VERIFY_REPRODUCTION_COMPLETED` on success.
- Any missing prerequisite or failed check must exit non-zero.
- `scripts/ci_check.sh` requires verifier completion sentinel; it must not report pass on partial verifier execution.
- Release sensitivity evidence is valid only when `release_evidence_ready=true` and robustness is conclusive (`PASS` or `FAIL`) with quality gates passing.
- Release-path strict preflight is always enforced. `status/synthesis/TURING_TEST_RESULTS.json` must be generated with `strict_computed=true`.
- If strict preflight is blocked only because source pages are unavailable/lost, results must record `status=BLOCKED` and `reason_code=DATA_AVAILABILITY`.
- A `BLOCKED` strict preflight with `reason_code=DATA_AVAILABILITY` is treated as a scoped data-availability constraint, not as proof of code malfunction.

Optional strict verification mode:

```bash
VERIFY_STRICT=1 bash scripts/verify_reproduction.sh
```

This enables additional `REQUIRE_COMPUTED=1` enforcement checks.

## 10. Release Baseline Checklist

Before declaring a reproducible release baseline:

1. Run verification commands in Section 9.
2. Confirm sensitivity report caveats are present in `reports/audit/SENSITIVITY_RESULTS.md`.
3. Confirm no unintended transient artifacts are staged:

```bash
git status --short
```

4. Confirm artifact policy alignment:

```bash
rg -n "^status/?$|^status/" .gitignore
```

5. Confirm required audit log is present and updated:

```bash
test -f AUDIT_LOG.md
```

6. Validate release-evidence sensitivity artifact and baseline gate:

```bash
bash scripts/audit/pre_release_check.sh
```

If a non-clean tree is intentional for a controlled release cut, you may override:

```bash
ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='AUDIT-10: controlled release-candidate validation' bash scripts/audit/pre_release_check.sh
```

`DIRTY_RELEASE_REASON` must include `:` and be at least 12 characters.

7. Optionally clean transient verification artifacts before release packaging:

```bash
bash scripts/audit/cleanup_status_artifacts.sh dry-run
bash scripts/audit/cleanup_status_artifacts.sh legacy-report
bash scripts/audit/cleanup_status_artifacts.sh clean
```
