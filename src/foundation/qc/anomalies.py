from typing import Dict, Optional
from foundation.runs.manager import RunManager
from foundation.storage.metadata import MetadataStore
import logging
logger = logging.getLogger(__name__)

class AnomalyLogger:
    def __init__(self, metadata_store: MetadataStore):
        self.store = metadata_store

    def log(self, severity: str, category: str, message: str, details: Optional[Dict] = None):
        """
        Log an anomaly to the active run.
        """
        try:
            run = RunManager.get_current_run()
            self.store.add_anomaly(
                run_id=run.run_id,
                severity=severity,
                category=category,
                message=message,
                details=details
            )
            # Also print to console/log if critical?
            # For now, just DB.
        except RuntimeError:
            logger.warning("Anomaly occurred outside active run: %s", message)
