"""
Track B1: Mapping Stability Tests

Tests whether consistent mappings from glyph clusters to abstract tokens
can be learned or defined without collapsing under perturbation.

Key questions:
- Do mappings survive segmentation perturbation?
- Do mappings survive ordering perturbation?
- Do mappings survive omission/addition?
"""

from typing import List, Dict, Any
import math
from collections import Counter

from analysis.stress_tests.interface import (
    StressTest,
    StressTestResult,
    StressTestOutcome,
)
from foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    WordRecord,
    LineRecord,
    GlyphCandidateRecord,
    GlyphAlignmentRecord,
    TranscriptionTokenRecord,
    TranscriptionLineRecord,
    WordAlignmentRecord,
    AnchorRecord,
)
from foundation.config import use_real_computation


# Iteration limits for bounded runtime on large datasets
MAX_PAGES_PER_TEST = 50  # Maximum pages to analyze per test
MAX_LINES_PER_PAGE = 100  # Maximum lines to analyze per page
MAX_WORDS_PER_LINE = 50  # Maximum words to analyze per line


class MappingStabilityTest(StressTest):
    """
    Tests mapping stability under various perturbations.

    A mapping is considered stable if:
    - It produces consistent outputs for similar inputs
    - Small perturbations produce small changes (Lipschitz-like)
    - It degrades gracefully rather than catastrophically
    """

    @property
    def test_id(self) -> str:
        return "mapping_stability"

    @property
    def description(self) -> str:
        return (
            "Tests whether structural mappings remain consistent under "
            "segmentation, ordering, and omission perturbations."
        )

    @property
    def applicable_classes(self) -> List[str]:
        return ["constructed_system", "visual_grammar", "hybrid_system"]

    def run(self, explanation_class: str, dataset_id: str,
            control_ids: List[str]) -> StressTestResult:
        """
        Execute mapping stability tests.

        Tests three perturbation types:
        1. Segmentation perturbation (boundary shifts)
        2. Ordering perturbation (sequence reordering)
        3. Omission perturbation (element removal)
        """
        session = self.store.Session()
        try:
            # Gather test data with limits for bounded runtime
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).limit(MAX_PAGES_PER_TEST).all()

            # Initialize metrics
            segmentation_stability = []
            ordering_stability = []
            omission_stability = []

            for page in pages:
                lines = session.query(LineRecord).filter_by(page_id=page.id).limit(MAX_LINES_PER_PAGE).all()

                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).limit(MAX_WORDS_PER_LINE).all()
                    if len(words) < 2:
                        continue

                    # Test 1: Segmentation Perturbation
                    seg_score = self._test_segmentation_stability(session, words, dataset_id)
                    segmentation_stability.append(seg_score)

                    # Test 2: Ordering Perturbation
                    ord_score = self._test_ordering_stability(session, words, dataset_id)
                    ordering_stability.append(ord_score)

                    # Test 3: Omission Perturbation
                    omit_score = self._test_omission_stability(session, words, dataset_id)
                    omission_stability.append(omit_score)

            # Calculate aggregate scores
            avg_seg = sum(segmentation_stability) / len(segmentation_stability) if segmentation_stability else 0
            avg_ord = sum(ordering_stability) / len(ordering_stability) if ordering_stability else 0
            avg_omit = sum(omission_stability) / len(omission_stability) if omission_stability else 0

            # Overall stability is the minimum (weakest link)
            overall_stability = min(avg_seg, avg_ord, avg_omit) if (avg_seg and avg_ord and avg_omit) else 0

            # Determine outcome based on class-specific thresholds
            outcome, collapse_threshold = self._determine_outcome(
                explanation_class, avg_seg, avg_ord, avg_omit
            )

            # Generate constraint implications
            implications = self._generate_implications(
                explanation_class, avg_seg, avg_ord, avg_omit, outcome
            )

            # Control comparison
            control_stability = self._test_controls(session, control_ids, dataset_id)
            control_differential = overall_stability - control_stability

            return StressTestResult(
                test_id=self.test_id,
                explanation_class=explanation_class,
                outcome=outcome,
                stability_score=overall_stability,
                control_differential=control_differential,
                collapse_threshold=collapse_threshold,
                metrics={
                    "segmentation_stability": avg_seg,
                    "ordering_stability": avg_ord,
                    "omission_stability": avg_omit,
                    "control_stability": control_stability,
                    "line_count": len(segmentation_stability),
                },
                failure_cases=self._identify_failure_cases(avg_seg, avg_ord, avg_omit),
                tightens_constraints=outcome in [StressTestOutcome.FRAGILE, StressTestOutcome.COLLAPSED],
                rules_out_class=outcome == StressTestOutcome.COLLAPSED,
                constraint_implications=implications,
                evidence_refs=["fixed_glyph_identity", "word_boundary_stability"],
                summary=self._generate_summary(explanation_class, outcome, overall_stability)
            )

        finally:
            session.close()

    def _test_segmentation_stability(self, session, words: List[WordRecord], dataset_id: str) -> float:
        """
        Test stability under segmentation perturbation.

        Simulates what happens when word boundaries shift.
        Measures how many glyphs would be affected.
        """
        if not use_real_computation("stress_tests"):
            # Legacy simulated value
            return 1.0 - 0.375  # 37.5% collapse = 62.5% stability

        if len(words) < 2:
            return 1.0

        total_glyphs = 0
        affected_glyphs = 0
        perturbation = 0.05  # 5% boundary shift

        for word in words:
            glyphs = session.query(GlyphCandidateRecord).filter_by(word_id=word.id).all()
            if not glyphs:
                continue

            word_bbox = word.bbox
            if not word_bbox:
                continue

            word_width = word_bbox.get("x_max", 1) - word_bbox.get("x_min", 0)
            shift = perturbation * word_width

            for glyph in glyphs:
                total_glyphs += 1
                glyph_bbox = glyph.bbox
                if not glyph_bbox:
                    continue

                glyph_center = (glyph_bbox.get("x_min", 0) + glyph_bbox.get("x_max", 0)) / 2

                # Distance from word boundaries
                dist_from_left = glyph_center - word_bbox.get("x_min", 0)
                dist_from_right = word_bbox.get("x_max", 1) - glyph_center

                # Affected if within shift distance of boundary
                if dist_from_left < shift or dist_from_right < shift:
                    affected_glyphs += 1

        if total_glyphs == 0:
            return 1.0

        collapse_rate = affected_glyphs / total_glyphs
        return 1.0 - collapse_rate

    def _test_ordering_stability(self, session, words: List[WordRecord], dataset_id: str) -> float:
        """
        Test stability under ordering perturbation.

        Measures correlation of metric values when word order is changed.
        """
        if not use_real_computation("stress_tests"):
            return 0.70  # Legacy simulated value

        if len(words) < 3:
            return 1.0

        # Get tokens for words
        tokens = []
        for word in words:
            alignment = session.query(WordAlignmentRecord).filter_by(word_id=word.id).first()
            if alignment and alignment.token_id:
                token = session.query(TranscriptionTokenRecord).filter_by(id=alignment.token_id).first()
                if token:
                    tokens.append(token.content)

        if len(tokens) < 3:
            return 1.0

        # Calculate bigram statistics for original order
        original_bigrams = Counter()
        for i in range(len(tokens) - 1):
            original_bigrams[(tokens[i], tokens[i + 1])] += 1

        # Simulate perturbation: swap adjacent pairs
        perturbed_tokens = tokens.copy()
        for i in range(0, len(perturbed_tokens) - 1, 2):
            perturbed_tokens[i], perturbed_tokens[i + 1] = perturbed_tokens[i + 1], perturbed_tokens[i]

        perturbed_bigrams = Counter()
        for i in range(len(perturbed_tokens) - 1):
            perturbed_bigrams[(perturbed_tokens[i], perturbed_tokens[i + 1])] += 1

        # Calculate overlap (Jaccard)
        original_set = set(original_bigrams.keys())
        perturbed_set = set(perturbed_bigrams.keys())

        if not original_set and not perturbed_set:
            return 1.0

        intersection = original_set & perturbed_set
        union = original_set | perturbed_set

        return len(intersection) / len(union) if union else 1.0

    def _test_omission_stability(self, session, words: List[WordRecord], dataset_id: str) -> float:
        """
        Test stability under omission perturbation.

        Measures reconstruction accuracy when words are removed.
        """
        if not use_real_computation("stress_tests"):
            return 0.65  # Legacy simulated value

        if len(words) < 3:
            return 1.0

        # Get tokens
        tokens = []
        for word in words:
            alignment = session.query(WordAlignmentRecord).filter_by(word_id=word.id).first()
            if alignment and alignment.token_id:
                token = session.query(TranscriptionTokenRecord).filter_by(id=alignment.token_id).first()
                if token:
                    tokens.append(token.content)

        if len(tokens) < 3:
            return 1.0

        # Calculate unigram statistics for original
        original_counts = Counter(tokens)

        # Simulate omission: remove every 3rd token
        omitted_tokens = [t for i, t in enumerate(tokens) if i % 3 != 0]

        if not omitted_tokens:
            return 0.0

        omitted_counts = Counter(omitted_tokens)

        # Calculate what proportion of the distribution is preserved
        preserved = 0
        total = sum(original_counts.values())

        for token, count in original_counts.items():
            if token in omitted_counts:
                preserved += min(count, omitted_counts[token])

        return preserved / total if total > 0 else 0.0

    def _test_controls(self, session, control_ids: List[str], dataset_id: str) -> float:
        """
        Test stability on control datasets.

        Returns average stability across controls.
        Uses iteration limits for bounded runtime.
        """
        if not use_real_computation("stress_tests"):
            return 0.30  # Legacy simulated value

        if not control_ids:
            return 0.3

        control_stabilities = []

        for ctrl_id in control_ids:
            pages = session.query(PageRecord).filter_by(dataset_id=ctrl_id).limit(MAX_PAGES_PER_TEST).all()
            if not pages:
                continue

            stabilities = []
            for page in pages:
                lines = session.query(LineRecord).filter_by(page_id=page.id).limit(MAX_LINES_PER_PAGE).all()
                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).limit(MAX_WORDS_PER_LINE).all()
                    if len(words) >= 2:
                        seg = self._test_segmentation_stability(session, words, ctrl_id)
                        stabilities.append(seg)

            if stabilities:
                control_stabilities.append(sum(stabilities) / len(stabilities))

        return sum(control_stabilities) / len(control_stabilities) if control_stabilities else 0.3

    def _determine_outcome(self, explanation_class: str,
                           seg: float, ord: float, omit: float) -> tuple:
        """Determine outcome based on stability scores."""
        min_stability = min(seg, ord, omit) if (seg and ord and omit) else 0

        # Class-specific thresholds
        if explanation_class == "constructed_system":
            # Constructed systems should show high ordering stability
            if ord < 0.5:
                return StressTestOutcome.COLLAPSED, ord
            elif min_stability < 0.6:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        elif explanation_class == "visual_grammar":
            # Visual grammar should tolerate segmentation changes
            if seg < 0.4:
                return StressTestOutcome.COLLAPSED, seg
            elif min_stability < 0.5:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        elif explanation_class == "hybrid_system":
            # Hybrid should show variable stability across tests
            variance = max(seg, ord, omit) - min(seg, ord, omit) if (seg and ord and omit) else 0
            if variance > 0.3:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        return StressTestOutcome.INCONCLUSIVE, None

    def _generate_implications(self, explanation_class: str,
                               seg: float, ord: float, omit: float,
                               outcome: StressTestOutcome) -> List[str]:
        """Generate constraint implications from results."""
        implications = []

        if seg < 0.7:
            implications.append(
                "Segmentation-dependent mappings are fragile; "
                "any mapping must be robust to boundary uncertainty"
            )

        if ord < 0.7:
            implications.append(
                "Order-dependent mappings are fragile; "
                "strict sequential decoding is structurally unsupported"
            )

        if omit < 0.7:
            implications.append(
                "Omission-sensitive mappings are fragile; "
                "system lacks redundancy expected for robust communication"
            )

        if outcome == StressTestOutcome.COLLAPSED:
            implications.append(
                f"{explanation_class} fails stability requirements; "
                "should be reconsidered for inadmissibility"
            )

        return implications

    def _identify_failure_cases(self, seg: float, ord: float, omit: float) -> List[Dict[str, Any]]:
        """Identify specific failure cases."""
        failures = []

        if seg < 0.7:
            failures.append({
                "type": "segmentation_collapse",
                "stability": seg,
                "detail": "Boundary shifts cause mapping inconsistency"
            })

        if ord < 0.7:
            failures.append({
                "type": "ordering_sensitivity",
                "stability": ord,
                "detail": "Sequence reordering disrupts structure"
            })

        if omit < 0.7:
            failures.append({
                "type": "omission_fragility",
                "stability": omit,
                "detail": "Element removal breaks coherence"
            })

        return failures

    def _generate_summary(self, explanation_class: str,
                          outcome: StressTestOutcome, stability: float) -> str:
        """Generate human-readable summary."""
        if outcome == StressTestOutcome.STABLE:
            return (
                f"{explanation_class}: Mappings are STABLE (score: {stability:.2f}). "
                "Structure survives perturbation within acceptable bounds."
            )
        elif outcome == StressTestOutcome.FRAGILE:
            return (
                f"{explanation_class}: Mappings are FRAGILE (score: {stability:.2f}). "
                "Structure degrades under perturbation but does not collapse."
            )
        elif outcome == StressTestOutcome.COLLAPSED:
            return (
                f"{explanation_class}: Mappings COLLAPSED (score: {stability:.2f}). "
                "Structure fails under minimal perturbation."
            )
        else:
            return f"{explanation_class}: Results INCONCLUSIVE."
