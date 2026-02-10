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
    bootstrap_delta_ci,
    classify_line_cohort,
    compute_consistency_summary,
    decide_status,
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

            results = {
                "generated_at": _utc_now_iso(),
                "status": status_payload["status"],
                "status_reason": status_payload["status_reason"],
                "allowed_claim": status_payload["allowed_claim"],
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
