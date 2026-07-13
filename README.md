# Turbojet Engine Degradation Analysis

This repository contains a Python script and associated resources for analyzing a turbojet engine dataset (`turbojet_complete_dataset.csv`). It performs exploratory data analysis, visualizes correlations and degradation trends, and establishes a baseline linear regression model to predict the engine pressure ratio (P2 Ratio).

## Files in the Repository

- `analysis.py`: The main Python script that performs data loading, processing, visualization, and modeling.
- `requirements.txt`: List of dependencies needed to run the analysis.
- `Dataset/`: Directory containing the turbojet dataset.
- Generated plots (output by the script):
  - `correlation_matrix.png`: Heatmap of selected features to understand linear correlations.
  - `degradation_trend.png`: A plot showing the P2 ratio degradation trend over engine cycles for the engine with the widest cycle range.
  - `baseline_scatter.png`: Scatter plot comparing the actual vs predicted P2 ratio using the baseline linear regression model.
- `results.zip`: A zip archive containing all generated plots.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd iiti-aerothon
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the analysis script:**
   Ensure the `Dataset/turbojet_complete_dataset.csv` is present.
   ```bash
   python analysis.py
   ```

## Key Findings & Outputs

Running the script will print statistics to the console, including:
- Number of unique engines.
- Engine cycle statistics.
- Altitude and Mach number ranges.
- A final summary with the baseline model's Mean Absolute Percentage Error (MAPE) and Root Mean Squared Error (RMSE).

Three PNG plots are also generated and zipped into `results.zip`.
