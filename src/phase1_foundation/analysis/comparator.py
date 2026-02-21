import logging
from typing import Any

from phase1_foundation.config import get_analysis_thresholds
from phase1_foundation.metrics.interface import MetricResult
from phase1_foundation.storage.metadata import MetadataStore

logger = logging.getLogger(__name__)

class Comparator:
    def __init__(self, store: MetadataStore):
        self.store = store
        thresholds = get_analysis_thresholds().get("comparator", {})
        self.significant_difference = float(thresholds.get("significant_difference", 0.05))
        self.negligible_difference = float(thresholds.get("negligible_difference", 0.02))

    def compare_datasets(self, real_id: str, control_id: str, metric_results: list[MetricResult]) -> dict[str, Any]:
        """
        Compare metric results between real and control datasets.
        """
        comparison = {}
        
        # Group by metric
        metrics = {}
        for r in metric_results:
            if r.metric_name not in metrics:
                metrics[r.metric_name] = {}
            metrics[r.metric_name][r.dataset_id] = r.value

        for metric_name, values in metrics.items():
            real_val = values.get(real_id)
            control_val = values.get(control_id)
            
            if real_val is not None and control_val is not None:
                diff = real_val - control_val
                # Simple logic for Level 3 demo
                # If difference is significant, it survives
                classification = "FAILS"
                if abs(diff) > self.significant_difference:
                    classification = "SURVIVES"
                elif abs(diff) > self.negligible_difference:
                    classification = "PARTIAL"
                
                comparison[metric_name] = {
                    "real": real_val,
                    "control": control_val,
                    "diff": diff,
                    "classification": classification
                }
                
                # Persist
                self.store.add_metric_comparison(
                    metric_name=metric_name,
                    real_dataset_id=real_id,
                    control_dataset_id=control_id,
                    difference_score=diff,
                    classification=classification
                )
                
        return comparison
