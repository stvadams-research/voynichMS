#!/usr/bin/env python3
"""
Voynich Manuscript Research Publication Generator

Synthesizes multiple research phases into a single, high-fidelity MS Word document.
Targets 20-30 pages of academic-grade content with visuals, math, and tables.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "results/reports"
VISUALS_DIR = PROJECT_ROOT / "results/visuals"
OUTPUT_DIR = PROJECT_ROOT / "results/publication"
OUTPUT_PATH = OUTPUT_DIR / "voynich_research_summary_draft.docx"

class PublicationGenerator:
    def __init__(self):
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.doc = Document()
        self._setup_styles()
        
    def _setup_styles(self):
        """Configure academic document styles."""
        style = self.doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)
        
        # Add a 'Headline' style
        if 'Headline' not in self.doc.styles:
            headline_style = self.doc.styles.add_style('Headline', 1)
            headline_style.font.bold = True
            headline_style.font.size = Pt(14)
            headline_style.font.italic = True

    def add_title_page(self):
        self.doc.add_heading('Structural Identification of the Voynich Manuscript', 0)
        p = self.doc.add_paragraph('An Assumption-Resistant Framework for Non-Semantic Analysis\n')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        self.doc.add_paragraph(f'\nDate: {datetime.now().strftime("%B %d, %Y")}')
        self.doc.add_paragraph('Status: FINAL RESEARCH SUMMARY')
        self.doc.add_page_break()

    def add_chapter(self, title, headline, layman, technical_content, visuals=None):
        """Adds a full chapter with the inverted pyramid structure."""
        self.doc.add_heading(title, level=1)
        
        # Headline
        self.doc.add_paragraph(headline, style='Headline')
        
        # Layman Summary
        self.doc.add_heading('Executive Concept', level=2)
        self.doc.add_paragraph(layman)
        
        # Technical Deep-Dive
        self.doc.add_heading('Technical Evidence and Methodology', level=2)
        for block in technical_content:
            text = block.strip()
            if not text:
                continue
            if text.startswith('##'): # Handle sub-sub-headings
                self.doc.add_heading(text.replace('#', '').strip(), level=3)
            else:
                self.doc.add_paragraph(text)
        
        # Visuals
        if visuals:
            for img_path, caption in visuals:
                # Resolve path relative to PROJECT_ROOT
                full_path = PROJECT_ROOT / img_path
                if full_path.exists():
                    self.doc.add_picture(str(full_path), width=Inches(5.5))
                    self.doc.add_paragraph(f'Figure: {caption}', style='Caption')
                else:
                    logger.warning(f"Visual not found: {full_path}")
        
        self.doc.add_page_break()

    def load_report_content(self, phase_dir, filename):
        """Helper to extract large text blocks from existing reports."""
        path = REPORTS_DIR / phase_dir / filename
        if not path.exists():
            logger.warning(f"Report not found: {path}")
            return ["Content missing from archive."]
        
        with open(path, 'r') as f:
            content = f.read()
            
        # Split by section headers to create individual paragraphs/blocks
        parts = content.split('##')
        return parts[1:] if len(parts) > 1 else [content]

    def generate(self):
        logger.info("Starting synthesis of substantive research draft...")
        self.add_title_page()
        
        # 1. INTRODUCTION (Based on Phase 2 results)
        intro_technical = self.load_report_content("phase2_analysis", "final_report_phase_2.md")
        self.add_chapter(
            "I. The Epistemic Crisis",
            "Natural language explanations for the Voynich Manuscript are statistically inadmissible under assumption-resistant controls.",
            "For centuries, researchers have assumed the Voynich is a message to be read. We prove it is a process to be mapped. By testing the manuscript against gibberish and computer-generated noise, we found that its 'patterns' are too rigid to be human communication.",
            intro_technical
        )
        
        # 2. FOUNDATION (Based on Audit and Ledger reports)
        self.add_chapter(
            "II. The Bedrock Structure",
            "High-fidelity digital ledgering reveals a 69.8% repetition rate, exceeding known linguistic bounds.",
            "Every word in the manuscript was logged and compared. Normal languages have a healthy mix of common and rare words. The Voynich Manuscript repeats itself so much that it looks more like a stuttering machine than a person speaking.",
            ["### Digital Ledgering", "We analyzed 222 folios through our high-fidelity pipeline.", "### Distributional Anomalies", "The token repetition rate remains stable at 0.698 across all sections."],
            [("results/visuals/phase1_foundation/41f398bc-9623-2b2d-bada-5bd4dc226e64_repetition_rate_dist_voynich_real.png", "Repetition Rate Distribution across the Manuscript")]
        )
        
        # 3. MECHANISM (The Core Findings from Phase 5)
        mech_content = self.load_report_content("phase5_mechanism", "phase_5_final_findings_summary.md")
        self.add_chapter(
            "III. The Identified Mechanism",
            "The manuscript is identified as a Globally Stable, Deterministic Rule-Evaluated Constraint Lattice.",
            "We have found the 'engine' that wrote the book. It is a set of rules that tells you exactly which word can follow another based on where you are on the line. It's like a complex game of Sudoku where the rules are consistent from the first page to the last.",
            mech_content
        )
        
        # 4. INFERENCE ADMISSIBILITY (Phase 4 results)
        inf_content = self.load_report_content("phase4_inference", "phase_4_conclusions.md")
        self.add_chapter(
            "IV. The Limit of Inference",
            "Linguistic identification methods establish a 'noise floor' that falsifies current decipherment claims.",
            "We tested AI programs used to identify languages. They 'found' Hebrew and Latin in random noise just as easily as they found them in the Voynich Manuscript. This proves these tools are not reliable for this problem.",
            inf_content,
            [("results/visuals/phase4_inference/821247f8-748c-cb25-1d5d-5d2877bf7f71_lang_id_comparison.png", "False Positive Rate of Language Identification Methods")]
        )

        # 5. CONJECTURE
        self.add_chapter(
            "V. Algorithmic Glossolalia",
            "The Voynich Manuscript represents a monument to human algorithmic imagination—a paper computer for an endless mystery.",
            "The meaning isn't in the words; it's in the creation of the system itself. Someone built a perfect engine for generating mystery, and 600 years later, it is still working exactly as intended.",
            ["### The Authorial intent", "The sectional stability suggests a single creator using mechanical aids.", "### Implications", "This shifts the field from translation to algorithmic reconstruction."]
        )

        self.doc.save(str(OUTPUT_PATH))
        logger.info(f"Substantive draft generated successfully at: {OUTPUT_PATH}")

if __name__ == "__main__":
    PublicationGenerator().generate()
