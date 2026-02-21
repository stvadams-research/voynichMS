"""
Formal System Analyzer

Evaluates whether a corpus exhibits signatures of a formal system execution.
Phase 6A implementation.
"""

import logging
from collections import Counter, defaultdict
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class FormalSystemAnalyzer:
    """
    Evaluates whether a corpus exhibits signatures of a formal system execution.
    Phase 6A implementation.
    """
    def __init__(self):
        pass

    def _extract_states(self, lines: list[list[str]]) -> list[tuple[Any, ...]]:
        """
        Extract states as (prev, curr, pos) triplets.
        Note: We use this to define where we ARE in the system.
        """
        states = []
        for line in lines:
            for i, token in enumerate(line):
                prev = line[i-1] if i > 0 else "<START>"
                states.append((prev, token, i))
        return states

    def analyze_coverage(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.1 State-Space Coverage Analysis
        Determines whether the manuscript exhibits patterns consistent with 
        systematic exploration of a formal state space.
        """
        states = self._extract_states(lines)
        counts = Counter(states)

        freqs = sorted(counts.values(), reverse=True)
        total_visits = sum(freqs)
        unique_states = len(freqs)

        # Coverage ratio: unique states / total visits (proxy for density)
        coverage_ratio = unique_states / total_visits if total_visits > 0 else 0

        # Tail behavior: % of states seen only once
        hapax_states = sum(1 for f in freqs if f == 1)
        hapax_ratio = hapax_states / unique_states if unique_states > 0 else 0

        return {
            "total_visits": total_visits,
            "unique_states": unique_states,
            "coverage_ratio": float(coverage_ratio),
            "hapax_ratio": float(hapax_ratio),
            "top_frequencies": freqs[:20]
        }

    def analyze_redundancy(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.2 Redundancy and Repetition Inefficiency
        Assess whether the manuscript tolerates inefficiency consistent with 
        formal execution.
        """
        # Path overlap: how often do we see the same sequence of length N
        N = 3
        sequences = []
        for line in lines:
            for i in range(len(line) - N + 1):
                sequences.append(tuple(line[i:i+N]))

        seq_counts = Counter(sequences)
        total_seqs = sum(seq_counts.values())
        unique_seqs = len(seq_counts)

        overlap_rate = (total_seqs - unique_seqs) / total_seqs if total_seqs > 0 else 0

        # Repetition distance: if a line is repeated, how far away is it?
        line_map = defaultdict(list)
        for i, line in enumerate(lines):
            line_map[tuple(line)].append(i)

        distances = []
        for indices in line_map.values():
            if len(indices) > 1:
                for i in range(len(indices) - 1):
                    distances.append(indices[i+1] - indices[i])

        return {
            "path_overlap_rate_n3": float(overlap_rate),
            "redundant_lines_count": int(sum(len(indices) - 1 for indices in line_map.values() if len(indices) > 1)),
            "mean_repetition_distance": float(np.mean(distances)) if distances else 0.0,
            "total_sequences_n3": total_seqs
        }

    def analyze_errors(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.3 Error Typology and Correction Behavior
        Characterize deviations from the inferred ruleset.
        """
        states = self._extract_states(lines)

        # Context (prev, pos) -> set of successors
        # Here we define context as (prev, pos) and we want to see if 'curr' is deterministic.
        # Actually, Phase 5K says (Prev, Curr, Pos) -> Next is the state.
        # So context is (Prev, Curr, Pos).

        triplets = []
        for line in lines:
            for i in range(len(line) - 1):
                prev = line[i-1] if i > 0 else "<START>"
                curr = line[i]
                nxt = line[i+1]
                triplets.append(((prev, curr, i), nxt))

        context_map = defaultdict(Counter)
        for context, nxt in triplets:
            context_map[context][nxt] += 1

        deviations = []
        for context, successors in context_map.items():
            if len(successors) > 1:
                total = sum(successors.values())
                # If one successor is very dominant (>90%) and others are rare (count=1)
                dominant = successors.most_common(1)[0]
                if dominant[1] / total >= 0.9:
                    for s, count in successors.items():
                        if s != dominant[0] and count == 1:
                            deviations.append({
                                "context": [str(c) for c in context],
                                "expected": dominant[0],
                                "actual": s
                            })

        return {
            "detected_deviations_count": len(deviations),
            "deviation_rate": float(len(deviations) / len(triplets)) if triplets else 0.0,
            "sample_deviations": deviations[:10]
        }

    def analyze_exhaustion(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.4 Completeness and Exhaustion Signatures
        Test whether the manuscript trends toward completeness or exhaustion.
        """
        seen_states = set()
        novelty_curve = []

        # Process in chunks of 100 lines to see the trend
        chunk_size = 100
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i+chunk_size]
            chunk_states = self._extract_states(chunk)

            if not chunk_states:
                continue

            new_in_chunk = 0
            for s in chunk_states:
                if s not in seen_states:
                    new_in_chunk += 1
                    seen_states.add(s)

            novelty_curve.append(float(new_in_chunk / len(chunk_states)))

        return {
            "novelty_curve": novelty_curve,
            "final_novelty_rate": novelty_curve[-1] if novelty_curve else 0.0,
            "initial_novelty_rate": novelty_curve[0] if novelty_curve else 0.0,
            "is_converging": bool(novelty_curve[-1] < novelty_curve[0]) if len(novelty_curve) > 1 else False
        }

    def run_full_analysis(self, lines: list[list[str]]) -> dict[str, Any]:
        return {
            "coverage": self.analyze_coverage(lines),
            "redundancy": self.analyze_redundancy(lines),
            "errors": self.analyze_errors(lines),
            "exhaustion": self.analyze_exhaustion(lines)
        }
