#!/usr/bin/env python3
"""
Audit anchored/unanchored cohort coverage before confirmatory coupling phase2_analysis.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Set

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rich.console import Console
from rich.table import Table
from sqlalchemy import and_

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import (
    AnchorMethodRecord,
    AnchorRecord,
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
)
from phase5_mechanism.anchor_coupling import DEFAULT_MULTIMODAL_POLICY

console = Console()
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_h1_multimodal_policy.json"
OUTPUT_PATH = PROJECT_ROOT / "core_status/phase5_mechanism/anchor_coverage_audit.json"


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


def _resolve_anchor_method(session, method_id: str | None, method_name: str | None) -> AnchorMethodRecord:
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit anchor coverage for SK-H1.")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    parser.add_argument("--dataset-id", default=None)
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--method-id", default=None)
    parser.add_argument("--method-name", default=None)
    parser.add_argument("--policy-path", default=str(DEFAULT_POLICY_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    policy = _load_policy(Path(args.policy_path))
    dataset_id = args.dataset_id or str(policy.get("dataset_id", "voynich_real"))
    source_id = args.source_id or str(policy.get("transcription_source_id", "zandbergen_landini"))
    method_name = args.method_name or str(policy.get("anchor_method_name", "geometric_v1"))

    with active_run(
        config={
            "command": "audit_anchor_coverage",
            "dataset_id": dataset_id,
            "source_id": source_id,
            "method_id": args.method_id,
            "method_name": method_name,
            "policy_path": str(args.policy_path),
        }
    ) as run:
        store = MetadataStore(args.db_url)
        session = store.Session()
        try:
            method = _resolve_anchor_method(session, args.method_id, method_name)

            token_rows = (
                session.query(
                    TranscriptionTokenRecord.id,
                    TranscriptionLineRecord.id,
                    PageRecord.id,
                )
                .join(
                    TranscriptionLineRecord,
                    TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
                )
                .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .filter(TranscriptionLineRecord.source_id == source_id)
                .all()
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
            token_to_word = {}
            for token_id, word_id in align_rows:
                key = str(token_id)
                if key not in token_to_word:
                    token_to_word[key] = str(word_id)

            anchor_rows = (
                session.query(AnchorRecord.source_id, AnchorRecord.relation_type)
                .join(PageRecord, AnchorRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .filter(AnchorRecord.method_id == method.id)
                .filter(AnchorRecord.source_type == "word")
                .all()
            )
            anchored_words: Set[str] = set()
            relation_type_counts: Counter[str] = Counter()
            for source_id_row, relation_type in anchor_rows:
                anchored_words.add(str(source_id_row))
                relation_type_counts[str(relation_type)] += 1

            token_count_total = len(token_rows)
            line_ids_total = {str(line_id) for _tok, line_id, _page in token_rows}
            page_ids_total = {str(page_id) for _tok, _line, page_id in token_rows}

            anchored_token_count = 0
            unanchored_token_count = 0
            anchored_line_ids: Set[str] = set()
            unanchored_line_ids: Set[str] = set()
            anchored_page_ids: Set[str] = set()
            unanchored_page_ids: Set[str] = set()

            for token_id, line_id, page_id in token_rows:
                word_id = token_to_word.get(str(token_id))
                anchored = bool(word_id and word_id in anchored_words)
                if anchored:
                    anchored_token_count += 1
                    anchored_line_ids.add(str(line_id))
                    anchored_page_ids.add(str(page_id))
                else:
                    unanchored_token_count += 1
                    unanchored_line_ids.add(str(line_id))
                    unanchored_page_ids.add(str(page_id))

            token_anchor_ratio = (
                anchored_token_count / token_count_total if token_count_total > 0 else 0.0
            )
            token_balance_ratio = (
                min(anchored_token_count, unanchored_token_count)
                / max(anchored_token_count, unanchored_token_count)
                if max(anchored_token_count, unanchored_token_count) > 0
                else 0.0
            )

            results = {
                "generated_at": _utc_now_iso(),
                "dataset_id": dataset_id,
                "transcription_source_id": source_id,
                "anchor_method": {
                    "id": method.id,
                    "name": method.name,
                    "parameters": method.parameters or {},
                },
                "counts": {
                    "tokens_total": token_count_total,
                    "lines_total": len(line_ids_total),
                    "pages_total": len(page_ids_total),
                    "tokens_anchored": anchored_token_count,
                    "tokens_unanchored": unanchored_token_count,
                    "lines_with_anchored_tokens": len(anchored_line_ids),
                    "lines_with_unanchored_tokens": len(unanchored_line_ids),
                    "pages_with_anchored_tokens": len(anchored_page_ids),
                    "pages_with_unanchored_tokens": len(unanchored_page_ids),
                    "anchored_words": len(anchored_words),
                },
                "ratios": {
                    "token_anchor_ratio": token_anchor_ratio,
                    "token_balance_ratio": token_balance_ratio,
                },
                "relation_type_counts": dict(sorted(relation_type_counts.items())),
            }

            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            ProvenanceWriter.save_results(results, OUTPUT_PATH)

            table = Table(title="Anchor Coverage Audit")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")
            table.add_row("Method", f"{method.name} ({method.id})")
            table.add_row("Tokens total", str(token_count_total))
            table.add_row("Anchored tokens", str(anchored_token_count))
            table.add_row("Unanchored tokens", str(unanchored_token_count))
            table.add_row("Token anchor ratio", f"{token_anchor_ratio:.4f}")
            table.add_row("Token balance ratio", f"{token_balance_ratio:.4f}")
            table.add_row("Lines total", str(len(line_ids_total)))
            table.add_row("Pages total", str(len(page_ids_total)))
            console.print(table)
            console.print(f"[green]{_utc_now_iso()}[/green] wrote {OUTPUT_PATH}")

            store.save_run(run)
        finally:
            session.close()


if __name__ == "__main__":
    main()
