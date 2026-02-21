# Developer Guide

How to extend the VoynichMS codebase with new metrics, phases, and tests.

---

## How to Add a New Metric

1. **Create the metric class** in `src/phase<N>_<name>/<submodule>/`:

```python
class MyMetricAnalyzer:
    def __init__(self, param: int = 10):
        self.param = param

    def analyze(self, tokens: List[str]) -> Dict[str, Any]:
        if not tokens:
            return {"status": "no_data"}
        # ... compute metric ...
        return {"metric_value": result, "sample_size": len(tokens)}
```

2. **Follow existing conventions:**
   - Accept `List[str]` (tokens) or `List[List[str]]` (lines) as input
   - Return `Dict[str, Any]` with a `status` key for error cases
   - Use `logging.getLogger(__name__)` for warnings
   - Document any thresholds in `governance/THRESHOLDS_RATIONALE.md`

3. **Write tests** in `tests/phase<N>_<name>/test_<module>.py`:

```python
class TestMyMetric:
    def test_empty_input(self):
        result = MyMetricAnalyzer().analyze([])
        assert result["status"] == "no_data"

    def test_basic_output_keys(self):
        result = MyMetricAnalyzer().analyze(["a", "b", "c"] * 20)
        assert "metric_value" in result
        assert "sample_size" in result
```

4. **Create a runner script** in `scripts/phase<N>_<name>/run_<step>.py`:
   - Use `argparse` with `--seed` and `--output-dir`
   - Wrap execution in `active_run(config={...})`
   - Save results via `ProvenanceWriter.save_results()`
   - End with `sys.exit(0)`

5. **Add to replication** by calling the script from the phase `replicate.py`.

---

## How to Add a New Phase

1. **Create source directory:** `src/phase<N>_<name>/` with `__init__.py`
2. **Create scripts directory:** `scripts/phase<N>_<name>/`
3. **Create test directory:** `tests/phase<N>_<name>/`

4. **Create `replicate.py`** in the scripts directory:

```python
#!/usr/bin/env python3
import subprocess, sys

SCRIPTS = [
    "scripts/phase<N>_<name>/run_<step>.py",
]

def main():
    for script in SCRIPTS:
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"FAILED: {script}")
            sys.exit(1)
    print("Phase <N> complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

5. **Register in `replicate_all.py`:** Add the replicate script path to the
   master list in `scripts/support_preparation/replicate_all.py`.

6. **Update documentation:**
   - Add phase to `ARCHITECTURE.md` (component diagram)
   - Add phase to `PHASE_DEPENDENCIES.md` (DAG, I/O table)
   - Add phase to `README.md` (research phases list)

---

## How to Write a Reproducible Test

All tests should be deterministic. Follow these patterns:

### Unit test (no database, no filesystem):

```python
import pytest

class TestMyAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from my_module import MyAnalyzer
        self.analyzer = MyAnalyzer()

    def test_basic_case(self):
        result = self.analyzer.analyze(["a", "b", "c"])
        assert result["value"] > 0
```

### Test requiring database:

```python
import pytest

@pytest.mark.requires_db
class TestWithDB:
    def test_query(self, populated_store):
        # populated_store fixture from conftest.py pre-loads sample data
        session = populated_store.Session()
        try:
            pages = session.query(PageRecord).all()
            assert len(pages) >= 1
        finally:
            session.close()
```

### Test with randomness:

```python
def test_seeded_reproducibility(clean_randomness):
    from phase1_foundation.core.randomness import RandomnessController
    ctrl = RandomnessController()
    ctrl.set_mode("SEEDED")
    ctrl.register_seed(42)
    # ... test that seeded operations produce identical results
```

### Available pytest markers:

| Marker | Meaning |
|---|---|
| `@pytest.mark.unit` | Pure unit test, no external dependencies |
| `@pytest.mark.integration` | Requires database or filesystem |
| `@pytest.mark.slow` | Takes >10 seconds |
| `@pytest.mark.requires_db` | Needs populated SQLite database |

### Shared fixtures (from `tests/conftest.py`):

| Fixture | Description |
|---|---|
| `tmp_db` | Temporary SQLite URL |
| `store` | MetadataStore on temporary DB |
| `populated_store` | Store with sample dataset, page, line, word, tokens |
| `sample_ivtff_file` | Temporary IVTFF file for parser testing |
| `clean_randomness` | Ensures RandomnessController is reset |
| `clean_run_manager` | Ensures RunManager has no active run |

---

## Project Conventions

### Code organization

- **Source code** lives in `src/phase<N>_<name>/`
- **Entry-point scripts** live in `scripts/phase<N>_<name>/`
- **Tests** live in `tests/phase<N>_<name>/`
- **Config files** live in `configs/`
- **Results** go to `results/data/` (JSON) and `results/reports/` (Markdown)

### Provenance

Every result file should be wrapped by `ProvenanceWriter.save_results()`:

```python
from phase1_foundation.core.provenance import ProvenanceWriter
ProvenanceWriter.save_results(results_dict, output_path)
```

This adds `{"provenance": {...}, "results": {...}}` structure with git commit,
timestamp, and run ID.

### Randomness

Use `RandomnessController` for any stochastic computation:

```python
from phase1_foundation.core.randomness import RandomnessController
ctrl = RandomnessController()
ctrl.set_mode("SEEDED")
ctrl.register_seed(42)
```

Or use the `require_seed_if_strict()` helper in module `__init__`:

```python
from phase1_foundation.config import require_seed_if_strict
require_seed_if_strict(seed, "MyModule")
```

### Error handling

- Use `logging.getLogger(__name__)` with `exc_info=True` for caught exceptions
- Do not use bare `except:` — catch specific exceptions

### "No data" sentinel conventions

Use the appropriate sentinel for the return type:

| Return type | Sentinel | Example |
|---|---|---|
| `MetricResult.value` (float) | `float("nan")` | `MetricResult(value=float("nan"), details={"status": "no_data"})` |
| Dict-returning methods | `{"status": "no_data", ...}` | `return {"status": "no_data", "num_tokens": 0}` |
| Optional returns | `None` | `return None` |

Always include `details["status"] = "no_data"` in MetricResult so callers can
distinguish "measured zero" from "no data available". Never use `0.0` as a
no-data sentinel for numeric metrics.

### Logging conventions

The codebase uses three logging mechanisms by design:

| Mechanism | When to use | Examples |
|---|---|---|
| `rich.Console` | User-facing terminal output: tables, panels, progress bars, colored status | Phase run scripts, interactive reports |
| `logging.getLogger(__name__)` | Machine-parseable diagnostics: warnings, errors, debug traces | Source modules (`src/`), library code |
| `print()` | Simple utility scripts, CI scripts, replication runners | `replicate.py`, `check_*.py`, `generate_*.py` |

For new **source modules** (`src/`), always use `logging`. For new **entry-point
scripts** (`scripts/`), prefer `rich.Console` for user-facing output. Do not
mix `print()` and `Console` in the same script.

### Documentation

- Document thresholds in `governance/THRESHOLDS_RATIONALE.md`
- Document claims in `governance/claim_artifact_map.md`
- Map paper references in `governance/PAPER_CODE_CONCORDANCE.md`
