import numpy as np
import pandas as pd

def add_derived_features(df):
    """
    Operates on a pandas DataFrame (with snake_case columns) to add derived physics features.
    """
    df = df.copy()
    
    # 1. p2_ratio = p2_pa / pamb_pa
    df['p2_ratio'] = df['p2_pa'] / df['pamb_pa']
    
    # 2. t2_ratio = t2_k / tamb_k
    df['t2_ratio'] = df['t2_k'] / df['tamb_k']
    
    # 3. t3_t4_ratio = (t3_k - t4_k) / t3_k
    df['t3_t4_ratio'] = (df['t3_k'] - df['t4_k']) / df['t3_k']
    
    # 4. corrected_rpm = rpm_rev_min / sqrt(tamb_k)
    df['corrected_rpm'] = df['rpm_rev_min'] / np.sqrt(df['tamb_k'])
    
    # 5. corrected_fuel_flow = fuel_flow_kg_s / (pamb_pa * sqrt(tamb_k))
    df['corrected_fuel_flow'] = df['fuel_flow_kg_s'] / (df['pamb_pa'] * np.sqrt(df['tamb_k']))
    
    # 6. Additional pressure ratios for Combustor and Turbine subsystems
    df['p3_p2_ratio'] = df['p3_pa'] / df['p2_pa']
    df['p4_p3_ratio'] = df['p4_pa'] / df['p3_pa']
    
    return df

def compute_features_dict(row):
    """
    Computes derived physics features for a single dictionary payload (snake_case).
    """
    res = dict(row)
    
    res['p2_ratio'] = res['p2_pa'] / res['pamb_pa']
    res['t2_ratio'] = res['t2_k'] / res['tamb_k']
    res['t3_t4_ratio'] = (res['t3_k'] - res['t4_k']) / res['t3_k']
    res['corrected_rpm'] = res['rpm_rev_min'] / np.sqrt(res['tamb_k'])
    res['corrected_fuel_flow'] = res['fuel_flow_kg_s'] / (res['pamb_pa'] * np.sqrt(res['tamb_k']))
    
    res['p3_p2_ratio'] = res['p3_pa'] / res['p2_pa']
    res['p4_p3_ratio'] = res['p4_pa'] / res['p3_pa']
    
    return res
