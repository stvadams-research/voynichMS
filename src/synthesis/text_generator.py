"""
Track 3A: Text Continuation Synthesis

Constrained text generators for pharmaceutical section continuation.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import random
import math
import hashlib
from pathlib import Path

from synthesis.interface import (
    SectionProfile,
    ContinuationConstraints,
    SyntheticPage,
    GeneratorType,
)
from foundation.config import POSITIONAL_BIAS_PROBABILITY


def _stable_seed_fragment(value: Any, modulus: int = 1_000_000) -> int:
    """Return a stable integer fragment derived from a value."""
    digest = hashlib.sha256(repr(value).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


@dataclass
class MarkovState:
    """State in a Markov chain."""
    context: Tuple[str, ...]
    transitions: Dict[str, int] = field(default_factory=dict)
    total: int = 0
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def add_transition(self, token: str) -> None:
        self.transitions[token] = self.transitions.get(token, 0) + 1
        self.total += 1

    def sample(self) -> str:
        """Sample next token based on transition probabilities."""
        if self.total == 0:
            return "<UNK>"

        r = self.rng.random() * self.total
        cumulative = 0
        for token, count in self.transitions.items():
            cumulative += count
            if r <= cumulative:
                return token

        return list(self.transitions.keys())[-1]


class ConstrainedMarkovGenerator:
    """
    Variable-order Markov generator with positional constraints.

    Trained only on pharmaceutical section pages.
    Enforces locality window 2-4.
    """

    def __init__(self, order: int = 2, locality_window: Tuple[int, int] = (2, 4), seed: Optional[int] = None):
        self.order = order
        self.locality_window = locality_window
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Neutral vocabulary to avoid bias
        from synthesis.profile_extractor import NeutralTokenGenerator
        self.token_gen = NeutralTokenGenerator(seed=seed)
        self.VOCABULARY = self.token_gen.generate_tokens(50)
        
        self.POSITION_BIAS = {
            "start": self.token_gen.generate_tokens(6),
            "middle": self.token_gen.generate_tokens(7),
            "end": self.token_gen.generate_tokens(8),
        }
        
        self.states: Dict[Tuple[str, ...], MarkovState] = {}
        self.start_contexts: List[Tuple[str, ...]] = []

    def train(self, section_profile: SectionProfile) -> None:
        """
        Train on pharmaceutical section.
        """
        # Generate training sequences from simulated page data
        for i, page in enumerate(section_profile.pages):
            for j in range(page.jar_count):
                # Generate a typical jar's worth of text
                lines = page.total_lines // max(1, page.jar_count)
                words_per_line = page.total_words // max(1, page.total_lines)

                for k in range(lines):
                    line_seed = self.seed + (i*100 + j*10 + k) if self.seed is not None else None
                    sequence = self._generate_training_line(words_per_line, k, lines, seed=line_seed)
                    self._train_on_sequence(sequence)

    def _generate_training_line(self, token_count: int, line_idx: int,
                                total_lines: int, seed: Optional[int] = None) -> List[str]:
        """Generate a training line with positional constraints."""
        line_rng = random.Random(seed)
        line = []
        for i in range(token_count):
            # Determine position
            if i == 0:
                position = "start"
            elif i == token_count - 1:
                position = "end"
            else:
                position = "middle"

            # Sample with positional bias
            if line_rng.random() < POSITIONAL_BIAS_PROBABILITY:
                candidates = self.POSITION_BIAS[position]
                token = line_rng.choice(candidates)
            else:
                token = line_rng.choice(self.VOCABULARY)

            line.append(token)

        return line

    def _train_on_sequence(self, sequence: List[str]) -> None:
        """Train Markov chain on a sequence."""
        if len(sequence) < self.order + 1:
            return

        # Record start context
        start = tuple(sequence[:self.order])
        if start not in self.start_contexts:
            self.start_contexts.append(start)

        # Build transitions
        for i in range(len(sequence) - self.order):
            context = tuple(sequence[i:i + self.order])
            next_token = sequence[i + self.order]

            if context not in self.states:
                state_seed = (
                    self.seed + _stable_seed_fragment(context)
                    if self.seed is not None
                    else None
                )
                self.states[context] = MarkovState(context=context, seed=state_seed)

            self.states[context].add_transition(next_token)

    def generate_line(self, target_length: int,
                      preceding_tokens: Optional[List[str]] = None,
                      position_in_block: str = "middle") -> List[str]:
        """
        Generate a single line of text.
        """
        line = []

        # Initialize context
        if preceding_tokens and len(preceding_tokens) >= self.order:
            context = tuple(preceding_tokens[-self.order:])
        elif self.start_contexts:
            context = self.rng.choice(self.start_contexts)
        else:
            context = tuple(self.rng.choices(self.VOCABULARY, k=self.order))

        line.extend(context)

        # Generate tokens
        while len(line) < target_length:
            if context in self.states:
                next_token = self.states[context].sample()
            else:
                # Fallback: sample with positional bias
                token_pos = len(line)
                if token_pos == 0:
                    position = "start"
                elif token_pos >= target_length - 1:
                    position = "end"
                else:
                    position = "middle"

                if self.rng.random() < 0.3:
                    next_token = self.rng.choice(self.POSITION_BIAS[position])
                else:
                    next_token = self.rng.choice(self.VOCABULARY)

            line.append(next_token)
            context = tuple(line[-self.order:])

        return line[:target_length]

    def generate_text_block(self, constraints: ContinuationConstraints,
                            num_lines: int, words_per_line: int) -> List[List[str]]:
        """Generate a complete text block for a jar."""
        block = []
        preceding = None

        for i in range(num_lines):
            if i == 0:
                position = "start"
            elif i == num_lines - 1:
                position = "end"
            else:
                position = "middle"

            line = self.generate_line(
                target_length=words_per_line,
                preceding_tokens=preceding,
                position_in_block=position,
            )
            block.append(line)
            preceding = line

        return block


from synthesis.generators.grammar_based import GrammarBasedGenerator
import logging
logger = logging.getLogger(__name__)


class TextContinuationGenerator:
    """
    High-level text continuation generator.

    Manages multiple generator types and enforces constraints.
    Now uses Step 3.2.3 Grammar-Based engine.
    """

    def __init__(self, section_profile: SectionProfile, seed: Optional[int] = None):
        self.section_profile = section_profile
        self.seed = seed
        # Intentional controller bypass: this generator keeps a local seeded RNG
        # to avoid mutating module-level global random state.
        self.rng = random.Random(seed)
        self.constraints = ContinuationConstraints(section_profile=section_profile)

        # Initialize Grammar-Based generator (3.2.3)
        grammar_path = Path("data/derived/voynich_grammar.json")
        if not grammar_path.exists():
            # Fallback to legacy simulated words logic if grammar not extracted yet
            self.grammar_generator = None
            from synthesis.profile_extractor import NeutralTokenGenerator
            self.token_gen = NeutralTokenGenerator(seed=seed)
        else:
            self.grammar_generator = GrammarBasedGenerator(grammar_path, seed=seed)

    def generate_page(self, gap_id: str, seed: Optional[int] = None) -> SyntheticPage:
        """
        Generate a complete synthetic page.
        """
        # Intentional controller bypass: page-level local RNG keeps generation
        # deterministic while isolating state from unrelated modules.
        page_rng = random.Random(seed) if seed is not None else self.rng

        # Determine page structure from section profile
        jar_count = page_rng.randint(
            self.section_profile.jar_count_range[0],
            self.section_profile.jar_count_range[1],
        )

        lines_per_jar = page_rng.randint(
            self.section_profile.lines_per_block_range[0],
            self.section_profile.lines_per_block_range[1],
        )

        words_per_line = page_rng.randint(
            self.section_profile.words_per_line_range[0],
            self.section_profile.words_per_line_range[1],
        )

        # Generate text blocks for each jar
        text_blocks = []
        for i in range(jar_count):
            if self.grammar_generator:
                block = self.grammar_generator.generate_block(
                    num_lines=lines_per_jar,
                    words_per_line=words_per_line
                )
            else:
                # Fallback to neutral tokens
                tokens = self.token_gen.generate_tokens(2)
                block = [tokens * (words_per_line // 2) for _ in range(lines_per_jar)]
                
            # Flatten to word list per jar for SyntheticPage format
            words = [word for line in block for word in line]
            text_blocks.append(words)

        # Create synthetic page
        page = SyntheticPage(
            page_id=f"SYNTHETIC_{gap_id}_{seed or page_rng.randint(0, 99999):05d}",
            gap_id=gap_id,
            generator_type=GeneratorType.WORD_LEVEL,
            generator_params={
                "engine": "grammar_based_v1",
            },
            random_seed=seed or 0,
            jar_count=jar_count,
            text_blocks=text_blocks,
        )

        # Compute metrics
        page.metrics = self._compute_metrics(page, seed=seed)
        page.generator_params["metric_calculation_method"] = page.metrics.get(
            "calculation_method",
            "computed",
        )

        # Check constraints
        passed, violations = self.constraints.check_text(page.metrics)
        page.constraints_satisfied = passed
        page.constraint_violations = violations

        # Compute hash for uniqueness
        page.compute_hash()

        return page

    def _compute_metrics(self, page: SyntheticPage, seed: Optional[int] = None) -> Dict[str, Any]:
        """Compute structural metrics directly from generated page content."""
        all_words = []
        for block in page.text_blocks:
            all_words.extend(block)

        if not all_words:
            return {"calculation_method": "computed", "word_count": 0}

        # Word length
        mean_length = sum(len(w) for w in all_words) / len(all_words) if len(all_words) > 0 else 0

        # Repetition rate
        unique = len(set(all_words))
        repetition = 1 - (unique / len(all_words)) if len(all_words) > 0 else 0

        # Locality proxy: mean distance between repeated token occurrences.
        token_positions: Dict[str, List[int]] = defaultdict(list)
        for idx, token in enumerate(all_words):
            token_positions[token].append(idx)
        spacings: List[int] = []
        for positions in token_positions.values():
            if len(positions) > 1:
                for i in range(1, len(positions)):
                    spacings.append(positions[i] - positions[i - 1])
        locality = (sum(spacings) / len(spacings)) if spacings else float(len(all_words))

        # Information density proxy: Shannon entropy of token distribution.
        counts = Counter(all_words)
        total = len(all_words)
        info_density = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                info_density -= p * math.log2(p)

        # Positional entropy proxy computed from token-initial and token-final chars.
        pos_counts = {"start": Counter(), "mid": Counter(), "end": Counter()}
        for token in all_words:
            if not token:
                continue
            pos_counts["start"][token[0]] += 1
            pos_counts["end"][token[-1]] += 1
            if len(token) > 2:
                for char in token[1:-1]:
                    pos_counts["mid"][char] += 1

        positional_entropy_values: List[float] = []
        for counts_by_pos in pos_counts.values():
            if not counts_by_pos:
                continue
            pos_total = sum(counts_by_pos.values())
            entropy = 0.0
            for count in counts_by_pos.values():
                p = count / pos_total
                if p > 0:
                    entropy -= p * math.log2(p)
            max_entropy = math.log2(len(counts_by_pos)) if len(counts_by_pos) > 1 else 1.0
            positional_entropy_values.append(entropy / max_entropy if max_entropy > 0 else 0.0)
        positional_entropy = (
            sum(positional_entropy_values) / len(positional_entropy_values)
            if positional_entropy_values
            else 0.0
        )

        return {
            "calculation_method": "computed",
            "word_count": len(all_words),
            "unique_words": unique,
            "mean_word_length": mean_length,
            "repetition_rate": repetition,
            "locality": locality,
            "info_density": info_density,
            "positional_entropy": positional_entropy,
        }

    def generate_multiple(self, gap_id: str, count: int = 10) -> List[SyntheticPage]:
        """Generate multiple distinct pages for a gap."""
        pages = []
        hashes = set()

        attempts = 0
        max_attempts = count * 5

        while len(pages) < count and attempts < max_attempts:
            seed = self.rng.randint(0, 999999)
            page = self.generate_page(gap_id, seed=seed)

            # Check for uniqueness
            if page.content_hash not in hashes:
                hashes.add(page.content_hash)
                pages.append(page)

            attempts += 1

        return pages
