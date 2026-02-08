"""
Destructive Hypotheses for Phase 1 Audit

These hypotheses are deliberately designed to fail or expose fragility
in common assumptions about the Voynich Manuscript. Their purpose is to
demonstrate the rigor of the negative control framework by recording
actual failures.

Per PRINCIPLES_AND_NONGOALS.md:
- "Failures and anomalies are first-class data"
- "If a signal survives controls, it is meaningful. If it does not, it is an artifact."
"""

from typing import List, Dict, Any
import math
from collections import Counter

from foundation.hypotheses.interface import Hypothesis, HypothesisResult
from foundation.storage.metadata import (
    MetadataStore,
    WordRecord,
    LineRecord,
    GlyphCandidateRecord,
    TranscriptionTokenRecord,
    TranscriptionLineRecord,
    TranscriptionSourceRecord,
    RegionRecord,
    AnchorRecord,
    PageRecord,
)
from foundation.config import use_real_computation


class FixedGlyphIdentityHypothesis(Hypothesis):
    """
    Tests if glyph identity persists under segmentation perturbation.

    Common Assumption: Glyphs are stable visual units that can be reliably
    identified regardless of how word boundaries are drawn.

    Test Logic: Perturb word boundaries by a small amount (5%) and re-segment.
    If glyph classes remain stable, the assumption holds.

    Expected Outcome: FALSIFIED
    Glyph identity is segmentation-dependent. Shifting word boundaries even
    slightly causes glyphs to merge, split, or become ambiguous.
    """

    @property
    def id(self) -> str:
        return "fixed_glyph_identity"

    @property
    def description(self) -> str:
        return "Glyph identity is stable under segmentation perturbation."

    @property
    def assumptions(self) -> str:
        return (
            "Glyphs are discrete visual units. "
            "Segmentation boundaries do not affect glyph identification."
        )

    @property
    def falsification_criteria(self) -> str:
        return (
            "If >20% of glyph identities change under 5% boundary perturbation, "
            "glyph identity is segmentation-dependent and the hypothesis is FALSIFIED."
        )

    def run(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        if not use_real_computation("hypotheses"):
            return self._run_simulated(real_dataset_id, control_dataset_ids)

        return self._run_real(real_dataset_id, control_dataset_ids)

    def _run_real(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """
        Simulate boundary perturbation and count affected glyphs.

        For each word, shift boundaries by perturbation_strength and count
        how many glyphs would be "collapsed" (fall too close to boundary).
        """
        session = self.store.Session()
        try:
            # Fetch all words and glyphs
            pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            word_count = 0
            glyph_count = 0

            perturbation_levels = [0.01, 0.05, 0.10, 0.15, 0.20]
            identity_collapse = {}

            for p_level in perturbation_levels:
                collapsed_count = 0
                total_glyphs = 0

                for page in pages:
                    lines = session.query(LineRecord).filter_by(page_id=page.id).all()
                    for line in lines:
                        words = session.query(WordRecord).filter_by(line_id=line.id).all()
                        word_count += len(words)

                        for word in words:
                            glyphs = (
                                session.query(GlyphCandidateRecord)
                                .filter_by(word_id=word.id)
                                .order_by(GlyphCandidateRecord.glyph_index)
                                .all()
                            )

                            if not glyphs:
                                continue

                            glyph_count += len(glyphs)
                            total_glyphs += len(glyphs)

                            # Get word bbox
                            word_bbox = word.bbox
                            if not word_bbox:
                                continue

                            word_width = word_bbox.get("x_max", 1) - word_bbox.get("x_min", 0)
                            shift = p_level * word_width

                            # Count glyphs that would be affected by boundary shift
                            for glyph in glyphs:
                                glyph_bbox = glyph.bbox
                                if not glyph_bbox:
                                    continue

                                glyph_center = (
                                    glyph_bbox.get("x_min", 0) + glyph_bbox.get("x_max", 0)
                                ) / 2

                                # Distance from word left boundary
                                dist_from_left = glyph_center - word_bbox.get("x_min", 0)
                                # Distance from word right boundary
                                dist_from_right = word_bbox.get("x_max", 1) - glyph_center

                                # Glyph is affected if it's within shift distance of either boundary
                                if dist_from_left < shift or dist_from_right < shift:
                                    collapsed_count += 1

                # Calculate collapse rate for this perturbation level
                collapse_rate = collapsed_count / total_glyphs if total_glyphs > 0 else 0
                identity_collapse[p_level] = collapse_rate

            collapse_at_5pct = identity_collapse.get(0.05, 0)

            # Falsified if >20% collapse at 5% perturbation
            if collapse_at_5pct > 0.20:
                outcome = "FALSIFIED"
            elif collapse_at_5pct > 0.10:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:word_count": float(word_count),
                f"{real_dataset_id}:glyph_count": float(glyph_count),
                f"{real_dataset_id}:collapse_at_5pct": collapse_at_5pct,
            }

            for p, rate in identity_collapse.items():
                metrics[f"{real_dataset_id}:collapse_at_{int(p*100)}pct"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "segmentation_perturbation",
                    "perturbation_threshold": 0.05,
                    "identity_collapse_rate": collapse_at_5pct,
                    "collapse_threshold": 0.20,
                    "verdict": "Glyph identity collapses under minor segmentation changes" if outcome == "FALSIFIED" else "Glyph identity is relatively stable",
                    "collapse_curve": identity_collapse,
                }
            )
        finally:
            session.close()

    def _run_simulated(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """Legacy simulated implementation."""
        session = self.store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            word_count = 0
            glyph_count = 0

            for page in pages:
                lines = session.query(LineRecord).filter_by(page_id=page.id).all()
                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).all()
                    word_count += len(words)
                    for word in words:
                        glyphs = session.query(GlyphCandidateRecord).filter_by(word_id=word.id).all()
                        glyph_count += len(glyphs)

            perturbation_levels = [0.01, 0.05, 0.10, 0.15, 0.20]
            identity_collapse = {}

            for p in perturbation_levels:
                collapse_rate = min(0.95, 0.15 + (p * 4.0) + (p ** 2 * 10))
                identity_collapse[p] = collapse_rate

            collapse_at_5pct = identity_collapse[0.05]

            if collapse_at_5pct > 0.20:
                outcome = "FALSIFIED"
            elif collapse_at_5pct > 0.10:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:word_count": float(word_count),
                f"{real_dataset_id}:glyph_count": float(glyph_count),
                f"{real_dataset_id}:collapse_at_5pct": collapse_at_5pct,
            }

            for p, rate in identity_collapse.items():
                metrics[f"{real_dataset_id}:collapse_at_{int(p*100)}pct"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "segmentation_perturbation",
                    "perturbation_threshold": 0.05,
                    "identity_collapse_rate": collapse_at_5pct,
                    "collapse_threshold": 0.20,
                    "verdict": "Glyph identity collapses under minor segmentation changes",
                    "collapse_curve": identity_collapse,
                    "simulated": True
                }
            )
        finally:
            session.close()


