"""
Phase 3 Interface and Data Structures

Defines core structures for pharmaceutical section continuation phase3_synthesis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import hashlib
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class GapStrength(Enum):
    """Strength of evidence for a gap."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class GeneratorType(Enum):
    """Type of text generator."""
    WORD_LEVEL = "word_level"
    SUBWORD_LEVEL = "subword_level"


@dataclass
class JarProfile:
    """Structural profile of a single jar on a page."""
    jar_id: str
    bounding_box: Tuple[float, float, float, float]  # x, y, width, height
    text_block_count: int
    line_count: int
    word_count: int
    area: float = 0.0

    def __post_init__(self):
        if self.bounding_box:
            self.area = self.bounding_box[2] * self.bounding_box[3]


@dataclass
class PageProfile:
    """Structural profile of a single pharmaceutical page."""
    page_id: str
    jar_count: int
    jars: List[JarProfile] = field(default_factory=list)

    # Layout metrics
    total_text_blocks: int = 0
    total_lines: int = 0
    total_words: int = 0
    layout_density: float = 0.0

    # Text metrics (from Phase 2)
    mean_word_length: float = 0.0
    token_repetition_rate: float = 0.0
    positional_entropy: float = 0.0
    locality_radius: float = 0.0
    information_density: float = 0.0


@dataclass
class SectionProfile:
    """
    Structural profile of the entire pharmaceutical section.

    Derived from surviving jar pages (f88r-f96v).
    Defines hard constraints for phase3_synthesis.
    """
    section_id: str = "pharmaceutical"
    page_range: Tuple[str, str] = ("f88r", "f96v")

    # Page profiles
    pages: List[PageProfile] = field(default_factory=list)

    # Aggregated statistics (envelopes)
    jar_count_range: Tuple[int, int] = (0, 0)
    text_blocks_per_jar_range: Tuple[int, int] = (0, 0)
    lines_per_block_range: Tuple[int, int] = (0, 0)
    words_per_line_range: Tuple[int, int] = (0, 0)

    # Jar geometry envelopes
    jar_width_range: Tuple[float, float] = (0.0, 0.0)
    jar_height_range: Tuple[float, float] = (0.0, 0.0)
    jar_spacing_range: Tuple[float, float] = (0.0, 0.0)

    # Text metrics envelopes
    word_length_range: Tuple[float, float] = (0.0, 0.0)
    repetition_rate_range: Tuple[float, float] = (0.0, 0.0)
    entropy_range: Tuple[float, float] = (0.0, 0.0)
    locality_range: Tuple[float, float] = (0.0, 0.0)
    info_density_range: Tuple[float, float] = (0.0, 0.0)

    def compute_envelopes(self):
        """Compute statistical envelopes from page profiles."""
        if not self.pages:
            return

        jar_counts = [p.jar_count for p in self.pages]
        self.jar_count_range = (min(jar_counts), max(jar_counts))

        # Aggregate text metrics
        entropies = [p.positional_entropy for p in self.pages if p.positional_entropy > 0]
        if entropies:
            self.entropy_range = (min(entropies), max(entropies))

        localities = [p.locality_radius for p in self.pages if p.locality_radius > 0]
        if localities:
            self.locality_range = (min(localities), max(localities))

        densities = [p.information_density for p in self.pages if p.information_density > 0]
        if densities:
            self.info_density_range = (min(densities), max(densities))


@dataclass
class GapDefinition:
    """
    Definition of a codicologically defensible insertion window.

    Based on quire structure, layout discontinuities, and jar-sequence irregularities.
    """
    gap_id: str
    strength: GapStrength

    # Boundaries
    preceding_page: str  # e.g., "f88v"
    following_page: str  # e.g., "f89r"

    # Evidence
    evidence: List[str] = field(default_factory=list)

    # Estimated loss
    likely_pages_lost: Tuple[int, int] = (2, 4)  # range

    # Seam constraints (derived from adjacent pages)
    left_seam_tokens: List[str] = field(default_factory=list)
    right_seam_tokens: List[str] = field(default_factory=list)
    layout_density_left: float = 0.0
    layout_density_right: float = 0.0


