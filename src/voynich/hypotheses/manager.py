from typing import Dict, Type, List
from voynich.storage.metadata import MetadataStore
from voynich.hypotheses.interface import Hypothesis, HypothesisResult

class HypothesisManager:
    def __init__(self, store: MetadataStore):
        self.store = store
        self._registry: Dict[str, Type[Hypothesis]] = {}

    def register_hypothesis(self, hypothesis_cls: Type[Hypothesis]):
        # Instantiate temporarily to get ID? Or make ID a class attribute?
        # Let's assume ID is a property, so we might need to instantiate or inspect.
        # For simplicity, let's instantiate.
        temp_instance = hypothesis_cls(self.store)
        self._registry[temp_instance.id] = hypothesis_cls
        
        # Ensure it's in the DB
        self.store.add_hypothesis(
            id=temp_instance.id,
            description=temp_instance.description,
            assumptions=temp_instance.assumptions,
            falsification_criteria=temp_instance.falsification_criteria
        )

    def run_hypothesis(self, hypothesis_id: str, real_dataset_id: str, control_dataset_ids: List[str], run_id: str) -> HypothesisResult:
        if hypothesis_id not in self._registry:
            raise ValueError(f"Hypothesis {hypothesis_id} not registered")
            
        hypothesis_cls = self._registry[hypothesis_id]
        hypothesis = hypothesis_cls(self.store)
        
        result = hypothesis.run(real_dataset_id, control_dataset_ids)
        
        # Persist results
        self.store.add_hypothesis_run(
            hypothesis_id=hypothesis_id,
            run_id=run_id,
            outcome=result.outcome,
            result_summary=result.summary
        )
        
        for metric_name, value in result.metrics.items():
            # We need to know which dataset the metric applies to.
            # The result.metrics dict might be flat or nested.
            # Let's assume flat for now, or we can parse keys like "real:entropy".
            # Better: HypothesisResult metrics should be structured.
            # For now, we'll store them associated with the run, not specific dataset rows unless we parse.
            # Let's just store them as generic metrics for the hypothesis run.
            # But `add_hypothesis_metric` requires dataset_id.
            # So the Hypothesis should return metrics keyed by dataset_id?
            # Let's handle parsing "dataset:metric" keys.
            
            parts = metric_name.split(":", 1)
            if len(parts) == 2:
                ds_id, m_name = parts
                self.store.add_hypothesis_metric(
                    run_id=run_id,
                    hypothesis_id=hypothesis_id,
                    dataset_id=ds_id,
                    metric_name=m_name,
                    value=value
                )
            else:
                # Global metric
                self.store.add_hypothesis_metric(
                    run_id=run_id,
                    hypothesis_id=hypothesis_id,
                    dataset_id="global",
                    metric_name=metric_name,
                    value=value
                )
                
        return result