class WordBoundaryStabilityHypothesis(Hypothesis):
    """
    Tests if word boundaries are stable across transcription sources.

    Common Assumption: Word boundaries in the Voynich Manuscript are
    objective features that different transcribers would identify consistently.

    Test Logic: Compare word boundary positions across EVA, Currier, and
    other transcription systems. Measure agreement rate.

    Expected Outcome: WEAKLY_SUPPORTED or FALSIFIED
    Significant disagreement exists between transcription systems,
    indicating word boundaries are interpretive, not objective.
    """

    @property
    def id(self) -> str:
        return "word_boundary_stability"

    @property
    def description(self) -> str:
        return "Word boundaries are consistent across transcription sources."

    @property
    def assumptions(self) -> str:
        return (
            "Spaces or delimiters between words are visually unambiguous. "
            "Different transcribers identify the same word boundaries."
        )

    @property
    def falsification_criteria(self) -> str:
        return (
            "If word boundary agreement between major transcription sources "
            "(EVA, Currier, Bennett) falls below 80%, the assumption that "
            "word boundaries are objective is FALSIFIED."
        )

    def run(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        if not use_real_computation("hypotheses"):
            return self._run_simulated(real_dataset_id, control_dataset_ids)

        return self._run_real(real_dataset_id, control_dataset_ids)

    def _run_real(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """
        Compare word/token counts across transcription sources.

        Agreement is measured by comparing the number of tokens per line
        across different transcription sources.
        """
        session = self.store.Session()
        try:
            # Get all transcription sources
            sources = session.query(TranscriptionSourceRecord).all()
            source_count = len(sources)

            if source_count < 2:
                return HypothesisResult(
                    outcome="INCONCLUSIVE",
                    metrics={f"{real_dataset_id}:source_count": float(source_count)},
                    summary={
                        "error": "Need at least 2 transcription sources to compare",
                        "sources_found": source_count
                    }
                )

            # Get pages for this dataset
            pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            page_ids = [p.id for p in pages]

            # Compare token counts per line across sources
            source_comparisons = {}
            source_ids = [s.id for s in sources]

            for i, src1 in enumerate(source_ids):
                for src2 in source_ids[i + 1:]:
                    matching_lines = 0
                    total_lines = 0

                    for page_id in page_ids:
                        # Get lines from source 1
                        lines1 = (
                            session.query(TranscriptionLineRecord)
                            .filter_by(source_id=src1, page_id=page_id)
                            .order_by(TranscriptionLineRecord.line_index)
                            .all()
                        )

                        # Get lines from source 2
                        lines2 = (
                            session.query(TranscriptionLineRecord)
                            .filter_by(source_id=src2, page_id=page_id)
                            .order_by(TranscriptionLineRecord.line_index)
                            .all()
                        )

                        # Compare token counts for matching line indices
                        lines1_by_idx = {l.line_index: l for l in lines1}
                        lines2_by_idx = {l.line_index: l for l in lines2}

                        common_indices = set(lines1_by_idx.keys()) & set(lines2_by_idx.keys())

                        for idx in common_indices:
                            total_lines += 1

                            # Count tokens in each line
                            tokens1 = (
                                session.query(TranscriptionTokenRecord)
                                .filter_by(line_id=lines1_by_idx[idx].id)
                                .count()
                            )
                            tokens2 = (
                                session.query(TranscriptionTokenRecord)
                                .filter_by(line_id=lines2_by_idx[idx].id)
                                .count()
                            )

                            # Lines "match" if token counts are equal
                            if tokens1 == tokens2:
                                matching_lines += 1

                    agreement = matching_lines / total_lines if total_lines > 0 else 0
                    source_comparisons[(src1, src2)] = agreement

            # Calculate aggregate metrics
            if source_comparisons:
                agreement_rates = list(source_comparisons.values())
                avg_agreement = sum(agreement_rates) / len(agreement_rates)
                min_agreement = min(agreement_rates)
                max_agreement = max(agreement_rates)
            else:
                avg_agreement = 0
                min_agreement = 0
                max_agreement = 0

            # Determine outcome
            if avg_agreement < 0.70:
                outcome = "FALSIFIED"
            elif avg_agreement < 0.80:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:source_count": float(source_count),
                f"{real_dataset_id}:avg_agreement": avg_agreement,
                f"{real_dataset_id}:min_agreement": min_agreement,
                f"{real_dataset_id}:max_agreement": max_agreement,
            }

            for pair, rate in source_comparisons.items():
                metrics[f"{real_dataset_id}:{pair[0]}_vs_{pair[1]}"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "cross_source_boundary_agreement",
                    "sources_compared": list(source_comparisons.keys()),
                    "average_agreement": avg_agreement,
                    "agreement_threshold": 0.80,
                    "verdict": "Word boundaries show significant inter-source disagreement" if outcome == "FALSIFIED" else "Word boundaries are reasonably consistent",
                }
            )
        finally:
            session.close()

    def _run_simulated(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """Legacy simulated implementation."""
        session = self.store.Session()
        try:
            sources = session.query(TranscriptionSourceRecord).all()
            source_count = len(sources)

            simulated_comparisons = {
                ("eva", "currier"): 0.72,
                ("eva", "bennett"): 0.78,
                ("currier", "bennett"): 0.75,
            }

            if source_count >= 2:
                agreement_rates = list(simulated_comparisons.values())
                avg_agreement = sum(agreement_rates) / len(agreement_rates)
                min_agreement = min(agreement_rates)
                max_agreement = max(agreement_rates)
            else:
                avg_agreement = 0.75
                min_agreement = 0.75
                max_agreement = 0.75

            if avg_agreement < 0.70:
                outcome = "FALSIFIED"
            elif avg_agreement < 0.80:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:source_count": float(source_count),
                f"{real_dataset_id}:avg_agreement": avg_agreement,
                f"{real_dataset_id}:min_agreement": min_agreement,
                f"{real_dataset_id}:max_agreement": max_agreement,
            }

            for pair, rate in simulated_comparisons.items():
                metrics[f"{real_dataset_id}:{pair[0]}_vs_{pair[1]}"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "cross_source_boundary_agreement",
                    "sources_compared": list(simulated_comparisons.keys()),
                    "average_agreement": avg_agreement,
                    "agreement_threshold": 0.80,
                    "verdict": "Word boundaries show significant inter-source disagreement",
                    "simulated": True
                }
            )
        finally:
            session.close()


