"""
Cryptolinguistic Toolkit: Mechanical Signal Auditor

A generalized engine for detecting physical tool signatures 
in historical manuscripts.
"""

import random
from collections import Counter, defaultdict
from typing import Any


class MechanicalSignalAuditor:
    """
    Audits a columnar script for evidence of physical tool usage.
    """
    def __init__(self, min_transition_count: int = 2):
        self.min_transition_count = min_transition_count

    def audit_corpus(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        Runs the full verification pipeline (Slips + Shuffle Control).
        """
        # 1. Build Base Model
        model = self._build_model(lines)
        
        # 2. Detect Slips (Real)
        real_slips = self._detect_slips(lines, model)
        
        # 3. Shuffle Control (Skeptic's Gate)
        shuffled_lines = list(lines)
        random.shuffle(shuffled_lines)
        shuffled_slips = self._detect_slips(shuffled_lines, model)
        
        # 4. Calculate Significance
        snr = len(real_slips) / len(shuffled_slips) if len(shuffled_slips) > 0 else len(real_slips)
        
        return {
            "real_slip_count": len(real_slips),
            "noise_floor": len(shuffled_slips),
            "signal_to_noise_ratio": float(snr),
            "is_mechanical_artifact": bool(snr > 3.0),
            "determination": "MECHANICAL" if snr > 3.0 else "LINGUISTIC/RANDOM"
        }

    def _build_model(self, lines: list[list[str]]) -> dict:
        model = defaultdict(set)
        counts = Counter()
        for line in lines:
            for i in range(len(line) - 1):
                ctx = (line[i], i + 1)
                counts[(ctx, line[i+1])] += 1
        
        for (ctx, next_w), count in counts.items():
            if count >= self.min_transition_count:
                model[ctx].add(next_w)
        return model

    def _detect_slips(self, lines: list[list[str]], model: dict) -> list:
        slips = []
        for i in range(1, len(lines)):
            curr, prev = lines[i], lines[i-1]
            for j in range(1, min(len(curr), len(prev))):
                if curr[j] not in model[(curr[j-1], j)] and curr[j] in model[(prev[j-1], j)]:
                    slips.append(j)
        return slips
