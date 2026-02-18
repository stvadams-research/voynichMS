from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any


@dataclass
class Stage4Config:
    baseline_closure_statement: str = (
        "structurally indistinguishable under tested methods"
    )


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def collect_method_decisions(
    stage1_summary: dict[str, Any] | None,
    stage1b_replication: dict[str, Any] | None,
    stage2_summary: dict[str, Any] | None,
    stage3_summary: dict[str, Any] | None,
) -> dict[str, str]:
    decisions: dict[str, str] = {
        "H": "unknown",
        "J": "unknown",
        "K": "unknown",
        "G": "unknown",
        "I": "unknown",
        "F": "unknown",
    }

    if isinstance(stage1_summary, dict):
        for key, value in stage1_summary.get("method_decisions", {}).items():
            decisions[str(key)] = str(value)

    if isinstance(stage1b_replication, dict):
        j_gate = stage1b_replication.get("method_j_status_after_gate")
        k_gate = stage1b_replication.get("method_k_status_after_gate")
        if isinstance(j_gate, str):
            decisions["J"] = j_gate
        if isinstance(k_gate, str):
            decisions["K"] = k_gate

    if isinstance(stage2_summary, dict):
        for key, value in stage2_summary.get("method_decisions", {}).items():
            decisions[str(key)] = str(value)

    if isinstance(stage3_summary, dict):
        for key, value in stage3_summary.get("method_decisions", {}).items():
            decisions[str(key)] = str(value)

    return decisions


