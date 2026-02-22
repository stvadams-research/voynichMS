# Script Interface Tiers

**Date:** 2026-02-22  
**Status:** Active

This policy defines which scripts are expected to offer stable, user-facing CLI
behavior versus internal/operator-only behavior.

Canonical machine-readable source:
- `configs/project/script_interface_tiers.json`

Validation command:

```bash
python3 scripts/core_audit/check_script_interface_contract.py
```

---

## Tier Definitions

1. `tier1_user_facing`
- External researcher entrypoints.
- Must support `--help` with exit code 0.
- Must expose explicit long-form flags (for reproducible automation).
- Must reject unknown flags with non-zero exit.
- If required args exist, missing-arg execution must fail with clear diagnostics.

2. `tier2_operator`
- Operational wrappers primarily invoked by other scripts.
- Stable behavior expected, but strict CLI-contract enforcement is optional.

3. `tier3_internal`
- Internal checker/helper scripts.
- No public CLI compatibility guarantee.

---

## Current Tier 1 Surface

- `scripts/support_preparation/replicate_all.py`
- `scripts/core_audit/check_runtime_dependencies.py`
- `scripts/core_audit/check_phase_manifest.py`
- `scripts/core_audit/check_claim_artifact_map.py`
- `scripts/core_audit/check_threshold_registry.py`
- `scripts/phase19_alignment/score_alignment.py`

`scripts/phase19_alignment/score_alignment.py` currently serves as the
required-argument contract probe (`--generated-file` required).
