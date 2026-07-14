import os
import zipfile
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error

from engine_data.models import EngineCycleRecord
from digitaltwin.features import add_derived_features
from digitaltwin.models_ml import run_twin_inference

class Command(BaseCommand):
    help = 'Generate baseline and digital twin comparison plots'

    def handle(self, *args, **options):
        # 1. Fetch records
        records = EngineCycleRecord.objects.all().values()
        if not records.exists():
            self.stdout.write(self.style.ERROR("No records in DB. Load dataset first."))
            return
            
        df = pd.DataFrame(list(records))
        df = add_derived_features(df)
        
        output_dir = os.path.dirname(settings.BASE_DIR)  # Save in project root
        
        # Plot 1: Correlation Matrix Heatmap
        cols_for_corr = [
            'altitude_m', 'mach', 'tamb_k', 'pamb_pa', 'rpm_rev_min', 'fuel_flow_kg_s', 
            'p2_pa', 't2_k', 'p3_pa', 't3_k', 'p4_pa', 't4_k', 
            'p2_ratio', 't3_t4_ratio', 'corrected_rpm', 'cycle'
        ]
        
        plt.figure(figsize=(12, 10))
        # Map snake_case to pretty labels for the plot
        corr_df = df[cols_for_corr].copy()
        corr_df.columns = [c.replace('_', ' ').title() for c in cols_for_corr]
        sns.heatmap(corr_df.corr(), cmap='coolwarm', annot=False)
        plt.title("Correlation Matrix of Selected Features")
        plt.tight_layout()
        plot1_path = os.path.join(output_dir, 'correlation_matrix.png')
        plt.savefig(plot1_path)
        plt.close()
        self.stdout.write(f"Generated {plot1_path}")
        
        # Plot 2: Wide cycle range engine degradation trend
        cycle_range_per_engine = df.groupby('engine_id')['cycle'].max() - df.groupby('engine_id')['cycle'].min()
        target_engine_id = cycle_range_per_engine.idxmax()
        engine_df = df[df['engine_id'] == target_engine_id]
        
        plt.figure(figsize=(10, 6))
        plt.plot(engine_df['cycle'], engine_df['p2_ratio'], label=f'Engine {target_engine_id}', color='#06b6d4', linewidth=2)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.xlabel("Cycle")
        plt.ylabel("P2 Ratio (P2 / Pamb)")
        plt.title(f"Degradation Trend (P2 Ratio vs Cycle) for Engine {target_engine_id}")
        plt.legend()
        plt.tight_layout()
        plot2_path = os.path.join(output_dir, 'degradation_trend.png')
        plt.savefig(plot2_path)
        plt.close()
        self.stdout.write(f"Generated {plot2_path}")
        
        # Plot 3: Build a linear regression baseline (reproduces baseline_scatter.png)
        features = ['altitude_m', 'mach', 'tamb_k', 'pamb_pa', 'rpm_rev_min', 'fuel_flow_kg_s', 'cycle']
        target = 'p2_ratio'
        
        sorted_engines = sorted(df['engine_id'].unique())
        test_engine_id = sorted_engines[-1]
        
        train_df = df[df['engine_id'] != test_engine_id]
        test_df = df[df['engine_id'] == test_engine_id]
        
        X_train = train_df[features]
        y_train = train_df[target]
        X_test = test_df[features]
        y_test = test_df[target]
        
        baseline_model = LinearRegression()
        baseline_model.fit(X_train, y_train)
        y_pred = baseline_model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100
        
        plt.figure(figsize=(8, 8))
        plt.scatter(y_test, y_pred, alpha=0.6, color='#3b82f6', edgecolors='w')
        # Perfect prediction line
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction', linewidth=2)
        plt.xlabel("Actual P2 Ratio")
        plt.ylabel("Predicted P2 Ratio")
        plt.title(f"Baseline Regression: Actual vs Predicted (MAPE: {mape:.2f}%)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plot3_path = os.path.join(output_dir, 'baseline_scatter.png')
        plt.savefig(plot3_path)
        plt.close()
        self.stdout.write(f"Generated {plot3_path}")
        
        # Plot 4: Health Estimation Scatter Plot (Predicted vs Actual OverallHealth)
        # We will collect predictions using the cascade on Engine 10 (test engine)
        test_engine_df = df[df['engine_id'] == test_engine_id].copy()
        
        actual_overall = test_engine_df['overall_health'].values
        pred_overall = []
        
        for idx, row in test_engine_df.iterrows():
            payload = {
                'altitude_m': row['altitude_m'],
                'mach': row['mach'],
                'tamb_k': row['tamb_k'],
                'pamb_pa': row['pamb_pa'],
                'rpm_rev_min': row['rpm_rev_min'],
                'fuel_flow_kg_s': row['fuel_flow_kg_s'],
                'p2_pa': row['p2_pa'],
                't2_k': row['t2_k'],
                'p3_pa': row['p3_pa'],
                't3_k': row['t3_k'],
                'p4_pa': row['p4_pa'],
                't4_k': row['t4_k'],
                'cycle': row['cycle']
            }
            res = run_twin_inference(payload)
            pred_overall.append(res['predicted_overall_health'])
            
        pred_overall = np.array(pred_overall)
        health_mape = mean_absolute_percentage_error(actual_overall, pred_overall) * 100
        health_rmse = np.sqrt(mean_squared_error(actual_overall, pred_overall))
        
        plt.figure(figsize=(8, 8))
        plt.scatter(actual_overall, pred_overall, alpha=0.7, color='#10b981', edgecolors='w', s=50)
        min_val = min(actual_overall.min(), pred_overall.min())
        max_val = max(actual_overall.max(), pred_overall.max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Estimation', linewidth=2)
        plt.xlabel("Actual Overall Health")
        plt.ylabel("Predicted Overall Health")
        plt.title(f"HoloTwin Overall Health Estimation: Actual vs Predicted (RMSE: {health_rmse:.4f})")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plot4_path = os.path.join(output_dir, 'health_estimation_scatter.png')
        plt.savefig(plot4_path)
        plt.close()
        self.stdout.write(f"Generated {plot4_path}")
        
        # 6. Zip the four plots
        zip_path = os.path.join(output_dir, 'results.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(plot1_path, arcname='correlation_matrix.png')
            zipf.write(plot2_path, arcname='degradation_trend.png')
            zipf.write(plot3_path, arcname='baseline_scatter.png')
            zipf.write(plot4_path, arcname='health_estimation_scatter.png')
            
        self.stdout.write(self.style.SUCCESS(f"Successfully zipped all four plots into {zip_path}"))
