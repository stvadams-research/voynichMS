#!/usr/bin/env python3
"""
Repair stale run statuses in metadata DB using run manifests under runs/<run_id>/run.json.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from foundation.storage.metadata import MetadataStore, RunRecord  # noqa: E402


def _parse_iso_timestamp(value: str):
    if not value:
        return None
    try:
        # Handles both `...+00:00` and `...Z`.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_summary(
    *,
    scanned: int,
    updated: int,
    reconciled: int,
    orphaned: int,
    backfilled_manifests: int,
    would_update: int,
    would_reconciled: int,
    would_orphaned: int,
    would_backfilled_manifests: int,
    missing_manifest_ids: list[str],
    report_path: str | None,
    dry_run: bool,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "scanned": scanned,
        "updated": updated,
        "reconciled": reconciled,
        "orphaned": orphaned,
        "backfilled_manifests": backfilled_manifests,
        "would_update": would_update,
        "would_reconciled": would_reconciled,
        "would_orphaned": would_orphaned,
        "would_backfilled_manifests": would_backfilled_manifests,
        "missing_manifests": len(missing_manifest_ids),
        "dry_run": dry_run,
    }
    if report_path:
        payload = {
            **summary,
            "missing_manifest_ids_sample": missing_manifest_ids[:50],
            "report_generated_utc": datetime.utcnow().isoformat() + "Z",
        }
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return summary


def _iso_or_none(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _build_backfilled_manifest(record: RunRecord, *, fallback_status: str) -> Dict[str, Any]:
    end_ts = record.timestamp_end or record.timestamp_start
    status = record.status if record.status else fallback_status
    if status == "running":
        status = fallback_status

    return {
        "run_id": str(record.id),
        "status": status,
        "timestamp_start": _iso_or_none(record.timestamp_start),
        "timestamp_end": _iso_or_none(end_ts),
        "git_commit": record.git_commit,
        "git_dirty": bool(record.git_dirty),
        "command_line": _jsonable(record.command_line),
        "config": _jsonable(record.config),
        "manifest_backfilled": True,
        "backfill_generated_utc": datetime.utcnow().isoformat() + "Z",
        "backfill_source": "scripts/audit/repair_run_statuses.py",
    }


def repair_run_statuses(
    db_url: str,
    orphan_status: str = "orphaned",
    report_path: str | None = None,
    backfill_missing_manifests: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    store = MetadataStore(db_url)
    session = store.Session()
    scanned = 0
    updated = 0
    reconciled = 0
    orphaned = 0
    backfilled_manifests = 0
    would_update = 0
    would_reconciled = 0
    would_orphaned = 0
    would_backfilled_manifests = 0
    missing_manifest_ids: list[str] = []
    try:
        if backfill_missing_manifests:
            candidates = session.query(RunRecord).all()
        else:
            candidates = (
                session.query(RunRecord)
                .filter((RunRecord.status == "running") | (RunRecord.timestamp_end.is_(None)))
                .all()
            )
        scanned = len(candidates)

        for record in candidates:
            is_stale = record.status == "running" or record.timestamp_end is None
            run_json = Path("runs") / str(record.id) / "run.json"
            if not run_json.exists():
                missing_manifest_ids.append(str(record.id))

                if backfill_missing_manifests:
                    manifest = _build_backfilled_manifest(
                        record,
                        fallback_status=orphan_status,
                    )
                    if dry_run:
                        would_backfilled_manifests += 1
                    else:
                        run_json.parent.mkdir(parents=True, exist_ok=True)
                        run_json.write_text(
                            json.dumps(manifest, indent=2),
                            encoding="utf-8",
                        )
                        backfilled_manifests += 1

                changed = False
                if is_stale and orphan_status:
                    if dry_run:
                        if record.status != orphan_status or (
                            record.timestamp_end is None and record.timestamp_start is not None
                        ):
                            changed = True
                    else:
                        if record.status != orphan_status:
                            record.status = orphan_status
                            changed = True
                        if record.timestamp_end is None and record.timestamp_start is not None:
                            record.timestamp_end = record.timestamp_start
                            changed = True
                    if changed:
                        if dry_run:
                            would_update += 1
                            would_orphaned += 1
                        else:
                            updated += 1
                            orphaned += 1
                    elif dry_run:
                        would_orphaned += 1
                    else:
                        orphaned += 1
                continue

            if not is_stale:
                continue

            payload = json.loads(run_json.read_text(encoding="utf-8"))
            final_status = payload.get("status")
            final_end = _parse_iso_timestamp(payload.get("timestamp_end"))
            if final_status is None and final_end is None:
                continue

            changed = False
            if final_status and record.status != final_status:
                record.status = final_status
                changed = True
            if final_end and record.timestamp_end != final_end:
                record.timestamp_end = final_end
                changed = True

            if changed:
                if dry_run:
                    would_update += 1
                    would_reconciled += 1
                else:
                    updated += 1
                    reconciled += 1

        if dry_run:
            session.rollback()
        else:
            session.commit()
    finally:
        session.close()
    return _build_summary(
        scanned=scanned,
        updated=updated,
        reconciled=reconciled,
        orphaned=orphaned,
        backfilled_manifests=backfilled_manifests,
        would_update=would_update,
        would_reconciled=would_reconciled,
        would_orphaned=would_orphaned,
        would_backfilled_manifests=would_backfilled_manifests,
        missing_manifest_ids=missing_manifest_ids,
        report_path=report_path,
        dry_run=dry_run,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair stale run statuses in metadata DB.")
    parser.add_argument(
        "--db-url",
        default="sqlite:///data/voynich.db",
        help="SQLAlchemy DB URL (default: sqlite:///data/voynich.db)",
    )
    parser.add_argument(
        "--orphan-status",
        default="orphaned",
        help="Status to assign stale rows that have no runs/<id>/run.json manifest.",
    )
    parser.add_argument(
        "--report-path",
        default="status/audit/run_status_repair_report.json",
        help="Write reconciliation summary JSON to this path.",
    )
    parser.add_argument(
        "--backfill-missing-manifests",
        action="store_true",
        help=(
            "Create runs/<id>/run.json for rows missing manifests. "
            "Backfilled manifests are marked with manifest_backfilled=true."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate repair actions and write summary report without mutating DB/manifests.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    summary = repair_run_statuses(
        args.db_url,
        orphan_status=args.orphan_status,
        report_path=args.report_path,
        backfill_missing_manifests=args.backfill_missing_manifests,
        dry_run=args.dry_run,
    )
    print(
        "scanned={scanned} updated={updated} reconciled={reconciled} "
        "orphaned={orphaned} backfilled_manifests={backfilled_manifests} "
        "missing_manifests={missing_manifests} dry_run={dry_run} "
        "would_update={would_update}".format(**summary)
    )
