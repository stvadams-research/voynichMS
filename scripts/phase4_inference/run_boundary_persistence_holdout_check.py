#!/usr/bin/env python3
# ruff: noqa: E402
"""
Out-of-sample holdout check for line-reset persistence controls.

Pipeline:
1) Split Voynich folios into train vs holdout folio sets.
2) Fit Markov / Backoff / Persistence generators on train folios only.
3) Generate token streams matched to holdout token count.
4) Compare against holdout using order constraints, discrimination, and NCD.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase4_inference.projection_diagnostics.discrimination import (  # noqa: E402
    DiscriminationCheckAnalyzer,
    DiscriminationCheckConfig,
)
from phase4_inference.projection_diagnostics.line_reset_backoff import (  # noqa: E402
    LineResetBackoffConfig,
    LineResetBackoffGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_markov import (  # noqa: E402
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_persistence import (  # noqa: E402
    LineResetPersistenceConfig,
    LineResetPersistenceGenerator,
)
from phase4_inference.projection_diagnostics.ncd import NCDAnalyzer, NCDConfig  # noqa: E402
from phase4_inference.projection_diagnostics.order_constraints import (  # noqa: E402
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
FOLIO_PATTERN = re.compile(r"^f(\d+)([rv])(\d*)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run boundary-persistence holdout check on unseen Voynich folios."
    )
    parser.add_argument("--holdout-fraction", type=float, default=0.20)
    parser.add_argument("--random-state", type=int, default=42)

    parser.add_argument("--backoff-trigram-use", type=float, default=0.55)
    parser.add_argument("--backoff-unigram-noise", type=float, default=0.03)
    parser.add_argument("--persistence-rho", type=float, default=0.50)
    parser.add_argument("--persistence-trigram-use", type=float, default=0.65)
    parser.add_argument("--persistence-unigram-noise", type=float, default=0.01)

    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=50)
    parser.add_argument("--ncd-token-limit", type=int, default=80000)
    parser.add_argument("--ncd-bootstraps", type=int, default=30)
    parser.add_argument("--ncd-block-size", type=int, default=512)

    parser.add_argument(
        "--output-name",
        type=str,
        default="boundary_persistence_holdout_check.json",
    )
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    if not (0.0 < args.holdout_fraction < 1.0):
        raise ValueError("--holdout-fraction must be in (0, 1)")

    console.print(
        Panel.fit(
            "[bold blue]Boundary Persistence Holdout Check[/bold blue]\n"
            f"holdout_fraction={args.holdout_fraction:.2f}, seed={args.random_state}\n"
            "Fit on train folios, evaluate on unseen holdout folios",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_boundary_persistence_holdout_check_phase4"}) as run:
        store = MetadataStore(DB_PATH)

        lines_by_folio = _load_voynich_lines_by_folio(store)
        all_folios = sorted(lines_by_folio.keys(), key=_folio_sort_key)
        if len(all_folios) < 3:
            raise RuntimeError("Need at least 3 folios for train/holdout split.")

        train_folios, holdout_folios = _split_folios(
            all_folios=all_folios,
            holdout_fraction=args.holdout_fraction,
            random_state=args.random_state,
        )

        train_lines = _collect_lines(lines_by_folio, train_folios)
        holdout_lines = _collect_lines(lines_by_folio, holdout_folios)
        holdout_tokens = [token for line in holdout_lines for token in line]

        if not train_lines or not holdout_tokens:
            raise RuntimeError("Split produced empty train or holdout data.")

        holdout_token_count = len(holdout_tokens)
        console.print(
            f"Split folios: train={len(train_folios)} holdout={len(holdout_folios)} | "
            f"train_lines={len(train_lines)} holdout_lines={len(holdout_lines)} | "
            f"holdout_tokens={holdout_token_count}"
        )

        dataset_labels = {
            "voynich_holdout": "Voynich Holdout",
            "line_reset_markov_trainfit": "Line-Reset Markov (Train-Fit)",
            "line_reset_backoff_trainfit": "Line-Reset Backoff (Train-Fit)",
            "line_reset_persistence_trainfit": "Line-Reset Persistence (Train-Fit)",
        }

        dataset_tokens: dict[str, list[str]] = {"voynich_holdout": holdout_tokens}

        markov = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=args.random_state))
        markov.fit(train_lines)
        markov_out = markov.generate(target_tokens=holdout_token_count)
        dataset_tokens["line_reset_markov_trainfit"] = markov_out["tokens"]  # type: ignore[index]

        backoff = LineResetBackoffGenerator(
            LineResetBackoffConfig(
                random_state=args.random_state,
                trigram_use_prob=args.backoff_trigram_use,
                unigram_noise_prob=args.backoff_unigram_noise,
                min_trigram_context_count=2,
            )
        )
        backoff.fit(train_lines)
        backoff_out = backoff.generate(target_tokens=holdout_token_count)
        dataset_tokens["line_reset_backoff_trainfit"] = backoff_out["tokens"]  # type: ignore[index]

        persistence = LineResetPersistenceGenerator(
            LineResetPersistenceConfig(
                random_state=args.random_state,
                trigram_use_prob=args.persistence_trigram_use,
                unigram_noise_prob=args.persistence_unigram_noise,
                min_trigram_context_count=2,
                boundary_persistence_rho=args.persistence_rho,
                boundary_trigram_use_prob=0.7,
            )
        )
        persistence.fit(train_lines)
        persistence_out = persistence.generate(target_tokens=holdout_token_count)
        dataset_tokens["line_reset_persistence_trainfit"] = persistence_out["tokens"]  # type: ignore[index]

        disc = DiscriminationCheckAnalyzer(
            DiscriminationCheckConfig(
                window_size=72,
                windows_per_dataset=160,
                max_features=args.disc_max_features,
                ngram_min=args.disc_ngram_min,
                ngram_max=args.disc_ngram_max,
                train_fraction=0.7,
                random_state=args.random_state,
                voynich_dataset_id="voynich_holdout",
            )
        ).analyze(dataset_tokens)
        disc["dataset_labels"] = dataset_labels

        order = OrderConstraintAnalyzer(
            OrderConstraintConfig(
                token_limit=args.order_token_limit,
                vocab_limit=args.order_vocab_limit,
                permutations=args.order_permutations,
                random_state=args.random_state,
            )
        ).analyze(dataset_tokens)
        order["dataset_labels"] = dataset_labels

        ncd = NCDAnalyzer(
            NCDConfig(
                token_limit=args.ncd_token_limit,
                bootstraps=args.ncd_bootstraps,
                block_size=args.ncd_block_size,
                random_state=args.random_state,
                focus_dataset_id="voynich_holdout",
            )
        ).analyze(dataset_tokens)
        ncd["dataset_labels"] = dataset_labels

        order_gap_rows = _compute_order_gap_rows(order)

        split_table = Table(title="Holdout Split")
        split_table.add_column("Field", style="cyan")
        split_table.add_column("Value", justify="right")
        split_table.add_row("Train folios", str(len(train_folios)))
        split_table.add_row("Holdout folios", str(len(holdout_folios)))
        split_table.add_row("Train lines", str(len(train_lines)))
        split_table.add_row("Holdout lines", str(len(holdout_lines)))
        split_table.add_row("Holdout tokens", str(holdout_token_count))
        console.print(split_table)

        order_table = Table(title="Holdout Order Gap to Voynich Holdout (Lower is Better)")
        order_table.add_column("Rank", justify="right")
        order_table.add_column("Dataset", style="cyan")
        order_table.add_column("H2 gap", justify="right")
        order_table.add_column("H3 gap", justify="right")
        order_table.add_column("MI2 gap", justify="right")
        order_table.add_column("L1 gap", justify="right")
        for i, row in enumerate(order_gap_rows, start=1):
            order_table.add_row(
                str(i),
                dataset_labels.get(row["dataset_id"], row["dataset_id"]),
                f"{row['h2_gap']:.4f}",
                f"{row['h3_gap']:.4f}",
                f"{row['mi2_gap']:.4f}",
                f"{row['order_l1_gap']:.4f}",
            )
        console.print(order_table)

        if disc.get("status") == "ok":
            disc_table = Table(title="Holdout Discrimination (Lower is Closer)")
            disc_table.add_column("Rank", justify="right")
            disc_table.add_column("Dataset", style="cyan")
            disc_table.add_column("Cosine Distance", justify="right")
            for i, row in enumerate(disc["voynich_summary"]["closest_centroids"], start=1):
                disc_table.add_row(
                    str(i),
                    dataset_labels.get(row["dataset_id"], row["dataset_id"]),
                    f"{row['cosine_distance']:.4f}",
                )
            console.print(disc_table)

        if ncd.get("status") == "ok":
            ncd_table = Table(title="Holdout NCD (Lower is Closer)")
            ncd_table.add_column("Rank", justify="right")
            ncd_table.add_column("Dataset", style="cyan")
            ncd_table.add_column("Point NCD", justify="right")
            ncd_table.add_column("P(Closest)", justify="right")
            ranked = sorted(
                ncd["focus_bootstrap_summary"].items(),
                key=lambda kv: kv[1]["point_ncd"],
            )
            for i, (dataset_id, row) in enumerate(ranked, start=1):
                ncd_table.add_row(
                    str(i),
                    dataset_labels.get(dataset_id, dataset_id),
                    f"{row['point_ncd']:.4f}",
                    f"{row['closest_probability']:.3f}",
                )
            console.print(ncd_table)

        results = {
            "status": "ok",
            "split": {
                "holdout_fraction": float(args.holdout_fraction),
                "random_state": int(args.random_state),
                "all_folios": all_folios,
                "train_folios": train_folios,
                "holdout_folios": holdout_folios,
                "train_line_count": len(train_lines),
                "holdout_line_count": len(holdout_lines),
                "holdout_token_count": holdout_token_count,
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
            "generators": {
                "line_reset_markov_trainfit": markov.fit_stats(),
                "line_reset_backoff_trainfit": backoff.fit_stats(),
                "line_reset_persistence_trainfit": persistence.fit_stats(),
            },
            "order_constraints": order,
            "order_holdout_gaps_ranked": order_gap_rows,
            "discrimination": disc,
            "ncd": ncd,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


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
        if current_line_id is not None and line_id != current_line_id:
            if current_folio is not None and current_tokens:
                lines_by_folio[str(current_folio)].append(current_tokens)
            current_tokens = []
        current_folio = str(folio)
        current_line_id = str(line_id)
        current_tokens.append(str(content))

    if current_folio is not None and current_tokens:
        lines_by_folio[current_folio].append(current_tokens)

    return dict(lines_by_folio)


def _split_folios(
    all_folios: list[str], holdout_fraction: float, random_state: int
) -> tuple[list[str], list[str]]:
    shuffled = list(all_folios)
    rng = np.random.default_rng(random_state)
    rng.shuffle(shuffled)

    holdout_count = int(round(len(shuffled) * holdout_fraction))
    holdout_count = max(1, min(len(shuffled) - 1, holdout_count))

    holdout = sorted(shuffled[:holdout_count], key=_folio_sort_key)
    train = sorted(shuffled[holdout_count:], key=_folio_sort_key)
    return train, holdout


def _collect_lines(
    lines_by_folio: dict[str, list[list[str]]], folios: list[str]
) -> list[list[str]]:
    out: list[list[str]] = []
    for folio in folios:
        out.extend(lines_by_folio.get(folio, []))
    return out


def _folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
    match = FOLIO_PATTERN.match(folio_id)
    if not match:
        return (10**9, 10**9, 10**9, folio_id)
    folio_num = int(match.group(1))
    side = 0 if match.group(2) == "r" else 1
    suffix = int(match.group(3)) if match.group(3) else 0
    return (folio_num, side, suffix, folio_id)


def _compute_order_gap_rows(order_payload: dict[str, object]) -> list[dict[str, float | str]]:
    datasets = order_payload["datasets"]  # type: ignore[index]
    target_metrics = datasets["voynich_holdout"]["metrics"]  # type: ignore[index]

    target_h2 = float(target_metrics["bigram_cond_entropy"]["delta"])  # type: ignore[index]
    target_h3 = float(target_metrics["trigram_cond_entropy"]["delta"])  # type: ignore[index]
    target_mi2 = float(target_metrics["bigram_mutual_information"]["delta"])  # type: ignore[index]

    rows: list[dict[str, float | str]] = []
    for dataset_id, payload in datasets.items():  # type: ignore[union-attr]
        if dataset_id == "voynich_holdout":
            continue
        if payload.get("status") != "ok":
            continue
        m = payload["metrics"]
        h2 = float(m["bigram_cond_entropy"]["delta"])
        h3 = float(m["trigram_cond_entropy"]["delta"])
        mi2 = float(m["bigram_mutual_information"]["delta"])

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

    rows.sort(key=lambda r: (r["order_l1_gap"], r["h3_gap"], r["h2_gap"]))
    return rows


if __name__ == "__main__":
    run_experiment(parse_args())
