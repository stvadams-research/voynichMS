#!/usr/bin/env python3
"""
Phase 5I anchor-coupling analysis with SK-H1 guardrails.

Outputs:
- results/mechanism/anchor_coupling_confirmatory.json (provenance-wrapped)
- results/mechanism/anchor_coupling.json (legacy plain payload)
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import and_

from foundation.core.provenance import ProvenanceWriter
from foundation.runs.manager import active_run
from foundation.storage.metadata import (
    AnchorMethodRecord,
    AnchorRecord,
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
)
from mechanism.anchor_coupling import (
    DEFAULT_MULTIMODAL_POLICY,
    H1_4_LANE_ALIGNED,
    H1_4_LANE_BLOCKED,
    H1_4_LANE_INCONCLUSIVE,
    H1_4_LANE_QUALIFIED,
    H1_5_LANE_ALIGNED,
    H1_5_LANE_BLOCKED,
    H1_5_LANE_BOUNDED,
    H1_5_LANE_INCONCLUSIVE,
    H1_5_LANE_QUALIFIED,
    ROBUSTNESS_CLASS_FRAGILE,
    ROBUSTNESS_CLASS_MIXED,
    ROBUSTNESS_CLASS_ROBUST,
    bootstrap_delta_ci,
    classify_line_cohort,
    compute_consistency_summary,
    decide_status,
    derive_h1_4_closure_lane,
    derive_h1_5_closure_lane,
    evaluate_adequacy,
    evaluate_inference,
    permutation_p_value,
)

console = Console()
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h1_multimodal_policy.json"
OUTPUT_PATH = PROJECT_ROOT / "results/mechanism/anchor_coupling_confirmatory.json"
LEGACY_OUTPUT_PATH = PROJECT_ROOT / "results/mechanism/anchor_coupling.json"


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_policy(path: Path) -> Dict[str, Any]:
    policy = copy.deepcopy(DEFAULT_MULTIMODAL_POLICY)
    if not path.exists():
        return policy
    loaded = json.loads(path.read_text(encoding="utf-8"))
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(policy.get(key), dict):
            policy[key].update(value)
        else:
            policy[key] = value
    return policy


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return list(value)
    return []


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _lane_class(lane: Dict[str, Any]) -> str:
    lane_class = str(lane.get("lane_class", "entitlement")).strip().lower()
    if lane_class in {"entitlement", "diagnostic", "stress"}:
        return lane_class
    return "entitlement"


def _resolve_lane(
    *,
    matrix_policy: Dict[str, Any],
    method_name: str,
    seed: int,
    max_lines_per_cohort: int,
) -> Dict[str, Any]:
    lane_registry = _as_list(matrix_policy.get("lane_registry"))
    for lane in lane_registry:
        if not isinstance(lane, dict):
            continue
        lane_seed = _coerce_int(lane.get("seed"))
        lane_max_lines = _coerce_int(lane.get("max_lines_per_cohort"))
        lane_method_name = str(lane.get("method_name", ""))
        if lane_seed is not None and lane_seed != seed:
            continue
        if lane_max_lines is not None and lane_max_lines != max_lines_per_cohort:
            continue
        if lane_method_name and lane_method_name != method_name:
            continue
        return lane
    return {
        "lane_id": "unregistered-lane",
        "purpose": "unregistered runtime lane",
        "lane_class": "entitlement",
        "seed": seed,
        "max_lines_per_cohort": max_lines_per_cohort,
        "method_name": method_name,
    }


def _collect_lane_outcomes(
    *,
    matrix_policy: Dict[str, Any],
    dataset_id: str,
    source_id: str,
    by_run_dir: Path,
) -> List[Dict[str, Any]]:
    lane_registry = _as_list(matrix_policy.get("lane_registry"))
    if not lane_registry:
        return []

    by_run_paths = sorted(by_run_dir.glob("anchor_coupling_confirmatory.*.json"))
    payloads: List[Dict[str, Any]] = []
    for path in by_run_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        payloads.append(payload)

    lane_outcomes: List[Dict[str, Any]] = []
    for lane in lane_registry:
        if not isinstance(lane, dict):
            continue
        lane_id = str(lane.get("lane_id", "unknown-lane"))
        lane_class = _lane_class(lane)
        lane_seed = _coerce_int(lane.get("seed"))
        lane_max_lines = _coerce_int(lane.get("max_lines_per_cohort"))
        lane_method_name = str(lane.get("method_name", ""))
        best_payload = None
        best_dt = None
        for payload in payloads:
            results = payload.get("results", {})
            if not isinstance(results, dict):
                continue
            if str(results.get("dataset_id", "")) != dataset_id:
                continue
            if str(results.get("transcription_source_id", "")) != source_id:
                continue
            method = results.get("anchor_method", {})
            if isinstance(method, dict):
                observed_method = str(method.get("name", ""))
            else:
                observed_method = ""
            sampling = ((results.get("policy") or {}).get("sampling") or {})
            observed_seed = _coerce_int(sampling.get("seed"))
            observed_max_lines = _coerce_int(sampling.get("max_lines_per_cohort"))
            if lane_seed is not None and observed_seed != lane_seed:
                continue
            if lane_max_lines is not None and observed_max_lines != lane_max_lines:
                continue
            if lane_method_name and observed_method != lane_method_name:
                continue

            provenance = payload.get("provenance", {})
            if not isinstance(provenance, dict):
                provenance = {}
            candidate_dt = _parse_iso_datetime(provenance.get("timestamp"))
            if candidate_dt is None:
                candidate_dt = _parse_iso_datetime(results.get("generated_at"))
            if best_payload is None:
                best_payload = payload
                best_dt = candidate_dt
                continue
            if candidate_dt is not None and (best_dt is None or candidate_dt > best_dt):
                best_payload = payload
                best_dt = candidate_dt

        if best_payload is None:
            lane_outcomes.append(
                {
                    "lane_id": lane_id,
                    "purpose": str(lane.get("purpose", "")),
                    "lane_class": lane_class,
                    "status": "MISSING",
                    "status_reason": "no_registered_run",
                    "run_id": None,
                    "timestamp": None,
                }
            )
            continue

        results = best_payload.get("results", {})
        if not isinstance(results, dict):
            results = {}
        provenance = best_payload.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}
        lane_outcomes.append(
            {
                "lane_id": lane_id,
                "purpose": str(lane.get("purpose", "")),
                "lane_class": lane_class,
                "status": str(results.get("status", "")),
                "status_reason": str(results.get("status_reason", "")),
                "run_id": provenance.get("run_id"),
                "timestamp": provenance.get("timestamp"),
            }
        )
    return lane_outcomes


def _build_robustness_summary(
    *,
    matrix_policy: Dict[str, Any],
    lane: Dict[str, Any],
    lane_outcomes: List[Dict[str, Any]],
    current_status: str,
) -> Dict[str, Any]:
    allowed_classes = [
        str(item) for item in _as_list(matrix_policy.get("allowed_robustness_classes"))
    ]
    observed = [row for row in lane_outcomes if row.get("status") not in {"", "MISSING"}]
    expected_lane_count = len(_as_list(matrix_policy.get("lane_registry")))
    observed_lane_count = len(observed)

    observed_entitlement = [
        row for row in observed if str(row.get("lane_class", "entitlement")) == "entitlement"
    ]
    observed_diagnostic = [
        row for row in observed if str(row.get("lane_class", "entitlement")) == "diagnostic"
    ]
    observed_stress = [
        row for row in observed if str(row.get("lane_class", "entitlement")) == "stress"
    ]

    expected_entitlement_lane_count = sum(
        1
        for lane in _as_list(matrix_policy.get("lane_registry"))
        if isinstance(lane, dict) and _lane_class(lane) == "entitlement"
    )
    expected_diagnostic_lane_count = sum(
        1
        for lane in _as_list(matrix_policy.get("lane_registry"))
        if isinstance(lane, dict) and _lane_class(lane) == "diagnostic"
    )
    expected_stress_lane_count = sum(
        1
        for lane in _as_list(matrix_policy.get("lane_registry"))
        if isinstance(lane, dict) and _lane_class(lane) == "stress"
    )

    conclusive_count = sum(
        1 for row in observed if str(row.get("status", "")).startswith("CONCLUSIVE_")
    )
    ambiguity_count = sum(
        1
        for row in observed
        if str(row.get("status", "")) == "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"
    )
    underpowered_count = sum(
        1 for row in observed if str(row.get("status", "")) == "INCONCLUSIVE_UNDERPOWERED"
    )
    blocked_count = sum(
        1 for row in observed if str(row.get("status", "")) == "BLOCKED_DATA_GEOMETRY"
    )
    matching_status_count = sum(
        1 for row in observed if str(row.get("status", "")) == current_status
    )
    agreement_ratio = (
        matching_status_count / observed_lane_count if observed_lane_count > 0 else 0.0
    )

    entitlement_conclusive_count = sum(
        1 for row in observed_entitlement if str(row.get("status", "")).startswith("CONCLUSIVE_")
    )
    entitlement_ambiguity_count = sum(
        1
        for row in observed_entitlement
        if str(row.get("status", "")) == "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"
    )
    entitlement_underpowered_count = sum(
        1
        for row in observed_entitlement
        if str(row.get("status", "")) == "INCONCLUSIVE_UNDERPOWERED"
    )
    entitlement_blocked_count = sum(
        1
        for row in observed_entitlement
        if str(row.get("status", "")) == "BLOCKED_DATA_GEOMETRY"
    )
    entitlement_matching_status_count = sum(
        1 for row in observed_entitlement if str(row.get("status", "")) == current_status
    )
    entitlement_observed_lane_count = len(observed_entitlement)
    entitlement_agreement_ratio = (
        entitlement_matching_status_count / entitlement_observed_lane_count
        if entitlement_observed_lane_count > 0
        else 0.0
    )

    required_ratio = float(
        matrix_policy.get("required_conclusive_agreement_ratio_for_robust", 1.0)
    )
    required_entitlement_ratio = float(
        matrix_policy.get(
            "required_conclusive_agreement_ratio_for_entitlement_robust",
            required_ratio,
        )
    )
    max_ambiguity = int(matrix_policy.get("max_ambiguity_lane_count_for_robust", 0))
    max_underpowered = int(matrix_policy.get("max_underpowered_lane_count_for_robust", 0))
    max_blocked = int(matrix_policy.get("max_blocked_lane_count_for_robust", 0))
    max_entitlement_ambiguity = int(
        matrix_policy.get("max_ambiguity_lane_count_for_entitlement_robust", max_ambiguity)
    )
    max_entitlement_underpowered = int(
        matrix_policy.get(
            "max_underpowered_lane_count_for_entitlement_robust", max_underpowered
        )
    )
    max_entitlement_blocked = int(
        matrix_policy.get("max_blocked_lane_count_for_entitlement_robust", max_blocked)
    )
    statuses = {str(row.get("status", "")) for row in observed}
    entitlement_statuses = {str(row.get("status", "")) for row in observed_entitlement}

    publication_lane_id = str(matrix_policy.get("publication_lane_id", "publication-default"))
    publication_lane = None
    for lane_cfg in _as_list(matrix_policy.get("lane_registry")):
        if isinstance(lane_cfg, dict) and str(lane_cfg.get("lane_id", "")) == publication_lane_id:
            publication_lane = lane_cfg
            break
    if publication_lane is None:
        robust_closure_reachable = False
        robust_closure_reachable_reason = "publication_lane_not_registered"
    elif _lane_class(publication_lane) != "entitlement":
        robust_closure_reachable = False
        robust_closure_reachable_reason = "publication_lane_not_entitlement"
    elif expected_entitlement_lane_count <= 0:
        robust_closure_reachable = False
        robust_closure_reachable_reason = "no_entitlement_lanes_registered"
    elif entitlement_observed_lane_count < expected_entitlement_lane_count:
        robust_closure_reachable = False
        robust_closure_reachable_reason = "entitlement_lane_runs_missing"
    else:
        robust_closure_reachable = True
        robust_closure_reachable_reason = "entitlement_matrix_covered"

    if (
        observed_lane_count == expected_lane_count
        and observed_lane_count > 0
        and conclusive_count == observed_lane_count
        and len(statuses) == 1
        and agreement_ratio >= required_ratio
        and ambiguity_count <= max_ambiguity
        and underpowered_count <= max_underpowered
        and blocked_count <= max_blocked
    ):
        robustness_class = ROBUSTNESS_CLASS_ROBUST
        basis = "all registered lanes conclusive and aligned"
    elif conclusive_count > 0:
        robustness_class = ROBUSTNESS_CLASS_MIXED
        basis = "canonical lane conclusive but one or more registered lanes are ambiguous or non-conclusive"
    else:
        robustness_class = ROBUSTNESS_CLASS_FRAGILE
        basis = "no conclusive support across registered lanes"

    if allowed_classes and robustness_class not in allowed_classes:
        robustness_class = ROBUSTNESS_CLASS_FRAGILE
        basis = "robustness class fell outside allowed policy set"

    if (
        entitlement_observed_lane_count == expected_entitlement_lane_count
        and entitlement_observed_lane_count > 0
        and entitlement_conclusive_count == entitlement_observed_lane_count
        and len(entitlement_statuses) == 1
        and entitlement_agreement_ratio >= required_entitlement_ratio
        and entitlement_ambiguity_count <= max_entitlement_ambiguity
        and entitlement_underpowered_count <= max_entitlement_underpowered
        and entitlement_blocked_count <= max_entitlement_blocked
    ):
        entitlement_robustness_class = ROBUSTNESS_CLASS_ROBUST
        entitlement_basis = "all entitlement lanes conclusive and aligned"
    elif entitlement_conclusive_count > 0:
        entitlement_robustness_class = ROBUSTNESS_CLASS_MIXED
        entitlement_basis = (
            "at least one entitlement lane conclusive but entitlement evidence remains mixed"
        )
    else:
        entitlement_robustness_class = ROBUSTNESS_CLASS_FRAGILE
        entitlement_basis = "no conclusive support across entitlement lanes"

    if allowed_classes and entitlement_robustness_class not in allowed_classes:
        entitlement_robustness_class = ROBUSTNESS_CLASS_FRAGILE
        entitlement_basis = "entitlement robustness class fell outside allowed policy set"

    diagnostic_non_conclusive_lane_count = sum(
        1
        for row in observed_diagnostic + observed_stress
        if not str(row.get("status", "")).startswith("CONCLUSIVE_")
    )

    lane_id = str(lane.get("lane_id", "unregistered-lane"))
    return {
        "matrix_id": str(matrix_policy.get("matrix_id", "SK_H1_4_MATRIX_UNSPECIFIED")),
        "matrix_version": str(matrix_policy.get("version", "2026-02-10-h1.4")),
        "lane_taxonomy_version": str(
            matrix_policy.get("lane_taxonomy_version", "2026-02-10-h1.5")
        ),
        "lane_id": lane_id,
        "lane_purpose": str(lane.get("purpose", "")),
        "lane_class": _lane_class(lane),
        "publication_lane_id": publication_lane_id,
        "is_publication_lane": lane_id == publication_lane_id,
        "robustness_class": robustness_class,
        "classification_basis": basis,
        "expected_lane_count": expected_lane_count,
        "observed_lane_count": observed_lane_count,
        "conclusive_lane_count": conclusive_count,
        "ambiguity_lane_count": ambiguity_count,
        "underpowered_lane_count": underpowered_count,
        "blocked_lane_count": blocked_count,
        "agreement_ratio": round(agreement_ratio, 6),
        "matching_status_count": matching_status_count,
        "expected_entitlement_lane_count": expected_entitlement_lane_count,
        "expected_diagnostic_lane_count": expected_diagnostic_lane_count,
        "expected_stress_lane_count": expected_stress_lane_count,
        "observed_entitlement_lane_count": entitlement_observed_lane_count,
        "observed_diagnostic_lane_count": len(observed_diagnostic),
        "observed_stress_lane_count": len(observed_stress),
        "entitlement_conclusive_lane_count": entitlement_conclusive_count,
        "entitlement_ambiguity_lane_count": entitlement_ambiguity_count,
        "entitlement_underpowered_lane_count": entitlement_underpowered_count,
        "entitlement_blocked_lane_count": entitlement_blocked_count,
        "entitlement_matching_status_count": entitlement_matching_status_count,
        "entitlement_agreement_ratio": round(entitlement_agreement_ratio, 6),
        "entitlement_robustness_class": entitlement_robustness_class,
        "entitlement_classification_basis": entitlement_basis,
        "diagnostic_non_conclusive_lane_count": diagnostic_non_conclusive_lane_count,
        "robust_closure_reachable": robust_closure_reachable,
        "robust_closure_reachable_reason": robust_closure_reachable_reason,
        "lane_outcomes_considered": lane_outcomes,
        "entitlement_lane_outcomes": observed_entitlement,
        "diagnostic_lane_outcomes": observed_diagnostic,
        "stress_lane_outcomes": observed_stress,
        "reopen_conditions": _as_list(matrix_policy.get("reopen_conditions")),
        "h1_5_reopen_conditions": _as_list(
            matrix_policy.get(
                "h1_5_reopen_conditions",
                matrix_policy.get("reopen_conditions"),
            )
        ),
    }


def _resolve_anchor_method(
    *,
    session,
    method_id: str | None,
    method_name: str | None,
) -> AnchorMethodRecord:
    if method_id:
        method = session.query(AnchorMethodRecord).filter_by(id=method_id).first()
        if method is None:
            raise ValueError(f"Anchor method id not found: {method_id}")
        return method
    if method_name:
        method = (
            session.query(AnchorMethodRecord)
            .filter(AnchorMethodRecord.name == method_name)
            .order_by(AnchorMethodRecord.created_at.desc())
            .first()
        )
        if method is None:
            raise ValueError(f"Anchor method name not found: {method_name}")
        return method
    method = (
        session.query(AnchorMethodRecord)
        .order_by(AnchorMethodRecord.created_at.desc())
        .first()
    )
    if method is None:
        raise ValueError("No anchor methods found in metadata store.")
    return method


def _token_is_anchored(
    anchor_events: Sequence[Dict[str, Any]],
    *,
    relation_types: Sequence[str],
    near_score_min: float,
) -> bool:
    relation_set = set(relation_types)
    for event in anchor_events:
        relation_type = str(event.get("relation_type", ""))
        score = float(event.get("score", 0.0) or 0.0)
        if relation_type not in relation_set:
            continue
        if relation_type == "near" and score < near_score_min:
            continue
        return True
    return False


def _sample_lines(
    lines: Sequence[Dict[str, Any]],
    *,
    limit: int,
    seed: int,
) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    if len(lines) <= limit:
        return list(lines)
    import random

    rng = random.Random(seed)
    idx = list(range(len(lines)))
    rng.shuffle(idx)
    selected = sorted(idx[:limit])
    return [lines[i] for i in selected]


def _line_payload(lines: Sequence[Dict[str, Any]]) -> List[List[str]]:
    return [list(line["tokens"]) for line in lines]


def _unique_page_count(lines: Sequence[Dict[str, Any]]) -> int:
    return len({str(line["page_id"]) for line in lines})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run confirmatory anchor-coupling analysis.")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    parser.add_argument("--dataset-id", default=None, help="Override policy dataset id.")
    parser.add_argument(
        "--source-id",
        default=None,
        help="Override policy transcription source id.",
    )
    parser.add_argument(
        "--method-id",
        default=None,
        help="Use a specific anchor method id.",
    )
    parser.add_argument(
        "--method-name",
        default=None,
        help="Use latest method matching this anchor method name.",
    )
    parser.add_argument(
        "--policy-path",
        default=str(POLICY_PATH),
        help="Path to SK-H1 multimodal policy JSON.",
    )
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=None,
        help="Override bootstrap iteration count.",
    )
    parser.add_argument(
        "--permutation-iterations",
        type=int,
        default=None,
        help="Override permutation iteration count.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override analysis seed.",
    )
    parser.add_argument(
        "--max-lines-per-cohort",
        type=int,
        default=None,
        help="Override sampling max lines per cohort.",
    )
    return parser.parse_args()


def run_anchor_coupling(
    *,
    db_url: str,
    dataset_id_override: str | None,
    source_id_override: str | None,
    method_id: str | None,
    method_name_override: str | None,
    policy_path: Path,
    bootstrap_iterations_override: int | None,
    permutation_iterations_override: int | None,
    seed_override: int | None,
    max_lines_override: int | None,
) -> Dict[str, Any]:
    policy = _load_policy(policy_path)
    dataset_id = dataset_id_override or str(policy.get("dataset_id", "voynich_real"))
    source_id = source_id_override or str(
        policy.get("transcription_source_id", "zandbergen_landini")
    )

    sampling_policy = policy.get("sampling", {})
    adequacy_policy = policy.get("adequacy", {})
    inference_policy = policy.get("inference", {})
    matrix_policy = policy.get("robustness_matrix", {})

    seed = int(seed_override if seed_override is not None else sampling_policy.get("seed", 42))
    matched_sampling = bool(sampling_policy.get("matched_sampling", True))
    max_lines_per_cohort = int(
        max_lines_override
        if max_lines_override is not None
        else sampling_policy.get("max_lines_per_cohort", 400)
    )
    bootstrap_iterations = int(
        bootstrap_iterations_override
        if bootstrap_iterations_override is not None
        else inference_policy.get("bootstrap_iterations", 250)
    )
    permutation_iterations = int(
        permutation_iterations_override
        if permutation_iterations_override is not None
        else inference_policy.get("permutation_iterations", 500)
    )

    relation_types = list(policy.get("anchor_relation_types", ["inside", "overlaps", "near"]))
    near_score_min = float(policy.get("near_score_min", 0.90))
    line_anchor_ratio_min = float(policy.get("line_anchor_ratio_min", 0.50))
    line_unanchored_ratio_max = float(policy.get("line_unanchored_ratio_max", 0.10))

    console.print(
        Panel.fit(
            "[bold blue]Phase 5I: Confirmatory Anchor Coupling[/bold blue]\n"
            f"dataset={dataset_id} source={source_id}",
            border_style="blue",
        )
    )

    with active_run(
        config={
            "command": "run_5i_anchor_coupling",
            "seed": seed,
            "dataset_id": dataset_id,
            "source_id": source_id,
            "policy_path": str(policy_path),
            "method_id": method_id,
            "method_name": method_name_override or policy.get("anchor_method_name"),
            "bootstrap_iterations": bootstrap_iterations,
            "permutation_iterations": permutation_iterations,
            "max_lines_per_cohort": max_lines_per_cohort,
            "matched_sampling": matched_sampling,
        }
    ) as run:
        store = MetadataStore(db_url)
        session = store.Session()
        try:
            method_name = method_name_override or str(policy.get("anchor_method_name", "geometric_v1"))
            method = _resolve_anchor_method(
                session=session,
                method_id=method_id,
                method_name=method_name,
            )
            console.print(
                f"[cyan]{_utc_now_iso()}[/cyan] using anchor method "
                f"{method.name} ({method.id})"
            )

            anchor_rows = (
                session.query(AnchorRecord.source_id, AnchorRecord.relation_type, AnchorRecord.score)
                .join(PageRecord, AnchorRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .filter(AnchorRecord.method_id == method.id)
                .filter(AnchorRecord.source_type == "word")
                .all()
            )
            anchors_by_word: Dict[str, List[Dict[str, Any]]] = {}
            relation_counts: Counter[str] = Counter()
            for anchor_source_id, relation_type, score in anchor_rows:
                key = str(anchor_source_id)
                anchors_by_word.setdefault(key, []).append(
                    {
                        "relation_type": str(relation_type),
                        "score": float(score or 0.0),
                    }
                )
                relation_counts[str(relation_type)] += 1

            token_rows = (
                session.query(
                    TranscriptionTokenRecord.id,
                    TranscriptionTokenRecord.content,
                    TranscriptionTokenRecord.token_index,
                    TranscriptionLineRecord.id,
                    TranscriptionLineRecord.line_index,
                    PageRecord.id,
                )
                .join(
                    TranscriptionLineRecord,
                    TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
                )
                .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .filter(TranscriptionLineRecord.source_id == source_id)
                .order_by(
                    PageRecord.id,
                    TranscriptionLineRecord.line_index,
                    TranscriptionTokenRecord.token_index,
                )
                .all()
            )
            console.print(
                f"[cyan]{_utc_now_iso()}[/cyan] loaded {len(token_rows)} tokens "
                f"for anchor-cohort assignment"
            )

            align_rows = (
                session.query(WordAlignmentRecord.token_id, WordAlignmentRecord.word_id)
                .join(
                    TranscriptionTokenRecord,
                    WordAlignmentRecord.token_id == TranscriptionTokenRecord.id,
                )
                .join(
                    TranscriptionLineRecord,
                    TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
                )
                .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .filter(TranscriptionLineRecord.source_id == source_id)
                .filter(
                    and_(
                        WordAlignmentRecord.token_id.isnot(None),
                        WordAlignmentRecord.word_id.isnot(None),
                    )
                )
                .all()
            )
            token_to_word: Dict[str, str] = {}
            for token_id, word_id in align_rows:
                key = str(token_id)
                if key not in token_to_word:
                    token_to_word[key] = str(word_id)

            line_map: Dict[str, Dict[str, Any]] = {}
            for token_id, content, _token_idx, line_id, _line_idx, page_id in token_rows:
                line_key = str(line_id)
                if line_key not in line_map:
                    line_map[line_key] = {
                        "line_id": line_key,
                        "page_id": str(page_id),
                        "tokens": [],
                        "anchored_flags": [],
                    }
                word_id = token_to_word.get(str(token_id))
                events = anchors_by_word.get(word_id, []) if word_id else []
                anchored = _token_is_anchored(
                    events,
                    relation_types=relation_types,
                    near_score_min=near_score_min,
                )
                line_map[line_key]["tokens"].append(str(content))
                line_map[line_key]["anchored_flags"].append(anchored)

            anchored_lines: List[Dict[str, Any]] = []
            unanchored_lines: List[Dict[str, Any]] = []
            ambiguous_lines: List[Dict[str, Any]] = []

            for line in line_map.values():
                cohort = classify_line_cohort(
                    line["anchored_flags"],
                    anchored_ratio_min=line_anchor_ratio_min,
                    unanchored_ratio_max=line_unanchored_ratio_max,
                )
                if cohort == "anchored":
                    anchored_lines.append(line)
                elif cohort == "unanchored":
                    unanchored_lines.append(line)
                else:
                    ambiguous_lines.append(line)

            if matched_sampling:
                matched_n = min(
                    len(anchored_lines),
                    len(unanchored_lines),
                    max_lines_per_cohort,
                )
                sampled_anchored = _sample_lines(
                    anchored_lines,
                    limit=matched_n,
                    seed=seed,
                )
                sampled_unanchored = _sample_lines(
                    unanchored_lines,
                    limit=matched_n,
                    seed=seed + 1,
                )
            else:
                sampled_anchored = _sample_lines(
                    anchored_lines,
                    limit=max_lines_per_cohort,
                    seed=seed,
                )
                sampled_unanchored = _sample_lines(
                    unanchored_lines,
                    limit=max_lines_per_cohort,
                    seed=seed + 1,
                )

            anchored_line_tokens = _line_payload(sampled_anchored)
            unanchored_line_tokens = _line_payload(sampled_unanchored)

            anchored_summary = compute_consistency_summary(anchored_line_tokens)
            unanchored_summary = compute_consistency_summary(unanchored_line_tokens)
            delta_mean_consistency = float(
                anchored_summary.get("mean_consistency", 0.0)
            ) - float(unanchored_summary.get("mean_consistency", 0.0))

            adequacy = evaluate_adequacy(
                available_anchor_line_count=len(sampled_anchored),
                available_unanchored_line_count=len(sampled_unanchored),
                anchored_page_count=_unique_page_count(sampled_anchored),
                unanchored_page_count=_unique_page_count(sampled_unanchored),
                anchored_recurring_contexts=int(
                    anchored_summary.get("num_recurring_contexts", 0)
                ),
                unanchored_recurring_contexts=int(
                    unanchored_summary.get("num_recurring_contexts", 0)
                ),
                policy=adequacy_policy,
            )

            if sampled_anchored and sampled_unanchored:
                bootstrap = bootstrap_delta_ci(
                    anchored_line_tokens,
                    unanchored_line_tokens,
                    iterations=bootstrap_iterations,
                    seed=seed,
                )
                p_value = permutation_p_value(
                    anchored_line_tokens,
                    unanchored_line_tokens,
                    iterations=permutation_iterations,
                    seed=seed + 7,
                    observed_delta=delta_mean_consistency,
                )
                delta_ci_low = float(bootstrap.get("delta_ci_low", 0.0))
                delta_ci_high = float(bootstrap.get("delta_ci_high", 0.0))
            else:
                p_value = 1.0
                delta_ci_low = 0.0
                delta_ci_high = 0.0

            inference = evaluate_inference(
                delta_mean_consistency=delta_mean_consistency,
                delta_ci_low=delta_ci_low,
                delta_ci_high=delta_ci_high,
                p_value=p_value,
                policy=inference_policy,
            )
            status_payload = decide_status(adequacy=adequacy, inference=inference)
            current_lane = _resolve_lane(
                matrix_policy=matrix_policy,
                method_name=str(method.name),
                seed=seed,
                max_lines_per_cohort=max_lines_per_cohort,
            )
            lane_outcomes = _collect_lane_outcomes(
                matrix_policy=matrix_policy,
                dataset_id=dataset_id,
                source_id=source_id,
                by_run_dir=OUTPUT_PATH.parent / "by_run",
            )
            lane_id = str(current_lane.get("lane_id", "unregistered-lane"))
            lane_updated = False
            for row in lane_outcomes:
                if str(row.get("lane_id", "")) != lane_id:
                    continue
                row["status"] = str(status_payload["status"])
                row["status_reason"] = str(status_payload["status_reason"])
                row["run_id"] = str(run.run_id)
                row["timestamp"] = _utc_now_iso()
                row["lane_class"] = _lane_class(current_lane)
                lane_updated = True
                break
            if not lane_updated:
                lane_outcomes.append(
                    {
                        "lane_id": lane_id,
                        "purpose": str(current_lane.get("purpose", "")),
                        "lane_class": _lane_class(current_lane),
                        "status": str(status_payload["status"]),
                        "status_reason": str(status_payload["status_reason"]),
                        "run_id": str(run.run_id),
                        "timestamp": _utc_now_iso(),
                    }
                )
            robustness = _build_robustness_summary(
                matrix_policy=matrix_policy,
                lane=current_lane,
                lane_outcomes=lane_outcomes,
                current_status=status_payload["status"],
            )
            h1_4_closure_lane = derive_h1_4_closure_lane(
                status=status_payload["status"],
                robustness_class=str(robustness.get("robustness_class", "")),
            )
            if h1_4_closure_lane == H1_4_LANE_ALIGNED:
                h1_4_residual_reason = "robust_multilane_alignment"
            elif h1_4_closure_lane == H1_4_LANE_QUALIFIED:
                h1_4_residual_reason = "registered_lane_fragility"
            elif h1_4_closure_lane == H1_4_LANE_INCONCLUSIVE:
                h1_4_residual_reason = "non_conclusive_multimodal_status"
            elif h1_4_closure_lane == H1_4_LANE_BLOCKED:
                h1_4_residual_reason = "cohort_geometry_or_contract_block"
            else:
                h1_4_residual_reason = "h1_4_lane_unclassified"

            h1_5_closure_lane = derive_h1_5_closure_lane(
                status=status_payload["status"],
                entitlement_robustness_class=str(
                    robustness.get("entitlement_robustness_class", "")
                ),
                diagnostic_lane_count=int(
                    robustness.get("observed_diagnostic_lane_count", 0)
                )
                + int(robustness.get("observed_stress_lane_count", 0)),
                diagnostic_non_conclusive_count=int(
                    robustness.get("diagnostic_non_conclusive_lane_count", 0)
                ),
                robust_closure_reachable=bool(
                    robustness.get("robust_closure_reachable", False)
                ),
            )
            if h1_5_closure_lane == H1_5_LANE_ALIGNED:
                h1_5_residual_reason = "entitlement_lanes_robustly_aligned"
            elif h1_5_closure_lane == H1_5_LANE_BOUNDED:
                h1_5_residual_reason = "diagnostic_lane_non_conclusive_bounded"
            elif h1_5_closure_lane == H1_5_LANE_QUALIFIED:
                h1_5_residual_reason = "entitlement_lane_fragility"
            elif h1_5_closure_lane == H1_5_LANE_BLOCKED:
                if not bool(robustness.get("robust_closure_reachable", False)):
                    h1_5_residual_reason = "entitlement_contract_unreachable"
                else:
                    h1_5_residual_reason = "cohort_geometry_or_contract_block"
            elif h1_5_closure_lane == H1_5_LANE_INCONCLUSIVE:
                h1_5_residual_reason = "non_conclusive_multimodal_status"
            else:
                h1_5_residual_reason = "h1_5_lane_unclassified"

            results = {
                "generated_at": _utc_now_iso(),
                "status": status_payload["status"],
                "status_reason": status_payload["status_reason"],
                "allowed_claim": status_payload["allowed_claim"],
                "h1_4_closure_lane": h1_4_closure_lane,
                "h1_4_residual_reason": h1_4_residual_reason,
                "h1_4_reopen_conditions": robustness.get("reopen_conditions", []),
                "h1_5_closure_lane": h1_5_closure_lane,
                "h1_5_residual_reason": h1_5_residual_reason,
                "h1_5_reopen_conditions": robustness.get("h1_5_reopen_conditions", []),
                "dataset_id": dataset_id,
                "transcription_source_id": source_id,
                "anchor_method": {
                    "id": method.id,
                    "name": method.name,
                    "parameters": method.parameters or {},
                },
                "policy": {
                    "selection": {
                        "anchor_relation_types": relation_types,
                        "near_score_min": near_score_min,
                        "line_anchor_ratio_min": line_anchor_ratio_min,
                        "line_unanchored_ratio_max": line_unanchored_ratio_max,
                    },
                    "sampling": {
                        "matched_sampling": matched_sampling,
                        "max_lines_per_cohort": max_lines_per_cohort,
                        "seed": seed,
                    },
                    "adequacy": adequacy_policy,
                    "inference": {
                        **inference_policy,
                        "bootstrap_iterations": bootstrap_iterations,
                        "permutation_iterations": permutation_iterations,
                    },
                    "robustness_matrix": matrix_policy,
                },
                "cohorts": {
                    "available": {
                        "anchored_line_count": len(anchored_lines),
                        "unanchored_line_count": len(unanchored_lines),
                        "ambiguous_line_count": len(ambiguous_lines),
                    },
                    "sampled": {
                        "anchored": {
                            **anchored_summary,
                            "page_count": _unique_page_count(sampled_anchored),
                        },
                        "unanchored": {
                            **unanchored_summary,
                            "page_count": _unique_page_count(sampled_unanchored),
                        },
                    },
                },
                "effect": {
                    "delta_mean_consistency": delta_mean_consistency,
                    "delta_ci_low": delta_ci_low,
                    "delta_ci_high": delta_ci_high,
                    "p_value": float(p_value),
                },
                "adequacy": adequacy,
                "inference": inference,
                "robustness": robustness,
                "diagnostics": {
                    "anchor_relation_type_counts": dict(sorted(relation_counts.items())),
                    "anchored_word_count": len(anchors_by_word),
                    "token_count_total": len(token_rows),
                    "token_alignment_count": len(token_to_word),
                },
            }

            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            ProvenanceWriter.save_results(results, OUTPUT_PATH)

            LEGACY_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            legacy_payload = {
                "anchored": anchored_summary,
                "unanchored": unanchored_summary,
                "status": results["status"],
                "status_reason": results["status_reason"],
                "delta_mean_consistency": delta_mean_consistency,
                "p_value": float(p_value),
                "delta_ci_low": delta_ci_low,
                "delta_ci_high": delta_ci_high,
            }
            with open(LEGACY_OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(legacy_payload, f, indent=2, sort_keys=True)

            table = Table(title="Phase 5I Confirmatory Anchor Coupling")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")
            table.add_row("Status", results["status"])
            table.add_row("Reason", results["status_reason"])
            table.add_row("H1.4 Closure Lane", results["h1_4_closure_lane"])
            table.add_row("H1.5 Closure Lane", results["h1_5_closure_lane"])
            table.add_row(
                "Robustness Class",
                str((results.get("robustness") or {}).get("robustness_class", "unknown")),
            )
            table.add_row(
                "Entitlement Robustness",
                str(
                    (results.get("robustness") or {}).get(
                        "entitlement_robustness_class", "unknown"
                    )
                ),
            )
            table.add_row(
                "Lane",
                str((results.get("robustness") or {}).get("lane_id", "unknown")),
            )
            table.add_row(
                "Robust Closure Reachable",
                str((results.get("robustness") or {}).get("robust_closure_reachable")),
            )
            table.add_row(
                "Sampled lines (A/U)",
                f"{len(sampled_anchored)}/{len(sampled_unanchored)}",
            )
            table.add_row(
                "Recurring contexts (A/U)",
                f"{anchored_summary.get('num_recurring_contexts', 0)}/"
                f"{unanchored_summary.get('num_recurring_contexts', 0)}",
            )
            table.add_row(
                "Mean consistency (A/U)",
                f"{anchored_summary.get('mean_consistency', 0.0):.4f}/"
                f"{unanchored_summary.get('mean_consistency', 0.0):.4f}",
            )
            table.add_row("Delta", f"{delta_mean_consistency:.4f}")
            table.add_row("95% CI", f"[{delta_ci_low:.4f}, {delta_ci_high:.4f}]")
            table.add_row("Permutation p-value", f"{float(p_value):.4f}")
            table.add_row("Adequacy pass", str(bool(adequacy.get("pass"))))
            console.print(table)

            console.print(
                f"[green]{_utc_now_iso()}[/green] wrote {OUTPUT_PATH} and "
                f"{LEGACY_OUTPUT_PATH}"
            )
            store.save_run(run)
            return results
        finally:
            session.close()


def main() -> None:
    args = _parse_args()
    run_anchor_coupling(
        db_url=args.db_url,
        dataset_id_override=args.dataset_id,
        source_id_override=args.source_id,
        method_id=args.method_id,
        method_name_override=args.method_name,
        policy_path=Path(args.policy_path),
        bootstrap_iterations_override=args.bootstrap_iterations,
        permutation_iterations_override=args.permutation_iterations,
        seed_override=args.seed,
        max_lines_override=args.max_lines_per_cohort,
    )


if __name__ == "__main__":
    main()
