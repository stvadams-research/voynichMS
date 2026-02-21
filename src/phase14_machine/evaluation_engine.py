"""
Voynich Machine Evaluation Engine (Phase 14D)

A centralized measurement framework for calculating model coverage, 
admissibility, MDL (Description Length), and overgeneration.
"""

import math
from typing import List, Set, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict

class EvaluationEngine:
    """
    Standardizes measurement logic for Voynich structural models.
    
    Attributes:
        vocab: The set of tokens that define the model's lexicon scope (lexicon clamp).
    """
    def __init__(self, vocab: Set[str]):
        """
        Initializes the evaluation engine with a fixed vocabulary.
        
        Args:
            vocab: A set of strings representing the allowed vocabulary.
        """
        self.vocab = vocab 

    def calculate_coverage(self, tokens: List[str]) -> float:
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
                               lines: List[List[str]], 
                               lattice_map: Dict[str, int], 
                               window_contents: Dict[int, List[str]], 
                               fuzzy_suffix: bool = False) -> Dict[str, Any]:
        """
        Measures how often real transitions follow the physical lattice constraints.
        
        Args:
            lines: The real manuscript lines (tokens).
            lattice_map: Mapping from word to its predicted next window ID.
            window_contents: Mapping from window ID to the list of words in that window.
            fuzzy_suffix: If True, allows admissibility if any word in the target window 
                         shares the same suffix as the actual word (simulates scribe bias).
                         
        Returns:
            A dictionary containing the admissibility rate and total clamped tokens processed.
        """
        admissible_count = 0
        total_transitions = 0
        current_window = 0
        
        suffixes = ["dy", "in", "y", "m", "ol"]
        
        for line in lines:
            for word in line:
                if word not in self.vocab: 
                    continue
                
                total_transitions += 1
                is_valid = False
                
                # Admissible if word is in current window or adjacent (drift)
                num_wins = len(window_contents)
                for offset in [-1, 0, 1]:
                    check_win = (current_window + offset) % num_wins
                    win_words = window_contents.get(check_win, [])
                    if word in win_words:
                        is_valid = True
                        current_window = check_win
                        break
                    
                    if fuzzy_suffix:
                        # Check if ANY word in window has same suffix (Scribe Suffix Bias)
                        for s in suffixes:
                            if word.endswith(s):
                                if any(w.endswith(s) for w in win_words):
                                    is_valid = True
                                    current_window = check_win
                                    break
                        if is_valid: 
                            break
                
                if is_valid:
                    admissible_count += 1
                    # Advance to next predicted window
                    current_window = lattice_map.get(word, (current_window + 1) % num_wins)
                else:
                    # Snap to real window if word is known, to recover from the error
                    if word in lattice_map:
                        current_window = lattice_map[word]
                        
        return {
            "admissibility_rate": admissible_count / total_transitions if total_transitions > 0 else 0,
            "total_clamped_tokens": total_transitions
        }

    def calculate_markov_residual_entropy(self, tokens: List[str]) -> float:
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
                           tokens: List[str], 
                           model_params: int, 
                           is_markov: bool = False) -> Dict[str, float]:
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
                                 syn_lines: List[List[str]], 
                                 real_lines: List[List[str]]) -> Dict[str, Any]:
        """
        Measures sequential overgeneration (BUR/TUR) within the lexicon clamp.
        
        Args:
            syn_lines: Generated synthetic lines.
            real_lines: Actual manuscript lines.
            
        Returns:
            A dictionary mapping BUR (Bigram Unattested Rate) and TUR (Trigram Unattested Rate)
            to their respective counts and rates.
        """
        def get_ngrams(lines: List[List[str]], n: int) -> Set[Tuple[str, ...]]:
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
