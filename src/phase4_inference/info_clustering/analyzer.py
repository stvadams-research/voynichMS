"""
Method A: Information Clustering (Montemurro & Zanette style)

Calculates the information content of words relative to their 
distribution across sections.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import math
import logging
logger = logging.getLogger(__name__)

class MontemurroAnalyzer:
    """
    Analyzes the 'topical' information of tokens based on section distributions.
    """
    def __init__(self, num_sections: int = 20):
        self.num_sections = num_sections

    def calculate_information(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Calculate information per word about section identity.
        
        Formula: i(w) = sum_s p(s|w) * log2( p(s|w) / p(s) )
        """
        if not tokens:
            logger.warning("MontemurroAnalyzer.calculate_information received no tokens")
            return {
                "status": "no_data",
                "metrics": {},
                "num_tokens": 0,
                "num_unique": 0,
                "word_info": [],
                "top_keywords": [],
            }

        # 1. Partition tokens into sections
        section_size = len(tokens) // self.num_sections
        word_section_counts = defaultdict(lambda: Counter())
        section_counts = Counter()
        
        for i, token in enumerate(tokens):
            section_idx = min(i // section_size, self.num_sections - 1)
            word_section_counts[token][section_idx] += 1
            section_counts[section_idx] += 1
            
        total_tokens = len(tokens)
        p_s = {s: count / total_tokens for s, count in section_counts.items()}
        
        # 2. Calculate information per word
        word_info = {}
        global_counts = Counter(tokens)
        
        for word, s_counts in word_section_counts.items():
            # Frequency filter: ignore rare words that produce noise in info metrics
            if global_counts[word] < 5:
                continue
                
            total_w = sum(s_counts.values())
            # Probability of section s given word w
            p_s_w = {s: count / total_w for s, count in s_counts.items()}
            
            # i(w) = sum_s p(s|w) log2( p(s|w) / p(s) )
            info_w = 0.0
            for s, p_sw in p_s_w.items():
                if p_sw > 0:
                    info_w += p_sw * math.log2(p_sw / p_s[s])
            
            word_info[word] = info_w
            
        # 3. Sort by information
        sorted_info = sorted(word_info.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "num_tokens": total_tokens,
            "num_unique": len(global_counts),
            "word_info": sorted_info,
            "top_keywords": sorted_info[:50]
        }

    def get_summary_metrics(self, info_results: Dict[str, Any]) -> Dict[str, float]:
        """Compute aggregate metrics like average information."""
        sorted_info = info_results.get("word_info", [])
        if not sorted_info:
            return {"avg_info": 0.0, "max_info": 0.0, "num_keywords": 0}
            
        avg_info = sum(val for word, val in sorted_info) / len(sorted_info)
        max_info = sorted_info[0][1] if sorted_info else 0.0
        
        return {
            "avg_info": avg_info,
            "max_info": max_info,
            "num_keywords": len([w for w, i in sorted_info if i > 1.0]) # Arbitrary threshold
        }
