from foundation.core.ids import RunID, PageID
import logging
logger = logging.getLogger(__name__)

def generate_run_summary(run_id: RunID):
    """
    Stub: Generate a summary report for a completed run.
    """
    # In Level 2, this would generate HTML/Markdown report
    logger.info("Generating summary for run %s...", run_id)
    pass

def generate_overlays(page_id: PageID):
    """
    Stub: Generate visual overlays for a page.
    """
    # In Level 2, this would draw boxes on the image
    logger.info("Generating overlays for page %s...", page_id)
    pass
