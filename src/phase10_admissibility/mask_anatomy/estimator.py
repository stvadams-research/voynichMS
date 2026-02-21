"""
Mask State Estimator (Hardware Bottleneck)

Quantifies the complexity of the physical tool required to explain 
the observed mask behavior.
"""

import math
from typing import Any

import numpy as np


class MaskStateEstimator:
    """
    Estimates the 'effective bits' of the persistent context mask.
    """
    def estimate_bottleneck(self, sliding_series: list[dict[str, Any]]) -> dict[str, Any]:
        residuals = np.array([r['residual'] for r in sliding_series])

        # Variance of the residuals represents the 'error' of a single-state model
        variance_unmasked = np.var(residuals)

        # We estimate information gain required to reach 'normal' variance (sigma < 1.0)
        # Information (bits) = log2(Var_unmasked / Var_target)
        # We assume target variance is 1/10th of unmasked for high significance
        bits_required = 0.0
        if variance_unmasked > 0:
            bits_required = 0.5 * math.log2(variance_unmasked / (variance_unmasked * 0.1)) # Theoretical lower bound

        # Effective discrete states = 2^bits
        effective_states = 2**bits_required

        return {
            "residual_variance": float(variance_unmasked),
            "estimated_mask_bits": float(bits_required),
            "effective_discrete_states": float(effective_states),
            "hardware_conjecture": self._conjecture_hardware(effective_states)
        }

    def _conjecture_hardware(self, states: float) -> str:
        if states < 2.5:
            return "Binary Toggle (e.g. 2-sided card, Currier A/B)"
        if states < 8:
            return "Low-Complexity Tool (e.g. 4-6 state wheel or grille)"
        if states < 32:
            return "Medium-Complexity Device (e.g. 20-30 page reference manual)"
        return "High-Complexity System (e.g. multi-layered combinatorial table)"
