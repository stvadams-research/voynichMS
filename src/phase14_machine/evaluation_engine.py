"""
Voynich Machine Evaluation Engine (Phase 14D)

A centralized measurement framework for calculating model coverage, 
admissibility, MDL (Description Length), and overgeneration.
"""

import math
from collections import Counter, defaultdict
from typing import Any


class EvaluationEngine:
    """
    Standardizes measurement logic for Voynich structural models.

    Attributes:
        vocab: The set of tokens that define the model's lexicon scope (lexicon clamp).
    """

    SUFFIX_PRIORITY = ["dy", "in", "y", "or", "ol", "al", "ar", "r",
                       "am", "an", "s", "m", "d", "l", "o", "ey"]

    @staticmethod
    def resolve_oov_window(word: str, suffix_window_map: dict[str, int]) -> int | None:
        """Predict window for an OOV word via suffix class.

        Args:
            word: The out-of-vocabulary token.
            suffix_window_map: Mapping from suffix string to predicted window ID.

        Returns:
            Predicted window ID, or None if no suffix matches.
        """
        for sfx in EvaluationEngine.SUFFIX_PRIORITY:
            if word.endswith(sfx) and len(word) > len(sfx) and sfx in suffix_window_map:
                return suffix_window_map[sfx]
        return None

    def __init__(self, vocab: set[str]):
        """
        Initializes the evaluation engine with a fixed vocabulary.
        
        Args:
            vocab: A set of strings representing the allowed vocabulary.
        """
        self.vocab = vocab

    def calculate_coverage(self, tokens: list[str]) -> float:
        """
        Calculates the percentage of tokens in a list that are covered by the lexicon clamp.
        
        Args:
            tokens: A list of tokens to check.
            
        Returns:
            The coverage ratio as a float (0.0 to 1.0).
        """
        if not tokens:
            return 0.0
        covered = sum(1 for t in tokens if t in self.vocab)
        return covered / len(tokens)

    def calculate_admissibility(self,
                               lines: list[list[str]],
                               lattice_map: dict[str, int],
                               window_contents: dict[int, list[str]],
                               fuzzy_suffix: bool = False,
                               suffix_window_map: dict[str, int] | None = None) -> dict[str, Any]:
        """
        Measures how often real transitions follow the physical lattice constraints.
        Reports both strict (offset=0 only) and drift (±1) admissibility rates,
        plus a chance baseline for each.

        Args:
            lines: The real manuscript lines (tokens).
            lattice_map: Mapping from word to its predicted next window ID.
            window_contents: Mapping from window ID to the list of words in that window.
            fuzzy_suffix: If True, allows admissibility if any word in the target window
                         shares the same suffix as the actual word (simulates scribe bias).
            suffix_window_map: Optional mapping from suffix → predicted window ID for
                OOV recovery (Phase 14O). When provided, OOV words are assigned windows
                via suffix class instead of being skipped.

        Returns:
            A dictionary containing strict and drift admissibility rates,
            chance baselines, and total clamped tokens processed.
            When suffix_window_map is provided, also includes oov_total,
            oov_recovered, and consolidated_admissibility.
        """
        strict_admissible = 0
        drift_admissible = 0
        total_transitions = 0
        oov_total = 0
        oov_recovered = 0
        oov_admissible = 0
        current_window = 0

        num_wins = len(window_contents)
        suffixes = ["dy", "in", "y", "m", "ol"]

        # Precompute chance baseline: probability a random vocab word
        # falls in k windows by vocabulary overlap
        all_window_words = set()
        for _wid, words in window_contents.items():
            all_window_words.update(words)
        total_lattice_vocab = len(all_window_words)
        total_words = sum(len(v) for v in window_contents.values())
        avg_window_size = total_words / num_wins if num_wins > 0 else 0
        strict_chance = avg_window_size / total_lattice_vocab if total_lattice_vocab > 0 else 0
        drift_chance = min(1.0, 3 * strict_chance)  # 3 windows checked

        for line in lines:
            for word in line:
                if word not in self.vocab:
                    # OOV recovery via suffix map
                    if suffix_window_map is not None:
                        oov_total += 1
                        predicted_win = self.resolve_oov_window(word, suffix_window_map)
                        if predicted_win is not None:
                            oov_recovered += 1
                            # Check if the predicted window is admissible (±1 drift)
                            for offset in [-1, 0, 1]:
                                check_win = (current_window + offset) % num_wins
                                if check_win == predicted_win:
                                    oov_admissible += 1
                                    current_window = predicted_win
                                    break
                            else:
                                # Not admissible — snap to predicted window
                                current_window = predicted_win
                        # If no suffix match, skip as before
                    continue

                total_transitions += 1
                is_strict = False
                is_drift = False

                # Check strict (offset=0 only)
                win_words = window_contents.get(current_window, [])
                if word in win_words:
                    is_strict = True
                    is_drift = True

                # Check drift (±1) if not already strict
                if not is_drift:
                    for offset in [-1, 1]:
                        check_win = (current_window + offset) % num_wins
                        drift_words = window_contents.get(check_win, [])
                        if word in drift_words:
                            is_drift = True
                            current_window = check_win
                            break

                        if fuzzy_suffix:
                            for s in suffixes:
                                if word.endswith(s) and any(
                                    w.endswith(s) for w in drift_words
                                ):
                                        is_drift = True
                                        current_window = check_win
                                        break
                            if is_drift:
                                break

                if is_strict:
                    strict_admissible += 1
                    drift_admissible += 1
                    current_window = lattice_map.get(word, (current_window + 1) % num_wins)
                elif is_drift:
                    drift_admissible += 1
                    current_window = lattice_map.get(word, (current_window + 1) % num_wins)
                else:
                    # Snap to real window if word is known, to recover
                    if word in lattice_map:
                        current_window = lattice_map[word]

        n = total_transitions
        strict_rate = strict_admissible / n if n > 0 else 0
        drift_rate = drift_admissible / n if n > 0 else 0
        result = {
            "strict_admissibility": strict_rate,
            "drift_admissibility": drift_rate,
            "admissibility_rate": drift_rate,
            "strict_chance_baseline": strict_chance,
            "drift_chance_baseline": drift_chance,
            "total_clamped_tokens": n,
        }

        if suffix_window_map is not None:
            total_consolidated = n + oov_recovered
            consolidated_admissible = drift_admissible + oov_admissible
            result["oov_total"] = oov_total
            result["oov_recovered"] = oov_recovered
            result["oov_admissible"] = oov_admissible
            result["consolidated_admissibility"] = (
                consolidated_admissible / total_consolidated
                if total_consolidated > 0 else 0
            )

        return result

    def calculate_markov_residual_entropy(self, tokens: list[str]) -> float:
        """
        Calculates the conditional entropy H(Y|X) of a token sequence (Order 1).
        
        Used as a baseline for MDL comparison.
        
        Args:
            tokens: A list of tokens.
            
        Returns:
            The total bits required to encode the data given a Markov-O1 model.
        """
        if not tokens:
            return 0.0

        # 1. Calculate P(x)
        counts = Counter(tokens)
        total = len(tokens)
        px = {t: c/total for t, c in counts.items()}

        # 2. Calculate P(y | x)
        transitions = defaultdict(Counter)
        for i in range(len(tokens)-1):
            u, v = tokens[i], tokens[i+1]
            if u in self.vocab and v in self.vocab:
                transitions[u][v] += 1

        # 3. Calculate conditional entropy
        cond_entropy = 0.0
        for x, next_tokens in transitions.items():
            total_x = sum(next_tokens.values())
            # H(Y | X=x)
            hx = -sum((c/total_x) * math.log2(c/total_x) for c in next_tokens.values())
            cond_entropy += px[x] * hx

        return float(cond_entropy * total)

    def calculate_mdl_bits(self,
                           tokens: list[str],
                           model_params: int,
                           is_markov: bool = False) -> dict[str, float]:
        """
        Calculates the total description length L(total) = L(model) + L(data | model).
        
        Args:
            tokens: The sequence of tokens to encode.
            model_params: The number of parameters in the model.
            is_markov: If True, uses conditional entropy for data encoding cost.
            
        Returns:
            A dictionary with bits for model, data, and total length.
        """
        # L(model) - Assumes 10 bits per parameter (standard approximation)
        param_bits = model_params * 10

        # L(data | model)
        if is_markov:
            data_bits = self.calculate_markov_residual_entropy(tokens)
        else:
            # For the lattice, use unigram entropy as a conservative upper bound
            # In a more precise implementation, this would be H(Word | Window)
            clamped_tokens = [t for t in tokens if t in self.vocab]
            if not clamped_tokens:
                data_bits = 0.0
            else:
                counts = Counter(clamped_tokens)
                total = len(clamped_tokens)
                data_bits = -sum(c * math.log2(c/total) for c in counts.values())

        return {
            "l_model": float(param_bits),
            "l_data_given_model": float(data_bits),
            "l_total": float(param_bits + data_bits)
        }

    def calculate_overgeneration(self,
                                 syn_lines: list[list[str]],
                                 real_lines: list[list[str]]) -> dict[str, Any]:
        """
        Measures sequential overgeneration (BUR/TUR) within the lexicon clamp.
        
        Args:
            syn_lines: Generated synthetic lines.
            real_lines: Actual manuscript lines.
            
        Returns:
            A dictionary mapping BUR (Bigram Unattested Rate) and TUR (Trigram Unattested Rate)
            to their respective counts and rates.
        """
        def get_ngrams(lines: list[list[str]], n: int) -> set[tuple[str, ...]]:
            ngrams = set()
            for line in lines:
                for i in range(len(line)-n+1):
                    ngram = tuple(line[i:i+n])
                    if all(t in self.vocab for t in ngram):
                        ngrams.add(ngram)
            return ngrams

        res = {}
        for n, label in [(2, "BUR"), (3, "TUR")]:
            real_ng = get_ngrams(real_lines, n)
            syn_ng = get_ngrams(syn_lines, n)

            # Unattested but "legal" according to the machine
            unattested = syn_ng - real_ng
            rate = len(unattested) / len(syn_ng) if syn_ng else 0

            res[label] = {
                "real_count": len(real_ng),
                "syn_count": len(syn_ng),
                "unattested_count": len(unattested),
                "rate": rate
            }
        return res
