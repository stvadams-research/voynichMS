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
2. A direct reference to `docs/REOPENING_CRITERIA.md`.
3. A "What This Does Not Claim" block where applicable.

## Source Anchor

Canonical criteria originate from:

- `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`

## Operational Entitlement Dependencies (SK-H2.2 / SK-M1.2)

Closure and claim interpretation must be read with:

- `status/audit/release_gate_health_status.json`

Operational reason-code taxonomy used for entitlement downgrade:

- `GATE_CONTRACT_BLOCKED`
- `SENSITIVITY_CONTRACT_BLOCKED`
- `SENSITIVITY_RELEASE_EVIDENCE_NOT_READY`
- `PROVENANCE_RUNNER_CONTRACT_BLOCKED`

When gate health is degraded, conclusions remain framework-bounded and reopenable, but claim strength is downgraded to qualified operational contingency.
