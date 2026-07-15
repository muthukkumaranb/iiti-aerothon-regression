import os
import json
import joblib
import pandas as pd
from django.conf import settings
from digitaltwin.features import compute_features_dict

# Cache models in memory to avoid repeated disk reads
_MODELS_CACHE = {}
_METRICS = None

def get_metrics():
    global _METRICS
    if _METRICS is None:
        metrics_path = os.path.join(settings.BASE_DIR, 'digitaltwin', 'trained_models', 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                _METRICS = json.load(f)
        else:
            _METRICS = {}
    return _METRICS

def load_model(name):
    global _MODELS_CACHE
    if name not in _MODELS_CACHE:
        model_path = os.path.join(settings.BASE_DIR, 'digitaltwin', 'trained_models', f"{name}.joblib")
        if os.path.exists(model_path):
            _MODELS_CACHE[name] = joblib.load(model_path)
        else:
            _MODELS_CACHE[name] = None
    return _MODELS_CACHE[name]

def run_twin_inference(raw_sensor_dict):
    """
    Executes the digital twin inference cascade on a raw sensor reading dictionary.
    Returns predicted health and performance values with uncertainty intervals.
    """
    # 1. Compute physics-derived features
    feats = compute_features_dict(raw_sensor_dict)
    df_feats = pd.DataFrame([feats])
    
    # 2. Subsystem feature lists
    FEATURES_BASE = [
        'altitude_m', 'mach', 'tamb_k', 'pamb_pa', 'rpm_rev_min', 'fuel_flow_kg_s', 'cycle',
        'p2_ratio', 't2_ratio', 'corrected_rpm', 'corrected_fuel_flow'
    ]
    FEATURES_COMPRESSOR = FEATURES_BASE
    FEATURES_COMBUSTOR = FEATURES_BASE + ['t3_t4_ratio', 'p3_p2_ratio']
    FEATURES_TURBINE = FEATURES_BASE + ['t3_t4_ratio', 'p4_p3_ratio']
    FEATURES_OVERALL = FEATURES_BASE + ['t3_t4_ratio', 'p3_p2_ratio', 'p4_p3_ratio']
    
    # 3. Predict Subsystem Healths
    comp_model = load_model('compressor_health')
    comb_model = load_model('combustor_health')
    turb_model = load_model('turbine_health')
    
    pred_comp = float(comp_model.predict(df_feats[FEATURES_COMPRESSOR])[0]) if comp_model else 1.0
    pred_comb = float(comb_model.predict(df_feats[FEATURES_COMBUSTOR])[0]) if comb_model else 1.0
    pred_turb = float(turb_model.predict(df_feats[FEATURES_TURBINE])[0]) if turb_model else 1.0
    
    # 4. Predict Overall Health (direct vs ensemble check)
    metrics = get_metrics()
    overall_method = metrics.get('overall_health', {}).get('method', 'ensemble_mean')
    
    if overall_method == 'direct':
        overall_model = load_model('overall_health')
        pred_overall = float(overall_model.predict(df_feats[FEATURES_OVERALL])[0]) if overall_model else 1.0
    else:
        pred_overall = (pred_comp + pred_comb + pred_turb) / 3.0
        
    # 5. Predict Performance (health-informed performance cascade)
    df_perf = df_feats.copy()
    df_perf['compressor_health'] = pred_comp
    df_perf['combustor_health'] = pred_comb
    df_perf['turbine_health'] = pred_turb
    
    FEATURES_PERFORMANCE = FEATURES_OVERALL + ['compressor_health', 'combustor_health', 'turbine_health']
    
    # Thrust
    thrust_median_model = load_model('thrust_n')
    thrust_low_model = load_model('thrust_n_low')
    thrust_high_model = load_model('thrust_n_high')
    
    pred_thrust = float(thrust_median_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if thrust_median_model else 0.0
    pred_thrust_low = float(thrust_low_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if thrust_low_model else 0.0
    pred_thrust_high = float(thrust_high_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if thrust_high_model else 0.0
    
    # TSFC
    tsfc_median_model = load_model('tsfc_g_n_s')
    tsfc_low_model = load_model('tsfc_g_n_s_low')
    tsfc_high_model = load_model('tsfc_g_n_s_high')
    
    pred_tsfc = float(tsfc_median_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if tsfc_median_model else 0.0
    pred_tsfc_low = float(tsfc_low_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if tsfc_low_model else 0.0
    pred_tsfc_high = float(tsfc_high_model.predict(df_perf[FEATURES_PERFORMANCE])[0]) if tsfc_high_model else 0.0
    
    # Combine results
    results = {
        'engineered_features': feats,
        'predicted_compressor_health': pred_comp,
        'predicted_combustor_health': pred_comb,
        'predicted_turbine_health': pred_turb,
        'predicted_overall_health': pred_overall,
        'predicted_thrust': {
            'value': pred_thrust,
            'low_ci': pred_thrust_low,
            'high_ci': pred_thrust_high
        },
        'predicted_tsfc': {
            'value': pred_tsfc,
            'low_ci': pred_tsfc_low,
            'high_ci': pred_tsfc_high
        }
    }
    return results
