"""
Track B1: Mapping Stability Tests

Tests whether consistent mappings from glyph clusters to abstract tokens
can be learned or defined without collapsing under perturbation.

Key questions:
- Do mappings survive segmentation perturbation?
- Do mappings survive ordering perturbation?
- Do mappings survive omission/addition?
"""

import logging
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session as SASession

from phase1_foundation.config import MAX_PAGES_PER_TEST, get_analysis_thresholds
from phase1_foundation.runs.manager import RunManager
from phase1_foundation.storage.metadata import (
    GlyphCandidateRecord,
    LineRecord,
    MetadataStore,
    PageRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
    WordRecord,
)
from phase2_analysis.stress_tests.interface import (
    StressTest,
    StressTestOutcome,
    StressTestResult,
)

logger = logging.getLogger(__name__)

# Local limits
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

    def __init__(self, store: MetadataStore) -> None:
        super().__init__(store)
        self.thresholds = get_analysis_thresholds().get("mapping_stability", {})

    def _threshold(self, *keys: str, default: float) -> float:
        node: Any = self.thresholds
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key)
        return float(node) if node is not None else default

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
    def applicable_classes(self) -> list[str]:
        return ["constructed_system", "visual_grammar", "hybrid_system"]

    def run(self, explanation_class: str, dataset_id: str,
            control_ids: list[str]) -> StressTestResult:
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
                self._evaluate_page_stability(
                    session, page, dataset_id,
                    segmentation_stability, ordering_stability, omission_stability,
                )

            # Calculate aggregate scores
            avg_seg = sum(segmentation_stability) / len(segmentation_stability) if segmentation_stability else 0
            avg_ord = sum(ordering_stability) / len(ordering_stability) if ordering_stability else 0
            avg_omit = sum(omission_stability) / len(omission_stability) if omission_stability else 0

            # Overall stability is the minimum (weakest link)
            overall_stability = min(avg_seg, avg_ord, avg_omit) if all(v is not None for v in [avg_seg, avg_ord, avg_omit]) else 0

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
            control_differential = (
                overall_stability - control_stability
                if control_stability is not None
                else float("nan")
            )
            try:
                run_id = str(RunManager.get_current_run().run_id)
            except RuntimeError:
                run_id = None

            return StressTestResult(
                test_id=self.test_id,
                explanation_class=explanation_class,
                run_id=run_id,
                dataset_id=dataset_id,
                timestamp=datetime.now(UTC).isoformat(),
                parameters={
                    "num_controls": len(control_ids),
                    "max_pages_per_test": MAX_PAGES_PER_TEST,
                },
                outcome=outcome,
                stability_score=overall_stability,
                control_differential=control_differential,
                collapse_threshold=collapse_threshold,
                metrics={
                    "segmentation_stability": avg_seg,
                    "ordering_stability": avg_ord,
                    "omission_stability": avg_omit,
                    "control_stability": control_stability if control_stability is not None else float("nan"),
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

    def _evaluate_page_stability(self, session: SASession, page: PageRecord, dataset_id: str,
                                 seg_results: list[float], ord_results: list[float], omit_results: list[float]) -> None:
        """Evaluate all stability metrics for a single page's lines."""
        lines = session.query(LineRecord).filter_by(page_id=page.id).limit(MAX_LINES_PER_PAGE).all()
        for line in lines:
            words = session.query(WordRecord).filter_by(line_id=line.id).limit(MAX_WORDS_PER_LINE).all()
            if len(words) < 2:
                continue
            seg_results.append(self._test_segmentation_stability(session, words, dataset_id))
            ord_results.append(self._test_ordering_stability(session, words, dataset_id))
            omit_results.append(self._test_omission_stability(session, words, dataset_id))

    def _test_segmentation_stability(self, session: SASession, words: list[WordRecord], dataset_id: str) -> float:
        """
        Test stability under segmentation perturbation.

        Simulates what happens when word boundaries shift.
        Measures how many glyphs would be affected.
        """
        if len(words) < 2:
            return 1.0

        total_glyphs = 0
        affected_glyphs = 0
        perturbation = self._threshold("perturbation_strength", default=0.05)

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

    def _test_ordering_stability(self, session: SASession, words: list[WordRecord], dataset_id: str) -> float:
        """
        Test stability under ordering perturbation.

        Measures correlation of metric values when word order is changed.
        """
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

    def _test_omission_stability(self, session: SASession, words: list[WordRecord], dataset_id: str) -> float:
        """
        Test stability under omission perturbation.

        Measures reconstruction accuracy when words are removed.
        """
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

    def _test_controls(self, session: SASession, control_ids: list[str], dataset_id: str) -> float | None:
        """
        Test stability on control datasets.

        Returns average stability across controls.
        Uses iteration limits for bounded runtime.
        """
        if not control_ids:
            logger.warning("No controls provided for mapping stability on dataset %s", dataset_id)
            return None

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

        if not control_stabilities:
            logger.warning("No control stability values available for dataset %s", dataset_id)
            return None
        return sum(control_stabilities) / len(control_stabilities)

    def _determine_outcome(self, explanation_class: str,
                           seg: float, ord: float, omit: float) -> tuple[StressTestOutcome, float | None]:
        """
        Determine outcome based on stability scores.
        
        Thresholds are based on the following benchmarks:
        - 0.7: High-confidence stability (standard baseline)
        - 0.6: Acceptable stability for noisy data
        - 0.5: Random chance / Toss-up (failure for structured systems)
        - 0.4: Catastrophic collapse threshold
        - 0.3: Maximum allowable variance for hybrid systems
        """
        min_stability = min(seg, ord, omit) if all(v is not None for v in [seg, ord, omit]) else 0

        ordering_collapse = self._threshold("constructed_system", "ordering_collapse", default=0.5)
        constructed_min_stable = self._threshold("constructed_system", "min_stable", default=0.6)
        segmentation_collapse = self._threshold("visual_grammar", "segmentation_collapse", default=0.4)
        visual_min_stable = self._threshold("visual_grammar", "min_stable", default=0.5)
        hybrid_variance_limit = self._threshold("hybrid_system", "variance_limit", default=0.3)

        # Class-specific thresholds
        if explanation_class == "constructed_system":
            # Constructed systems should show high ordering stability (>0.5)
            # because they rely on mechanical rules.
            if ord < ordering_collapse:
                return StressTestOutcome.COLLAPSED, ord
            elif min_stability < constructed_min_stable:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        elif explanation_class == "visual_grammar":
            # Visual grammar should tolerate segmentation changes better than 
            # text-based systems but collapses below 0.4.
            if seg < segmentation_collapse:
                return StressTestOutcome.COLLAPSED, seg
            elif min_stability < visual_min_stable:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        elif explanation_class == "hybrid_system":
            # Hybrid should show variable stability across tests.
            # Variance > 0.3 indicates excessive instability in one track.
            variance = max(seg, ord, omit) - min(seg, ord, omit) if all(v is not None for v in [seg, ord, omit]) else 0
            if variance > hybrid_variance_limit:
                return StressTestOutcome.FRAGILE, min_stability
            else:
                return StressTestOutcome.STABLE, None

        return StressTestOutcome.INCONCLUSIVE, None

    def _generate_implications(self, explanation_class: str,
                               seg: float, ord: float, omit: float,
                               outcome: StressTestOutcome) -> list[str]:
        """
        Generate constraint implications from results.
        
        Uses 0.7 as the standard high-confidence stability baseline.
        """
        implications = []
        confidence_threshold = self._threshold("standard_high_confidence", default=0.7)

        if seg < confidence_threshold:
            implications.append(
                "Segmentation-dependent mappings are fragile; "
                "any mapping must be robust to boundary uncertainty"
            )

        if ord < confidence_threshold:
            implications.append(
                "Order-dependent mappings are fragile; "
                "strict sequential decoding is structurally unsupported"
            )

        if omit < confidence_threshold:
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

    def _identify_failure_cases(self, seg: float, ord: float, omit: float) -> list[dict[str, Any]]:
        """Identify specific failure cases."""
        failures = []
        confidence_threshold = self._threshold("standard_high_confidence", default=0.7)

        if seg < confidence_threshold:
            failures.append({
                "type": "segmentation_collapse",
                "stability": seg,
                "detail": "Boundary shifts cause mapping inconsistency"
            })

        if ord < confidence_threshold:
            failures.append({
                "type": "ordering_sensitivity",
                "stability": ord,
                "detail": "Sequence reordering disrupts structure"
            })

        if omit < confidence_threshold:
            failures.append({
                "type": "omission_fragility",
                "stability": omit,
                "detail": "Element removal breaks coherence"
            })

        return failures

    def _generate_summary(self, explanation_class: str,
                          outcome: StressTestOutcome, stability: float) -> str:
        """Generate phase7_human-readable summary."""
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
