#!/usr/bin/env python3
# ruff: noqa: E402
"""
Boundary-persistence sweep and benchmark.

1) Sweep rho values for line-reset persistence generator.
2) Score each rho by order-signature match to Voynich + zlib NCD.
3) Run full diagnostics on best rho vs existing controls.
"""

import argparse
import sys
import zlib
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.queries import (  # noqa: E402
    get_lines_from_store,
    get_tokens_and_boundaries,
)
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run boundary persistence sweep + benchmark.")
    parser.add_argument("--rho-values", type=str, default="0.00,0.10,0.20,0.30,0.40,0.50,0.60")
    parser.add_argument("--trigram-use-probs", type=str, default="0.45,0.55,0.65")
    parser.add_argument("--unigram-noise-probs", type=str, default="0.01,0.03,0.05")
    parser.add_argument("--sweep-target-tokens", type=int, default=120000)
    parser.add_argument("--target-tokens", type=int, default=230000)
    parser.add_argument("--sweep-order-token-limit", type=int, default=120000)
    parser.add_argument("--sweep-order-vocab-limit", type=int, default=500)
    parser.add_argument("--sweep-order-permutations", type=int, default=20)
    parser.add_argument("--sweep-ncd-token-limit", type=int, default=80000)
    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=50)
    parser.add_argument("--ncd-token-limit", type=int, default=80000)
    parser.add_argument("--ncd-bootstraps", type=int, default=30)
    parser.add_argument("--ncd-block-size", type=int, default=512)
    parser.add_argument("--output-name", type=str, default="boundary_persistence_sweep.json")
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    rho_values = _parse_rho_values(args.rho_values)
    trigram_values = _parse_float_values(args.trigram_use_probs)
    noise_values = _parse_float_values(args.unigram_noise_probs)
    console.print(
        Panel.fit(
            "[bold blue]Boundary Persistence Sweep[/bold blue]\n"
            f"rho grid: {rho_values}\n"
            f"trigram_use grid: {trigram_values}\n"
            f"unigram_noise grid: {noise_values}",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_boundary_persistence_sweep_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
            "line_reset_markov": "Line-Reset Markov",
            "line_reset_backoff": "Line-Reset Backoff",
            "line_reset_persistence_best": "Line-Reset Persistence (Best Rho)",
        }

        dataset_tokens: dict[str, list[str]] = {}
        for dataset_id in (
            "voynich_real",
            "latin_classic",
            "self_citation",
            "table_grille",
            "mechanical_reuse",
            "shuffled_global",
        ):
            tokens, _ = get_tokens_and_boundaries(store, dataset_id)
            dataset_tokens[dataset_id] = tokens
            console.print(f"Loaded {datasets[dataset_id]}: {len(tokens)} tokens")

        lines = get_lines_from_store(store, "voynich_real")
        voynich_tokens = dataset_tokens["voynich_real"]

        sweep_order = OrderConstraintAnalyzer(
            OrderConstraintConfig(
                token_limit=args.sweep_order_token_limit,
                vocab_limit=args.sweep_order_vocab_limit,
                permutations=args.sweep_order_permutations,
                random_state=42,
            )
        )
        voynich_metrics = sweep_order.analyze({"voynich_real": voynich_tokens})["datasets"][
            "voynich_real"
        ]["metrics"]
        voynich_target = {
            "H2": float(voynich_metrics["bigram_cond_entropy"]["delta"]),
            "H3": float(voynich_metrics["trigram_cond_entropy"]["delta"]),
            "MI2": float(voynich_metrics["bigram_mutual_information"]["delta"]),
        }

        sweep_rows: list[dict[str, float]] = []
        for trigram_use in trigram_values:
            for noise in noise_values:
                for rho in rho_values:
                    gen = LineResetPersistenceGenerator(
                        LineResetPersistenceConfig(
                            random_state=42,
                            trigram_use_prob=trigram_use,
                            unigram_noise_prob=noise,
                            min_trigram_context_count=2,
                            boundary_persistence_rho=rho,
                            boundary_trigram_use_prob=0.7,
                        )
                    )
                    gen.fit(lines)
                    out = gen.generate(target_tokens=args.sweep_target_tokens)
                    cand_tokens = out["tokens"]  # type: ignore[index]

                    cand_metrics = sweep_order.analyze(
                        {"candidate": cand_tokens}
                    )["datasets"]["candidate"]["metrics"]
                    cand = {
                        "H2": float(cand_metrics["bigram_cond_entropy"]["delta"]),
                        "H3": float(cand_metrics["trigram_cond_entropy"]["delta"]),
                        "MI2": float(cand_metrics["bigram_mutual_information"]["delta"]),
                    }
                    order_l1 = (
                        abs(cand["H2"] - voynich_target["H2"])
                        + abs(cand["H3"] - voynich_target["H3"])
                        + abs(cand["MI2"] - voynich_target["MI2"])
                    )

                    ncd = _zlib_ncd(
                        voynich_tokens,
                        cand_tokens,
                        token_limit=args.sweep_ncd_token_limit,
                    )
                    composite = order_l1 + ncd

                    sweep_rows.append(
                        {
                            "rho": rho,
                            "trigram_use_prob": trigram_use,
                            "unigram_noise_prob": noise,
                            "H2": cand["H2"],
                            "H3": cand["H3"],
                            "MI2": cand["MI2"],
                            "order_l1": order_l1,
                            "ncd_to_voynich": ncd,
                            "composite": composite,
                        }
                    )

        sweep_rows.sort(key=lambda r: (r["composite"], r["order_l1"], r["ncd_to_voynich"]))
        best = sweep_rows[0]
        best_rho = float(best["rho"])
        best_trigram = float(best["trigram_use_prob"])
        best_noise = float(best["unigram_noise_prob"])

        sweep_table = Table(title="Boundary Persistence Sweep (Lower Composite is Better)")
        sweep_table.add_column("Rank", justify="right")
        sweep_table.add_column("rho", justify="right")
        sweep_table.add_column("tri", justify="right")
        sweep_table.add_column("noise", justify="right")
        sweep_table.add_column("H2", justify="right")
        sweep_table.add_column("H3", justify="right")
        sweep_table.add_column("MI2", justify="right")
        sweep_table.add_column("order_L1", justify="right")
        sweep_table.add_column("NCD", justify="right")
        sweep_table.add_column("composite", justify="right")
        for i, row in enumerate(sweep_rows, start=1):
            sweep_table.add_row(
                str(i),
                f"{row['rho']:.2f}",
                f"{row['trigram_use_prob']:.2f}",
                f"{row['unigram_noise_prob']:.2f}",
                f"{row['H2']:.4f}",
                f"{row['H3']:.4f}",
                f"{row['MI2']:.4f}",
                f"{row['order_l1']:.4f}",
                f"{row['ncd_to_voynich']:.4f}",
                f"{row['composite']:.4f}",
            )
        console.print(sweep_table)
        console.print(
            "[bold green]Best params selected: "
            f"rho={best_rho:.2f}, trigram_use={best_trigram:.2f}, noise={best_noise:.2f}"
            "[/bold green]"
        )

        # Build full comparison set using best rho.
        markov = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=42))
        markov.fit(lines)
        dataset_tokens["line_reset_markov"] = markov.generate(args.target_tokens)["tokens"]  # type: ignore[index]

        backoff = LineResetBackoffGenerator(LineResetBackoffConfig(random_state=42))
        backoff.fit(lines)
        dataset_tokens["line_reset_backoff"] = backoff.generate(args.target_tokens)["tokens"]  # type: ignore[index]

        persist = LineResetPersistenceGenerator(
            LineResetPersistenceConfig(
                random_state=42,
                trigram_use_prob=best_trigram,
                unigram_noise_prob=best_noise,
                min_trigram_context_count=2,
                boundary_persistence_rho=best_rho,
                boundary_trigram_use_prob=0.7,
            )
        )
        persist.fit(lines)
        p_out = persist.generate(args.target_tokens)
        dataset_tokens["line_reset_persistence_best"] = p_out["tokens"]  # type: ignore[index]

        disc = DiscriminationCheckAnalyzer(
            DiscriminationCheckConfig(
                window_size=72,
                windows_per_dataset=160,
                max_features=args.disc_max_features,
                ngram_min=args.disc_ngram_min,
                ngram_max=args.disc_ngram_max,
                train_fraction=0.7,
                random_state=42,
                voynich_dataset_id="voynich_real",
            )
        ).analyze(dataset_tokens)
        disc["dataset_labels"] = datasets

        order = OrderConstraintAnalyzer(
            OrderConstraintConfig(
                token_limit=args.order_token_limit,
                vocab_limit=args.order_vocab_limit,
                permutations=args.order_permutations,
                random_state=42,
            )
        ).analyze(dataset_tokens)
        order["dataset_labels"] = datasets

        ncd = NCDAnalyzer(
            NCDConfig(
                token_limit=args.ncd_token_limit,
                bootstraps=args.ncd_bootstraps,
                block_size=args.ncd_block_size,
                random_state=42,
                focus_dataset_id="voynich_real",
            )
        ).analyze(dataset_tokens)
        ncd["dataset_labels"] = datasets

        if disc.get("status") == "ok":
            closest = Table(title="Voynich Closest Families (Discrimination)")
            closest.add_column("Rank", justify="right")
            closest.add_column("Dataset", style="cyan")
            closest.add_column("Cosine Distance", justify="right")
            for i, row in enumerate(disc["voynich_summary"]["closest_centroids"][:8], start=1):
                closest.add_row(
                    str(i),
                    datasets.get(row["dataset_id"], row["dataset_id"]),
                    f"{row['cosine_distance']:.4f}",
                )
            console.print(closest)

        order_table = Table(title="Order Constraints: Delta vs Shuffled Baseline")
        order_table.add_column("Dataset", style="cyan")
        order_table.add_column("H2 delta", justify="right")
        order_table.add_column("H3 delta", justify="right")
        order_table.add_column("MI2 delta", justify="right")
        for dataset_id in (
            "voynich_real",
            "line_reset_markov",
            "line_reset_backoff",
            "line_reset_persistence_best",
            "mechanical_reuse",
            "shuffled_global",
        ):
            row = order["datasets"].get(dataset_id, {})
            if row.get("status") != "ok":
                order_table.add_row(datasets[dataset_id], "n/a", "n/a", "n/a")
                continue
            m = row["metrics"]
            order_table.add_row(
                datasets[dataset_id],
                f"{m['bigram_cond_entropy']['delta']:.4f}",
                f"{m['trigram_cond_entropy']['delta']:.4f}",
                f"{m['bigram_mutual_information']['delta']:.4f}",
            )
        console.print(order_table)

        if ncd.get("status") == "ok":
            ncd_table = Table(title="Voynich NCD Ranking (Lower is Closer)")
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
                    datasets.get(dataset_id, dataset_id),
                    f"{row['point_ncd']:.4f}",
                    f"{row['closest_probability']:.3f}",
                )
            console.print(ncd_table)

        results = {
            "status": "ok",
            "sweep": {
                "rho_values": rho_values,
                "trigram_use_probs": trigram_values,
                "unigram_noise_probs": noise_values,
                "voynich_target": voynich_target,
                "rows_sorted": sweep_rows,
                "best_rho": best_rho,
                "best_trigram_use_prob": best_trigram,
                "best_unigram_noise_prob": best_noise,
            },
            "generators": {
                "line_reset_markov": markov.fit_stats(),
                "line_reset_backoff": backoff.fit_stats(),
                "line_reset_persistence_best": persist.fit_stats(),
            },
            "discrimination": disc,
            "order_constraints": order,
            "ncd": ncd,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


def _parse_rho_values(raw: str) -> list[float]:
    return _parse_float_values(raw)


def _parse_float_values(raw: str) -> list[float]:
    values: list[float] = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            values.append(float(part))
    if not values:
        raise ValueError("No values provided")
    return values


def _zlib_ncd(tokens_a: list[str], tokens_b: list[str], token_limit: int) -> float:
    a = " ".join(tokens_a[:token_limit]).encode("utf-8", errors="ignore")
    b = " ".join(tokens_b[:token_limit]).encode("utf-8", errors="ignore")
    ca = len(zlib.compress(a, level=9))
    cb = len(zlib.compress(b, level=9))
    cab = len(zlib.compress(a + b"\n--SEP--\n" + b, level=9))
    denom = max(ca, cb)
    if denom == 0:
        return 0.0
    return float((cab - min(ca, cb)) / denom)


if __name__ == "__main__":
    run_experiment(parse_args())
