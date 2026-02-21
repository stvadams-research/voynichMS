"""
Foundation Hypotheses Library

Real implementations that compute hypothesis metrics from actual database records.
"""

import logging
import math
from collections import Counter

from phase1_foundation.hypotheses.interface import Hypothesis, HypothesisResult
from phase1_foundation.storage.metadata import (
    GlyphCandidateRecord,
    LineRecord,
    PageRecord,
    WordRecord,
)

logger = logging.getLogger(__name__)


class GlyphPositionHypothesis(Hypothesis):
    """
    Tests whether certain glyphs are positionally constrained (start/mid/end of words).

    Real implementation computes Shannon entropy from actual GlyphCandidateRecord
    positions within words.
    """

    @property
    def id(self) -> str:
        return "glyph_position_entropy"

    @property
    def description(self) -> str:
        return "Certain glyphs are positionally constrained (start/mid/end of words)."

    @property
    def assumptions(self) -> str:
        return "Word boundaries are meaningful. Glyph identities are consistent."

    @property
    def falsification_criteria(self) -> str:
        return "If positional entropy in Real data is >= Scrambled data, the constraints are artifacts."

    def run(self, real_dataset_id: str, control_dataset_ids: list[str]) -> HypothesisResult:
        return self._run_real(real_dataset_id, control_dataset_ids)

    def _run_real(self, real_dataset_id: str, control_dataset_ids: list[str]) -> HypothesisResult:
        """
        Calculate positional entropy from actual glyph positions.

        Shannon entropy formula: H = -sum(p * log2(p))
        Computed separately for start, middle, and end positions.
        """
        real_entropy = self._calculate_entropy_real(real_dataset_id)
        control_entropies = {cid: self._calculate_entropy_real(cid) for cid in control_dataset_ids}

        # Compare: hypothesis is that Real < Control (more constrained)
        outcome = "SUPPORTED"
        min_control = min(control_entropies.values()) if control_entropies else 1.0

        if real_entropy >= min_control:
            outcome = "FALSIFIED"
        elif real_entropy > (min_control * 0.8):
            outcome = "WEAKLY_SUPPORTED"

        metrics = {
            f"{real_dataset_id}:entropy": real_entropy
        }
        for cid, val in control_entropies.items():
            metrics[f"{cid}:entropy"] = val

        return HypothesisResult(
            outcome=outcome,
            metrics=metrics,
            summary={
                "real_entropy": real_entropy,
                "control_entropies": control_entropies,
                "margin": min_control - real_entropy
            }
        )

    def _calculate_entropy_real(self, dataset_id: str) -> float:
        """
        Compute Shannon entropy of glyph positional distribution.

        For each glyph identity (character), we track whether it appears at:
        - Start (index 0)
        - End (last index in word)
        - Middle (any other position)

        Low entropy = glyphs are constrained to specific positions
        High entropy = glyphs appear randomly at any position
        """
        session = self.store.Session()
        try:
            # Get all pages for this dataset
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()

            if not pages:
                logger.warning("No pages found for dataset %s, returning NaN entropy", dataset_id)
                return float("nan")

            page_ids = [p.id for p in pages]

            # Collect glyph position data
            # Position categories: 'start', 'middle', 'end'
            glyph_positions: dict[str, Counter] = {}  # glyph_symbol -> Counter of positions

            for page_id in page_ids:
                lines = session.query(LineRecord).filter_by(page_id=page_id).all()

                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).all()

                    for word in words:
                        glyphs = (
                            session.query(GlyphCandidateRecord)
                            .filter_by(word_id=word.id)
                            .order_by(GlyphCandidateRecord.glyph_index)
                            .all()
                        )

                        if not glyphs:
                            continue

                        word_length = len(glyphs)

                        for i, glyph in enumerate(glyphs):
                            # Use glyph_id or derive symbol from alignments
                            # For now, use glyph's id as identity proxy
                            glyph_symbol = self._get_glyph_symbol(session, glyph)

                            if glyph_symbol not in glyph_positions:
                                glyph_positions[glyph_symbol] = Counter()

                            # Determine position category
                            if i == 0:
                                position = "start"
                            elif i == word_length - 1:
                                position = "end"
                            else:
                                position = "middle"

                            glyph_positions[glyph_symbol][position] += 1

            if not glyph_positions:
                logger.warning("No glyph data found for dataset %s, returning NaN entropy", dataset_id)
                return float("nan")

            # Compute entropy for each glyph and average
            entropies = []
            for symbol, position_counts in glyph_positions.items():
                total = sum(position_counts.values())
                if total < 3:  # Skip rare glyphs
                    continue

                entropy = 0.0
                for count in position_counts.values():
                    if count > 0:
                        p = count / total
                        entropy -= p * math.log2(p)

                # Normalize by max possible entropy (3 positions = log2(3) = 1.585)
                max_entropy = math.log2(3)
                normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

                entropies.append(normalized_entropy)

            if not entropies:
                logger.warning("No entropy values computed for dataset %s, returning NaN", dataset_id)
                return float("nan")

            # Return average normalized entropy
            if not entropies:
                logger.warning("No entropies available for dataset %s, returning NaN", dataset_id)
                return float("nan")
                
            return sum(entropies) / len(entropies)

        finally:
            session.close()

    def _get_glyph_symbol(self, session, glyph: GlyphCandidateRecord) -> str:
        """
        Get the symbol/identity for a glyph.

        Tries to get from GlyphAlignmentRecord, falls back to bbox-based hash.
        """
        from phase1_foundation.storage.metadata import GlyphAlignmentRecord

        alignment = (
            session.query(GlyphAlignmentRecord)
            .filter_by(glyph_id=glyph.id)
            .first()
        )

        if alignment and alignment.symbol:
            return alignment.symbol

        # Fallback: use bbox dimensions as a rough proxy for glyph identity
        bbox = glyph.bbox
        if bbox:
            width = bbox.get("x_max", 0) - bbox.get("x_min", 0)
            height = bbox.get("y_max", 0) - bbox.get("y_min", 0)
            # Bucket into size categories
            w_bucket = int(width * 10)
            h_bucket = int(height * 10)
            return f"g_{w_bucket}_{h_bucket}"

        return f"glyph_{glyph.id[:8]}"
