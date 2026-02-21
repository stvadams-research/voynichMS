"""
Adversarial and Learnability Metrics

Implementation of metrics for Phase 6C:
- Learnability Gradient
- Decoy Regularity
- Observer Conditioning Sensitivity
"""

import logging
from collections import Counter, defaultdict
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class AdversarialAnalyzer:
    """
    Analyzes whether a corpus exhibits adversarial tuning or indifferent structure.
    """
    def __init__(self):
        pass

    def analyze_learnability_gradient(self, lines: list[list[str]], steps: int = 10) -> dict[str, Any]:
        """
        6.1 Learnability Gradient Test
        Measure prediction accuracy as corpus fraction increases.
        We use a simple Markov-style predictor (Prev, Curr, Pos -> Next).
        """
        def get_accuracy(train_lines, test_lines):
            # Build model
            model = {}
            for line in train_lines:
                for i in range(len(line) - 1):
                    prev = line[i-1] if i > 0 else "<START>"
                    curr = line[i]
                    nxt = line[i+1]
                    state = (prev, curr, i)
                    if state not in model:
                        model[state] = Counter()
                    model[state][nxt] += 1

            # Test model
            correct = 0
            total = 0
            for line in test_lines:
                for i in range(len(line) - 1):
                    prev = line[i-1] if i > 0 else "<START>"
                    curr = line[i]
                    nxt = line[i+1]
                    state = (prev, curr, i)
                    if state in model:
                        prediction = model[state].most_common(1)[0][0]
                        if prediction == nxt:
                            correct += 1
                    total += 1
            return correct / total if total > 0 else 0

        # Split into 80/20 train/test globally, then vary train size
        split_idx = int(len(lines) * 0.8)
        train_pool = lines[:split_idx]
        test_lines = lines[split_idx:]

        gradient = []
        fractions = np.linspace(0.1, 1.0, steps)
        for f in fractions:
            subset_size = int(len(train_pool) * f)
            train_subset = train_pool[:subset_size]
            acc = get_accuracy(train_subset, test_lines)
            gradient.append(float(acc))

        return {
            "fractions": fractions.tolist(),
            "accuracies": gradient,
            "is_monotonic": bool(all(x <= y for x, y in zip(gradient, gradient[1:]))) if len(gradient) > 1 else True,
            "final_accuracy": gradient[-1] if gradient else 0
        }

    def analyze_decoy_regularity(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        6.2 Decoy Regularity Test
        Detect local regularities that fail to generalize.
        Compare rule confidence in small chunks vs global data.
        """
        def get_rules(subset):
            rules = defaultdict(Counter)
            for line in subset:
                for i in range(len(line) - 1):
                    prev = line[i-1] if i > 0 else "<START>"
                    curr = line[i]
                    nxt = line[i+1]
                    rules[(prev, curr, i)][nxt] += 1
            return rules

        chunk_size = 500
        global_rules = get_rules(lines)

        misdirection_scores = []
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i+chunk_size]
            local_rules = get_rules(chunk)

            for state, nxts in local_rules.items():
                if sum(nxts.values()) > 5: # Significant local rule
                    local_top = nxts.most_common(1)[0]
                    local_conf = local_top[1] / sum(nxts.values())

                    if local_conf > 0.8: # Strong local rule
                        # Check global
                        global_nxts = global_rules[state]
                        global_top = global_nxts.most_common(1)[0]
                        global_conf = global_top[1] / sum(global_nxts.values())

                        if global_top[0] != local_top[0]:
                            # Local rule is a decoy!
                            misdirection_scores.append(local_conf)

        return {
            "decoy_rule_count": len(misdirection_scores),
            "mean_decoy_strength": float(np.mean(misdirection_scores)) if misdirection_scores else 0.0,
            "decoy_rate": float(len(misdirection_scores) / len(global_rules)) if global_rules else 0
        }

    def analyze_conditioning_sensitivity(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        6.3 Observer Conditioning Sensitivity
        Test whether adding context paradoxically increases ambiguity.
        Compare H(Next | Curr) vs H(Next | Curr, Prev, Pos).
        """
        c1 = defaultdict(Counter) # Next | Curr
        c2 = defaultdict(Counter) # Next | Curr, Prev, Pos

        for line in lines:
            for i in range(len(line) - 1):
                prev = line[i-1] if i > 0 else "<START>"
                curr = line[i]
                nxt = line[i+1]
                c1[curr][nxt] += 1
                c2[(prev, curr, i)][nxt] += 1

        def get_avg_entropy(counter_dict):
            ents = []
            weights = []
            for nxts in counter_dict.values():
                total = sum(nxts.values())
                probs = np.array([count / total for count in nxts.values()])
                ent = -np.sum(probs * np.log2(probs))
                ents.append(ent)
                weights.append(total)
            return np.average(ents, weights=weights) if ents else 0

        h1 = get_avg_entropy(c1)
        h2 = get_avg_entropy(c2)

        return {
            "h_base": float(h1),
            "h_conditioned": float(h2),
            "entropy_reduction": float(h1 - h2),
            "is_paradoxical": bool(h2 > h1 + 0.01) # Small epsilon for noise
        }

    def run_adversarial_audit(self, lines: list[list[str]]) -> dict[str, Any]:
        return {
            "learnability": self.analyze_learnability_gradient(lines),
            "decoy_regularity": self.analyze_decoy_regularity(lines),
            "conditioning_sensitivity": self.analyze_conditioning_sensitivity(lines)
        }
