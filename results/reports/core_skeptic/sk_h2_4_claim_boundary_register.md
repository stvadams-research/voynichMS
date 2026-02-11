# SK-H2.4 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_H2_4_EXECUTION_PLAN.md`

## Purpose

Bind closure and claim language to deterministic H2.4 entitlement lanes.

## Lane-Bound Taxonomy

| Lane | Preconditions | Allowed Claim | Disallowed Claim |
|---|---|---|---|
| `H2_4_ALIGNED` | `GATE_HEALTH_OK`, healthy checker parity, fresh gate artifact | framework-bounded conclusive-within-scope language | degraded-state contingent framing as if still blocked |
| `H2_4_QUALIFIED` | `GATE_HEALTH_DEGRADED`, checker parity, fresh gate artifact, explicit dependency marker | qualified/reopenable/operationally contingent closure language | unqualified terminal or fully entitled closure language |
| `H2_4_BLOCKED` | lane/class/checker mismatch or stale gate-health artifact | unresolved governance inconsistency language | any aligned/qualified closure claim |
| `H2_4_INCONCLUSIVE` | missing required gate-health evidence for lane assignment | provisional entitlement language | any conclusive closure claim |

## Current Cycle Lane

Current entitlement lane from canonical artifact:

- `h2_4_closure_lane=H2_4_QUALIFIED`

Required qualifier pattern across tracked docs:

- explicit operational contingency,
- `GATE_HEALTH_DEGRADED` marker,
- explicit SK-C1 release sensitivity dependency marker.

## Required Anchors Before Claim Publication

1. `core_status/core_audit/release_gate_health_status.json`:
   - `status`
   - `allowed_claim_class`
   - `allowed_closure_class`
   - `h2_4_closure_lane`
   - freshness timestamp (`generated_utc`)
2. `configs/core_skeptic/sk_h2_claim_language_policy.json` (H2 lane mapping)
3. `configs/core_skeptic/sk_m1_closure_policy.json` (closure lane mapping)
4. Checker parity:
   - `scripts/core_skeptic/check_claim_boundaries.py`
   - `scripts/core_skeptic/check_closure_conditionality.py`
   - `scripts/core_skeptic/check_claim_entitlement_coherence.py`

## Reopen Conditions

- Gate health recovers to `GATE_HEALTH_OK` with passing SK-C1 release evidence contract.
- Entitlement policy revisions are accepted with parity-tested checker updates.
