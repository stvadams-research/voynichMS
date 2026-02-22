import math
from collections import Counter, defaultdict
import numpy as np

def entropy_bits(counts):
    """Shannon entropy of a count distribution in bits."""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h

def conditional_entropy(groups):
    """Weighted average entropy across groups: H(Y | X) = sum p(x) H(Y|X=x)."""
    total = sum(len(v) for v in groups.values())
    if total == 0:
        return 0.0
    h = 0.0
    for words in groups.values():
        p_group = len(words) / total
        counts = list(Counter(words).values())
        h += p_group * entropy_bits(counts)
    return h

def position_bucket(token_pos, n_buckets=5):
    """Bin token position into buckets."""
    if token_pos <= 0: return 0
    if token_pos <= 2: return 1
    if token_pos <= 5: return 2
    if token_pos <= 9: return 3
    return 4

class ResidualBandwidthAnalyzer:
    """Analyzes residual bandwidth after accounting for known drivers."""

    def __init__(self, choices):
        """
        Args:
            choices (list): List of choice dictionaries.
        """
        self.choices = choices
        self.choices_with_recency = self._prepare_recency()

    def _prepare_recency(self):
        last_seen = {}
        enriched = []
        for i, c in enumerate(self.choices):
            key = (c.get("window_id"), c.get("chosen_word"))
            is_recent = 0
            if key in last_seen and (i - last_seen[key]) <= 50:
                is_recent = 1
            last_seen[key] = i
            enriched.append({**c, "is_recent": is_recent})
        return enriched

    def compute_entropy_chain(self):
        """Progressively condition choice entropy on each driver."""
        # 1. H(choice | window)
        groups_w = defaultdict(list)
        for c in self.choices:
            groups_w[c.get("window_id")].append(c.get("chosen_word"))
        h_window = conditional_entropy(groups_w)

        # 2. H(choice | window, prev_word)
        groups_wp = defaultdict(list)
        for c in self.choices:
            prev = c.get("prev_word") or "__none__"
            groups_wp[(c.get("window_id"), prev)].append(c.get("chosen_word"))
        h_window_prev = conditional_entropy(groups_wp)

        # 3. H(choice | window, prev_word, position)
        groups_wpp = defaultdict(list)
        for c in self.choices:
            prev = c.get("prev_word") or "__none__"
            pos_b = position_bucket(c.get("token_pos", 0))
            groups_wpp[(c.get("window_id"), prev, pos_b)].append(c.get("chosen_word"))
        h_window_prev_pos = conditional_entropy(groups_wpp)

        # 4. H(choice | window, prev, pos, recency)
        groups_wppr = defaultdict(list)
        for c in self.choices_with_recency:
            prev = c.get("prev_word") or "__none__"
            pos_b = position_bucket(c.get("token_pos", 0))
            groups_wppr[(c.get("window_id"), prev, pos_b, c["is_recent"])].append(c.get("chosen_word"))
        h_window_prev_pos_rec = conditional_entropy(groups_wppr)

        # 5. H(choice | all drivers including suffix)
        groups_wpprs = defaultdict(list)
        for c in self.choices_with_recency:
            prev = c.get("prev_word") or "__none__"
            pos_b = position_bucket(c.get("token_pos", 0))
            suffix = prev[-2:] if prev and len(prev) >= 2 and prev != "__none__" else "__"
            groups_wpprs[(c.get("window_id"), prev, pos_b, c["is_recent"], suffix)].append(c.get("chosen_word"))
        h_all_drivers = conditional_entropy(groups_wpprs)

        chain = [
            {"conditioning": "window", "h": h_window},
            {"conditioning": "window + prev_word", "h": h_window_prev},
            {"conditioning": "window + prev_word + position", "h": h_window_prev_pos},
            {"conditioning": "window + prev_word + position + recency", "h": h_window_prev_pos_rec},
            {"conditioning": "window + prev_word + position + recency + suffix", "h": h_all_drivers},
        ]
        return chain

    def check_independence(self, chain):
        """Checks independence of drivers."""
        h_window = chain[0]["h"]
        h_all = chain[-1]["h"]
        joint_reduction = h_window - h_all
        marginal_sum = 2.4316 + 0.6365 + 0.2163 + 0.1629 + 0.1234  # approximate from 15D
        
        overlap = marginal_sum - joint_reduction
        overlap_pct = (overlap / marginal_sum * 100) if marginal_sum > 0 else 0
        
        return {
            "joint_reduction_bits": joint_reduction,
            "marginal_sum_bits": marginal_sum,
            "overlap_bits": overlap,
            "overlap_pct": overlap_pct,
            "drivers_mostly_independent": overlap < 0.5
        }
