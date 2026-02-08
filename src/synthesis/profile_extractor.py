"""
Pharmaceutical Section Profile Extractor

Extracts structural profiles from surviving jar pages (f88r-f96v).
These profiles define hard constraints for synthesis.
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import math
import random

from synthesis.interface import (
    SectionProfile,
    PageProfile,
    JarProfile,
    GapDefinition,
    GapStrength,
)
from foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    WordRecord,
    LineRecord,
    RegionRecord,
    AnchorRecord,
    GlyphCandidateRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from foundation.config import use_real_computation


class PharmaceuticalProfileExtractor:
    """
    Extracts structural profiles from the pharmaceutical (jar) section.

    Uses Phase 1/2 data to derive:
    - Jar count per page
    - Jar bounding-box geometry
    - Text block distributions
    - Token metrics
    """

    # Pharmaceutical section page range
    SECTION_PAGES = [
        "f88r", "f88v", "f89r", "f89v",
        "f90r", "f90v", "f91r", "f91v",
        "f92r", "f92v", "f93r", "f93v",
        "f94r", "f94v", "f95r", "f95v",
        "f96r", "f96v",
    ]

    # Legacy simulated data for backward compatibility
    SIMULATED_PAGE_DATA = {
        "f88r": {"jars": 4, "blocks": 8, "lines": 24, "words": 72},
        "f88v": {"jars": 4, "blocks": 8, "lines": 26, "words": 78},
        "f89r": {"jars": 5, "blocks": 10, "lines": 30, "words": 90},
        "f89v": {"jars": 5, "blocks": 10, "lines": 28, "words": 84},
        "f90r": {"jars": 4, "blocks": 8, "lines": 24, "words": 72},
        "f90v": {"jars": 4, "blocks": 8, "lines": 25, "words": 75},
        "f91r": {"jars": 5, "blocks": 10, "lines": 30, "words": 90},
        "f91v": {"jars": 4, "blocks": 8, "lines": 26, "words": 78},
        "f92r": {"jars": 5, "blocks": 10, "lines": 32, "words": 96},
        "f92v": {"jars": 5, "blocks": 10, "lines": 30, "words": 90},
        "f93r": {"jars": 4, "blocks": 8, "lines": 24, "words": 72},
        "f93v": {"jars": 4, "blocks": 8, "lines": 25, "words": 75},
        "f94r": {"jars": 5, "blocks": 10, "lines": 28, "words": 84},
        "f94v": {"jars": 4, "blocks": 8, "lines": 26, "words": 78},
        "f95r": {"jars": 5, "blocks": 10, "lines": 30, "words": 90},
        "f95v": {"jars": 5, "blocks": 10, "lines": 28, "words": 84},
        "f96r": {"jars": 4, "blocks": 8, "lines": 24, "words": 72},
        "f96v": {"jars": 3, "blocks": 6, "lines": 18, "words": 54},
    }

    def __init__(self, store: Optional[MetadataStore] = None):
        self.store = store
        self.section_profile = SectionProfile()

    def extract_page_profile(self, page_id: str) -> PageProfile:
        """Extract structural profile for a single page."""
        if not use_real_computation("synthesis") or self.store is None:
            return self._extract_simulated_profile(page_id)

        return self._extract_real_profile(page_id)

    def _extract_real_profile(self, page_id: str) -> PageProfile:
        """Extract profile from actual database records."""
        session = self.store.Session()
        try:
            # Find the page
            page = session.query(PageRecord).filter_by(id=page_id).first()
            if not page:
                # Fall back to simulated if page not found
                return self._extract_simulated_profile(page_id)

            # Count jars (mid-scale regions, typically visual elements)
            jar_regions = (
                session.query(RegionRecord)
                .filter_by(page_id=page.id, scale="mid")
                .all()
            )
            jar_count = len(jar_regions)

            # Count lines
            lines = session.query(LineRecord).filter_by(page_id=page.id).all()
            total_lines = len(lines)

            # Count words
            total_words = 0
            for line in lines:
                word_count = (
                    session.query(WordRecord)
                    .filter_by(line_id=line.id)
                    .count()
                )
                total_words += word_count

            # Count text blocks (coarse-scale regions with text)
            text_regions = (
                session.query(RegionRecord)
                .filter_by(page_id=page.id, scale="coarse")
                .all()
            )
            total_blocks = len(text_regions) if text_regions else max(1, jar_count * 2)

            # Build jar profiles with real geometry
            jars = []
            for i, region in enumerate(jar_regions):
                bbox = region.bbox or {}
                x = bbox.get("x_min", 0.1 + (i % 2) * 0.45)
                y = bbox.get("y_min", 0.1 + (i // 2) * 0.25)
                width = bbox.get("x_max", x + 0.35) - x
                height = bbox.get("y_max", y + 0.20) - y

                # Count words anchored to this region
                anchored_word_count = (
                    session.query(AnchorRecord)
                    .filter_by(page_id=page.id, target_id=region.id, source_type="word")
                    .count()
                )

                # Estimate lines from anchored words (roughly 3 words per line)
                estimated_lines = max(1, anchored_word_count // 3)

                jar = JarProfile(
                    jar_id=f"{page_id}_jar_{i}",
                    bounding_box=(x, y, width, height),
                    text_block_count=max(1, total_blocks // max(1, jar_count)),
                    line_count=estimated_lines,
                    word_count=anchored_word_count if anchored_word_count > 0 else total_words // max(1, jar_count),
                )
                jars.append(jar)

            # Compute text metrics from actual data
            mean_word_length = self._compute_mean_word_length(session, page.id)
            token_repetition_rate = self._compute_repetition_rate(session, page.id)
            positional_entropy = self._compute_positional_entropy(session, page.id)
            locality_radius = self._compute_locality_radius(session, page.id)
            information_density = self._compute_information_density(session, page.id)

            profile = PageProfile(
                page_id=page_id,
                jar_count=jar_count if jar_count > 0 else 4,  # Default if no regions
                jars=jars,
                total_text_blocks=total_blocks,
                total_lines=total_lines if total_lines > 0 else 24,
                total_words=total_words if total_words > 0 else 72,
                layout_density=total_words / max(1, total_blocks),
                mean_word_length=mean_word_length,
                token_repetition_rate=token_repetition_rate,
                positional_entropy=positional_entropy,
                locality_radius=locality_radius,
                information_density=information_density,
            )

            return profile

        finally:
            session.close()

    def _compute_mean_word_length(self, session, page_id: str) -> float:
        """Compute mean word length from glyph counts."""
        lines = session.query(LineRecord).filter_by(page_id=page_id).all()

        total_glyphs = 0
        total_words = 0

        for line in lines:
            words = session.query(WordRecord).filter_by(line_id=line.id).all()
            for word in words:
                glyph_count = (
                    session.query(GlyphCandidateRecord)
                    .filter_by(word_id=word.id)
                    .count()
                )
                if glyph_count > 0:
                    total_glyphs += glyph_count
                    total_words += 1

        if total_words == 0:
            return 5.2  # Default

        return total_glyphs / total_words

    def _compute_repetition_rate(self, session, page_id: str) -> float:
        """Compute token repetition rate."""
        trans_lines = (
            session.query(TranscriptionLineRecord)
            .filter_by(page_id=page_id)
            .all()
        )

        if not trans_lines:
            return 0.20  # Default

        tokens = []
        for line in trans_lines:
            line_tokens = (
                session.query(TranscriptionTokenRecord)
                .filter_by(line_id=line.id)
                .all()
            )
            tokens.extend([t.content for t in line_tokens])

        if not tokens:
            return 0.20

        token_counts = Counter(tokens)
        total = len(tokens)
        unique = len(token_counts)

        return 1.0 - (unique / total) if total > 0 else 0.0

    def _compute_positional_entropy(self, session, page_id: str) -> float:
        """Compute positional entropy of glyphs within words."""
        lines = session.query(LineRecord).filter_by(page_id=page_id).all()

        positions = {"start": Counter(), "mid": Counter(), "end": Counter()}

        for line in lines:
            words = session.query(WordRecord).filter_by(line_id=line.id).all()
            for word in words:
                glyphs = (
                    session.query(GlyphCandidateRecord)
                    .filter_by(word_id=word.id)
                    .order_by(GlyphCandidateRecord.glyph_index)  # Changed from .position to .glyph_index
                    .all()
                )

                if len(glyphs) == 0:
                    continue

                for i, glyph in enumerate(glyphs):
                    # Try to get symbol from alignment, fallback to ID if needed (though alignment preferred)
                    # For entropy, we need symbols. If not populated, this metric will be skewed.
                    # We'll try to join with GlyphAlignmentRecord if possible, but for now let's assume
                    # we can get symbol via a separate query or if it's not joined.
                    
                    # Optimization: In real run, we should join. For now, let's just use a placeholder
                    # or try to get alignment.
                    
                    from foundation.storage.metadata import GlyphAlignmentRecord
                    alignment = session.query(GlyphAlignmentRecord).filter_by(glyph_id=glyph.id).first()
                    symbol = alignment.symbol if alignment else f"g_{glyph.id}"

                    if i == 0:
                        positions["start"][symbol] += 1
                    elif i == len(glyphs) - 1:
                        positions["end"][symbol] += 1
                    else:
                        positions["mid"][symbol] += 1

        # Compute average entropy across positions
        entropies = []
        for pos, counts in positions.items():
            if not counts:
                continue

            total = sum(counts.values())
            entropy = 0.0
            for count in counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)

            max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
            normalized = entropy / max_entropy if max_entropy > 0 else 0.0
            entropies.append(normalized)

        return sum(entropies) / len(entropies) if entropies else 0.40

    def _compute_locality_radius(self, session, page_id: str) -> float:
        """Compute locality radius from anchor distances."""
        anchors = session.query(AnchorRecord).filter_by(page_id=page_id).all()

        if not anchors:
            return 3.0  # Default

        distances = []
        for anchor in anchors:
            # Get source and target positions
            word = session.query(WordRecord).filter_by(id=anchor.source_id).first()
            region = session.query(RegionRecord).filter_by(id=anchor.target_id).first()

            if not word or not word.bbox or not region or not region.bbox:
                continue

            word_bbox = word.bbox
            region_bbox = region.bbox

            # Calculate center distance (normalized)
            word_cx = (word_bbox.get("x_min", 0) + word_bbox.get("x_max", 1)) / 2
            word_cy = (word_bbox.get("y_min", 0) + word_bbox.get("y_max", 1)) / 2

            region_cx = (region_bbox.get("x_min", 0) + region_bbox.get("x_max", 1)) / 2
            region_cy = (region_bbox.get("y_min", 0) + region_bbox.get("y_max", 1)) / 2

            dist = math.sqrt((word_cx - region_cx) ** 2 + (word_cy - region_cy) ** 2)
            distances.append(dist)

        if not distances:
            return 3.0

        # Convert average distance to locality radius (inverse relationship)
        avg_dist = sum(distances) / len(distances)
        # Normalize: smaller average distance = smaller locality radius
        return max(1.0, min(6.0, avg_dist * 10))

    def _compute_information_density(self, session, page_id: str) -> float:
        """Compute information density from token entropy."""
        trans_lines = (
            session.query(TranscriptionLineRecord)
            .filter_by(page_id=page_id)
            .all()
        )

        if not trans_lines:
            return 4.0  # Default

        tokens = []
        for line in trans_lines:
            line_tokens = (
                session.query(TranscriptionTokenRecord)
                .filter_by(line_id=line.id)
                .all()
            )
            tokens.extend([t.content for t in line_tokens])

        if len(tokens) < 2:
            return 4.0

        token_counts = Counter(tokens)
        total = len(tokens)
        vocab_size = len(token_counts)

        if vocab_size < 2:
            return 1.0

        # Shannon entropy
        entropy = 0.0
        for count in token_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize to z-score equivalent (higher entropy = higher info density)
        # Typical language entropy is ~4-5 bits for word-level tokens
        # Normalize to 0-8 range like Phase 2 z-scores
        normalized_density = entropy  # Direct entropy as density measure

        return normalized_density

    def _extract_simulated_profile(self, page_id: str) -> PageProfile:
        """Legacy simulated profile extraction."""
        data = self.SIMULATED_PAGE_DATA.get(page_id, {})

        jar_count = data.get("jars", 4)
        total_blocks = data.get("blocks", 8)
        total_lines = data.get("lines", 24)
        total_words = data.get("words", 72)

        # Generate jar profiles
        jars = []
        for i in range(jar_count):
            x = 0.1 + (i % 2) * 0.45
            y = 0.1 + (i // 2) * 0.25
            width = 0.35 + random.uniform(-0.05, 0.05)
            height = 0.20 + random.uniform(-0.03, 0.03)

            jar = JarProfile(
                jar_id=f"{page_id}_jar_{i}",
                bounding_box=(x, y, width, height),
                text_block_count=total_blocks // jar_count,
                line_count=total_lines // jar_count,
                word_count=total_words // jar_count,
            )
            jars.append(jar)

        profile = PageProfile(
            page_id=page_id,
            jar_count=jar_count,
            jars=jars,
            total_text_blocks=total_blocks,
            total_lines=total_lines,
            total_words=total_words,
            layout_density=total_words / max(1, total_blocks),
            mean_word_length=5.2 + random.uniform(-0.3, 0.3),
            token_repetition_rate=0.20 + random.uniform(-0.02, 0.02),
            positional_entropy=0.40 + random.uniform(-0.05, 0.05),
            locality_radius=3.0 + random.uniform(-0.5, 0.5),
            information_density=4.0 + random.uniform(-0.3, 0.3),
        )

        return profile

    def extract_section_profile(self) -> SectionProfile:
        """Extract complete profile for the pharmaceutical section."""
        pages = []

        for page_id in self.SECTION_PAGES:
            profile = self.extract_page_profile(page_id)
            pages.append(profile)

        self.section_profile = SectionProfile(
            section_id="pharmaceutical",
            page_range=("f88r", "f96v"),
            pages=pages,
        )

        # Compute envelopes
        self._compute_envelopes()

        return self.section_profile

    def _compute_envelopes(self):
        """Compute statistical envelopes from all pages."""
        if not self.section_profile.pages:
            return

        pages = self.section_profile.pages

        # Jar count range
        jar_counts = [p.jar_count for p in pages]
        self.section_profile.jar_count_range = (min(jar_counts), max(jar_counts))

        # Text blocks per jar
        blocks_per_jar = []
        for p in pages:
            if p.jar_count > 0:
                blocks_per_jar.append(p.total_text_blocks // p.jar_count)
        if blocks_per_jar:
            self.section_profile.text_blocks_per_jar_range = (
                min(blocks_per_jar), max(blocks_per_jar)
            )

        # Lines per block
        lines_per_block = []
        for p in pages:
            if p.total_text_blocks > 0:
                lines_per_block.append(p.total_lines // p.total_text_blocks)
        if lines_per_block:
            self.section_profile.lines_per_block_range = (
                min(lines_per_block), max(lines_per_block)
            )

        # Words per line
        words_per_line = []
        for p in pages:
            if p.total_lines > 0:
                words_per_line.append(p.total_words // p.total_lines)
        if words_per_line:
            self.section_profile.words_per_line_range = (
                min(words_per_line), max(words_per_line)
            )

        # Jar geometry (from all jars)
        widths = []
        heights = []
        for p in pages:
            for j in p.jars:
                widths.append(j.bounding_box[2])
                heights.append(j.bounding_box[3])

        if widths:
            self.section_profile.jar_width_range = (min(widths), max(widths))
        if heights:
            self.section_profile.jar_height_range = (min(heights), max(heights))

        # Text metrics
        word_lengths = [p.mean_word_length for p in pages]
        self.section_profile.word_length_range = (min(word_lengths), max(word_lengths))

        rep_rates = [p.token_repetition_rate for p in pages]
        self.section_profile.repetition_rate_range = (min(rep_rates), max(rep_rates))

        entropies = [p.positional_entropy for p in pages]
        self.section_profile.entropy_range = (min(entropies), max(entropies))

        localities = [p.locality_radius for p in pages]
        self.section_profile.locality_range = (min(localities), max(localities))

        densities = [p.information_density for p in pages]
        self.section_profile.info_density_range = (min(densities), max(densities))

    def define_gaps(self) -> List[GapDefinition]:
        """
        Define codicologically defensible insertion windows.

        Based on quire structure, layout discontinuities, and jar-sequence irregularities.
        """
        gaps = [
            GapDefinition(
                gap_id="gap_a",
                strength=GapStrength.STRONG,
                preceding_page="f88v",
                following_page="f89r",
                evidence=[
                    "Abrupt layout shift between pages",
                    "Jar count discontinuity (4 → 5)",
                    "Early pharmaceutical section instability",
                    "Quire structure suggests missing bifolio",
                ],
                likely_pages_lost=(2, 4),
            ),
            GapDefinition(
                gap_id="gap_b",
                strength=GapStrength.MODERATE,
                preceding_page="f91v",
                following_page="f92r",
                evidence=[
                    "Density and alignment shift",
                    "Change in jar-text balance",
                    "Possible bifolio loss",
                ],
                likely_pages_lost=(2, 4),
            ),
            GapDefinition(
                gap_id="gap_c",
                strength=GapStrength.WEAK,
                preceding_page="f94v",
                following_page="f95r",
                evidence=[
                    "Subtle layout pattern break",
                    "Less consensus among codicologists",
                    "Possible but uncertain bifolio loss",
                ],
                likely_pages_lost=(0, 2),
            ),
        ]

        # Extract seam constraints from adjacent pages
        for gap in gaps:
            gap.left_seam_tokens = self._extract_seam_tokens(gap.preceding_page, "end")
            gap.right_seam_tokens = self._extract_seam_tokens(gap.following_page, "start")

            # Get layout densities
            left_page = next(
                (p for p in self.section_profile.pages if p.page_id == gap.preceding_page),
                None
            )
            right_page = next(
                (p for p in self.section_profile.pages if p.page_id == gap.following_page),
                None
            )

            if left_page:
                gap.layout_density_left = left_page.layout_density
            if right_page:
                gap.layout_density_right = right_page.layout_density

        return gaps

    def _extract_seam_tokens(self, page_id: str, position: str) -> List[str]:
        """
        Extract tokens near the seam (start or end of page).

        Uses actual transcription data if available, otherwise falls back to simulated.
        """
        if not use_real_computation("synthesis") or self.store is None:
            return self._extract_simulated_seam_tokens()

        session = self.store.Session()
        try:
            page = session.query(PageRecord).filter_by(id=page_id).first()
            if not page:
                return self._extract_simulated_seam_tokens()

            trans_lines = (
                session.query(TranscriptionLineRecord)
                .filter_by(page_id=page.id)
                .order_by(TranscriptionLineRecord.line_index) # Changed from line_number to line_index
                .all()
            )

            if not trans_lines:
                return self._extract_simulated_seam_tokens()

            # Get tokens from first or last lines
            if position == "start":
                target_lines = trans_lines[:2]  # First 2 lines
            else:
                target_lines = trans_lines[-2:]  # Last 2 lines

            tokens = []
            for line in target_lines:
                line_tokens = (
                    session.query(TranscriptionTokenRecord)
                    .filter_by(line_id=line.id)
                    .order_by(TranscriptionTokenRecord.token_index) # Changed from position to token_index
                    .all()
                )
                tokens.extend([t.content for t in line_tokens])

            # Return 4-6 tokens
            if len(tokens) < 4:
                return self._extract_simulated_seam_tokens()

            return tokens[:6]

        finally:
            session.close()

    def _extract_simulated_seam_tokens(self) -> List[str]:
        """Simulated Voynichese-like tokens for seam context."""
        voynich_tokens = [
            "daiin", "chedy", "qokedy", "shedy", "qokeedy",
            "chol", "chor", "cheol", "shor", "shol",
            "okedy", "okeedy", "okaiin", "otedy", "oteey",
            "ar", "or", "al", "ol", "am", "om",
            "qokaiin", "qotedy", "qokeey", "qokain",
            "dain", "chain", "shain", "kain",
            "chey", "shey", "dey", "key",
        ]

        num_tokens = random.randint(4, 6)
        return random.sample(voynich_tokens, num_tokens)

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the section profile."""
        return {
            "section_id": self.section_profile.section_id,
            "page_count": len(self.section_profile.pages),
            "jar_count_range": self.section_profile.jar_count_range,
            "text_blocks_per_jar": self.section_profile.text_blocks_per_jar_range,
            "lines_per_block": self.section_profile.lines_per_block_range,
            "words_per_line": self.section_profile.words_per_line_range,
            "jar_width_range": self.section_profile.jar_width_range,
            "jar_height_range": self.section_profile.jar_height_range,
            "word_length_range": self.section_profile.word_length_range,
            "repetition_rate_range": self.section_profile.repetition_rate_range,
            "entropy_range": self.section_profile.entropy_range,
            "locality_range": self.section_profile.locality_range,
            "info_density_range": self.section_profile.info_density_range,
        }