from typing import List
from phase1_foundation.core.ids import FolioID
import logging
logger = logging.getLogger(__name__)

def check_unique_ids(ids: List[str]) -> bool:
    """
    Verify that a list of IDs contains no duplicates.
    """
    return len(ids) == len(set(ids))

def check_folio_format(ids: List[str]) -> List[str]:
    """
    Return a list of invalid folio IDs.
    """
    invalid = []
    for i in ids:
        try:
            FolioID(i)
        except ValueError:
            logger.warning("Invalid folio ID detected during QC: %s", i)
            invalid.append(i)
    return invalid
