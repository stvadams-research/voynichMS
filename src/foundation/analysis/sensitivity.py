from typing import Callable, List, Dict, Any
from foundation.storage.metadata import MetadataStore

class SensitivityAnalyzer:
    def __init__(self, store: MetadataStore):
        self.store = store

    def run_parameter_sweep(
        self, 
        structure_id: str, 
        metric_func: Callable[[Any], float], 
        param_name: str, 
        value_range: List[Any],
        run_id: str
    ) -> List[Dict[str, Any]]:
        """
        Run a sensitivity analysis by sweeping a parameter.
        metric_func: A function that takes a parameter value and returns a metric score.
        """
        results = []
        for val in value_range:
            try:
                score = metric_func(val)
                self.store.add_sensitivity_result(
                    structure_id=structure_id,
                    parameter_name=param_name,
                    parameter_value=str(val),
                    metric_value=score,
                    run_id=run_id
                )
                results.append({"param": val, "score": score})
            except Exception as e:
                # Log error but continue sweep
                print(f"Error in sensitivity sweep for {param_name}={val}: {e}")
                
        return results
