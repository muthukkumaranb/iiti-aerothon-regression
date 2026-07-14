import os
import json
import time
import joblib
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from engine_data.models import EngineCycleRecord
from digitaltwin.features import add_derived_features

# Feature definitions
FEATURES_BASE = [
    'altitude_m', 'mach', 'tamb_k', 'pamb_pa', 'rpm_rev_min', 'fuel_flow_kg_s', 'cycle',
    'p2_ratio', 't2_ratio', 'corrected_rpm', 'corrected_fuel_flow'
]
FEATURES_COMPRESSOR = FEATURES_BASE
FEATURES_COMBUSTOR = FEATURES_BASE + ['t3_t4_ratio', 'p3_p2_ratio']
FEATURES_TURBINE = FEATURES_BASE + ['t3_t4_ratio', 'p4_p3_ratio']
FEATURES_OVERALL = FEATURES_BASE + ['t3_t4_ratio', 'p3_p2_ratio', 'p4_p3_ratio']
FEATURES_PERFORMANCE = FEATURES_OVERALL + ['compressor_health', 'combustor_health', 'turbine_health']

def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

class Command(BaseCommand):
    help = 'Train ML models and save them under digitaltwin/trained_models/'

    def handle(self, *args, **options):
        # 1. Fetch records from DB
        records = EngineCycleRecord.objects.all().values()
        if not records.exists():
            self.stdout.write(self.style.ERROR("No records in database. Please run python manage.py load_dataset first."))
            return
            
        df = pd.DataFrame(list(records))
        
        # 2. Add derived features
        df = add_derived_features(df)
        
        # 3. Create Leave-Last-Engine-Out Split
        # Hold out the engine with the highest ID (Engine ID 10)
        test_engine_id = sorted(df['engine_id'].unique())[-1]
        
        train_df = df[df['engine_id'] != test_engine_id].copy()
        test_df = df[df['engine_id'] == test_engine_id].copy()
        
        self.stdout.write(f"Training on engines 1-{test_engine_id-1} ({len(train_df)} cycles)")
        self.stdout.write(f"Testing/validating on engine {test_engine_id} ({len(test_df)} cycles)")
        
        trained_models = {}
        metrics = {}
        
        # Create output directory
        model_dir = os.path.join(settings.BASE_DIR, 'digitaltwin', 'trained_models')
        os.makedirs(model_dir, exist_ok=True)
        
        # Helper to train and evaluate a model
        def train_eval_save(target_name, features, save_name=None):
            if save_name is None:
                save_name = target_name
                
            X_train = train_df[features]
            y_train = train_df[target_name]
            X_test = test_df[features]
            y_test = test_df[target_name]
            
            # Setup Pipeline
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', GradientBoostingRegressor(random_state=42, n_estimators=100, max_depth=4))
            ])
            
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            
            # Compute metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            mape = mean_absolute_percentage_error(y_test, y_pred)
            
            # Save joblib
            model_path = os.path.join(model_dir, f"{save_name}.joblib")
            joblib.dump(pipeline, model_path)
            
            # Get feature importances
            importances = pipeline.named_steps['regressor'].feature_importances_
            feature_imp = {feat: float(imp) for feat, imp in zip(features, importances)}
            
            # Estimate latency
            t0 = time.perf_counter()
            for _ in range(100):
                pipeline.predict(X_test.iloc[[0]])
            latency_ms = ((time.perf_counter() - t0) / 100.0) * 1000.0
            
            metrics[save_name] = {
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape),
                'latency_ms': float(latency_ms),
                'model_size_kb': float(os.path.getsize(model_path) / 1024.0),
                'feature_importances': feature_imp
            }
            
            self.stdout.write(f"  {save_name}: RMSE={rmse:.4f}, MAPE={mape:.4f}%, R2={r2:.4f}, Latency={latency_ms:.2f}ms")
            return pipeline, y_pred
            
        # A. Train Subsystem Health Models
        self.stdout.write("Training Subsystem Health Models...")
        comp_model, comp_pred = train_eval_save('compressor_health', FEATURES_COMPRESSOR)
        comb_model, comb_pred = train_eval_save('combustor_health', FEATURES_COMBUSTOR)
        turb_model, turb_pred = train_eval_save('turbine_health', FEATURES_TURBINE)
        
        # B. Train Overall Health Model (with comparison)
        self.stdout.write("Training Overall Health Model & Ensemble Comparison...")
        # 1. Direct OverallHealth Regressor
        direct_model, direct_pred = train_eval_save('overall_health', FEATURES_OVERALL, 'overall_health_direct')
        
        # 2. Ensemble (Mean of predictions)
        ensemble_pred = (comp_pred + comb_pred + turb_pred) / 3.0
        y_test_overall = test_df['overall_health']
        ens_rmse = np.sqrt(mean_squared_error(y_test_overall, ensemble_pred))
        ens_mae = mean_absolute_error(y_test_overall, ensemble_pred)
        ens_r2 = r2_score(y_test_overall, ensemble_pred)
        ens_mape = mean_absolute_percentage_error(y_test_overall, ensemble_pred)
        
        self.stdout.write(f"  OverallHealth Direct: R2={metrics['overall_health_direct']['r2']:.4f}, RMSE={metrics['overall_health_direct']['rmse']:.4f}")
        self.stdout.write(f"  OverallHealth Subsystem Mean: R2={ens_r2:.4f}, RMSE={ens_rmse:.4f}")
        
        # Save comparison metrics
        metrics['overall_health_ensemble'] = {
            'rmse': float(ens_rmse),
            'mae': float(ens_mae),
            'r2': float(ens_r2),
            'mape': float(ens_mape),
            'latency_ms': float(metrics['compressor_health']['latency_ms'] + metrics['combustor_health']['latency_ms'] + metrics['turbine_health']['latency_ms']),
            'model_size_kb': 0.0,
            'feature_importances': {}
        }
        
        # Keep the better one
        if metrics['overall_health_direct']['r2'] >= ens_r2:
            self.stdout.write(self.style.SUCCESS("  -> Choosing Direct Overall Health model (better R2)"))
            joblib.dump(joblib.load(os.path.join(model_dir, 'overall_health_direct.joblib')), os.path.join(model_dir, 'overall_health.joblib'))
            metrics['overall_health'] = metrics['overall_health_direct']
            metrics['overall_health']['method'] = 'direct'
        else:
            self.stdout.write(self.style.SUCCESS("  -> Choosing Subsystem Mean Ensemble (better R2)"))
            # We don't save a joblib since it's computed as a mean dynamically
            metrics['overall_health'] = metrics['overall_health_ensemble']
            metrics['overall_health']['method'] = 'ensemble_mean'
            
        # C. Train Performance Models (Health-Informed)
        self.stdout.write("Training Performance Models (Thrust, TSFC)...")
        # For training Thrust and TSFC, we use the true health from the dataset
        # For validating, we use the predicted health from our models on the test set to mimic inference cascade!
        
        def train_eval_performance(target_name):
            # Median/Standard prediction model (squared error loss)
            X_train = train_df[FEATURES_PERFORMANCE]
            y_train = train_df[target_name]
            
            # Predict health for the test set to evaluate cascade
            test_df_pred = test_df.copy()
            test_df_pred['compressor_health'] = comp_model.predict(test_df[FEATURES_COMPRESSOR])
            test_df_pred['combustor_health'] = comb_model.predict(test_df[FEATURES_COMBUSTOR])
            test_df_pred['turbine_health'] = turb_model.predict(test_df[FEATURES_TURBINE])
            
            X_test_pred = test_df_pred[FEATURES_PERFORMANCE]
            y_test = test_df[target_name]
            
            # Standard GBR (median prediction)
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', GradientBoostingRegressor(random_state=42, n_estimators=100, max_depth=4))
            ])
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test_pred)
            
            # Save median model
            model_path = os.path.join(model_dir, f"{target_name}.joblib")
            joblib.dump(pipeline, model_path)
            
            # Quantiles (alpha=0.1 and 0.9)
            pipeline_low = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', GradientBoostingRegressor(loss='quantile', alpha=0.1, random_state=42, n_estimators=100, max_depth=4))
            ])
            pipeline_low.fit(X_train, y_train)
            joblib.dump(pipeline_low, os.path.join(model_dir, f"{target_name}_low.joblib"))
            
            pipeline_high = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', GradientBoostingRegressor(loss='quantile', alpha=0.9, random_state=42, n_estimators=100, max_depth=4))
            ])
            pipeline_high.fit(X_train, y_train)
            joblib.dump(pipeline_high, os.path.join(model_dir, f"{target_name}_high.joblib"))
            
            # Compute metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            mape = mean_absolute_percentage_error(y_test, y_pred)
            
            # Get feature importances
            importances = pipeline.named_steps['regressor'].feature_importances_
            feature_imp = {feat: float(imp) for feat, imp in zip(FEATURES_PERFORMANCE, importances)}
            
            # Estimate latency
            t0 = time.perf_counter()
            for _ in range(100):
                pipeline.predict(X_test_pred.iloc[[0]])
            latency_ms = ((time.perf_counter() - t0) / 100.0) * 1000.0
            
            metrics[target_name] = {
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape),
                'latency_ms': float(latency_ms),
                'model_size_kb': float(os.path.getsize(model_path) / 1024.0),
                'feature_importances': feature_imp
            }
            
            self.stdout.write(f"  {target_name}: RMSE={rmse:.4f}, MAPE={mape:.4f}%, R2={r2:.4f}, Latency={latency_ms:.2f}ms")
            
        train_eval_performance('thrust_n')
        train_eval_performance('tsfc_g_n_s')
        
        # Save metrics JSON
        metrics_path = os.path.join(model_dir, 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
            
        self.stdout.write(self.style.SUCCESS(f"Saved all models and metrics to {model_dir}"))