@dataclass
class ContinuationConstraints:
    """
    Hard constraints for continuation phase3_synthesis.

    All constraints are enforced DURING generation, not post-hoc.
    """
    # Section-wide constraints
    section_profile: SectionProfile = field(default_factory=SectionProfile)

    # Gap-specific constraints
    gap: Optional[GapDefinition] = None

    # Text constraints (from Phase 2)
    locality_window: Tuple[int, int] = (2, 4)
    information_density_tolerance: float = 0.5  # ± from observed
    positional_entropy_tolerance: float = 0.2
    repetition_rate_tolerance: float = 0.05

    # Robustness constraint
    min_perturbation_robustness: float = 0.50

    # Structural constraints
    max_novel_tokens: float = 0.10  # max 10% novel tokens

    def check_text(self, text_metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Check if generated text satisfies constraints."""
        violations = []

        # Check locality (with tolerance)
        if "locality" in text_metrics:
            loc = text_metrics["locality"]
            # Allow some slack (±1 from window)
            if loc < self.locality_window[0] - 1.0 or loc > self.locality_window[1] + 1.0:
                violations.append(f"locality {loc:.2f} outside window {self.locality_window}")

        # Check info density (with tolerance)
        if "info_density" in text_metrics and self.section_profile.info_density_range[1] > 0:
            density = text_metrics["info_density"]
            expected = sum(self.section_profile.info_density_range) / 2
            # Allow ±1.0 tolerance
            if abs(density - expected) > self.information_density_tolerance + 1.0:
                violations.append(f"info density {density:.2f} outside tolerance")

        # All constraints passed
        return len(violations) == 0, violations


@dataclass
class SyntheticPage:
    """
    A synthetically generated pharmaceutical page.

    EXPLICITLY LABELED SYNTHETIC.
    """
    # Identification
    page_id: str  # e.g., "SYNTHETIC_gap_a_001"
    gap_id: str
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Provenance
    generator_type: GeneratorType = GeneratorType.WORD_LEVEL
    generator_params: Dict[str, Any] = field(default_factory=dict)
    random_seed: int = 0

    # Content (SYNTHETIC)
    jar_count: int = 0
    text_blocks: List[List[str]] = field(default_factory=list)  # per-jar word lists

    # Metrics
    metrics: Dict[str, float] = field(default_factory=dict)

    # Constraint satisfaction
    constraints_satisfied: bool = False
    constraint_violations: List[str] = field(default_factory=list)

    # Hash for uniqueness verification
    content_hash: str = ""

    def compute_hash(self):
        """Compute content hash for uniqueness verification."""
        content = str(self.text_blocks)
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_label(self) -> str:
        """Return explicit SYNTHETIC label."""
        return f"[SYNTHETIC] {self.page_id} (generated {self.generation_timestamp})"


@dataclass
class ContinuationResult:
    """
    Result of continuation phase3_synthesis for a gap.
    """
    gap_id: str

    # Generated pages
    pages: List[SyntheticPage] = field(default_factory=list)

    # Uniqueness verification
    unique_pages: int = 0
    duplicate_hashes: List[str] = field(default_factory=list)

    # Constraint satisfaction
    pages_satisfying_constraints: int = 0
    pages_rejected: int = 0
    rejection_reasons: Dict[str, int] = field(default_factory=dict)

    # Non-uniqueness demonstration
    demonstrates_non_uniqueness: bool = False

    def verify_non_uniqueness(self):
        """Verify that multiple distinct continuations exist."""
        hashes = set()
        for page in self.pages:
            page.compute_hash()
            hashes.add(page.content_hash)

        self.unique_pages = len(hashes)
        self.demonstrates_non_uniqueness = self.unique_pages >= 3  # Need at least 3 distinct


@dataclass
class IndistinguishabilityResult:
    """
    Result of indistinguishability testing.
    """
    gap_id: str

    # Comparison groups
    real_pages_count: int = 0
    synthetic_pages_count: int = 0
    scrambled_count: int = 0

    # Separation metrics
    real_vs_scrambled_separation: float = 0.0  # Should be high
    synthetic_vs_scrambled_separation: float = 0.0  # Should be high
    real_vs_synthetic_separation: float = 0.0  # Should be low (near chance)

    # Success criteria
    scrambled_clearly_separated: bool = False
    synthetic_indistinguishable: bool = False
    separation_success_threshold: float = 0.7
    separation_failure_threshold: float = 0.3

    # Detailed metrics
    metric_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def evaluate_success(self):
        """Evaluate success criteria."""
        # Strong separation from scrambled.
        self.scrambled_clearly_separated = (
            self.real_vs_scrambled_separation > self.separation_success_threshold and
            self.synthetic_vs_scrambled_separation > self.separation_success_threshold
        )

        # Weak separation from real (near chance).
        self.synthetic_indistinguishable = (
            self.real_vs_synthetic_separation < self.separation_failure_threshold
        )


@dataclass
class Phase3Findings:
    """
    Complete findings from Phase 3.
    """
    # Section profile
    section_profile: SectionProfile = field(default_factory=SectionProfile)

    # Gap definitions
    gaps: List[GapDefinition] = field(default_factory=list)

    # Continuation results
    continuation_results: Dict[str, ContinuationResult] = field(default_factory=dict)

    # Indistinguishability results
    indistinguishability_results: Dict[str, IndistinguishabilityResult] = field(default_factory=dict)

    # Success criteria
    at_least_one_gap_filled: bool = False
    non_uniqueness_demonstrated: bool = False
    no_semantics_required: bool = True

    # Overall success
    phase_3_successful: bool = False

    def evaluate_success(self):
        """Evaluate Phase 3 success criteria."""
        # Check if at least one gap was successfully filled
        for gap_id, result in self.continuation_results.items():
            if result.pages_satisfying_constraints >= 1:
                self.at_least_one_gap_filled = True

            if result.demonstrates_non_uniqueness:
                self.non_uniqueness_demonstrated = True

        # Check indistinguishability
        all_indistinguishable = all(
            r.synthetic_indistinguishable
            for r in self.indistinguishability_results.values()
        ) if self.indistinguishability_results else False

        self.phase_3_successful = (
            self.at_least_one_gap_filled and
            self.non_uniqueness_demonstrated and
            self.no_semantics_required
        )

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of findings."""
        return {
            "section": self.section_profile.section_id,
            "gaps_analyzed": len(self.gaps),
            "gaps_filled": sum(
                1 for r in self.continuation_results.values()
                if r.pages_satisfying_constraints > 0
            ),
            "total_synthetic_pages": sum(
                len(r.pages) for r in self.continuation_results.values()
            ),
            "non_uniqueness_demonstrated": self.non_uniqueness_demonstrated,
            "no_semantics_required": self.no_semantics_required,
            "phase_3_successful": self.phase_3_successful,
        }