class DiagramTextAlignmentHypothesis(Hypothesis):
    """
    Tests if text-to-diagram alignment survives scrambling.

    Common Assumption: Text labels near diagrams are meaningfully related
    to those diagrams (i.e., they label, describe, or annotate them).

    Test Logic: Calculate alignment scores between text regions and diagram
    regions in real data vs scrambled data. If real alignment is not
    significantly better than scrambled, the relationship is chance.

    Expected Outcome: Depends on data quality
    - If alignment score degrades significantly on scrambled data: SUPPORTED
    - If alignment score is similar: FALSIFIED (relationship is geometric accident)
    """

    @property
    def id(self) -> str:
        return "diagram_text_alignment"

    @property
    def description(self) -> str:
        return "Text near diagrams is semantically related to those diagrams."

    @property
    def assumptions(self) -> str:
        return (
            "Proximity of text to diagrams indicates meaningful labeling. "
            "The spatial relationship is intentional, not accidental."
        )

    @property
    def falsification_criteria(self) -> str:
        return (
            "If the alignment score for real data is not significantly higher "
            "(>2 standard deviations) than scrambled controls, the text-diagram "
            "relationship is indistinguishable from chance and FALSIFIED."
        )

    def run(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        if not use_real_computation("hypotheses"):
            return self._run_simulated(real_dataset_id, control_dataset_ids)

        return self._run_real(real_dataset_id, control_dataset_ids)

    def _run_real(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """
        Count real anchors and compare to controls.

        Computes a label density metric: proportion of text objects
        that have anchors to diagram regions.
        """
        session = self.store.Session()
        try:
            def calculate_alignment_score(dataset_id: str) -> tuple:
                """Calculate alignment score as anchor density."""
                pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()
                if not pages:
                    return 0.0, 0

                page_ids = [p.id for p in pages]

                # Count total anchors
                anchor_count = (
                    session.query(AnchorRecord)
                    .filter(AnchorRecord.page_id.in_(page_ids))
                    .count()
                )

                # Count total text objects (words)
                text_count = (
                    session.query(WordRecord)
                    .join(LineRecord, WordRecord.line_id == LineRecord.id)
                    .filter(LineRecord.page_id.in_(page_ids))
                    .count()
                )

                # Alignment score = anchors / text objects
                score = anchor_count / text_count if text_count > 0 else 0
                return score, anchor_count

            real_score, real_anchor_count = calculate_alignment_score(real_dataset_id)

            control_scores = {}
            control_anchor_counts = {}
            for ctrl_id in control_dataset_ids:
                score, count = calculate_alignment_score(ctrl_id)
                control_scores[ctrl_id] = score
                control_anchor_counts[ctrl_id] = count

            # Statistical test
            if control_scores:
                mean_control = sum(control_scores.values()) / len(control_scores)
                variance = sum((s - mean_control) ** 2 for s in control_scores.values()) / len(control_scores)
                std_control = math.sqrt(variance) if variance > 0 else 0.1

                z_score = (real_score - mean_control) / std_control if std_control > 0 else 0
            else:
                mean_control = 0
                std_control = 0.1
                z_score = 0

            # Determine outcome based on z-score
            if z_score >= 2.0:
                outcome = "SUPPORTED"
            elif z_score >= 1.0:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "FALSIFIED"

            metrics = {
                f"{real_dataset_id}:anchor_count": float(real_anchor_count),
                f"{real_dataset_id}:alignment_score": real_score,
                f"{real_dataset_id}:z_score": z_score,
            }

            for ctrl_id, score in control_scores.items():
                metrics[f"{ctrl_id}:alignment_score"] = score
                metrics[f"{ctrl_id}:anchor_count"] = float(control_anchor_counts.get(ctrl_id, 0))

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "scrambling_survival",
                    "real_alignment_score": real_score,
                    "control_mean": mean_control,
                    "control_std": std_control,
                    "z_score": z_score,
                    "significance_threshold": 2.0,
                    "verdict": "Text-diagram alignment is significant" if outcome == "SUPPORTED" else "Alignment may be geometric artifact",
                }
            )
        finally:
            session.close()

    def _run_simulated(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """Legacy simulated implementation."""
        session = self.store.Session()
        try:
            real_anchor_count = 0
            real_pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            for page in real_pages:
                anchors = session.query(AnchorRecord).filter_by(page_id=page.id).all()
                real_anchor_count += len(anchors)

            control_anchor_counts = {}
            for ctrl_id in control_dataset_ids:
                count = 0
                ctrl_pages = session.query(PageRecord).filter_by(dataset_id=ctrl_id).all()
                for page in ctrl_pages:
                    anchors = session.query(AnchorRecord).filter_by(page_id=page.id).all()
                    count += len(anchors)
                control_anchor_counts[ctrl_id] = count

            real_score = 0.45
            control_scores = {}
            for ctrl_id in control_dataset_ids:
                if "scrambled" in ctrl_id:
                    control_scores[ctrl_id] = 0.38
                elif "synthetic" in ctrl_id:
                    control_scores[ctrl_id] = 0.25
                else:
                    control_scores[ctrl_id] = 0.40

            if control_scores:
                mean_control = sum(control_scores.values()) / len(control_scores)
                variance = sum((s - mean_control) ** 2 for s in control_scores.values()) / len(control_scores)
                std_control = variance ** 0.5 if variance > 0 else 0.1
                z_score = (real_score - mean_control) / std_control if std_control > 0 else 0
            else:
                mean_control = 0
                std_control = 0.1
                z_score = 0

            if z_score >= 2.0:
                outcome = "SUPPORTED"
            elif z_score >= 1.0:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "FALSIFIED"

            metrics = {
                f"{real_dataset_id}:anchor_count": float(real_anchor_count),
                f"{real_dataset_id}:alignment_score": real_score,
                f"{real_dataset_id}:z_score": z_score,
            }

            for ctrl_id, score in control_scores.items():
                metrics[f"{ctrl_id}:alignment_score"] = score
                metrics[f"{ctrl_id}:anchor_count"] = float(control_anchor_counts.get(ctrl_id, 0))

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "scrambling_survival",
                    "real_alignment_score": real_score,
                    "control_mean": mean_control,
                    "control_std": std_control,
                    "z_score": z_score,
                    "significance_threshold": 2.0,
                    "verdict": "Alignment scores show only modest degradation under scrambling.",
                    "simulated": True
                }
            )
        finally:
            session.close()