def interpret_priority_urgent(
    stage3_priority_gate: dict[str, Any] | None,
    stage1_summary: dict[str, Any] | None,
    stage2_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    priority = "unknown"
    gate_reason = "No priority gate artifact was available."
    if isinstance(stage3_priority_gate, dict):
        priority = str(stage3_priority_gate.get("priority", "unknown"))
        gate_reason = str(stage3_priority_gate.get("reason", gate_reason))

    stage1_decisions = {}
    stage2_decisions = {}
    if isinstance(stage1_summary, dict):
        stage1_decisions = dict(stage1_summary.get("method_decisions", {}))
    if isinstance(stage2_summary, dict):
        stage2_decisions = dict(stage2_summary.get("method_decisions", {}))

    meaning = (
        "Urgent is a scheduling/compute-priority designation for Method F. "
        "It means Stage 1/2 had at least one non-strengthening signal and deep reverse search "
        "should not be deferred. It is not itself evidence that closure is defeated."
        if priority == "urgent"
        else (
            "Lower priority means Stage 2 produced jointly closure-strengthening outcomes for "
            "G and I, so Method F can be deprioritized. "
            "This is a workflow signal, not a final verdict."
        )
    )

    trigger_summary = (
        "Rule trigger: urgent when not (G and I both closure_strengthened) "
        "or when Stage 1 contains closure_weakened findings."
    )

    return {
        "priority": priority,
        "gate_reason": gate_reason,
        "meaning": meaning,
        "trigger_rule": trigger_summary,
        "inputs": {
            "stage1_method_decisions": stage1_decisions,
            "stage2_method_decisions": stage2_decisions,
        },
    }


def synthesize_stage4(
    config: Stage4Config,
    stage1_summary: dict[str, Any] | None,
    stage1b_replication: dict[str, Any] | None,
    stage2_summary: dict[str, Any] | None,
    stage3_summary: dict[str, Any] | None,
    stage3_priority_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    method_decisions = collect_method_decisions(
        stage1_summary=stage1_summary,
        stage1b_replication=stage1b_replication,
        stage2_summary=stage2_summary,
        stage3_summary=stage3_summary,
    )
    counts = {
        "closure_defeated": 0,
        "closure_strengthened": 0,
        "closure_weakened": 0,
        "indeterminate": 0,
        "test_invalid": 0,
        "unknown": 0,
    }
    for value in method_decisions.values():
        if value in counts:
            counts[value] += 1
        else:
            counts["unknown"] += 1

    if counts["closure_defeated"] > 0:
        aggregate_class = "closure_revised"
        closure_status = "reopen_domain"
        closure_reason = (
            "At least one method defeated closure; "
            "Phase 4.5 closure must be revised in the affected domain."
        )
    elif all(value == "closure_strengthened" for value in method_decisions.values()):
        aggregate_class = "closure_upgraded"
        closure_status = "upgraded"
        closure_reason = (
            "All methods strengthened closure; closure can be upgraded to include "
            "content-ungrounded and sequence-unexploitable claims."
        )
    else:
        aggregate_class = "mixed_results_tension"
        closure_status = "in_tension"
        closure_reason = (
            "Results are mixed across methods; closure is neither defeated nor upgradable and must "
            "be stated with explicit tensions."
        )

    urgency = interpret_priority_urgent(
        stage3_priority_gate=stage3_priority_gate,
        stage1_summary=stage1_summary,
        stage2_summary=stage2_summary,
    )

    return {
        "status": "ok",
        "stage": "10.4",
        "generated_at": now_utc_iso(),
        "baseline_closure_statement": config.baseline_closure_statement,
        "method_decisions": method_decisions,
        "outcome_counts": counts,
        "aggregate_class": aggregate_class,
        "closure_status": closure_status,
        "closure_reason": closure_reason,
        "urgent_designation": urgency,
        "inputs": {
            "stage1": stage1_summary,
            "stage1b": stage1b_replication,
            "stage2": stage2_summary,
            "stage3": stage3_summary,
            "stage3_priority_gate": stage3_priority_gate,
        },
    }


def build_phase10_results_markdown(
    synthesis: dict[str, Any],
    artifacts: dict[str, str],
    status_path: str,
) -> str:
    decisions = synthesis.get("method_decisions", {})
    urgent = synthesis.get("urgent_designation", {})
    lines = [
        "# Phase 10 Results",
        "",
        f"Generated: {synthesis.get('generated_at')}",
        f"Aggregate class: **{synthesis.get('aggregate_class')}**",
        f"Closure status: **{synthesis.get('closure_status')}**",
        "",
        "## Method Outcomes",
        "",
        f"- Method H: `{decisions.get('H', 'n/a')}`",
        f"- Method J: `{decisions.get('J', 'n/a')}`",
        f"- Method K: `{decisions.get('K', 'n/a')}`",
        f"- Method G: `{decisions.get('G', 'n/a')}`",
        f"- Method I: `{decisions.get('I', 'n/a')}`",
        f"- Method F: `{decisions.get('F', 'n/a')}`",
        "",
        "## Aggregate Interpretation",
        "",
        f"- Baseline closure statement: `{synthesis.get('baseline_closure_statement')}`",
        f"- Aggregate reason: {synthesis.get('closure_reason')}",
        "- Mixed-results rule applied: no by-fiat resolution; tensions are recorded explicitly.",
        "",
        "## Urgent Designation Meaning",
        "",
        f"- Priority gate: `{urgent.get('priority', 'unknown')}`",
        f"- Gate reason: {urgent.get('gate_reason', 'n/a')}",
        f"- Meaning: {urgent.get('meaning', 'n/a')}",
        f"- Trigger rule: {urgent.get('trigger_rule', 'n/a')}",
        "",
        "## Artifacts",
        "",
        f"- Stage 4 synthesis artifact: `{artifacts.get('stage4', 'n/a')}`",
        f"- Stage 4 status tracker: `{status_path}`",
        f"- Stage 1 summary: `{artifacts.get('stage1', 'n/a')}`",
        f"- Stage 1b replication: `{artifacts.get('stage1b', 'n/a')}`",
        f"- Stage 2 summary: `{artifacts.get('stage2', 'n/a')}`",
        f"- Stage 3 summary: `{artifacts.get('stage3', 'n/a')}`",
        "",
    ]
    return "\n".join(lines)


def build_phase10_closure_update_markdown(synthesis: dict[str, Any]) -> str:
    decisions = synthesis.get("method_decisions", {})
    urgent = synthesis.get("urgent_designation", {})
    lines = [
        "# Phase 10 Closure Update",
        "",
        f"Generated: {synthesis.get('generated_at')}",
        "",
        "## Updated Closure Statement",
        "",
        "Phase 10 does not produce a closure defeat signal, but it does not support "
        "a closure upgrade. The closure remains in documented tension: some methods "
        "strengthen procedural-artifact closure while others weaken it or remain "
        "indeterminate.",
        "",
        "## Why Closure Is In Tension",
        "",
        f"- Strengthening outcomes: H=`{decisions.get('H', 'n/a')}`, "
        f"I=`{decisions.get('I', 'n/a')}`",
        f"- Weakening outcomes: J=`{decisions.get('J', 'n/a')}`, K=`{decisions.get('K', 'n/a')}`",
        f"- Indeterminate outcomes: G=`{decisions.get('G', 'n/a')}`, "
        f"F=`{decisions.get('F', 'n/a')}`",
        "- Because outcomes are mixed, the project records explicit tension "
        "rather than resolving by fiat.",
        "",
        "## Urgent Designation Clarification",
        "",
        f"- Stage 3 priority was `{urgent.get('priority', 'unknown')}`.",
        "- `urgent` means Method F should be executed promptly because earlier "
        "stages were not jointly closure-strengthening. It is an "
        "execution-priority flag, not a closure-defeat verdict.",
        "",
        "## Operational Follow-up",
        "",
        "- Preserve current closure as `in_tension` until a new test family "
        "resolves J/K weakening vs H/I strengthening.",
        "- Future upgrades require either (a) weakened methods to strengthen "
        "under stricter controls or (b) independent tests showing no stable "
        "content/decoding signal.",
        "",
    ]
    return "\n".join(lines)
