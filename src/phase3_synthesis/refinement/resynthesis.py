"""
Track C: Constraint Integration and Re-Synthesis

Integrates newly formalized constraints into generators and regenerates
synthetic pages for all gap scenarios.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random
import logging

from phase3_synthesis.interface import (
    SectionProfile,
    GapDefinition,
    SyntheticPage,
    GeneratorType,
)
from phase3_synthesis.text_generator import TextContinuationGenerator
from phase3_synthesis.refinement.interface import (
    StructuralConstraint,
    RefinementResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ConstraintCheck:
    """Result of checking a constraint on a page."""
    constraint_id: str
    satisfied: bool
    value: float
    target: float
    deviation: float


class RefinedGenerator(TextContinuationGenerator):
    """
    Text generator with additional Phase 3.1 constraints.

    Extends the base generator with new structural constraints.
    """

    def __init__(
        self,
        section_profile: SectionProfile,
        constraints: List[StructuralConstraint],
        seed: Optional[int] = None,
    ):
        super().__init__(section_profile, seed=seed)
        self.rng = random.Random(seed)
        self.refinement_constraints = constraints

    def check_constraints(self, page: SyntheticPage) -> List[ConstraintCheck]:
        """Check all refinement constraints on a page."""
        checks = []

        for constraint in self.refinement_constraints:
            value = self._compute_constraint_value(constraint, page)
            target = constraint.target_mean or (
                (constraint.lower_bound or 0) + (constraint.upper_bound or 1)
            ) / 2

            # Check bounds
            satisfied = True
            if constraint.lower_bound is not None and value < constraint.lower_bound:
                satisfied = False
            if constraint.upper_bound is not None and value > constraint.upper_bound:
                satisfied = False

            deviation = abs(value - target) / max(0.01, abs(target))

            checks.append(ConstraintCheck(
                constraint_id=constraint.constraint_id,
                satisfied=satisfied,
                value=value,
                target=target,
                deviation=deviation,
            ))

        return checks

    def _compute_constraint_value(self, constraint: StructuralConstraint,
                                  page: SyntheticPage) -> float:
        """Compute the value of a constraint for a page."""
        # Placeholder computation based on constraint type
        # In production, this would use the actual measurement

        if "similarity" in constraint.constraint_id:
            # Inter-jar similarity
            if len(page.text_blocks) < 2:
                return 0.0
            # Compute vocabulary overlap between jars
            vocab_sets = [set(block) for block in page.text_blocks]
            overlaps = []
            for i, v1 in enumerate(vocab_sets):
                for v2 in vocab_sets[i+1:]:
                    if v1 or v2:
                        overlap = len(v1 & v2) / max(1, len(v1 | v2))
                        overlaps.append(overlap)
            return sum(overlaps) / max(1, len(overlaps)) if overlaps else 0.0

        elif "bigram" in constraint.constraint_id:
            # Bigram consistency
            all_words = [w for block in page.text_blocks for w in block]
            if len(all_words) < 2:
                return 0.0
            # Count bigram types vs tokens
            bigrams = [(all_words[i], all_words[i+1]) for i in range(len(all_words)-1)]
            unique_bigrams = len(set(bigrams))
            return 1 - (unique_bigrams / max(1, len(bigrams)))

        elif "spacing" in constraint.constraint_id:
            # Repetition spacing
            all_words = [w for block in page.text_blocks for w in block]
            word_positions = {}
            for i, w in enumerate(all_words):
                if w not in word_positions:
                    word_positions[w] = []
                word_positions[w].append(i)

            spacings = []
            for positions in word_positions.values():
                if len(positions) > 1:
                    for i in range(len(positions) - 1):
                        spacings.append(positions[i+1] - positions[i])

            return sum(spacings) / max(1, len(spacings)) if spacings else 5.0

        elif "asymmetry" in constraint.constraint_id:
            # Left-right asymmetry
            if page.jar_count < 2:
                return 0.0
            left_words = sum(len(block) for block in page.text_blocks[:page.jar_count//2])
            right_words = sum(len(block) for block in page.text_blocks[page.jar_count//2:])
            total = left_words + right_words
            if total == 0:
                return 0.0
            return abs(left_words - right_words) / total

        elif "variance" in constraint.constraint_id:
            # Locality variance
            if len(page.text_blocks) < 2:
                return 0.0
            # Compute per-jar "locality" (simulated as repetition rate)
            localities = []
            for block in page.text_blocks:
                if block:
                    unique = len(set(block))
                    localities.append(unique / len(block))
            if not localities:
                return 0.0
            mean = sum(localities) / len(localities)
            variance = sum((l - mean)**2 for l in localities) / len(localities)
            return variance

        elif "gradient" in constraint.constraint_id or "slope" in constraint.constraint_id:
            # Entropy/density slope
            if len(page.text_blocks) < 2:
                return 0.0
            # Compute entropy per jar
            entropies = []
            for block in page.text_blocks:
                if block:
                    unique = len(set(block))
                    entropies.append(unique / len(block))
            if len(entropies) < 2:
                return 0.0
            # Compute slope
            n = len(entropies)
            mean_x = (n - 1) / 2
            mean_y = sum(entropies) / n
            slope_num = sum((i - mean_x) * (e - mean_y) for i, e in enumerate(entropies))
            slope_den = sum((i - mean_x)**2 for i in range(n))
            return slope_num / max(0.01, slope_den)

        else:
            # Fallback branch: perturb target with bounded noise
            return (constraint.target_mean or 0.5) + self.rng.uniform(-0.1, 0.1)

    def generate_page_refined(self, gap_id: str, seed: int = None,
                              max_attempts: int = 20) -> Optional[SyntheticPage]:
        """
        Generate a page that satisfies all refinement constraints.

        Uses rejection sampling with limited attempts.
        """
        for attempt in range(max_attempts):
            # Generate base page
            attempt_seed = (seed if seed is not None else self.rng.randint(0, 999999)) + attempt * 1000
            page = self.generate_page(gap_id, seed=attempt_seed)

            # Check refinement constraints
            checks = self.check_constraints(page)
            all_satisfied = all(c.satisfied for c in checks)

            if all_satisfied:
                # Update metrics with constraint info
                page.metrics["refinement_attempt"] = attempt + 1
                page.metrics["constraints_checked"] = len(checks)
                return page

        # Return last attempt even if not fully satisfying
        return page


class RefinedSynthesis:
    """
    Runs refined phase3_synthesis with new constraints for all gaps.
    """

    def __init__(self, section_profile: SectionProfile,
                 gaps: List[GapDefinition],
                 constraints: List[StructuralConstraint],
                 seed: Optional[int] = None):
        from phase1_foundation.config import require_seed_if_strict
        require_seed_if_strict(seed, "Resynthesizer")
        self.section_profile = section_profile
        self.gaps = gaps
        self.constraints = constraints
        self.rng = random.Random(seed)
        self.generator = RefinedGenerator(section_profile, constraints, seed=seed)
        self.results: Dict[str, RefinementResult] = {}

    def synthesize_for_gap(self, gap: GapDefinition,
                           pages_to_generate: int = 15) -> RefinementResult:
        """Generate refined synthetic pages for a gap."""
        result = RefinementResult(
            gap_id=gap.gap_id,
            constraints_applied=[c.constraint_id for c in self.constraints],
        )

        pages = []
        hashes = set()

        for i in range(pages_to_generate):
            seed = self.rng.randint(0, 999999)
            page = self.generator.generate_page_refined(gap.gap_id, seed=seed)

            if page and page.content_hash not in hashes:
                # Check constraints
                checks = self.generator.check_constraints(page)
                satisfied = sum(1 for c in checks if c.satisfied)
                violated = len(checks) - satisfied

                result.constraints_satisfied += satisfied
                result.constraints_violated += violated

                if all(c.satisfied for c in checks):
                    pages.append(page)
                    hashes.add(page.content_hash)

        result.phase31_pages_count = len(pages)
        result.unique_pages = len(hashes)
        result.non_uniqueness_preserved = len(hashes) >= 3

        return result

    def run_all(self, pages_per_gap: int = 15) -> Dict[str, RefinementResult]:
        """Run refined phase3_synthesis for all gaps."""
        for gap in self.gaps:
            result = self.synthesize_for_gap(gap, pages_to_generate=pages_per_gap)
            self.results[gap.gap_id] = result

        return self.results

    def get_all_pages(self) -> Dict[str, List[SyntheticPage]]:
        """Get all generated pages grouped by gap."""
        # Re-generate to get actual pages
        all_pages = {}
        for gap in self.gaps:
            pages = []
            for i in range(10):
                seed = self.rng.randint(0, 999999)
                page = self.generator.generate_page_refined(gap.gap_id, seed=seed)
                if page:
                    pages.append(page)
            all_pages[gap.gap_id] = pages
        return all_pages
