# Reopening Criteria (Canonical)

## Purpose

This document is the canonical reference for when framework-bounded closure claims may be reopened.

## Gatekeeper Criteria

A closure claim may be reopened if at least one criterion is satisfied:

1. `Irreducible Signal`: identification of a statistical signal that survives comparison against known non-semantic structured generators and cannot be reproduced without latent-state coupling.
2. `External Grounding`: discovery of independent external evidence (for example a bilingual crib or non-textual structural alignment) that bypasses pure text statistics.
3. `Framework Shift`: formally specified change to the admissibility framework that introduces new falsifiable assumptions.

## Decision Rule

- If none of the criteria are satisfied, the current closure remains framework-bounded and conditional.
- If any criterion is satisfied with auditable evidence, the relevant phase or claim must be reopened and re-evaluated.

## Required Reference Pattern

Closure-bearing reports should include:

1. An explicit framework-bounded closure statement.
2. A direct reference to `governance/REOPENING_CRITERIA.md`.
3. A "What This Does Not Claim" block where applicable.

## Source Anchor

Canonical criteria originate from:

- `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`

## Operational Entitlement Dependencies (SK-H2.2 / SK-M1.2)

Closure and claim interpretation must be read with:

- `core_status/core_audit/release_gate_health_status.json`

Operational reason-code taxonomy used for entitlement downgrade:

- `GATE_CONTRACT_BLOCKED`
- `SENSITIVITY_CONTRACT_BLOCKED`
- `SENSITIVITY_RELEASE_EVIDENCE_NOT_READY`
- `PROVENANCE_RUNNER_CONTRACT_BLOCKED`

When gate health is degraded, conclusions remain framework-bounded and reopenable, but claim strength is downgraded to qualified operational contingency.

## SK-H2.4 Entitlement Reopen Triggers

SK-H2.4 claim-entitlement classification must be revisited when either trigger
occurs:

1. Gate health transitions from `GATE_HEALTH_DEGRADED` to `GATE_HEALTH_OK`
   with passing release sensitivity contract evidence.
2. Claim/closure entitlement policies are revised with documented rationale and
   parity-tested checker updates.
