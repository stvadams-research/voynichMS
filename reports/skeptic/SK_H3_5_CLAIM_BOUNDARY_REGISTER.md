# SK-H3.5 Claim Boundary Register

Date: 2026-02-10  
Scope: Allowed/disallowed SK-H3 language by closure lane

## H3_5_ALIGNED

Allowed:

- "Control comparability is closed at full-dataset scope."
- "Full-data closure is feasible and policy-aligned."

Disallowed:

- "Still blocked by data availability."

## H3_5_TERMINAL_QUALIFIED

Allowed:

- "Full-data closure is terminally blocked by approved irrecoverable source gaps."
- "Available-subset evidence is bounded and non-conclusive."
- "Reopen requires new primary pages, policy-evidence change, parity/freshness failure, or claim-boundary violation."

Disallowed:

- "Full-data comparability is closed."
- "Missing pages are expected to be fixed by rerunning existing pipelines."
- Any language implying terminal irrecoverable constraints are an unresolved software defect.

## H3_5_BLOCKED

Allowed:

- "SK-H3 remains process-blocked pending parity/freshness/contract repair."

Disallowed:

- "Terminal-qualified closure achieved."
- "Full-data closure achieved."

## H3_5_INCONCLUSIVE

Allowed:

- "SK-H3.5 lane is provisional; evidence is incomplete for deterministic closure."

Disallowed:

- "Terminal-qualified closure achieved."
- "Full-data closure achieved."

## Mandatory Terminal-Qualified Markers

When `h3_5_closure_lane=H3_5_TERMINAL_QUALIFIED`, SK-H3 narrative must include all of:

- `reason_code=DATA_AVAILABILITY`
- explicit approved-irrecoverable scope statement
- bounded `available_subset` non-conclusive qualifier
- objective reopen trigger statement (not generic "rerun and retry")
