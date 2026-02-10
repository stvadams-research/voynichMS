import json
import math
import sys
from pathlib import Path
from sqlalchemy import create_engine

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

from foundation.storage.metadata import MetadataStore
from foundation.metrics.library import RepetitionRate, ClusterTightness

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        # Keep fixtures strict-JSON compatible.
        return obj if math.isfinite(obj) else None
    elif isinstance(obj, (str, int, bool, type(None))):
        return obj
    else:
        return str(obj)

def generate_fixtures():
    print("Generating regression fixtures...")
    db_path = "sqlite:///data/voynich.db"
    store = MetadataStore(db_path)
    
    # We use 'test_ds' from acceptance_test.py
    dataset_id = "test_ds"
    
    # 1. RepetitionRate Fixture
    rep_metric = RepetitionRate(store)
    rep_results = rep_metric.calculate(dataset_id)
    rep_data = [sanitize_for_json(r.to_dict()) for r in rep_results]
        
    with open("tests/fixtures/repetition_rate_baseline.json", "w") as f:
        json.dump(rep_data, f, indent=2, sort_keys=True)
        
    # 2. ClusterTightness Fixture
    ct_metric = ClusterTightness(store)
    ct_results = ct_metric.calculate(dataset_id)
    ct_data = [sanitize_for_json(r.to_dict()) for r in ct_results]
        
    with open("tests/fixtures/cluster_tightness_baseline.json", "w") as f:
        json.dump(ct_data, f, indent=2, sort_keys=True)
        
    print("Fixtures generated in tests/fixtures/")

if __name__ == "__main__":
    generate_fixtures()
