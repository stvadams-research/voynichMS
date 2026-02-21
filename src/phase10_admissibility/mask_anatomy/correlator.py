"""
Thematic Mask Correlator

Tests if different illustration sections (Botanical, Zodiac, etc.) 
use distinct mask profiles.
"""

from collections import defaultdict
from typing import Any

import numpy as np
from scipy import stats


class ThematicMaskCorrelator:
    """
    Correlates z-score residuals with thematic sections.
    """
    def __init__(self, illustration_data: dict[str, Any]):
        self.folio_to_section = {}
        for fid, f_data in illustration_data.get("folios", {}).items():
            self.folio_to_section[fid] = f_data.get("section", "unknown")

    def correlate(self, sliding_series: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Groups residuals by section and performs statistical significance tests.
        """
        section_residuals = defaultdict(list)
        
        for point in sliding_series:
            # Map the point to a section (use the first folio in the window)
            fid = point['folio_ids'][0] if point['folio_ids'] else "unknown"
            section = self.folio_to_section.get(fid, "unknown")
            section_residuals[section].append(point['z_score'])
            
        stats_by_section = {}
        groups = []
        labels = []
        
        for section, residuals in section_residuals.items():
            if len(residuals) < 2: continue
            
            stats_by_section[section] = {
                "mean_z": float(np.mean(residuals)),
                "std_z": float(np.std(residuals)),
                "count": len(residuals)
            }
            groups.append(residuals)
            labels.append(section)
            
        # One-way ANOVA to see if means differ significantly
        f_stat = 0.0
        p_val = 1.0
        if len(groups) > 1:
            f_stat, p_val = stats.f_oneway(*groups)
            
        return {
            "stats_by_section": stats_by_section,
            "anova": {
                "f_statistic": float(f_stat),
                "p_value": float(p_val),
                "is_significant": bool(p_val < 0.01)
            }
        }
