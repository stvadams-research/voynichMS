from __future__ import annotations

import datetime
import math
import zlib
from dataclasses import dataclass
from typing import Any

import numpy as np

from phase1_foundation.storage.metadata import MetadataStore
from phase10_admissibility.stage1_pipeline import load_dataset_bundle


@dataclass
class Stage3Config:
    seed: int = 42
    target_tokens: int = 30000
    param_samples_per_family: int = 10000
    null_sequences: int = 1000
    perturbations_per_candidate: int = 12
    max_outlier_probes: int = 12
    null_block_min: int = 2
    null_block_max: int = 12
    symbol_alphabet_size: int = 64


@dataclass
class TokenAttributes:
    attr_stack: np.ndarray
    attr_names: list[str]
    index: np.ndarray

    @property
    def length(self) -> int:
        return int(self.index.size)


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def evaluate_stage3_priority_gate(
    stage1_summary: dict[str, Any] | None,
    stage2_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    stage1_decisions = {}
    stage2_decisions = {}
    if isinstance(stage1_summary, dict):
        stage1_decisions = dict(stage1_summary.get("method_decisions", {}))
    if isinstance(stage2_summary, dict):
        stage2_decisions = dict(stage2_summary.get("method_decisions", {}))

    method_g = str(stage2_decisions.get("G", "unknown"))
    method_i = str(stage2_decisions.get("I", "unknown"))
    any_stage1_weakened = any(
        str(value) == "closure_weakened" for value in stage1_decisions.values()
    )
    stage2_both_strengthened = (
        method_g == "closure_strengthened" and method_i == "closure_strengthened"
    )

    if any_stage1_weakened or not stage2_both_strengthened:
        priority = "urgent"
        reason = (
            "Method F is prioritized because Stage 1/2 includes non-strengthening "
            "signals (weakened or indeterminate outcomes)."
        )
    else:
        priority = "lower"
        reason = (
            "Method F is lower priority because both Method G and Method I are "
            "closure-strengthening and Stage 1 has no weakened signal."
        )

    return {
        "status": "ok",
        "generated_at": now_utc_iso(),
        "priority": priority,
        "reason": reason,
        "inputs": {
            "stage1_method_decisions": stage1_decisions,
            "stage2_method_decisions": stage2_decisions,
        },
    }


def _safe_token(token: str) -> str:
    stripped = token.strip()
    return stripped if stripped else "?"


def _build_token_attributes(tokens: list[str], alphabet_size: int) -> TokenAttributes:
    if not tokens:
        raise RuntimeError("Method F requires a non-empty token sequence.")

    token_ids: dict[str, int] = {}
    first_code = np.empty(len(tokens), dtype=np.int64)
    last_code = np.empty(len(tokens), dtype=np.int64)
    third_code = np.empty(len(tokens), dtype=np.int64)
    length_code = np.empty(len(tokens), dtype=np.int64)
    token_mod_code = np.empty(len(tokens), dtype=np.int64)
    vowel_code = np.empty(len(tokens), dtype=np.int64)
    vowels = set("aeiouy")

    for idx, raw in enumerate(tokens):
        token = _safe_token(raw)
        tok_id = token_ids.setdefault(token, len(token_ids))
        first = token[0]
        last = token[-1]
        third = token[2] if len(token) >= 3 else last
        vowel_count = sum(1 for char in token.lower() if char in vowels)

        first_code[idx] = ord(first) % alphabet_size
        last_code[idx] = ord(last) % alphabet_size
        third_code[idx] = ord(third) % alphabet_size
        length_code[idx] = len(token) % alphabet_size
        token_mod_code[idx] = tok_id % alphabet_size
        vowel_code[idx] = vowel_count % alphabet_size

    attr_stack = np.vstack(
        [
            token_mod_code,
            first_code,
            last_code,
            third_code,
            length_code,
            vowel_code,
        ]
    )
    return TokenAttributes(
        attr_stack=attr_stack.astype(np.int64, copy=False),
        attr_names=[
            "token_mod",
            "first_char_mod",
            "last_char_mod",
            "third_char_mod",
            "length_mod",
            "vowel_count_mod",
        ],
        index=np.arange(len(tokens), dtype=np.int64),
    )


def _symbol_entropy(symbols: np.ndarray, alphabet_size: int) -> float:
    counts = np.bincount(symbols, minlength=alphabet_size).astype(np.float64, copy=False)
    total = float(counts.sum())
    if total <= 0:
        return 0.0
    probs = counts / total
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def _symbol_bigram_mi(symbols: np.ndarray, alphabet_size: int) -> float:
    if symbols.size < 2:
        return 0.0
    prev = symbols[:-1]
    nxt = symbols[1:]
    n = float(prev.size)

    prev_counts = np.bincount(prev, minlength=alphabet_size).astype(np.float64)
    next_counts = np.bincount(nxt, minlength=alphabet_size).astype(np.float64)
    joint_codes = prev * alphabet_size + nxt
    joint_counts = np.bincount(joint_codes, minlength=alphabet_size * alphabet_size).astype(
        np.float64
    )

    joint_nonzero = np.nonzero(joint_counts)[0]
    if joint_nonzero.size == 0:
        return 0.0

    mi = 0.0
    for code in joint_nonzero:
        c_ab = joint_counts[code]
        a = int(code // alphabet_size)
        b = int(code % alphabet_size)
        p_ab = c_ab / n
        p_a = prev_counts[a] / n
        p_b = next_counts[b] / n
        if p_a > 0 and p_b > 0 and p_ab > 0:
            mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return float(mi)


def _symbol_zipf_alpha(symbols: np.ndarray, rank_limit: int = 64) -> float:
    counts = np.bincount(symbols).astype(np.float64)
    counts = counts[counts > 0]
    if counts.size <= 5:
        return 0.0
    freqs = np.sort(counts)[::-1]
    limit = min(rank_limit, int(freqs.size))
    ranks = np.arange(1, limit + 1, dtype=np.float64)
    log_ranks = np.log(ranks)
    log_freqs = np.log(freqs[:limit])
    slope, _ = np.polyfit(log_ranks, log_freqs, 1)
    return float(-slope)


def _symbol_top_frequency(symbols: np.ndarray, alphabet_size: int) -> float:
    counts = np.bincount(symbols, minlength=alphabet_size).astype(np.float64)
    total = float(counts.sum())
    if total <= 0:
        return 0.0
    return float(np.max(counts) / total)


def _symbol_compression_ratio(symbols: np.ndarray) -> float:
    if symbols.size == 0:
        return 0.0
    payload = symbols.astype(np.uint16, copy=False).tobytes()
    if not payload:
        return 0.0
    compressed = zlib.compress(payload, level=9)
    return float(len(compressed) / len(payload))


def _sample_null_indices(
    rng: np.random.Generator,
    length: int,
    block_min: int,
    block_max: int,
) -> np.ndarray:
    if length <= 1:
        return np.zeros(length, dtype=np.int64)
    block_min = max(1, block_min)
    block_max = max(block_min, block_max)
    out = np.empty(length, dtype=np.int64)
    cursor = 0
    while cursor < length:
        block_size = int(rng.integers(block_min, block_max + 1))
        start = int(rng.integers(0, max(1, length - block_size + 1)))
        take = min(block_size, length - cursor)
        out[cursor : cursor + take] = np.arange(start, start + take, dtype=np.int64)
        cursor += take
    return out


def _sample_table_params(
    rng: np.random.Generator,
    n_samples: int,
    attr_count: int,
    alphabet_size: int,
) -> list[tuple[int, int, int, int, int, int, int]]:
    params: list[tuple[int, int, int, int, int, int, int]] = []
    for _ in range(n_samples):
        params.append(
            (
                int(rng.integers(5, 32)),
                int(rng.integers(1, 12)),
                int(rng.integers(1, 12)),
                int(rng.integers(0, 31)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(1, 32)),
                int(rng.integers(0, alphabet_size)),
            )
        )
    return params


def _sample_slot_params(
    rng: np.random.Generator,
    n_samples: int,
    attr_count: int,
    alphabet_size: int,
) -> list[tuple[int, int, int, int, int, int, int]]:
    params: list[tuple[int, int, int, int, int, int, int]] = []
    for _ in range(n_samples):
        params.append(
            (
                int(rng.integers(3, 19)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(1, 17)),
                int(rng.integers(1, 17)),
                int(rng.integers(0, alphabet_size)),
            )
        )
    return params


def _sample_markov_params(
    rng: np.random.Generator,
    n_samples: int,
    attr_count: int,
    alphabet_size: int,
) -> list[tuple[int, int, int, int, int, int, int]]:
    params: list[tuple[int, int, int, int, int, int, int]] = []
    for _ in range(n_samples):
        params.append(
            (
                int(rng.integers(1, 8)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(0, attr_count)),
                int(rng.integers(1, 17)),
                int(rng.integers(0, 17)),
                int(rng.integers(3, 23)),
                int(rng.integers(0, alphabet_size)),
            )
        )
    return params


def _decode_table_symbols(
    attrs: TokenAttributes,
    param: tuple[int, int, int, int, int, int, int],
    alphabet_size: int,
    source_indices: np.ndarray | None = None,
) -> np.ndarray:
    width, step_r, step_c, offset, attr_idx, mix, bias = param
    idx = attrs.index
    source = attrs.attr_stack[attr_idx]
    if source_indices is not None:
        source = source[source_indices]

    row = idx // width
    col = idx % width
    grille = (step_r * row + step_c * col + offset) % width
    symbols = (source + mix * grille + bias) % alphabet_size
    return symbols.astype(np.int64, copy=False)


def _decode_slot_symbols(
    attrs: TokenAttributes,
    param: tuple[int, int, int, int, int, int, int],
    alphabet_size: int,
    source_indices: np.ndarray | None = None,
) -> np.ndarray:
    period, attr_a, attr_b, attr_c, phase_mix, block_mix, bias = param
    idx = attrs.index
    a = attrs.attr_stack[attr_a]
    b = attrs.attr_stack[attr_b]
    c = attrs.attr_stack[attr_c]
    if source_indices is not None:
        a = a[source_indices]
        b = b[source_indices]
        c = c[source_indices]

    phase = idx % period
    cut1 = max(1, period // 3)
    cut2 = max(cut1 + 1, (2 * period) // 3)
    base = np.where(phase < cut1, a, np.where(phase < cut2, b, c))
    symbols = (base + phase_mix * phase + block_mix * (idx // period) + bias) % alphabet_size
    return symbols.astype(np.int64, copy=False)


def _decode_markov_symbols(
    attrs: TokenAttributes,
    param: tuple[int, int, int, int, int, int, int],
    alphabet_size: int,
    source_indices: np.ndarray | None = None,
) -> np.ndarray:
    lag, attr_curr, attr_prev, prev_mix, phase_mix, phase_mod, bias = param
    idx = attrs.index
    curr = attrs.attr_stack[attr_curr]
    prev = attrs.attr_stack[attr_prev]
    if source_indices is not None:
        curr = curr[source_indices]
        prev = prev[source_indices]

    prev_shift = np.roll(prev, lag)
    if lag > 0:
        prev_shift[:lag] = prev[:lag]
    symbols = (
        curr + prev_mix * prev_shift + phase_mix * (idx % max(1, phase_mod)) + bias
    ) % alphabet_size
    return symbols.astype(np.int64, copy=False)


def _decode_symbols(
    family: str,
    attrs: TokenAttributes,
    param: tuple[int, ...],
    alphabet_size: int,
    source_indices: np.ndarray | None = None,
) -> np.ndarray:
    if family == "table_grille":
        return _decode_table_symbols(attrs, param, alphabet_size, source_indices)
    if family == "slot_logic":
        return _decode_slot_symbols(attrs, param, alphabet_size, source_indices)
    if family == "constrained_markov":
        return _decode_markov_symbols(attrs, param, alphabet_size, source_indices)
    raise ValueError(f"Unknown Method F mechanism family: {family}")


def _estimate_space_size(family: str, attr_count: int, alphabet_size: int) -> int:
    if family == "table_grille":
        return 27 * 11 * 11 * 31 * attr_count * 31 * alphabet_size
    if family == "slot_logic":
        return 16 * attr_count * attr_count * attr_count * 16 * 16 * alphabet_size
    if family == "constrained_markov":
        return 7 * attr_count * attr_count * 16 * 17 * 20 * alphabet_size
    raise ValueError(f"Unknown family for space estimation: {family}")


def _perturb_params(
    family: str,
    param: tuple[int, ...],
    rng: np.random.Generator,
    n: int,
    attr_count: int,
    alphabet_size: int,
) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for _ in range(n):
        if family == "table_grille":
            width, step_r, step_c, offset, attr_idx, mix, bias = param
            out.append(
                (
                    int(np.clip(width + rng.integers(-1, 2), 5, 31)),
                    int(np.clip(step_r + rng.integers(-1, 2), 1, 11)),
                    int(np.clip(step_c + rng.integers(-1, 2), 1, 11)),
                    int(np.clip(offset + rng.integers(-2, 3), 0, 30)),
                    int((attr_idx + rng.integers(0, attr_count)) % attr_count),
                    int(np.clip(mix + rng.integers(-2, 3), 1, 31)),
                    int((bias + rng.integers(-4, 5)) % alphabet_size),
                )
            )
            continue

        if family == "slot_logic":
            period, attr_a, attr_b, attr_c, phase_mix, block_mix, bias = param
            out.append(
                (
                    int(np.clip(period + rng.integers(-1, 2), 3, 18)),
                    int((attr_a + rng.integers(0, attr_count)) % attr_count),
                    int((attr_b + rng.integers(0, attr_count)) % attr_count),
                    int((attr_c + rng.integers(0, attr_count)) % attr_count),
                    int(np.clip(phase_mix + rng.integers(-2, 3), 1, 16)),
                    int(np.clip(block_mix + rng.integers(-2, 3), 1, 16)),
                    int((bias + rng.integers(-4, 5)) % alphabet_size),
                )
            )
            continue

        if family == "constrained_markov":
            lag, attr_curr, attr_prev, prev_mix, phase_mix, phase_mod, bias = param
            out.append(
                (
                    int(np.clip(lag + rng.integers(-1, 2), 1, 7)),
                    int((attr_curr + rng.integers(0, attr_count)) % attr_count),
                    int((attr_prev + rng.integers(0, attr_count)) % attr_count),
                    int(np.clip(prev_mix + rng.integers(-2, 3), 1, 16)),
                    int(np.clip(phase_mix + rng.integers(-2, 3), 0, 16)),
                    int(np.clip(phase_mod + rng.integers(-2, 3), 3, 22)),
                    int((bias + rng.integers(-4, 5)) % alphabet_size),
                )
            )
            continue

        raise ValueError(f"Unknown family for perturbation: {family}")
    return out


def _family_null_metrics(
    family: str,
    params: list[tuple[int, ...]],
    attrs: TokenAttributes,
    config: Stage3Config,
    rng: np.random.Generator,
    progress: callable[[str], None] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    null_entropy = np.empty(config.null_sequences, dtype=np.float64)
    null_bigram = np.empty(config.null_sequences, dtype=np.float64)
    null_zipf = np.empty(config.null_sequences, dtype=np.float64)
    stride = max(1, config.null_sequences // 10)

    for idx in range(config.null_sequences):
        param = params[int(rng.integers(0, len(params)))]
        source_idx = _sample_null_indices(
            rng=rng,
            length=attrs.length,
            block_min=config.null_block_min,
            block_max=config.null_block_max,
        )
        symbols = _decode_symbols(
            family=family,
            attrs=attrs,
            param=param,
            alphabet_size=config.symbol_alphabet_size,
            source_indices=source_idx,
        )
        null_entropy[idx] = _symbol_entropy(symbols, config.symbol_alphabet_size)
        null_bigram[idx] = _symbol_bigram_mi(symbols, config.symbol_alphabet_size)
        null_zipf[idx] = _symbol_zipf_alpha(symbols)
        if progress and ((idx + 1) % stride == 0 or idx + 1 == config.null_sequences):
            progress(f"[{family}] null calibration {idx + 1}/{config.null_sequences}")

    return null_entropy, null_bigram, null_zipf


def _family_real_entropy_scan(
    family: str,
    params: list[tuple[int, ...]],
    attrs: TokenAttributes,
    config: Stage3Config,
    progress: callable[[str], None] | None = None,
) -> np.ndarray:
    values = np.empty(len(params), dtype=np.float64)
    stride = max(1, len(params) // 10)
    for idx, param in enumerate(params):
        symbols = _decode_symbols(
            family=family,
            attrs=attrs,
            param=param,
            alphabet_size=config.symbol_alphabet_size,
            source_indices=None,
        )
        values[idx] = _symbol_entropy(symbols, config.symbol_alphabet_size)
        if progress and ((idx + 1) % stride == 0 or idx + 1 == len(params)):
            progress(f"[{family}] parameter scan {idx + 1}/{len(params)}")
    return values


def _family_search(
    family: str,
    params: list[tuple[int, ...]],
    attrs: TokenAttributes,
    config: Stage3Config,
    seed: int,
    progress: callable[[str], None] | None = None,
) -> dict[str, Any]:
    if progress:
        progress(
            f"[{family}] search start: params={len(params)}, null_sequences={config.null_sequences}"
        )

    rng = np.random.default_rng(seed)
    real_entropy = _family_real_entropy_scan(family, params, attrs, config, progress)
    null_entropy, null_bigram, null_zipf = _family_null_metrics(
        family=family,
        params=params,
        attrs=attrs,
        config=config,
        rng=rng,
        progress=progress,
    )

    threshold = float(np.quantile(null_entropy, 0.01))
    null_bigram_q95 = float(np.quantile(null_bigram, 0.95))
    outlier_indices = np.where(real_entropy <= threshold)[0]
    ranked = (
        outlier_indices[np.argsort(real_entropy[outlier_indices])]
        if outlier_indices.size
        else np.array([], dtype=np.int64)
    )
    probe_indices = ranked[: config.max_outlier_probes]

    candidates: list[dict[str, Any]] = []
    stable_any = 0
    stable_natural = 0
    for rank, idx in enumerate(probe_indices):
        param = params[int(idx)]
        symbols = _decode_symbols(
            family=family,
            attrs=attrs,
            param=param,
            alphabet_size=config.symbol_alphabet_size,
            source_indices=None,
        )
        entropy = _symbol_entropy(symbols, config.symbol_alphabet_size)
        bigram_mi = _symbol_bigram_mi(symbols, config.symbol_alphabet_size)
        zipf = _symbol_zipf_alpha(symbols)
        top_freq = _symbol_top_frequency(symbols, config.symbol_alphabet_size)
        compression = _symbol_compression_ratio(symbols)

        natural_like = bool(
            0.6 <= zipf <= 1.6
            and top_freq <= 0.45
            and bigram_mi >= null_bigram_q95
        )

        perturb_params = _perturb_params(
            family=family,
            param=param,
            rng=rng,
            n=config.perturbations_per_candidate,
            attr_count=attrs.attr_stack.shape[0],
            alphabet_size=config.symbol_alphabet_size,
        )
        perturb_pass = 0
        perturb_entropy: list[float] = []
        for pert in perturb_params:
            pert_symbols = _decode_symbols(
                family=family,
                attrs=attrs,
                param=pert,
                alphabet_size=config.symbol_alphabet_size,
                source_indices=None,
            )
            pert_ent = _symbol_entropy(pert_symbols, config.symbol_alphabet_size)
            pert_bmi = _symbol_bigram_mi(pert_symbols, config.symbol_alphabet_size)
            perturb_entropy.append(float(pert_ent))
            if pert_ent <= threshold and pert_bmi >= null_bigram_q95 * 0.9:
                perturb_pass += 1

        stability_rate = float(perturb_pass / max(len(perturb_params), 1))
        stable = bool(stability_rate >= 0.7)
        if stable:
            stable_any += 1
        if stable and natural_like:
            stable_natural += 1

        candidates.append(
            {
                "rank": rank + 1,
                "parameter_index": int(idx),
                "parameterization": list(param),
                "entropy": float(entropy),
                "bigram_mutual_information": float(bigram_mi),
                "zipf_alpha": float(zipf),
                "top_symbol_frequency": float(top_freq),
                "compression_ratio": float(compression),
                "natural_like_profile": natural_like,
                "stability": {
                    "perturbations": len(perturb_params),
                    "pass_count": int(perturb_pass),
                    "pass_rate": float(stability_rate),
                    "stable": stable,
                    "perturb_entropy_min": float(min(perturb_entropy))
                    if perturb_entropy
                    else 0.0,
                    "perturb_entropy_max": float(max(perturb_entropy))
                    if perturb_entropy
                    else 0.0,
                },
            }
        )

    if stable_natural > 0:
        decision = "closure_weakened"
        reason = (
            "Stable low-entropy reverse decodes with language-like frequency profile were "
            "detected below the calibrated null threshold."
        )
    elif outlier_indices.size == 0:
        decision = "closure_strengthened"
        reason = (
            "No sampled reverse parameterization produced entropy below the 1st percentile "
            "of the calibrated null distribution."
        )
    else:
        decision = "indeterminate"
        reason = (
            "Low-entropy outliers were found, but they were unstable or lacked language-like "
            "frequency support."
        )

    space = _estimate_space_size(
        family=family,
        attr_count=attrs.attr_stack.shape[0],
        alphabet_size=config.symbol_alphabet_size,
    )
    coverage_ratio = float(len(params) / space) if space > 0 else 0.0

    if progress:
        progress(
            f"[{family}] complete: decision={decision}, "
            f"outliers={int(outlier_indices.size)}, stable_natural={stable_natural}"
        )

    return {
        "family": family,
        "decision": decision,
        "reason": reason,
        "coverage": {
            "parameter_samples": len(params),
            "constrained_space_estimate": int(space),
            "coverage_ratio_estimate": coverage_ratio,
        },
        "entropy_thresholds": {
            "null_q01": threshold,
            "null_q05": float(np.quantile(null_entropy, 0.05)),
            "null_q50": float(np.quantile(null_entropy, 0.50)),
        },
        "real_entropy_distribution": {
            "mean": float(np.mean(real_entropy)),
            "std": float(np.std(real_entropy)),
            "min": float(np.min(real_entropy)),
            "q01": float(np.quantile(real_entropy, 0.01)),
            "q05": float(np.quantile(real_entropy, 0.05)),
        },
        "null_entropy_distribution": {
            "mean": float(np.mean(null_entropy)),
            "std": float(np.std(null_entropy)),
            "min": float(np.min(null_entropy)),
            "q01": float(np.quantile(null_entropy, 0.01)),
            "q05": float(np.quantile(null_entropy, 0.05)),
        },
        "null_reference_metrics": {
            "bigram_mutual_information_q95": null_bigram_q95,
            "zipf_alpha_q05": float(np.quantile(null_zipf, 0.05)),
            "zipf_alpha_q95": float(np.quantile(null_zipf, 0.95)),
        },
        "outlier_count_below_q01": int(outlier_indices.size),
        "stable_outlier_count": int(stable_any),
        "stable_natural_outlier_count": int(stable_natural),
        "candidate_reviews": candidates,
    }


def run_method_f(
    store: MetadataStore,
    config: Stage3Config,
    progress: callable[[str], None] | None = None,
) -> dict[str, Any]:
    voynich_bundle = load_dataset_bundle(store, "voynich_real", "Voynich (Real)")
    token_cap = max(1000, config.target_tokens)
    tokens = voynich_bundle.tokens[:token_cap]
    if len(tokens) < 1000:
        return {
            "method": "F",
            "status": "failed",
            "decision": "test_invalid",
            "reason": "Insufficient token coverage for reverse mechanism search.",
        }

    attrs = _build_token_attributes(tokens, alphabet_size=config.symbol_alphabet_size)
    if progress:
        progress(
            "Method F attributes prepared: "
            f"token_count={len(tokens)}, attr_count={attrs.attr_stack.shape[0]}"
        )

    rng = np.random.default_rng(config.seed)
    param_sets = {
        "table_grille": _sample_table_params(
            rng=rng,
            n_samples=config.param_samples_per_family,
            attr_count=attrs.attr_stack.shape[0],
            alphabet_size=config.symbol_alphabet_size,
        ),
        "slot_logic": _sample_slot_params(
            rng=rng,
            n_samples=config.param_samples_per_family,
            attr_count=attrs.attr_stack.shape[0],
            alphabet_size=config.symbol_alphabet_size,
        ),
        "constrained_markov": _sample_markov_params(
            rng=rng,
            n_samples=config.param_samples_per_family,
            attr_count=attrs.attr_stack.shape[0],
            alphabet_size=config.symbol_alphabet_size,
        ),
    }

    family_results: dict[str, dict[str, Any]] = {}
    for family_idx, family in enumerate(["table_grille", "slot_logic", "constrained_markov"]):
        family_results[family] = _family_search(
            family=family,
            params=param_sets[family],
            attrs=attrs,
            config=config,
            seed=config.seed + 100 + family_idx,
            progress=progress,
        )

    family_decisions = {key: value["decision"] for key, value in family_results.items()}
    if any(value == "closure_weakened" for value in family_decisions.values()):
        decision = "closure_weakened"
        reason = (
            "At least one mechanism family produced stable, null-defeating reverse decodes "
            "with language-like profile."
        )
    elif all(value == "closure_strengthened" for value in family_decisions.values()):
        decision = "closure_strengthened"
        reason = (
            "All mechanism families failed to produce stable reverse decodes below null "
            "calibration thresholds."
        )
    else:
        decision = "indeterminate"
        reason = "Reverse search produced mixed or unstable outliers across mechanism families."

    return {
        "method": "F",
        "status": "ok",
        "decision": decision,
        "reason": reason,
        "config": {
            "seed": config.seed,
            "target_tokens": token_cap,
            "param_samples_per_family": config.param_samples_per_family,
            "null_sequences": config.null_sequences,
            "perturbations_per_candidate": config.perturbations_per_candidate,
            "max_outlier_probes": config.max_outlier_probes,
            "null_block_min": config.null_block_min,
            "null_block_max": config.null_block_max,
            "symbol_alphabet_size": config.symbol_alphabet_size,
        },
        "token_attributes": {
            "token_count": len(tokens),
            "attribute_names": attrs.attr_names,
        },
        "family_decisions": family_decisions,
        "family_results": family_results,
    }


def summarize_stage3(
    priority_gate: dict[str, Any],
    method_f_result: dict[str, Any],
) -> dict[str, Any]:
    method_decision = str(method_f_result.get("decision", "indeterminate"))
    stage_decision = (
        "test_invalid" if method_decision == "test_invalid" else method_decision
    )

    return {
        "status": "ok",
        "stage": "10.3",
        "priority": priority_gate.get("priority", "unknown"),
        "stage_decision": stage_decision,
        "method_decisions": {"F": method_decision},
        "generated_at": now_utc_iso(),
    }


def build_stage3_markdown(
    summary: dict[str, Any],
    method_artifacts: dict[str, str],
    status_path: str,
) -> str:
    lines = [
        "# Phase 10 Stage 3 Results (Method F)",
        "",
        f"Generated: {summary['generated_at']}",
        f"Stage decision: **{summary['stage_decision']}**",
        f"Priority gate: **{summary.get('priority', 'unknown')}**",
        "",
        "## Method Decision",
        "",
        f"- Method F (Reverse Mechanism Test): `{summary['method_decisions'].get('F', 'n/a')}`",
        "",
        "## Artifacts",
        "",
        f"- Priority gate artifact: `{method_artifacts.get('priority_gate', 'n/a')}`",
        f"- Method F artifact: `{method_artifacts.get('F', 'n/a')}`",
        f"- Stage 3 summary artifact: `{method_artifacts.get('stage3', 'n/a')}`",
        f"- Restart status tracker: `{status_path}`",
        "",
        "## Notes",
        "",
        "- Method F used sampled reverse parameterizations for table-grille, slot-logic, and "
        "constrained-Markov families.",
        "- Null calibration used block-bootstrap token sequences preserving Voynich-like local "
        "statistics.",
        "",
    ]
    return "\n".join(lines)
