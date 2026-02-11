# Visualization Layer: Goals and Master Plan

## 1. Vision
The Visualization Layer provides a unified framework for generating, storing, and publishing visual representations of the Voynich Manuscript project's findings. It bridges the gap between raw metric data (stored in databases/run logs) and human-interpretable insights (graphs, heatmaps, and diagnostic plots).

This layer is strictly descriptive and diagnostic; it does not introduce new assumptions or interpretations beyond what the analytical layers (1-4) have established.

## 2. Goals
- **Phase-Specific Visualization**: Provide tailored plots for each of the four project layers.
- **Reproducibility**: Ensure every plot is tied to a specific `RunID` and dataset provenance.
- **Publication Readiness**: Generate high-quality assets suitable for research reports and public documentation.
- **Diagnostic Utility**: Help researchers identify anomalies, stability shifts, and method failures during development.
- **Automation**: Integrate visualization into the CI/CD and run lifecycle.

## 3. Architectural Design

### 3.1. Directory Structure
```text
src/support_visualization/
├── __init__.py
├── base.py                 # Abstract Base Class for visualizers
├── core/
│   ├── engine.py           # Matplotlib/Seaborn orchestration
│   ├── themes.py           # Project-specific styling (Voynich aesthetics)
│   └── utils.py            # Data transformation helpers
├── layers/                 # Phase-specific visualizers
│   ├── layer_1_foundation.py
│   ├── layer_2_analysis.py
│   ├── layer_3_synthesis.py
│   └── layer_4_inference.py
└── cli/
    └── main.py             # Typer-based CLI for plot generation
```

### 3.2. Data Flow
1. **Source**: Metrics from `SQLAlchemy` (MetadataStore) or JSON from `runs/<run_id>/outputs.json`.
2. **Transform**: `VisualizationLayer` converts raw metrics into plot-ready dataframes.
3. **Render**: `matplotlib` or `seaborn` generates the image.
4. **Sink**: Assets are saved to `results/reports/visuals/<phase>/<run_id>_<plot_name>.png`.

## 4. Implementation Roadmap

### Phase 1: Foundation (Layer 1)
- **Framework**: Implement `BaseVisualizer` and theme system.
- **L1 Plots**:
  - Token Frequency Distributions (Zipfian plots).
  - Repetition Rate Histograms.
  - Page-level Metric Heatmaps (Visualizing cluster tightness across the manuscript).

### Phase 2: Admissibility & Sensitivity (Layer 2)
- **Sweep Visuals**:
  - Parameter Sensitivity Heatmaps (from `run_sensitivity_sweep.py`).
  - Admissibility Boundary Plots (Showing where explanation classes are rejected).
  - Stability Curves for Anomaly detection.

### Phase 3: Structural Sufficiency (Layer 3)
- **The Turing Test**:
  - Comparative Histograms (Real vs. Synthetic metrics).
  - Separation Analysis (Can a classifier distinguish them? Visualizing the ROC/AUC).
  - Glyph-level Grammar transition matrices.

### Phase 4: Inference Evaluation (Layer 4)
- **Method Admissibility**:
  - False Positive Rate (FPR) Comparison across methods (Information Theory vs. Topic Modeling).
  - Method Reliability Heatmaps.
  - "Inference Closure" diagrams showing remaining semantic loopholes.

### Phase 5: Integration & CLI
- **Typer CLI**: `foundation viz generate --run-id <uuid> --layer 2`.
- **Report Integration**: Automatically embed generated plots into `AUDIT_LOG.md` and phase reports.

## 5. Success Criteria
- [ ] Visualizers exist for all current Layer 2 and Layer 3 metrics.
- [ ] Plots are automatically generated at the end of a "Release" run.
- [ ] Visual style is consistent across all phases.
- [ ] No visualization code depends on "meaning" or "translation" assumptions.
