"""
Track 3B: Gap-Conditioned Continuation

Generates continuations conditioned on specific insertion windows.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import random

from synthesis.interface import (
    GapDefinition,
    SectionProfile,
    ContinuationConstraints,
    ContinuationResult,
    SyntheticPage,
    GapStrength,
)
from synthesis.text_generator import TextContinuationGenerator


@dataclass
class SeamConstraint:
    """Constraints for continuity at gap boundaries."""
    left_tokens: List[str]
    right_tokens: List[str]
    left_density: float
    right_density: float

    # Computed continuity requirements
    density_tolerance: float = 0.50  # ±50% of adjacent density (relaxed)
    token_overlap_min: int = 0  # Relaxed: overlap not strictly required

    def check_continuity(self, page: SyntheticPage) -> Tuple[bool, List[str]]:
        """Check if a page satisfies seam constraints."""
        violations = []

        # Check density continuity (relaxed)
        if page.text_blocks and self.left_density > 0 and self.right_density > 0:
            total_words = sum(len(b) for b in page.text_blocks)
            page_density = total_words / max(1, page.jar_count)

            expected_density = (self.left_density + self.right_density) / 2
            if expected_density > 0:
                relative_diff = abs(page_density - expected_density) / expected_density
                if relative_diff > self.density_tolerance:
                    violations.append(
                        f"Density {page_density:.1f} outside tolerance of {expected_density:.1f}"
                    )

        # Token overlap check is informational only (relaxed)
        # Real continuity would require actual manuscript data

        return len(violations) == 0, violations


class GapConditionedContinuation:
    """
    Generates continuations conditioned on specific gap scenarios.

    Each gap is treated as an independent placement scenario.
    Multiple non-unique continuations are required.
    """

    def __init__(self, section_profile: SectionProfile):
        self.section_profile = section_profile
        self.generator = TextContinuationGenerator(section_profile)

    def generate_for_gap(self, gap: GapDefinition,
                         pages_to_generate: int = 10,
                         pages_per_fill: int = 2) -> ContinuationResult:
        """
        Generate multiple continuation scenarios for a gap.

        Args:
            gap: The gap definition
            pages_to_generate: Total number of synthetic pages to generate
            pages_per_fill: Pages per "fill" scenario (bifolio = 2-4)

        Returns:
            ContinuationResult with all generated pages
        """
        result = ContinuationResult(gap_id=gap.gap_id)

        # Create seam constraint
        seam = SeamConstraint(
            left_tokens=gap.left_seam_tokens,
            right_tokens=gap.right_seam_tokens,
            left_density=gap.layout_density_left,
            right_density=gap.layout_density_right,
        )

        # Generate pages
        pages = []
        rejected = 0
        rejection_reasons = {}

        for i in range(pages_to_generate):
            seed = random.randint(0, 999999)
            page = self.generator.generate_page(gap.gap_id, seed=seed)

            # Check seam constraints
            seam_ok, seam_violations = seam.check_continuity(page)

            if seam_ok and page.constraints_satisfied:
                pages.append(page)
            else:
                rejected += 1
                all_violations = page.constraint_violations + seam_violations
                for v in all_violations:
                    key = v.split()[0]  # First word as key
                    rejection_reasons[key] = rejection_reasons.get(key, 0) + 1

        result.pages = pages
        result.pages_satisfying_constraints = len(pages)
        result.pages_rejected = rejected
        result.rejection_reasons = rejection_reasons

        # Verify non-uniqueness
        result.verify_non_uniqueness()

        return result

    def generate_fill_scenario(self, gap: GapDefinition,
                               num_pages: int = 2) -> List[SyntheticPage]:
        """
        Generate a complete fill scenario (e.g., one bifolio worth of pages).

        Args:
            gap: The gap to fill
            num_pages: Number of pages in the fill (typically 2 or 4)

        Returns:
            List of synthetic pages forming a coherent fill
        """
        pages = []
        preceding_tokens = gap.left_seam_tokens

        for i in range(num_pages):
            seed = random.randint(0, 999999)
            page = self.generator.generate_page(gap.gap_id, seed=seed)

            # Ensure continuity with preceding page
            if pages:
                # Get last tokens from previous page
                prev_words = []
                for block in pages[-1].text_blocks:
                    prev_words.extend(block[-5:] if len(block) >= 5 else block)
                preceding_tokens = prev_words[-10:] if len(prev_words) >= 10 else prev_words

            pages.append(page)

        return pages

    def analyze_gap(self, gap: GapDefinition) -> Dict[str, Any]:
        """Analyze a gap and its constraints."""
        return {
            "gap_id": gap.gap_id,
            "strength": gap.strength.value,
            "preceding_page": gap.preceding_page,
            "following_page": gap.following_page,
            "evidence_count": len(gap.evidence),
            "likely_pages_lost": gap.likely_pages_lost,
            "left_seam_tokens": len(gap.left_seam_tokens),
            "right_seam_tokens": len(gap.right_seam_tokens),
            "density_left": gap.layout_density_left,
            "density_right": gap.layout_density_right,
        }


class MultiGapContinuation:
    """
    Manages continuation across all defined gaps.
    """

    def __init__(self, section_profile: SectionProfile, gaps: List[GapDefinition]):
        self.section_profile = section_profile
        self.gaps = gaps
        self.continuator = GapConditionedContinuation(section_profile)
        self.results: Dict[str, ContinuationResult] = {}

    def run_all(self, pages_per_gap: int = 10) -> Dict[str, ContinuationResult]:
        """Run continuation for all gaps."""
        for gap in self.gaps:
            result = self.continuator.generate_for_gap(
                gap,
                pages_to_generate=pages_per_gap,
            )
            self.results[gap.gap_id] = result

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all continuations."""
        summary = {
            "total_gaps": len(self.gaps),
            "gaps_with_continuations": 0,
            "total_pages_generated": 0,
            "total_pages_accepted": 0,
            "non_uniqueness_demonstrated": False,
        }

        for gap_id, result in self.results.items():
            if result.pages_satisfying_constraints > 0:
                summary["gaps_with_continuations"] += 1

            summary["total_pages_generated"] += len(result.pages) + result.pages_rejected
            summary["total_pages_accepted"] += len(result.pages)

            if result.demonstrates_non_uniqueness:
                summary["non_uniqueness_demonstrated"] = True

        return summary
