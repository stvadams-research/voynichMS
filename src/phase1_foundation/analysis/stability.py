import logging
from typing import Any

from phase1_foundation.storage.metadata import AnchorRecord, MetadataStore

logger = logging.getLogger(__name__)

class AnchorStabilityAnalyzer:
    def __init__(self, store: MetadataStore):
        self.store = store

    def compare_anchor_counts(self, real_dataset_id: str, control_dataset_id: str, run_id: str) -> dict[str, Any]:
        """
        Compare anchor counts between real and control datasets.
        """
        session = self.store.Session()
        try:
            # Helper to count anchors for a dataset
            # We assume anchors are linked to pages which are linked to datasets.
            # So we join Anchor -> Page -> Dataset
            from phase1_foundation.storage.metadata import PageRecord
            
            def count_anchors(dataset_id):
                results = session.query(AnchorRecord.relation_type, AnchorRecord.id).\
                    join(PageRecord, AnchorRecord.page_id == PageRecord.id).\
                    filter(PageRecord.dataset_id == dataset_id).all()
                
                counts = {}
                for r_type, _ in results:
                    counts[r_type] = counts.get(r_type, 0) + 1
                return counts

            real_counts = count_anchors(real_dataset_id)
            control_counts = count_anchors(control_dataset_id)
            
            comparison = {
                "real": real_counts,
                "control": control_counts,
                "degradation": {}
            }
            
            # Calculate degradation
            all_types = set(real_counts.keys()) | set(control_counts.keys())
            for t in all_types:
                r = real_counts.get(t, 0)
                c = control_counts.get(t, 0)
                
                if r > 0:
                    deg = (r - c) / r
                else:
                    deg = 0.0 # No anchors to degrade
                
                comparison["degradation"][t] = deg
                
                # Persist metric
                self.store.add_anchor_metric(
                    run_id=run_id,
                    dataset_id=real_dataset_id,
                    metric_name=f"anchor_stability_{t}",
                    value=deg,
                    details={"real_count": r, "control_count": c}
                )
            
            return comparison
        finally:
            session.close()
