import math
from collections import Counter, defaultdict
import numpy as np
from scipy import stats

def entropy(counts):
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

class SelectionDriverAnalyzer:
    """Analyzes hypotheses for what drives scribal selection within windows."""

    def __init__(self, choices, window_contents, corpus_freq):
        """
        Args:
            choices (list): List of choice dictionaries.
            window_contents (dict): Window ID -> list of tokens.
            corpus_freq (dict): Token -> frequency mapping.
        """
        self.choices = choices
        self.window_contents = {int(k): v for k, v in window_contents.items()}
        self.corpus_freq = corpus_freq

    def test_positional_bias(self):
        """Test if chosen_index is biased toward small values (top-of-window)."""
        positions = []
        for c in self.choices:
            if c.get("candidates_count", 0) > 1:
                rel_pos = c["chosen_index"] / (c["candidates_count"] - 1)
                positions.append(rel_pos)

        positions = np.array(positions)
        if len(positions) == 0:
            return {"bits_explained": 0.0, "is_significant": False}

        mean_pos = np.mean(positions)
        median_pos = np.median(positions)
        ks_stat, ks_p = stats.kstest(positions, "uniform")

        # Effect size: how much entropy is reduced vs uniform
        hist, _ = np.histogram(positions, bins=20, range=(0, 1))
        h_observed = entropy(hist.tolist())
        h_uniform = math.log2(20)  # max entropy for 20 bins
        bits_explained = h_uniform - h_observed

        return {
            "mean_relative_position": float(mean_pos),
            "median_relative_position": float(median_pos),
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(ks_p),
            "is_significant": ks_p < 0.01,
            "bits_explained": float(bits_explained),
            "n": len(positions),
            "direction": "top" if mean_pos < 0.45 else ("bottom" if mean_pos > 0.55 else "neutral"),
        }

    def test_bigram_context(self):
        """Test if prev_word reduces entropy of chosen_word within window."""
        window_choices = defaultdict(list)
        for c in self.choices:
            window_choices[c["window_id"]].append(c["chosen_word"])

        h_given_window = 0.0
        total = len(self.choices)
        if total == 0: return {"bits_explained": 0.0, "is_significant": False}

        for _win_id, words in window_choices.items():
            p_window = len(words) / total
            counts = list(Counter(words).values())
            h_given_window += p_window * entropy(counts)

        pair_choices = defaultdict(list)
        for c in self.choices:
            if c.get("prev_word"):
                key = (c["window_id"], c["prev_word"])
                pair_choices[key].append(c["chosen_word"])

        h_given_pair = 0.0
        eligible_total = 0
        eligible_pairs = 0
        for _key, words in pair_choices.items():
            if len(words) >= 5:
                eligible_total += len(words)
                eligible_pairs += 1

        if eligible_total > 0:
            for _key, words in pair_choices.items():
                if len(words) >= 5:
                    p_pair = len(words) / eligible_total
                    counts = list(Counter(words).values())
                    h_given_pair += p_pair * entropy(counts)

        info_gain = h_given_window - h_given_pair if eligible_total > 0 else 0

        return {
            "h_given_window": float(h_given_window),
            "h_given_window_prev": float(h_given_pair),
            "information_gain_bits": float(info_gain),
            "eligible_pairs": eligible_pairs,
            "eligible_observations": eligible_total,
            "is_significant": info_gain > 0.1,
            "bits_explained": float(info_gain),
        }

    def test_suffix_affinity(self):
        """Test if chosen_word shares suffix with prev_word more than expected."""
        observed_matches = 0
        expected_rate_sum = 0.0
        valid_count = 0

        for c in self.choices:
            prev = c.get("prev_word")
            chosen = c.get("chosen_word")
            win_id = c.get("window_id")

            if not prev or not chosen or len(prev) < 2 or len(chosen) < 2:
                continue

            suffix = prev[-2:]
            match = chosen[-2:] == suffix

            win_words = self.window_contents.get(win_id, [])
            matching_in_window = sum(1 for w in win_words if len(w) >= 2 and w[-2:] == suffix)
            expected = matching_in_window / len(win_words) if win_words else 0

            if match:
                observed_matches += 1
            expected_rate_sum += expected
            valid_count += 1

        if valid_count == 0:
            return {"bits_explained": 0.0, "is_significant": False}

        observed_rate = observed_matches / valid_count
        expected_rate = expected_rate_sum / valid_count

        if expected_rate > 0:
            excess = observed_rate / expected_rate
            se = math.sqrt(expected_rate * (1 - expected_rate) / valid_count)
            z = (observed_rate - expected_rate) / se if se > 0 else 0
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        else:
            excess = 0
            z = 0
            p_value = 1.0

        return {
            "observed_match_rate": float(observed_rate),
            "expected_match_rate": float(expected_rate),
            "excess_ratio": float(excess),
            "z_score": float(z),
            "p_value": float(p_value),
            "is_significant": p_value < 0.01,
            "valid_observations": valid_count,
            "bits_explained": float(abs(observed_rate - expected_rate) * math.log2(max(excess, 0.001))) if excess > 0 else 0.0,
        }

    def test_frequency_bias(self):
        """Test if globally frequent words are preferentially chosen within windows."""
        window_word_selections = defaultdict(Counter)
        for c in self.choices:
            window_word_selections[c["window_id"]][c["chosen_word"]] += 1

        freq_ranks = []
        sel_rates = []

        for _win_id, selections in window_word_selections.items():
            total_selections = sum(selections.values())
            for word, sel_count in selections.items():
                sel_rate = sel_count / total_selections
                freq = self.corpus_freq.get(word, 0)
                freq_ranks.append(freq)
                sel_rates.append(sel_rate)

        if len(freq_ranks) < 2:
            return {"bits_explained": 0.0, "is_significant": False}

        rho, p_value = stats.spearmanr(freq_ranks, sel_rates)
        bits_explained = abs(rho) * 0.5

        return {
            "spearman_rho": float(rho),
            "p_value": float(p_value),
            "is_significant": p_value < 0.01,
            "n_word_window_pairs": len(freq_ranks),
            "bits_explained": float(bits_explained),
        }

    def test_recency_bias(self, recent_window=50):
        """Test if recently-used words in the same window are re-chosen more often."""
        last_seen = {}
        recency_scores = []

        for i, c in enumerate(self.choices):
            win_id = c["window_id"]
            word = c["chosen_word"]
            key = (win_id, word)

            if key in last_seen:
                gap = i - last_seen[key]
                recency_scores.append(1 if gap <= recent_window else 0)
            else:
                recency_scores.append(0)
            last_seen[key] = i

        if not recency_scores:
            return {"bits_explained": 0.0, "is_significant": False}

        observed_recent_rate = np.mean(recency_scores)

        # Null expectation via shuffle
        rng = np.random.RandomState(42)
        null_scores = []
        for _ in range(50): # Reduced iterations for speed
            shuffled_last_seen = {}
            null_recency = []
            shuffled_choices = list(self.choices)
            rng.shuffle(shuffled_choices)
            for j, c in enumerate(shuffled_choices):
                key = (c["window_id"], c["chosen_word"])
                if key in shuffled_last_seen:
                    gap = j - shuffled_last_seen[key]
                    null_recency.append(1 if gap <= recent_window else 0)
                else:
                    null_recency.append(0)
                shuffled_last_seen[key] = j
            null_scores.append(np.mean(null_recency))

        null_mean = np.mean(null_scores)
        null_std = np.std(null_scores)
        z = (observed_recent_rate - null_mean) / null_std if null_std > 0 else 0
        advantage = observed_recent_rate - null_mean

        return {
            "observed_recent_rate": float(observed_recent_rate),
            "null_mean": float(null_mean),
            "null_std": float(null_std),
            "recency_advantage": float(advantage),
            "z_score": float(z),
            "is_significant": abs(z) > 2.576,
            "recent_window": recent_window,
            "bits_explained": float(abs(advantage) * 2),
        }
