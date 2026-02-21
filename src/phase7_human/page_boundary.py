"""
Page Boundary and Layout Coupling Analysis

Tests whether text generation adapts to physical page boundaries and layout.
Phase 7B implementation.
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class PageBoundaryAnalyzer:
    """
    Analyzes coupling between text and page geometry.
    """
    def __init__(self):
        """Initialize the PageBoundaryAnalyzer.

        No configuration is required. All analysis parameters are derived
        from the page data passed to individual analysis methods.
        """
        pass

    def analyze_boundary_adaptation(self, pages: dict[str, list[list[str]]]) -> dict[str, Any]:
        """
        6.1 Page Boundary Adaptation Test
        Measures changes in line length and entropy as a function of distance from page bottom.
        """
        all_page_stats = []
        
        for page_id, lines in pages.items():
            if not lines:
                continue
            
            num_lines = len(lines)
            for i, line in enumerate(lines):
                # Distance from top (0.0) to bottom (1.0)
                pos_ratio = i / (num_lines - 1) if num_lines > 1 else 0
                
                line_len = sum(len(w) for w in line)
                avg_word_len = np.mean([len(w) for w in line]) if line else 0
                
                all_page_stats.append({
                    "pos_ratio": pos_ratio,
                    "line_len": line_len,
                    "avg_word_len": avg_word_len
                })
        
        if not all_page_stats:
            return {
                "num_lines_sampled": 0,
                "line_length_pos_correlation": 0.0,
                "word_length_pos_correlation": 0.0,
                "top_20_mean_len": 0.0,
                "bot_20_mean_len": 0.0,
                "boundary_effect_detected": False,
                "status": "no_data",
            }

        # Correlate position with length
        ratios = [s['pos_ratio'] for s in all_page_stats]
        lengths = [s['line_len'] for s in all_page_stats]
        word_lengths = [s['avg_word_len'] for s in all_page_stats]
        
        len_corr = self._safe_correlation(ratios, lengths)
        word_len_corr = self._safe_correlation(ratios, word_lengths)
        
        # Compare top 20% vs bottom 20%
        top_20 = [s['line_len'] for s in all_page_stats if s['pos_ratio'] < 0.2]
        bot_20 = [s['line_len'] for s in all_page_stats if s['pos_ratio'] > 0.8]
        
        return {
            "num_lines_sampled": len(all_page_stats),
            "line_length_pos_correlation": float(len_corr),
            "word_length_pos_correlation": float(word_len_corr),
            "top_20_mean_len": float(np.mean(top_20)) if top_20 else 0,
            "bot_20_mean_len": float(np.mean(bot_20)) if bot_20 else 0,
            "boundary_effect_detected": bool(abs(len_corr) > 0.2)
        }

    def analyze_layout_obstruction(self, pages: dict[str, list[list[str]]]) -> dict[str, Any]:
        """
        6.4 Layout Obstruction Test (Proxy)
        In the absence of explicit layout masks, we look for line length variance.
        If generation is in-situ, we expect high variance in line length 
        compared to a fixed-width external copy.
        """
        page_vars = []
        for lines in pages.values():
            if len(lines) > 5:
                lengths = [sum(len(w) for w in line) for line in lines]
                page_vars.append(np.std(lengths) / np.mean(lengths) if np.mean(lengths) > 0 else 0)
        
        return {
            "mean_coefficient_of_variation": float(np.mean(page_vars)) if page_vars else 0,
            "interpretation": "High CV suggests adaptation to irregular layout (in-situ).",
            "status": "computed" if page_vars else "no_data",
        }

    def _safe_correlation(self, x: list[float], y: list[float]) -> float:
        """Avoid NaN correlation for underspecified or constant vectors."""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        arr_x = np.asarray(x, dtype=float)
        arr_y = np.asarray(y, dtype=float)
        if np.allclose(arr_y, arr_y[0]):
            return 0.0
        corr = np.corrcoef(arr_x, arr_y)[0, 1]
        if np.isnan(corr):
            return 0.0
        return float(corr)
