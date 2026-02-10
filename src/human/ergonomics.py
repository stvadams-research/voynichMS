"""
Human Factors and Ergonomics Analysis

Evaluates production constraints, fatigue proxies, and correction behavior.
Phase 7A implementation.
"""

import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import re
import logging
logger = logging.getLogger(__name__)

class ErgonomicsAnalyzer:
    """
    Analyzes human factors in manuscript production.
    """
    def __init__(self):
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
        # Group metrics by line index
        pos_lengths = defaultdict(list)
        pos_entropies = defaultdict(list)
        
        for line in lines:
            # We don't have absolute line index on page here if we just pass a list of lines.
            # But we can assume the order in the list is the order on the page if grouped by page.
            pass

        return {} # To be implemented in the runner with page grouping

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
            return {}
            
        line_lengths = [len(" ".join(line)) for line in page_lines]
        avg_word_lengths = [np.mean([len(w) for w in line]) if line else 0 for line in page_lines]
        
        # Calculate correlations with line index
        indices = np.arange(len(page_lines))
        
        len_corr = np.corrcoef(indices, line_lengths)[0, 1] if len(indices) > 1 else 0
        word_len_corr = np.corrcoef(indices, avg_word_lengths)[0, 1] if len(indices) > 1 else 0
        
        return {
            "num_lines": len(page_lines),
            "line_length_correlation": float(len_corr),
            "word_length_correlation": float(word_len_corr),
            "first_line_avg_word_len": float(avg_word_lengths[0]),
            "last_line_avg_word_len": float(avg_word_lengths[-1])
        }
