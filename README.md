# HoloTwin: Physics-Informed Digital Twin Platform
### (Aerothon 2026 · HAL x IIT Indore)

HoloTwin is a **Physics-Informed Digital Twin Platform** designed for a single-spool, four-stage turbojet engine. Built as a full-stack web application, it integrates physical gas-turbine constraints with machine learning surrogate models to predict component-level degradation (Compressor, Combustor, Turbine, and Overall Health) and forecast real-time engine performance parameters (Thrust, TSFC) with built-in uncertainty quantification.

---
## AI/ML Component — PINN Surrogate Model
This project integrates a Physics-Informed Neural Network (PINN) surrogate model for [brief description of what it predicts/does].
Model repo: https://github.com/muthukkumaranb/HoloTwin-AeroThon
Also embedded in this repo as a submodule at `ml-service/` (see below).
## 🛠️ Architecture Overview

The codebase is organized into a decoupled full-stack architecture:

```
iiti-aerothon-regression/
├── holotwin/                # Backend Django Project
│   ├── manage.py
│   ├── holotwin/            # Core settings & routing configuration
│   ├── engine_data/         # Data ingestion, DB schema definitions
│   ├── digitaltwin/         # Physics feature engineering & ML pipelines
│   └── api/                 # REST API endpoints & serializers
├── frontend/                # Frontend Vite + React SPA dashboard
│   ├── src/
│   │   ├── components/      # UI components (HUD panels, Gauges, Charts)
│   │   ├── App.jsx          # Main application cockpit view
│   │   ├── index.css        # Space-cockpit HUD design system
│   │   └── main.jsx         # App entry point
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── technical_report_outline.md  # Mapping criteria to implementation
├── Dataset/                 # Raw and split datasets
├── results.zip              # Package of all generated plots
├── correlation_matrix.png   # Generated heatmap plot
├── degradation_trend.png    # Generated degradation trend plot
├── baseline_scatter.png     # Generated baseline P2 regression plot
└── health_estimation_scatter.png # Generated twin OverallHealth scatter plot
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have the following installed on your system:
- **Python 3.11+**
- **Node.js v20+** and **npm**

---

### 2. Django Backend Setup

Navigate to the backend directory:
```bash
cd holotwin
```

Install the required Python packages (with system override if required by PEP 668):
```bash
pip install django djangorestframework django-cors-headers joblib scikit-learn pandas numpy matplotlib seaborn --break-system-packages
```

Run database migrations to initialize the SQLite database:
```bash
python3 manage.py makemigrations engine_data
python3 manage.py migrate
```

Load the complete turbojet dataset from the CSV file into the database:
```bash
python3 manage.py load_dataset
```

Train the digital twin ML surrogate models (including Cascade pipelines and Quantile bounds):
```bash
python3 manage.py train_models
```

Start the Django REST API server:
```bash
python3 manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/`.

---

### 3. React Frontend Setup

Navigate to the frontend directory:
```bash
cd ../frontend
```

Install npm dependencies:
```bash
npm install
```

Start the Vite React development server:
```bash
npm run dev
```
Open your browser and navigate to `http://localhost:5173/` to view the interactive cockpit interface.

To build the client for production:
```bash
npm run build
```

---

## 🧪 Running Automated Tests

A comprehensive test suite is provided to verify both feature engineering and API routing.

Run the test suite using Django's test runner:
```bash
cd holotwin
python3 manage.py test
```

---

## 📊 Reproducing Plots & Results

You can regenerate the correlation heatmap, the degradation line graph, the linear baseline regression plot, and the health estimation accuracy scatter plot with a single command:

```bash
python3 manage.py generate_plots
```
This command regenerates the plots and zips them into `/results.zip` in the project root.

---

## 🔌 API Endpoints Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/engines/` | `GET` | List all engines, their latest operating cycle, and overall health index. |
| `/api/engines/{id}/history/` | `GET` | Retrieve full cycle-by-cycle sensor readings, derived features, and predictions. |
| `/api/engines/{id}/latest/` | `GET` | Get a snapshot of the latest cycle, degradation slope, and 5-cycle extrapolation. |
| `/api/predict/` | `POST` | Input custom sensor values to get instant digital twin predictions. |
| `/api/model-metrics/` | `GET` | Fetch RMSE, MAE, R², MAPE, latencies, and feature importances for all models. |

---

## 📝 Key Code References

- **ORM Schema**: [engine_data/models.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/engine_data/models.py)
- **Physics Formulas**: [digitaltwin/features.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/features.py)
- **Inference Cascade**: [digitaltwin/models_ml.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/digitaltwin/models_ml.py)
- **REST Endpoints**: [api/views.py](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/holotwin/api/views.py)
- **HUD Interface**: [frontend/src/App.jsx](file:///home/cygnusvale/coding/projects/iiti-aerothon-regression/frontend/src/App.jsx)
