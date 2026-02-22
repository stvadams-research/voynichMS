class BandwidthAuditor:
    """Audits the steganographic bandwidth of the choice stream."""

    REFERENCE_BANDWIDTHS = {
        "English prose (Shannon)": 1.3,
        "English words (semantic)": 8.0,
        "Latin Vulgate (per char)": 4.1,
        "Random coin flip": 1.0,
    }

    def __init__(self, bias_data, effort_data=None):
        """
        Args:
            bias_data (dict): Selection bias data from Phase 14P.
            effort_data (dict): Effort correlation data from Phase 16B (optional).
        """
        self.bias_data = bias_data
        self.effort_data = effort_data or {}

    def audit(self, stego_threshold=3.0):
        """
        Calculates realized bandwidth and compares against thresholds.
        
        Returns:
            dict: Audit results.
        """
        num_decisions = self.bias_data.get("admissible_choices", 0)
        observed_entropy = self.bias_data.get("real_choice_entropy", 0.0)
        uniform_entropy = self.bias_data.get("uniform_random_entropy", 0.0)
        
        realized_capacity_bpw = observed_entropy
        ergonomic_overhead_bpw = uniform_entropy - observed_entropy
        
        total_capacity_bits = num_decisions * realized_capacity_bpw
        
        has_sufficient_bandwidth = realized_capacity_bpw >= stego_threshold
        
        return {
            "num_decisions": num_decisions,
            "max_bandwidth_bpw": uniform_entropy,
            "realized_bandwidth_bpw": realized_capacity_bpw,
            "ergonomic_overhead_bpw": ergonomic_overhead_bpw,
            "total_capacity_bits": total_capacity_bits,
            "total_capacity_kb": total_capacity_bits / 8192,
            "stego_threshold_bpw": stego_threshold,
            "has_sufficient_bandwidth": has_sufficient_bandwidth,
            "ergonomic_rho": self.effort_data.get("correlation_rho"),
        }
