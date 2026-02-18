#!/usr/bin/env python3
"""
Download multilingual corpora for Phase 10 Method I coverage expansion.

Sources are machine-extracted from Wikipedia plaintext API endpoints, with
resume checkpoints written after each language so interrupted runs can restart
without losing completed work.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

WORD_PATTERN = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)?", flags=re.UNICODE)
TYPOLOGY_MAP: dict[str, str] = {
    "latin": "fusional",
    "english": "fusional",
    "german": "fusional",
    "russian": "fusional",
    "greek": "fusional",
    "turkish": "agglutinative",
    "finnish": "agglutinative",
    "hungarian": "agglutinative",
    "nahuatl": "agglutinative",
    "mandarin": "isolating",
    "vietnamese": "isolating",
    "arabic": "abjad",
    "hebrew": "abjad",
    "japanese": "syllabic",
    "cherokee": "syllabic",
}
_CJK_BLOCKS: tuple[tuple[int, int], ...] = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0x3040, 0x309F),
    (0x30A0, 0x30FF),
    (0x31F0, 0x31FF),
    (0xAC00, 0xD7AF),
)


@dataclass(frozen=True)
class LanguageSpec:
    language_id: str
    wikipedia_code: str
    display_name: str

    @property
    def typology(self) -> str:
        return TYPOLOGY_MAP.get(self.language_id, "unknown")


LANGUAGES: tuple[LanguageSpec, ...] = (
    LanguageSpec("english", "en", "English"),
    LanguageSpec("german", "de", "German"),
    LanguageSpec("latin", "la", "Latin"),
    LanguageSpec("russian", "ru", "Russian"),
    LanguageSpec("greek", "el", "Greek"),
    LanguageSpec("turkish", "tr", "Turkish"),
    LanguageSpec("finnish", "fi", "Finnish"),
    LanguageSpec("hungarian", "hu", "Hungarian"),
    LanguageSpec("vietnamese", "vi", "Vietnamese"),
    LanguageSpec("mandarin", "zh", "Mandarin Chinese"),
    LanguageSpec("arabic", "ar", "Arabic"),
    LanguageSpec("hebrew", "he", "Hebrew"),
    LanguageSpec("japanese", "ja", "Japanese"),
)


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _log(console: Console, message: str) -> None:
    stamp = now_utc_iso().replace("T", " ").split(".")[0]
    console.print(f"[dim]{stamp}[/dim] {message}")


def _is_cjk_or_kana(char: str) -> bool:
    code = ord(char)
    return any(start <= code <= end for start, end in _CJK_BLOCKS)


def _tokenize_line_multiscript(raw: str) -> list[str]:
    tokens = WORD_PATTERN.findall(raw.lower())
    if not tokens:
        return []

    expanded: list[str] = []
    for token in tokens:
        if any(_is_cjk_or_kana(char) for char in token):
            expanded.extend(char for char in token if _is_cjk_or_kana(char))
        else:
            expanded.append(token)
    return expanded


def _tokenize_text_to_lines(text: str) -> list[list[str]]:
    lines: list[list[str]] = []
    for raw in text.splitlines():
        tokens = _tokenize_line_multiscript(raw)
        if tokens:
            lines.append(tokens)
    if lines:
        return lines
    tokens = _tokenize_line_multiscript(text)
    if not tokens:
        return []
    return [tokens[i : i + 12] for i in range(0, len(tokens), 12)]


def _flatten_lines(lines: list[list[str]]) -> list[str]:
    return [token for line in lines for token in line]


def _count_tokens(text: str) -> int:
    return len(_flatten_lines(_tokenize_text_to_lines(text)))


def _fetch_extract_batch(
    spec: LanguageSpec,
    batch_size: int,
    timeout_seconds: float,
) -> list[str]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "random",
        "grnnamespace": "0",
        "grnlimit": str(batch_size),
        "prop": "extracts",
        "explaintext": "1",
        "exlimit": "max",
    }
    base = f"https://{spec.wikipedia_code}.wikipedia.org/w/api.php"
    url = f"{base}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "voynich-phase10-corpus-expander/1.0 (+local research automation)",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8", errors="ignore"))

    pages = payload.get("query", {}).get("pages", {})
    extracts: list[str] = []
    if isinstance(pages, dict):
        for page in pages.values():
            if not isinstance(page, dict):
                continue
            extract = str(page.get("extract", "")).strip()
            if extract:
                extracts.append(extract)
    return extracts


def _build_language_text(
    spec: LanguageSpec,
    target_tokens: int,
    batch_size: int,
    max_batches: int,
    min_article_tokens: int,
    timeout_seconds: float,
    sleep_seconds: float,
    max_retries_per_batch: int,
    retry_backoff_seconds: float,
    console: Console,
) -> tuple[str, int, int]:
    chunks: list[str] = []
    token_count = 0
    article_count = 0

    for batch_index in range(1, max_batches + 1):
        extracts: list[str] = []
        for attempt in range(1, max_retries_per_batch + 1):
            try:
                extracts = _fetch_extract_batch(
                    spec=spec,
                    batch_size=batch_size,
                    timeout_seconds=timeout_seconds,
                )
                break
            except (HTTPError, URLError, TimeoutError) as exc:
                _log(
                    console,
                    f"[{spec.language_id}] batch {batch_index} fetch attempt "
                    f"{attempt}/{max_retries_per_batch} failed: {exc}",
                )
                if attempt == max_retries_per_batch:
                    extracts = []
                    break
                time.sleep(retry_backoff_seconds * attempt)

        accepted = 0
        for extract in extracts:
            compact = " ".join(extract.split())
            if not compact:
                continue
            tokens = _count_tokens(compact)
            if tokens < min_article_tokens:
                continue
            chunks.append(compact)
            accepted += 1
            article_count += 1
            token_count += tokens
            if token_count >= target_tokens:
                break

        _log(
            console,
            f"[{spec.language_id}] batch {batch_index}/{max_batches}: "
            f"accepted_articles={accepted}, token_count={token_count}/{target_tokens}",
        )
        if token_count >= target_tokens:
            break
        time.sleep(sleep_seconds)

    return "\n\n".join(chunks), token_count, article_count


def _default_language_status(spec: LanguageSpec) -> dict[str, Any]:
    return {
        "status": "pending",
        "language_id": spec.language_id,
        "display_name": spec.display_name,
        "wikipedia_code": spec.wikipedia_code,
        "typology": spec.typology,
        "token_count": 0,
        "article_count": 0,
        "output_path": None,
        "started_at": None,
        "completed_at": None,
        "error": None,
    }


def _refresh_coverage(status: dict[str, Any], selected_specs: list[LanguageSpec]) -> None:
    selected_ids = {spec.language_id for spec in selected_specs}
    completed_entries = [
        row
        for lang_id, row in status.get("languages", {}).items()
        if lang_id in selected_ids and row.get("status") == "completed"
    ]
    typologies = sorted({str(row.get("typology", "unknown")) for row in completed_entries})
    status["coverage"] = {
        "requested_language_count": len(selected_specs),
        "completed_language_count": len(completed_entries),
        "typology_classes": typologies,
        "typology_class_count": len(typologies),
    }


def _load_status(
    path: Path,
    selected_specs: list[LanguageSpec],
    target_tokens: int,
) -> dict[str, Any]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {
            "status": "pending",
            "started_at": now_utc_iso(),
            "updated_at": now_utc_iso(),
            "target_tokens_per_language": target_tokens,
            "languages": {},
            "coverage": {},
        }

    payload["target_tokens_per_language"] = target_tokens
    languages = payload.setdefault("languages", {})
    for spec in selected_specs:
        languages.setdefault(spec.language_id, _default_language_status(spec))
    _refresh_coverage(payload, selected_specs)
    return payload


def _save_status(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = now_utc_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download multilingual corpora for Method I.")
    parser.add_argument(
        "--output-dir",
        default="data/external_corpora",
        help="Directory where language corpora text files are written.",
    )
    parser.add_argument(
        "--status-path",
        default="results/data/phase10_admissibility/corpus_expansion_status.json",
        help="Checkpoint status file for resumable downloads.",
    )
    parser.add_argument(
        "--target-tokens",
        type=int,
        default=15000,
        help="Target token count per language corpus.",
    )
    parser.add_argument(
        "--min-article-tokens",
        type=int,
        default=80,
        help="Discard fetched article extracts shorter than this many tokens.",
    )
    parser.add_argument(
        "--min-final-tokens",
        type=int,
        default=2500,
        help="Fail a language if final corpus is below this threshold.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Random Wikipedia pages fetched per batch.",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=40,
        help="Maximum number of fetch batches per language.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.15,
        help="Delay between API batches.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="HTTP timeout per API request.",
    )
    parser.add_argument(
        "--max-retries-per-batch",
        type=int,
        default=5,
        help="Max fetch retries for each batch before skipping it.",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=1.0,
        help="Base backoff seconds between failed fetch retries.",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default=",".join(spec.language_id for spec in LANGUAGES),
        help="Comma-separated list of language IDs to process.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download languages even if status says completed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()
    selected_ids = [part.strip().lower() for part in args.languages.split(",") if part.strip()]
    selected_specs = [spec for spec in LANGUAGES if spec.language_id in selected_ids]
    missing_ids = sorted(set(selected_ids) - {spec.language_id for spec in selected_specs})
    if missing_ids:
        raise SystemExit(f"Unsupported language IDs requested: {', '.join(missing_ids)}")
    if not selected_specs:
        raise SystemExit("No languages selected.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    status_path = Path(args.status_path)
    status = _load_status(
        path=status_path,
        selected_specs=selected_specs,
        target_tokens=args.target_tokens,
    )

    console.print(
        Panel.fit(
            "[bold blue]Phase 10 Method I Corpus Expansion[/bold blue]\n"
            "Machine-extracted multilingual corpora from Wikipedia plaintext endpoints",
            border_style="blue",
        )
    )
    _log(
        console,
        "Config: "
        f"languages={selected_ids}, target_tokens={args.target_tokens}, "
        f"min_article_tokens={args.min_article_tokens}, min_final_tokens={args.min_final_tokens}, "
        f"batch_size={args.batch_size}, max_batches={args.max_batches}, "
        f"max_retries_per_batch={args.max_retries_per_batch}, force={args.force}",
    )

    status["status"] = "in_progress"
    _save_status(status_path, status)

    for spec in selected_specs:
        lang_status = status["languages"].setdefault(
            spec.language_id,
            _default_language_status(spec),
        )
        output_path = output_dir / f"{spec.language_id}.txt"

        if (
            not args.force
            and lang_status.get("status") == "completed"
            and output_path.exists()
            and int(lang_status.get("token_count", 0)) >= args.target_tokens
        ):
            _log(
                console,
                f"[{spec.language_id}] reused from checkpoint "
                f"({lang_status['token_count']} tokens)",
            )
            continue

        lang_status.update(
            {
                "status": "running",
                "started_at": now_utc_iso(),
                "completed_at": None,
                "error": None,
                "output_path": str(output_path),
            }
        )
        _refresh_coverage(status, selected_specs)
        _save_status(status_path, status)
        _log(console, f"[{spec.language_id}] download start (wiki={spec.wikipedia_code})")

        try:
            text, token_count, article_count = _build_language_text(
                spec=spec,
                target_tokens=args.target_tokens,
                batch_size=args.batch_size,
                max_batches=args.max_batches,
                min_article_tokens=args.min_article_tokens,
                timeout_seconds=args.timeout_seconds,
                sleep_seconds=args.sleep_seconds,
                max_retries_per_batch=args.max_retries_per_batch,
                retry_backoff_seconds=args.retry_backoff_seconds,
                console=console,
            )
            if token_count < args.min_final_tokens:
                raise RuntimeError(
                    f"Token count below threshold: {token_count} < {args.min_final_tokens}"
                )

            output_path.write_text(text, encoding="utf-8")
            lang_status.update(
                {
                    "status": "completed",
                    "token_count": int(token_count),
                    "article_count": int(article_count),
                    "completed_at": now_utc_iso(),
                    "error": None,
                    "output_path": str(output_path),
                }
            )
            _log(
                console,
                f"[{spec.language_id}] complete: tokens={token_count}, "
                f"articles={article_count}, path={output_path}",
            )
        except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError) as exc:
            lang_status.update(
                {
                    "status": "failed",
                    "completed_at": now_utc_iso(),
                    "error": str(exc),
                    "output_path": str(output_path),
                }
            )
            _log(console, f"[{spec.language_id}] failed: {exc}")

        _refresh_coverage(status, selected_specs)
        _save_status(status_path, status)

    _refresh_coverage(status, selected_specs)
    completed = int(status["coverage"]["completed_language_count"])
    requested = int(status["coverage"]["requested_language_count"])
    status["status"] = "completed" if completed == requested else "partial"
    status["completed_at"] = now_utc_iso()
    _save_status(status_path, status)

    table = Table(title="Method I Corpus Expansion Summary")
    table.add_column("Language", style="cyan")
    table.add_column("Status")
    table.add_column("Tokens", justify="right")
    table.add_column("Typology")
    for spec in selected_specs:
        row = status["languages"][spec.language_id]
        table.add_row(
            spec.language_id,
            str(row.get("status")),
            str(row.get("token_count", 0)),
            str(row.get("typology", "unknown")),
        )
    console.print(table)
    console.print(f"[green]Status checkpoint:[/green] {status_path}")
    console.print(f"[green]Output directory:[/green] {output_dir}")
    _log(
        console,
        "Coverage: "
        f"completed_languages={status['coverage']['completed_language_count']}/"
        f"{status['coverage']['requested_language_count']}, "
        f"typology_classes={status['coverage']['typology_class_count']} "
        f"({status['coverage']['typology_classes']})",
    )


if __name__ == "__main__":
    main()