class AnchorDisruptionHypothesis(Hypothesis):
    """
    Tests if anchor relationships survive region perturbation.

    Measures how many anchors break when regions are geometrically shifted.
    """

    @property
    def id(self) -> str:
        return "anchor_disruption"

    @property
    def description(self) -> str:
        return "Anchor relationships between text and regions are robust to geometric perturbation."

    @property
    def assumptions(self) -> str:
        return (
            "Text-region anchors represent intentional relationships. "
            "Small geometric shifts should not break these relationships."
        )

    @property
    def falsification_criteria(self) -> str:
        return (
            "If >50% of anchors break under 10% region shift, "
            "the anchoring is geometrically fragile and FALSIFIED."
        )

    def run(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        if not use_real_computation("hypotheses"):
            return self._run_simulated(real_dataset_id, control_dataset_ids)

        return self._run_real(real_dataset_id, control_dataset_ids)

    def _run_real(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """
        Measure anchor survival after simulated region shift.

        For each anchor, check if the overlap would survive a shift.
        """
        session = self.store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            page_ids = [p.id for p in pages]

            # Get all anchors
            anchors = (
                session.query(AnchorRecord)
                .filter(AnchorRecord.page_id.in_(page_ids))
                .all()
            )

            if not anchors:
                return HypothesisResult(
                    outcome="INCONCLUSIVE",
                    metrics={f"{real_dataset_id}:anchor_count": 0},
                    summary={"error": "No anchors found to test"}
                )

            # Perturbation levels
            perturbation_levels = [0.05, 0.10, 0.15, 0.20]
            survival_rates = {}

            for p_level in perturbation_levels:
                surviving = 0
                total = len(anchors)

                for anchor in anchors:
                    # Get source (text) and target (region) bboxes
                    source_id = anchor.source_id
                    target_id = anchor.target_id

                    # Get source bbox (word)
                    word = session.query(WordRecord).filter_by(id=source_id).first()
                    if not word or not word.bbox:
                        surviving += 1  # Can't test, assume survives
                        continue

                    # Get target bbox (region)
                    region = session.query(RegionRecord).filter_by(id=target_id).first()
                    if not region or not region.bbox:
                        surviving += 1
                        continue

                    word_bbox = word.bbox
                    region_bbox = region.bbox

                    # Simulate region shift
                    region_width = region_bbox.get("x_max", 1) - region_bbox.get("x_min", 0)
                    region_height = region_bbox.get("y_max", 1) - region_bbox.get("y_min", 0)

                    shift_x = p_level * region_width
                    shift_y = p_level * region_height

                    # Check if word center is still within shifted region
                    word_cx = (word_bbox.get("x_min", 0) + word_bbox.get("x_max", 1)) / 2
                    word_cy = (word_bbox.get("y_min", 0) + word_bbox.get("y_max", 1)) / 2

                    # Shifted region boundaries (shift in random direction - use positive for consistency)
                    new_x_min = region_bbox.get("x_min", 0) + shift_x
                    new_x_max = region_bbox.get("x_max", 1) + shift_x
                    new_y_min = region_bbox.get("y_min", 0) + shift_y
                    new_y_max = region_bbox.get("y_max", 1) + shift_y

                    # Check containment after shift
                    if (new_x_min <= word_cx <= new_x_max and
                            new_y_min <= word_cy <= new_y_max):
                        surviving += 1

                survival_rate = surviving / total if total > 0 else 1.0
                survival_rates[p_level] = survival_rate

            survival_at_10pct = survival_rates.get(0.10, 1.0)

            # Falsified if <50% survive at 10% shift
            if survival_at_10pct < 0.50:
                outcome = "FALSIFIED"
            elif survival_at_10pct < 0.70:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:anchor_count": float(len(anchors)),
                f"{real_dataset_id}:survival_at_10pct": survival_at_10pct,
            }

            for p, rate in survival_rates.items():
                metrics[f"{real_dataset_id}:survival_at_{int(p*100)}pct"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "anchor_disruption",
                    "perturbation_tested": 0.10,
                    "survival_rate": survival_at_10pct,
                    "survival_threshold": 0.50,
                    "survival_curve": survival_rates,
                    "verdict": "Anchors are fragile under geometric shift" if outcome == "FALSIFIED" else "Anchors survive moderate perturbation",
                }
            )
        finally:
            session.close()

    def _run_simulated(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """Legacy simulated implementation."""
        session = self.store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=real_dataset_id).all()
            page_ids = [p.id for p in pages]

            anchor_count = (
                session.query(AnchorRecord)
                .filter(AnchorRecord.page_id.in_(page_ids))
                .count()
            )

            # Simulated survival rates (anchors are fragile)
            perturbation_levels = [0.05, 0.10, 0.15, 0.20]
            survival_rates = {}

            for p in perturbation_levels:
                # Exponential decay
                survival = max(0.1, 1.0 - (p * 5))
                survival_rates[p] = survival

            survival_at_10pct = survival_rates.get(0.10, 0.5)

            if survival_at_10pct < 0.50:
                outcome = "FALSIFIED"
            elif survival_at_10pct < 0.70:
                outcome = "WEAKLY_SUPPORTED"
            else:
                outcome = "SUPPORTED"

            metrics = {
                f"{real_dataset_id}:anchor_count": float(anchor_count),
                f"{real_dataset_id}:survival_at_10pct": survival_at_10pct,
            }

            for p, rate in survival_rates.items():
                metrics[f"{real_dataset_id}:survival_at_{int(p*100)}pct"] = rate

            return HypothesisResult(
                outcome=outcome,
                metrics=metrics,
                summary={
                    "test": "anchor_disruption",
                    "perturbation_tested": 0.10,
                    "survival_rate": survival_at_10pct,
                    "survival_threshold": 0.50,
                    "survival_curve": survival_rates,
                    "verdict": "Anchors are fragile under geometric shift",
                    "simulated": True
                }
            )
        finally:
            session.close()
