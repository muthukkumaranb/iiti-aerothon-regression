# Technical Report Outline — HoloTwin Digital Twin Platform

This document serves as the mapping guide for the evaluation criteria specified in the **HoloTwin** problem statement, linking each requirement directly to its implementation in the source codebase.

---

## 1. Health Estimation Accuracy (Weight: 30%)
**Requirement**: Per-subsystem models (Compressor/Combustor/Turbine) + OverallHealth, validated against ground truth (MAE, RMSE, R²).
*   **Implementation**: 
    *   Models are trained for each subsystem and overall health targets using the `GradientBoostingRegressor` in the custom management command: [train_models.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/management/commands/train_models.py#L74-L105).
    *   Evaluation metrics (RMSE, MAE, R², MAPE) are calculated on a held-out test engine and saved in: [metrics.json](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/trained_models/metrics.json).
    *   Actual vs predicted Overall Health comparison is plotted in: [health_estimation_scatter.png](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/health_estimation_scatter.png).

---

## 2. Surrogate Model Performance (Weight: 20%)
**Requirement**: Fast ML models (not full thermodynamic simulation) approximating engine state; report inference latency.
*   **Implementation**:
    *   Surrogate models run real-time inference in a cascaded workflow (using predictions of preceding stages to inform the next), implemented in: [models_ml.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/models_ml.py#L31-L91).
    *   Inference latency is measured on test samples and reported: [train_models.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/management/commands/train_models.py#L65-L67). Latencies (averaging < 25-50ms per cascade) are recorded in `metrics.json` and rendered in the dashboard.

---

## 3. Physics Consistency (Weight: 15%)
**Requirement**: Derived physics ratios ($P_2/P_{\text{amb}}$, $T_2/T_{\text{amb}}$, $(T_3 - T_4)/T_3$, corrected RPM, corrected Fuel Flow) as features/constraints; sanity-check degradation.
*   **Implementation**:
    *   The physics-derived ratios and gas-turbine corrections are calculated in: [features.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/features.py).
    *   Subsystem models are constrained to use their respective physical features (e.g. Combustor uses combustor exit ratios, Turbine uses turbine pressure ratios): [train_models.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/management/commands/train_models.py#L18-L23).
    *   A single-engine P2 ratio degradation trend is visualised in: [degradation_trend.png](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/degradation_trend.png).

---

## 4. Generalization Capability (Weight: 15%)
**Requirement**: Leave-one-engine-out (or last-engine-held-out) split; cross-engine metrics.
*   **Implementation**:
    *   The train-test split splits cycles engine-wise, holding out the last engine (Engine 10) entirely to prevent temporal leaks: [train_models.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/management/commands/train_models.py#L38-L44).
    *   Validation metrics in `metrics.json` report purely on this unseen held-out engine.

---

## 5. Computational Efficiency (Weight: 10%)
**Requirement**: Lightweight models (Gradient Boosting / Ridge) with low footprint and rapid inference.
*   **Implementation**:
    *   We employ optimized, lightweight scikit-learn standard models (GradientBoostingRegressor with minimal trees and depth) to keep models trainable in seconds and keep inference times to milliseconds.
    *   Model file sizes (stored in `metrics.json` and shown in the dashboard) average under 250 KB per model.

---

## 6. Dashboard & Interpretability (Weight: 10%)
**Requirement**: React dashboard + feature importance / SHAP-style explanations.
*   **Implementation**:
    *   The single-page cockpit dashboard is built in: [App.jsx](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/frontend/src/App.jsx).
    *   Interactive HUD features include dropdown selectors, scrubber, gauges, and historical degradation charts with linear extrapolations.
    *   The Twin Diagnostics panel retrieves feature importances from `metrics.json` and renders horizontal bar charts explaining exactly which sensor readings impact each model: [App.jsx](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/frontend/src/App.jsx#L427-L457).
