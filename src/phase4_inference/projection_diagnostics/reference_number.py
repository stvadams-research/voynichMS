"""
Reference-number relevance diagnostics.

Evaluates whether a target integer (default 42) appears as an unusually
frequent structural value across supplied metric distributions.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any


@dataclass
class ReferenceNumberConfig:
    target_value: int = 42
    local_window_radius: int = 6
    top_k: int = 5


class ReferenceNumberAnalyzer:
    """Scores target-number relevance across structural count metrics."""

    def __init__(self, config: ReferenceNumberConfig | None = None):
        self.config = config or ReferenceNumberConfig()

    def analyze(self, metric_values: dict[str, Sequence[int]]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "status": "ok",
            "config": self._config_dict(),
            "metrics": {},
        }

        for metric_name, raw_values in metric_values.items():
            values = [int(v) for v in raw_values if int(v) >= 0]
            if not values:
                results["metrics"][metric_name] = {
                    "status": "insufficient_data",
                    "n_observations": 0,
                }
                continue
            results["metrics"][metric_name] = self._analyze_single_metric(values)

        results["aggregate"] = self._build_aggregate(results["metrics"])
        return results

    def _analyze_single_metric(self, values: list[int]) -> dict[str, Any]:
        target = int(self.config.target_value)
        window_radius = max(1, int(self.config.local_window_radius))
        counts = Counter(values)
        n = len(values)
        v_min = min(values)
        v_max = max(values)
        target_count = int(counts.get(target, 0))
        target_rate = float(target_count / n)

        global_slot_count = int((v_max - v_min) + 1)
        global_expected = float(n / global_slot_count)
        global_std = self._binomial_std(n, global_slot_count)
        global_z, global_p = self._normal_tail_from_observed(
            observed=target_count,
            expected=global_expected,
            std=global_std,
        )

        local_low = target - window_radius
        local_high = target + window_radius
        local_values = list(range(local_low, local_high + 1))
        local_slot_count = len(local_values)
        local_observation_total = int(sum(counts.get(v, 0) for v in local_values))
        local_expected = float(local_observation_total / local_slot_count)
        local_std = self._binomial_std(local_observation_total, local_slot_count)
        local_z, local_p = self._normal_tail_from_observed(
            observed=target_count,
            expected=local_expected,
            std=local_std,
        )

        neighbor_counts = [counts.get(v, 0) for v in local_values if v != target]
        neighbor_mean = float(mean(neighbor_counts)) if neighbor_counts else 0.0
        neighbor_std = float(pstdev(neighbor_counts)) if len(neighbor_counts) > 1 else 0.0
        neighbor_z, neighbor_p = self._normal_tail_from_observed(
            observed=target_count,
            expected=neighbor_mean,
            std=neighbor_std,
        )

        classification = self._classify_signal(target_count, local_z, neighbor_z)

        top_values = [
            {"value": int(value), "count": int(count)}
            for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
                : self.config.top_k
            ]
        ]
        closest_to_target = [
            {"value": int(value), "count": int(count), "distance": int(abs(value - target))}
            for value, count in sorted(
                counts.items(), key=lambda item: (abs(item[0] - target), -item[1], item[0])
            )[: self.config.top_k]
        ]

        return {
            "status": "ok",
            "target_value": target,
            "n_observations": n,
            "target_count": target_count,
            "target_rate": target_rate,
            "value_range": {
                "min": v_min,
                "max": v_max,
                "slot_count": global_slot_count,
            },
            "global_uniform_test": {
                "expected_count": global_expected,
                "std_count": global_std,
                "z_score": global_z,
                "p_one_sided": global_p,
            },
            "local_window_test": {
                "window_radius": window_radius,
                "window_low": local_low,
                "window_high": local_high,
                "slot_count": local_slot_count,
                "observations_in_window": local_observation_total,
                "expected_count": local_expected,
                "std_count": local_std,
                "z_score": local_z,
                "p_one_sided": local_p,
            },
            "neighborhood_test": {
                "window_radius": window_radius,
                "neighbor_mean_count": neighbor_mean,
                "neighbor_std_count": neighbor_std,
                "z_score": neighbor_z,
                "p_one_sided": neighbor_p,
                "max_neighbor_count": int(max(neighbor_counts)) if neighbor_counts else 0,
            },
            "top_values": top_values,
            "closest_to_target": closest_to_target,
            "classification": classification,
        }

    def _build_aggregate(self, metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
        ok_rows = [row for row in metrics.values() if row.get("status") == "ok"]
        hit_rows = [row for row in ok_rows if int(row.get("target_count", 0)) > 0]
        strong_rows = [row for row in ok_rows if row.get("classification") == "STRONG_SIGNAL"]
        weak_rows = [row for row in ok_rows if row.get("classification") == "WEAK_SIGNAL"]

        by_category: dict[str, list[dict[str, Any]]] = {
            "line": [],
            "page": [],
            "section": [],
            "other": [],
        }
        for metric_name, row in metrics.items():
            if row.get("status") != "ok":
                continue
            category = metric_name.split("_", 1)[0]
            if category not in by_category:
                category = "other"
            by_category[category].append(row)

        category_coverage: dict[str, dict[str, Any]] = {}
        for category, rows in by_category.items():
            if not rows:
                continue
            category_coverage[category] = {
                "metrics": len(rows),
                "hit": any(int(row.get("target_count", 0)) > 0 for row in rows),
                "strong_signal": any(row.get("classification") == "STRONG_SIGNAL" for row in rows),
            }

        max_local_z = max(
            (float(row["local_window_test"]["z_score"]) for row in ok_rows),
            default=0.0,
        )
        max_neighbor_z = max(
            (float(row["neighborhood_test"]["z_score"]) for row in ok_rows),
            default=0.0,
        )
        mean_target_rate = (
            float(mean(float(row["target_rate"]) for row in ok_rows)) if ok_rows else 0.0
        )

        assessment = self._assess_overall(
            strong_signal_metric_count=len(strong_rows),
            weak_signal_metric_count=len(weak_rows),
            hit_metric_count=len(hit_rows),
            category_coverage=category_coverage,
        )

        return {
            "target_value": int(self.config.target_value),
            "metric_count": len(ok_rows),
            "hit_metric_count": len(hit_rows),
            "strong_signal_metric_count": len(strong_rows),
            "weak_signal_metric_count": len(weak_rows),
            "mean_target_rate": mean_target_rate,
            "max_local_z_score": max_local_z,
            "max_neighbor_z_score": max_neighbor_z,
            "category_coverage": category_coverage,
            "assessment": assessment,
        }

    def _classify_signal(self, target_count: int, local_z: float, neighbor_z: float) -> str:
        if target_count <= 0:
            return "NO_HIT"
        if local_z >= 2.0 or neighbor_z >= 2.0:
            return "STRONG_SIGNAL"
        if local_z >= 1.0 or neighbor_z >= 1.0:
            return "WEAK_SIGNAL"
        return "NO_SIGNAL"

    def _assess_overall(
        self,
        strong_signal_metric_count: int,
        weak_signal_metric_count: int,
        hit_metric_count: int,
        category_coverage: dict[str, dict[str, Any]],
    ) -> str:
        strong_categories = sum(
            1 for payload in category_coverage.values() if bool(payload.get("strong_signal"))
        )
        hit_categories = sum(
            1 for payload in category_coverage.values() if bool(payload.get("hit"))
        )

        if strong_signal_metric_count >= 2 and strong_categories >= 2:
            return "ELEVATED_REFERENCE_SIGNAL"
        if strong_signal_metric_count >= 1 or weak_signal_metric_count >= 2:
            return "WEAK_REFERENCE_SIGNAL"
        if hit_metric_count > 0 and hit_categories >= 2:
            return "PRESENCE_WITHOUT_ENRICHMENT"
        if hit_metric_count > 0:
            return "SPARSE_PRESENCE"
        return "NO_REFERENCE_SIGNAL"

    def _binomial_std(self, n: int, slot_count: int) -> float:
        if n <= 0 or slot_count <= 1:
            return 0.0
        p = 1.0 / float(slot_count)
        return float(math.sqrt(n * p * (1.0 - p)))

    def _normal_tail_from_observed(
        self, observed: float, expected: float, std: float
    ) -> tuple[float, float]:
        if std <= 0:
            if observed > expected:
                return 10.0, 0.0
            if observed < expected:
                return -10.0, 1.0
            return 0.0, 0.5
        z = float((observed - expected) / std)
        p = float(0.5 * math.erfc(z / math.sqrt(2.0)))
        return z, p

    def _config_dict(self) -> dict[str, Any]:
        return {
            "target_value": int(self.config.target_value),
            "local_window_radius": int(self.config.local_window_radius),
            "top_k": int(self.config.top_k),
        }
