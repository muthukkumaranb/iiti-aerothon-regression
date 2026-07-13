import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import zipfile
import os

# 1. Load the data, print shape, column names, and first 5 rows
df = pd.read_csv('d:/iiti-aerothon/Dataset/turbojet_complete_dataset.csv')
print("Shape of the dataset:", df.shape)
print("\nColumn Names:")
print(df.columns.tolist())
print("\nFirst 5 Rows:")
print(df.head())

# 2. Compute and print statistics
num_engines = df['EngineID'].nunique()
print(f"\nNumber of unique Engine IDs: {num_engines}")

engine_cycle_stats = df.groupby('EngineID')['Cycle'].agg(['min', 'max', 'mean'])
print("\nPer-engine cycle stats:")
print(engine_cycle_stats)

overall_cycle_min = df['Cycle'].min()
overall_cycle_max = df['Cycle'].max()
overall_cycle_mean = df['Cycle'].mean()

alt_min_m = df['Altitude_m'].min()
alt_max_m = df['Altitude_m'].max()
alt_min_km = alt_min_m / 1000.0
alt_max_km = alt_max_m / 1000.0
print(f"\nAltitude range: {alt_min_km:.2f} - {alt_max_km:.2f} km")

mach_min = df['Mach'].min()
mach_max = df['Mach'].max()
print(f"\nMach number range: {mach_min:.4f} - {mach_max:.4f}")

missing_values = df.isnull().sum()
print("\nMissing values per column:")
print(missing_values)

missing_details = "none" if missing_values.sum() == 0 else str(missing_values[missing_values > 0].to_dict())

# 3. Create derived features
df['P2_ratio'] = df['P2_Pa'] / df['Pamb_Pa']
df['T2_ratio'] = df['T2_K'] / df['Tamb_K']
df['T3_T4_ratio'] = (df['T3_K'] - df['T4_K']) / df['T3_K']
df['Corrected_RPM'] = df['RPM_rev_min'] / np.sqrt(df['Tamb_K'])

# 4. Generate correlation heatmap
cols_for_corr = [
    'Altitude_m', 'Mach', 'Tamb_K', 'Pamb_Pa', 'RPM_rev_min', 'FuelFlow_kg_s', 
    'P2_Pa', 'T2_K', 'P3_Pa', 'T3_K', 'P4_Pa', 'T4_K', 
    'P2_ratio', 'T3_T4_ratio', 'Corrected_RPM', 'Cycle'
]

plt.figure(figsize=(12, 10))
sns.heatmap(df[cols_for_corr].corr(), cmap='coolwarm', annot=False)
plt.title("Correlation Matrix of Selected Features")
plt.tight_layout()
plt.savefig('correlation_matrix.png')
plt.close()

# 5. Wide cycle range engine degradation trend
cycle_range_per_engine = df.groupby('EngineID')['Cycle'].max() - df.groupby('EngineID')['Cycle'].min()
target_engine_id = cycle_range_per_engine.idxmax()
engine_df = df[df['EngineID'] == target_engine_id]

plt.figure(figsize=(10, 6))
plt.plot(engine_df['Cycle'], engine_df['P2_ratio'], label=f'Engine {target_engine_id}')
plt.grid(True)
plt.xlabel("Cycle")
plt.ylabel("P2 Ratio (P2 / Pamb)")
plt.title(f"Degradation Trend (P2 Ratio vs Cycle) for Engine {target_engine_id}")
plt.legend()
plt.tight_layout()
plt.savefig('degradation_trend.png')
plt.close()

# 6. Build a linear regression baseline
features = ['Altitude_m', 'Mach', 'Tamb_K', 'Pamb_Pa', 'RPM_rev_min', 'FuelFlow_kg_s', 'Cycle']
target = 'P2_ratio'

sorted_engines = sorted(df['EngineID'].unique())
test_engine_id = sorted_engines[-1]

train_df = df[df['EngineID'] != test_engine_id]
test_df = df[df['EngineID'] == test_engine_id]

X_train = train_df[features]
y_train = train_df[target]
X_test = test_df[features]
y_test = test_df[target]

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mape = mean_absolute_percentage_error(y_test, y_pred) * 100

print(f"\nBaseline RMSE: {rmse:.4f}")
print(f"Baseline MAPE: {mape:.4f}%")

# 7. Predicted-vs-actual scatter plot
plt.figure(figsize=(8, 8))
plt.scatter(y_test, y_pred, alpha=0.5)
# Perfect prediction line
min_val = min(y_test.min(), y_pred.min())
max_val = max(y_test.max(), y_pred.max())
plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
plt.xlabel("Actual P2 Ratio")
plt.ylabel("Predicted P2 Ratio")
plt.title(f"Baseline Regression: Actual vs Predicted (MAPE: {mape:.2f}%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('baseline_scatter.png')
plt.close()

# 8. Print final summary block
print("\n--- FINAL SUMMARY ---")
print(f"- Number of engines: {num_engines}")
print(f"- Cycle range: min {overall_cycle_min}, max {overall_cycle_max}, mean {overall_cycle_mean:.2f}")
print(f"- Altitude range: {alt_min_km:.2f} - {alt_max_km:.2f} km")
print(f"- Mach range: {mach_min:.4f} - {mach_max:.4f}")
print(f"- Missing values: {missing_details}")
print(f"- Baseline MAPE: {mape:.4f}%")
print(f"- Baseline RMSE: {rmse:.4f}")

# 9. Zip the three PNGs
with zipfile.ZipFile('results.zip', 'w') as zipf:
    zipf.write('correlation_matrix.png')
    zipf.write('degradation_trend.png')
    zipf.write('baseline_scatter.png')

print("\nSaved images to results.zip")
