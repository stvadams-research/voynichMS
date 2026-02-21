"""
Human Factors and Ergonomics Analysis

Evaluates production constraints, fatigue proxies, and correction behavior.
Phase 7A implementation.
"""

import numpy as np
from collections import Counter
from typing import List, Dict, Any
import re
import math
import logging
logger = logging.getLogger(__name__)

class ErgonomicsAnalyzer:
    """
    Analyzes phase7_human factors in manuscript production.
    """
    def __init__(self):
        """Initialize the ErgonomicsAnalyzer with EVA stroke-count estimates.

        Populates self.stroke_map with approximate stroke counts for common
        EVA transliteration characters, used for production cost estimation.
        """
        # Estimated stroke counts for common EVA characters
        self.stroke_map = {
            'i': 1, 'e': 1, 'o': 1, 'c': 1, 'r': 1, 's': 1, 'y': 2,
            'a': 2, 'n': 2, 'd': 2, 'h': 2, 'l': 2,
            'm': 3, 'g': 2, 'k': 3, 't': 3,
            'p': 4, 'f': 4, 'v': 3, 'x': 2
        }

    def calculate_correction_density(self, raw_lines: List[str]) -> Dict[str, Any]:
        """
        Measures density of corrections/uncertainties using IVTFF notation.
        Patterns: [a:b] (correction), {ab} (expansion/uncertainty)
        """
        correction_pattern = re.compile(r"\[[^\]]+:[^\]]+\]")
        uncertainty_pattern = re.compile(r"\{[^\}]+\}")
        
        total_chars = 0
        total_corrections = 0
        total_uncertainties = 0
        
        for line in raw_lines:
            total_chars += len(line)
            total_corrections += len(correction_pattern.findall(line))
            total_uncertainties += len(uncertainty_pattern.findall(line))
            
        return {
            "total_lines": len(raw_lines),
            "correction_count": total_corrections,
            "uncertainty_count": total_uncertainties,
            "corrections_per_100_lines": (total_corrections / len(raw_lines)) * 100 if raw_lines else 0
        }

    def calculate_fatigue_gradient(self, lines: List[List[str]]) -> Dict[str, Any]:
        """
        Measures drift in metrics (length, entropy) as a function of line index.
        Expectation: Fatigue may lead to shorter words or lower entropy.
        """
        if not lines:
            return {
                "num_lines": 0,
                "line_length_correlation": 0.0,
                "entropy_correlation": 0.0,
                "mean_line_length": 0.0,
                "mean_line_entropy": 0.0,
            }

        line_lengths: List[float] = []
        line_entropies: List[float] = []
        for line in lines:
            line_lengths.append(float(sum(len(token) for token in line)))
            line_entropies.append(self._token_entropy(line))

        indices = np.arange(len(lines), dtype=float)
        return {
            "num_lines": len(lines),
            "line_length_correlation": self._safe_correlation(indices, np.array(line_lengths, dtype=float)),
            "entropy_correlation": self._safe_correlation(indices, np.array(line_entropies, dtype=float)),
            "mean_line_length": float(np.mean(line_lengths)) if line_lengths else 0.0,
            "mean_line_entropy": float(np.mean(line_entropies)) if line_entropies else 0.0,
        }

    def estimate_production_cost(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Estimates 'cost' of production based on stroke count proxies.
        """
        total_strokes = 0
        total_chars = 0
        
        for token in tokens:
            for char in token:
                total_chars += 1
                total_strokes += self.stroke_map.get(char, 2)  # Fallback 2 for unknown symbols
                
        return {
            "total_chars": total_chars,
            "total_strokes": total_strokes,
            "mean_strokes_per_char": total_strokes / total_chars if total_chars > 0 else 0,
            "mean_strokes_per_token": total_strokes / len(tokens) if tokens else 0
        }

    def analyze_page_fatigue(self, page_lines: List[List[str]]) -> Dict[str, Any]:
        """
        Analyzes drift within a single page.
        """
        if not page_lines:
            return {
                "num_lines": 0,
                "line_length_correlation": 0.0,
                "word_length_correlation": 0.0,
                "first_line_avg_word_len": 0.0,
                "last_line_avg_word_len": 0.0,
            }
            
        line_lengths = [len(" ".join(line)) for line in page_lines]
        avg_word_lengths = [np.mean([len(w) for w in line]) if line else 0 for line in page_lines]
        
        # Calculate correlations with line index
        indices = np.arange(len(page_lines))
        
        len_corr = self._safe_correlation(indices, np.array(line_lengths, dtype=float))
        word_len_corr = self._safe_correlation(indices, np.array(avg_word_lengths, dtype=float))
        
        return {
            "num_lines": len(page_lines),
            "line_length_correlation": float(len_corr),
            "word_length_correlation": float(word_len_corr),
            "first_line_avg_word_len": float(avg_word_lengths[0]),
            "last_line_avg_word_len": float(avg_word_lengths[-1])
        }

    def _token_entropy(self, line: List[str]) -> float:
        """Shannon entropy over token frequency for one line."""
        if not line:
            return 0.0
        counts = Counter(line)
        total = len(line)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return float(entropy)

    def _safe_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """Correlation helper that avoids NaN on constant vectors."""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        if np.allclose(y, y[0]):
            return 0.0
        corr = np.corrcoef(x, y)[0, 1]
        if np.isnan(corr):
            return 0.0
        return float(corr)
