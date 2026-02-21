import logging
from collections.abc import Callable
from typing import Any

from phase1_foundation.storage.metadata import MetadataStore

logger = logging.getLogger(__name__)

class SensitivityAnalyzer:
    def __init__(self, store: MetadataStore):
        self.store = store

    def run_parameter_sweep(
        self, 
        structure_id: str, 
        metric_func: Callable[[Any], float], 
        param_name: str, 
        value_range: list[Any],
        run_id: str
    ) -> list[dict[str, Any]]:
        """
        Run a sensitivity phase2_analysis by sweeping a parameter.
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
                logger.error(
                    "Sensitivity sweep error for %s=%s: %s",
                    param_name,
                    val,
                    e,
                    exc_info=True,
                )
                
        return results
