
import pandas as pd

from phase1_foundation.metrics.interface import MetricResult


def metric_results_to_df(results: list[MetricResult]) -> pd.DataFrame:
    """
    Convert a list of MetricResult objects into a pandas DataFrame.
    """
    data = [r.to_dict() for r in results]
    return pd.DataFrame(data)

def smooth_distribution(data: list[float], window: int = 5) -> list[float]:
    """
    Simple moving average for smoothing noisy distribution plots.
    """
    if not data:
        return []
    series = pd.Series(data)
    return series.rolling(window=window, center=True).mean().tolist()
