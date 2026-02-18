#!/usr/bin/env python3
# ruff: noqa: E402
"""
Section-holdout robustness check for line-reset persistence controls.

For each held-out section:
1) Fit Markov / Backoff / Persistence on all other sections.
2) Generate matched-length synthetic streams.
3) Compare to held-out real section using order constraints, discrimination, NCD.
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase4_inference.projection_diagnostics.discrimination import (
    DiscriminationCheckAnalyzer,
    DiscriminationCheckConfig,
)
from phase4_inference.projection_diagnostics.line_reset_backoff import (
    LineResetBackoffConfig,
    LineResetBackoffGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_markov import (
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_persistence import (
    LineResetPersistenceConfig,
    LineResetPersistenceGenerator,
)
from phase4_inference.projection_diagnostics.ncd import NCDAnalyzer, NCDConfig
from phase4_inference.projection_diagnostics.order_constraints import (
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
FOLIO_PATTERN = re.compile(r"^f(\d+)([rv])(\d*)$")

# Mirrors scripts/phase5_mechanism/categorize_sections.py
SECTION_RANGES = {
    "herbal": (1, 66),
    "astronomical": (67, 73),
    "biological": (75, 84),
    "cosmological": (85, 86),
    "pharmaceutical": (87, 102),
    "stars": (103, 116),
}

MODEL_IDS = [
    "line_reset_markov_trainfit",
    "line_reset_backoff_trainfit",
    "line_reset_persistence_trainfit",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run section-holdout robustness check for boundary persistence."
    )
    parser.add_argument(
        "--sections",
        type=str,
        default="herbal,astronomical,biological,cosmological,pharmaceutical,stars",
        help="Comma-separated section names to hold out.",
    )
    parser.add_argument("--min-holdout-folios", type=int, default=4)
    parser.add_argument("--random-state", type=int, default=42)

    parser.add_argument("--backoff-trigram-use", type=float, default=0.55)
    parser.add_argument("--backoff-unigram-noise", type=float, default=0.03)
    parser.add_argument("--persistence-rho", type=float, default=0.50)
    parser.add_argument("--persistence-trigram-use", type=float, default=0.65)
    parser.add_argument("--persistence-unigram-noise", type=float, default=0.01)
    parser.add_argument(
        "--persistence-section-overrides",
        type=str,
        default="",
        help=(
            "Optional per-section persistence params, format: "
            "section:rho:trigram_use:noise;section:rho:trigram_use:noise"
        ),
    )

    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--disc-windows-per-dataset", type=int, default=160)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=30)
    parser.add_argument("--ncd-token-limit", type=int, default=80000)
    parser.add_argument("--ncd-bootstraps", type=int, default=20)
    parser.add_argument("--ncd-block-size", type=int, default=512)

    parser.add_argument(
        "--output-name",
        type=str,
        default="boundary_persistence_section_holdout_check.json",
    )
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    section_list = _parse_sections(args.sections)
    section_overrides = _parse_persistence_section_overrides(args.persistence_section_overrides)
    console.print(
        Panel.fit(
            "[bold blue]Boundary Persistence Section-Holdout Check[/bold blue]\n"
            f"sections={section_list} | seed={args.random_state}",
            border_style="blue",
        )
    )

    with active_run(
        config={"command": "run_boundary_persistence_section_holdout_check_phase4"}
    ) as run:
        store = MetadataStore(DB_PATH)
        lines_by_folio = _load_voynich_lines_by_folio(store)
        all_folios = sorted(lines_by_folio.keys(), key=_folio_sort_key)

        by_section: dict[str, list[str]] = defaultdict(list)
        for folio in all_folios:
            section = _get_section(folio)
            if section in section_list:
                by_section[section].append(folio)

        section_results: dict[str, dict[str, Any]] = {}
        skipped: dict[str, str] = {}
        for i, section in enumerate(section_list):
            holdout_folios = sorted(by_section.get(section, []), key=_folio_sort_key)
            if len(holdout_folios) < args.min_holdout_folios:
                skipped[section] = (
                    f"insufficient_holdout_folios:{len(holdout_folios)}"
                    f"<{args.min_holdout_folios}"
                )
                continue

            train_folios = [f for f in all_folios if f not in set(holdout_folios)]
            if not train_folios:
                skipped[section] = "empty_train_split"
                continue

            eval_seed = int(args.random_state + i)
            result = _evaluate_single_section(
                section=section,
                train_folios=train_folios,
                holdout_folios=holdout_folios,
                lines_by_folio=lines_by_folio,
                args=args,
                section_overrides=section_overrides,
                random_state=eval_seed,
            )
            section_results[section] = result
            holdout_tokens = result["split"]["holdout_token_count"]
            console.print(f"Completed section={section} | holdout_tokens={holdout_tokens}")

        if not section_results:
            raise RuntimeError(f"No evaluable sections. skipped={skipped}")

        summary = _summarize_across_sections(section_results)

        _print_section_winner_table(section_results)
        _print_aggregate_table(summary)

        results = {
            "status": "ok",
            "config": {
                "sections": section_list,
                "min_holdout_folios": int(args.min_holdout_folios),
                "random_state": int(args.random_state),
            },
            "generator_params": {
                "markov": {"random_state": args.random_state},
                "backoff": {
                    "random_state": args.random_state,
                    "trigram_use_prob": args.backoff_trigram_use,
                    "unigram_noise_prob": args.backoff_unigram_noise,
                },
                "persistence": {
                    "random_state": args.random_state,
                    "trigram_use_prob": args.persistence_trigram_use,
                    "unigram_noise_prob": args.persistence_unigram_noise,
                    "boundary_persistence_rho": args.persistence_rho,
                },
            },
            "persistence_section_overrides": section_overrides,
            "section_results": section_results,
            "summary": summary,
            "skipped_sections": skipped,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


def _evaluate_single_section(
    section: str,
    train_folios: list[str],
    holdout_folios: list[str],
    lines_by_folio: dict[str, list[list[str]]],
    args: argparse.Namespace,
    section_overrides: dict[str, dict[str, float]],
    random_state: int,
) -> dict[str, Any]:
    train_lines = _collect_lines(lines_by_folio, train_folios)
    holdout_lines = _collect_lines(lines_by_folio, holdout_folios)
    holdout_tokens = [t for line in holdout_lines for t in line]
    holdout_token_count = len(holdout_tokens)
    if not train_lines or not holdout_tokens:
        raise RuntimeError(
            f"invalid split for section={section}: "
            f"train_lines={len(train_lines)} holdout_tokens={len(holdout_tokens)}"
        )

    dataset_tokens: dict[str, list[str]] = {"voynich_holdout": holdout_tokens}

    markov = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=random_state))
    markov.fit(train_lines)
    dataset_tokens["line_reset_markov_trainfit"] = markov.generate(holdout_token_count)["tokens"]  # type: ignore[index]

    backoff = LineResetBackoffGenerator(
        LineResetBackoffConfig(
            random_state=random_state,
            trigram_use_prob=args.backoff_trigram_use,
            unigram_noise_prob=args.backoff_unigram_noise,
            min_trigram_context_count=2,
        )
    )
    backoff.fit(train_lines)
    dataset_tokens["line_reset_backoff_trainfit"] = backoff.generate(holdout_token_count)["tokens"]  # type: ignore[index]

    persistence = LineResetPersistenceGenerator(
        LineResetPersistenceConfig(
            random_state=random_state,
            trigram_use_prob=_get_persistence_param(
                section_overrides,
                section,
                "trigram_use_prob",
                default=float(args.persistence_trigram_use),
            ),
            unigram_noise_prob=_get_persistence_param(
                section_overrides,
                section,
                "unigram_noise_prob",
                default=float(args.persistence_unigram_noise),
            ),
            min_trigram_context_count=2,
            boundary_persistence_rho=_get_persistence_param(
                section_overrides,
                section,
                "boundary_persistence_rho",
                default=float(args.persistence_rho),
            ),
            boundary_trigram_use_prob=0.7,
        )
    )
    persistence.fit(train_lines)
    dataset_tokens["line_reset_persistence_trainfit"] = persistence.generate(holdout_token_count)[  # type: ignore[index]
        "tokens"
    ]

    disc = DiscriminationCheckAnalyzer(
        DiscriminationCheckConfig(
            window_size=72,
            windows_per_dataset=args.disc_windows_per_dataset,
            max_features=args.disc_max_features,
            ngram_min=args.disc_ngram_min,
            ngram_max=args.disc_ngram_max,
            train_fraction=0.7,
            random_state=random_state,
            voynich_dataset_id="voynich_holdout",
        )
    ).analyze(dataset_tokens)

    order = OrderConstraintAnalyzer(
        OrderConstraintConfig(
            token_limit=args.order_token_limit,
            vocab_limit=args.order_vocab_limit,
            permutations=args.order_permutations,
            random_state=random_state,
        )
    ).analyze(dataset_tokens)

    ncd = NCDAnalyzer(
        NCDConfig(
            token_limit=args.ncd_token_limit,
            bootstraps=args.ncd_bootstraps,
            block_size=args.ncd_block_size,
            random_state=random_state,
            focus_dataset_id="voynich_holdout",
        )
    ).analyze(dataset_tokens)

    order_rows = _compute_order_gap_rows(order)
    order_by_model = {row["dataset_id"]: row for row in order_rows}
    disc_by_model = _extract_disc_distances(disc)
    ncd_by_model = _extract_ncd_summary(ncd)

    winners = {
        "order_l1": min(MODEL_IDS, key=lambda m: order_by_model[m]["order_l1_gap"]),
        "discrimination": min(MODEL_IDS, key=lambda m: disc_by_model[m]),
        "ncd_point": min(MODEL_IDS, key=lambda m: ncd_by_model[m]["point_ncd"]),
        "ncd_prob": max(MODEL_IDS, key=lambda m: ncd_by_model[m]["closest_probability"]),
    }

    return {
        "split": {
            "section": section,
            "train_folios": train_folios,
            "holdout_folios": holdout_folios,
            "train_line_count": len(train_lines),
            "holdout_line_count": len(holdout_lines),
            "holdout_token_count": holdout_token_count,
        },
        "effective_persistence_params": {
            "boundary_persistence_rho": _get_persistence_param(
                section_overrides,
                section,
                "boundary_persistence_rho",
                default=float(args.persistence_rho),
            ),
            "trigram_use_prob": _get_persistence_param(
                section_overrides,
                section,
                "trigram_use_prob",
                default=float(args.persistence_trigram_use),
            ),
            "unigram_noise_prob": _get_persistence_param(
                section_overrides,
                section,
                "unigram_noise_prob",
                default=float(args.persistence_unigram_noise),
            ),
        },
        "metrics": {
            "order_l1_gap": {
                model_id: float(order_by_model[model_id]["order_l1_gap"]) for model_id in MODEL_IDS
            },
            "order_h3_gap": {
                model_id: float(order_by_model[model_id]["h3_gap"]) for model_id in MODEL_IDS
            },
            "discrimination_distance": {
                model_id: float(disc_by_model[model_id]) for model_id in MODEL_IDS
            },
            "ncd_point": {
                model_id: float(ncd_by_model[model_id]["point_ncd"]) for model_id in MODEL_IDS
            },
            "ncd_p_closest": {
                model_id: float(ncd_by_model[model_id]["closest_probability"])
                for model_id in MODEL_IDS
            },
        },
        "winners": winners,
        "order_holdout_gaps_ranked": order_rows,
        "discrimination": disc,
        "ncd": ncd,
    }


def _load_voynich_lines_by_folio(store: MetadataStore) -> dict[str, list[list[str]]]:
    session = store.Session()
    try:
        rows = (
            session.query(
                PageRecord.id,
                TranscriptionTokenRecord.line_id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
                TranscriptionTokenRecord.content,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )
    finally:
        session.close()

    lines_by_folio: dict[str, list[list[str]]] = defaultdict(list)
    current_line_id = None
    current_folio = None
    current_tokens: list[str] = []

    for folio, line_id, _line_index, _token_index, content in rows:
        line_id_s = str(line_id)
        folio_s = str(folio)
        if current_line_id is not None and line_id_s != current_line_id:
            if current_folio is not None and current_tokens:
                lines_by_folio[current_folio].append(current_tokens)
            current_tokens = []
        current_folio = folio_s
        current_line_id = line_id_s
        current_tokens.append(str(content))

    if current_folio is not None and current_tokens:
        lines_by_folio[current_folio].append(current_tokens)
    return dict(lines_by_folio)


def _parse_sections(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.split(","):
        key = part.strip().lower()
        if key:
            out.append(key)
    if not out:
        raise ValueError("No sections provided.")
    for section in out:
        if section not in SECTION_RANGES:
            expected = sorted(SECTION_RANGES)
            raise ValueError(f"Unknown section '{section}'. Expected one of {expected}")
    return out


def _parse_persistence_section_overrides(raw: str) -> dict[str, dict[str, float]]:
    raw = raw.strip()
    if not raw:
        return {}

    overrides: dict[str, dict[str, float]] = {}
    entries = [part.strip() for part in raw.split(";") if part.strip()]
    for entry in entries:
        bits = [b.strip() for b in entry.split(":")]
        if len(bits) != 4:
            raise ValueError(
                f"Invalid override '{entry}'. Expected section:rho:trigram_use:noise"
            )
        section, rho_s, tri_s, noise_s = bits
        if section not in SECTION_RANGES:
            expected = sorted(SECTION_RANGES)
            raise ValueError(f"Unknown section '{section}' in override. Expected one of {expected}")
        overrides[section] = {
            "boundary_persistence_rho": float(rho_s),
            "trigram_use_prob": float(tri_s),
            "unigram_noise_prob": float(noise_s),
        }
    return overrides


def _get_persistence_param(
    section_overrides: dict[str, dict[str, float]],
    section: str,
    key: str,
    default: float,
) -> float:
    row = section_overrides.get(section)
    if row is None:
        return default
    return float(row.get(key, default))


def _get_section(folio_id: str) -> str:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return "unknown"
    folio_num = int(match.group(1))
    for section, (start, end) in SECTION_RANGES.items():
        if start <= folio_num <= end:
            return section
    return "unknown"


def _collect_lines(
    lines_by_folio: dict[str, list[list[str]]], folios: list[str]
) -> list[list[str]]:
    lines: list[list[str]] = []
    for folio in folios:
        lines.extend(lines_by_folio.get(folio, []))
    return lines


def _folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return (10**9, 10**9, 10**9, folio_id)
    folio_num = int(match.group(1))
    side = 0 if match.group(2) == "r" else 1
    suffix = int(match.group(3)) if match.group(3) else 0
    return (folio_num, side, suffix, folio_id)


def _compute_order_gap_rows(order_payload: dict[str, Any]) -> list[dict[str, float | str]]:
    datasets = order_payload["datasets"]
    target_metrics = datasets["voynich_holdout"]["metrics"]
    target_h2 = float(target_metrics["bigram_cond_entropy"]["delta"])
    target_h3 = float(target_metrics["trigram_cond_entropy"]["delta"])
    target_mi2 = float(target_metrics["bigram_mutual_information"]["delta"])

    rows: list[dict[str, float | str]] = []
    for dataset_id, payload in datasets.items():
        if dataset_id == "voynich_holdout":
            continue
        if payload.get("status") != "ok":
            continue
        metrics = payload["metrics"]
        h2 = float(metrics["bigram_cond_entropy"]["delta"])
        h3 = float(metrics["trigram_cond_entropy"]["delta"])
        mi2 = float(metrics["bigram_mutual_information"]["delta"])

        h2_gap = abs(h2 - target_h2)
        h3_gap = abs(h3 - target_h3)
        mi2_gap = abs(mi2 - target_mi2)
        rows.append(
            {
                "dataset_id": dataset_id,
                "h2_gap": h2_gap,
                "h3_gap": h3_gap,
                "mi2_gap": mi2_gap,
                "order_l1_gap": h2_gap + h3_gap + mi2_gap,
            }
        )

    rows.sort(key=lambda row: (row["order_l1_gap"], row["h3_gap"], row["h2_gap"]))
    return rows


def _extract_disc_distances(disc: dict[str, Any]) -> dict[str, float]:
    if disc.get("status") != "ok":
        raise RuntimeError(f"Discrimination analyzer failed: {disc.get('status')}")
    rows = disc["voynich_summary"]["closest_centroids"]
    by_model = {row["dataset_id"]: float(row["cosine_distance"]) for row in rows}
    return {model_id: by_model[model_id] for model_id in MODEL_IDS}


def _extract_ncd_summary(ncd: dict[str, Any]) -> dict[str, dict[str, float]]:
    if ncd.get("status") != "ok":
        raise RuntimeError(f"NCD analyzer failed: {ncd.get('status')}")
    summary = ncd["focus_bootstrap_summary"]
    return {
        model_id: {
            "point_ncd": float(summary[model_id]["point_ncd"]),
            "closest_probability": float(summary[model_id]["closest_probability"]),
        }
        for model_id in MODEL_IDS
    }


def _summarize_across_sections(section_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    accum: dict[str, dict[str, list[float]]] = {
        model_id: {
            "order_l1_gap": [],
            "order_h3_gap": [],
            "discrimination_distance": [],
            "ncd_point": [],
            "ncd_p_closest": [],
        }
        for model_id in MODEL_IDS
    }
    wins = {
        "order_l1": Counter(),
        "discrimination": Counter(),
        "ncd_point": Counter(),
        "ncd_prob": Counter(),
    }

    for _section, payload in section_results.items():
        metrics = payload["metrics"]
        winners = payload["winners"]
        for key in wins:
            wins[key][winners[key]] += 1
        for model_id in MODEL_IDS:
            accum[model_id]["order_l1_gap"].append(float(metrics["order_l1_gap"][model_id]))
            accum[model_id]["order_h3_gap"].append(float(metrics["order_h3_gap"][model_id]))
            accum[model_id]["discrimination_distance"].append(
                float(metrics["discrimination_distance"][model_id])
            )
            accum[model_id]["ncd_point"].append(float(metrics["ncd_point"][model_id]))
            accum[model_id]["ncd_p_closest"].append(float(metrics["ncd_p_closest"][model_id]))

    def mean(values: list[float]) -> float:
        return float(sum(values) / len(values)) if values else float("nan")

    model_means = {
        model_id: {metric: mean(values) for metric, values in metric_map.items()}
        for model_id, metric_map in accum.items()
    }
    win_counts = {key: dict(counter) for key, counter in wins.items()}

    return {
        "num_sections_evaluated": len(section_results),
        "model_metric_means": model_means,
        "winner_counts": win_counts,
    }


def _pretty_model_name(model_id: str) -> str:
    names = {
        "line_reset_markov_trainfit": "Markov (Train-Fit)",
        "line_reset_backoff_trainfit": "Backoff (Train-Fit)",
        "line_reset_persistence_trainfit": "Persistence (Train-Fit)",
    }
    return names.get(model_id, model_id)


def _print_section_winner_table(section_results: dict[str, dict[str, Any]]) -> None:
    table = Table(title="Section Holdout Winners")
    table.add_column("Section", style="cyan")
    table.add_column("Holdout Folios", justify="right")
    table.add_column("Holdout Tokens", justify="right")
    table.add_column("Order Winner")
    table.add_column("Disc Winner")
    table.add_column("NCD Winner")
    table.add_column("NCD P(Closest) Winner")

    for section in sorted(section_results):
        payload = section_results[section]
        split = payload["split"]
        winners = payload["winners"]
        table.add_row(
            section,
            str(len(split["holdout_folios"])),
            str(split["holdout_token_count"]),
            _pretty_model_name(winners["order_l1"]),
            _pretty_model_name(winners["discrimination"]),
            _pretty_model_name(winners["ncd_point"]),
            _pretty_model_name(winners["ncd_prob"]),
        )
    console.print(table)


def _print_aggregate_table(summary: dict[str, Any]) -> None:
    means = summary["model_metric_means"]
    wins = summary["winner_counts"]

    table = Table(title="Section-Holdout Aggregate Means")
    table.add_column("Model", style="cyan")
    table.add_column("Mean Order L1", justify="right")
    table.add_column("Mean H3 Gap", justify="right")
    table.add_column("Mean Disc Dist", justify="right")
    table.add_column("Mean NCD", justify="right")
    table.add_column("Mean P(Closest)", justify="right")
    table.add_column("Order Wins", justify="right")
    table.add_column("Disc Wins", justify="right")
    table.add_column("NCD Wins", justify="right")
    table.add_column("NCD-P Wins", justify="right")

    for model_id in MODEL_IDS:
        row = means[model_id]
        table.add_row(
            _pretty_model_name(model_id),
            f"{row['order_l1_gap']:.4f}",
            f"{row['order_h3_gap']:.4f}",
            f"{row['discrimination_distance']:.4f}",
            f"{row['ncd_point']:.4f}",
            f"{row['ncd_p_closest']:.3f}",
            str(wins["order_l1"].get(model_id, 0)),
            str(wins["discrimination"].get(model_id, 0)),
            str(wins["ncd_point"].get(model_id, 0)),
            str(wins["ncd_prob"].get(model_id, 0)),
        )
    console.print(table)


if __name__ == "__main__":
    run_experiment(parse_args())
