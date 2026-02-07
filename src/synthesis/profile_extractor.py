"""
Pharmaceutical Section Profile Extractor

Extracts structural profiles from surviving jar pages (f88r-f96v).
These profiles define hard constraints for synthesis.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import random

from synthesis.interface import (
    SectionProfile,
    PageProfile,
    JarProfile,
    GapDefinition,
    GapStrength,
)


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

    # Simulated structural data based on manuscript characteristics
    # In production, this would be extracted from Phase 1 ledgers
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

    def __init__(self, store=None):
        self.store = store
        self.section_profile = SectionProfile()

    def extract_page_profile(self, page_id: str) -> PageProfile:
        """Extract structural profile for a single page."""
        data = self.SIMULATED_PAGE_DATA.get(page_id, {})

        jar_count = data.get("jars", 4)
        total_blocks = data.get("blocks", 8)
        total_lines = data.get("lines", 24)
        total_words = data.get("words", 72)

        # Generate jar profiles
        jars = []
        for i in range(jar_count):
            # Simulated jar geometry (normalized 0-1 coordinates)
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

        # Compute text metrics (from Phase 2 findings)
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

        In production, this would use Phase 1 text ledger.
        Here we simulate with characteristic Voynichese tokens.
        """
        # Simulated Voynichese-like tokens
        voynich_tokens = [
            "daiin", "chedy", "qokedy", "shedy", "qokeedy",
            "chol", "chor", "cheol", "shor", "shol",
            "okedy", "okeedy", "okaiin", "otedy", "oteey",
            "ar", "or", "al", "ol", "am", "om",
            "qokaiin", "qotedy", "qokeey", "qokain",
            "dain", "chain", "shain", "kain",
            "chey", "shey", "dey", "key",
        ]

        # Return 4-6 tokens as seam context
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
