import numpy as np
import pandas as pd
from django.test import TestCase
from digitaltwin.features import add_derived_features, compute_features_dict

class FeatureEngineeringTestCase(TestCase):
    def setUp(self):
        # Create a sample row in snake_case
        self.sample_data = {
            'p2_pa': 76228.31,
            'pamb_pa': 39779.10,
            't2_k': 302.37,
            'tamb_k': 240.05,
            't3_k': 990.92,
            't4_k': 937.08,
            'rpm_rev_min': 37691.73,
            'fuel_flow_kg_s': 0.30,
            'p3_pa': 74966.68,
            'p4_pa': 59230.69
        }
        
    def test_add_derived_features_df(self):
        df = pd.DataFrame([self.sample_data])
        df_feats = add_derived_features(df)
        
        # Manually compute expected values
        expected_p2_ratio = self.sample_data['p2_pa'] / self.sample_data['pamb_pa']
        expected_t2_ratio = self.sample_data['t2_k'] / self.sample_data['tamb_k']
        expected_t3_t4_ratio = (self.sample_data['t3_k'] - self.sample_data['t4_k']) / self.sample_data['t3_k']
        expected_corrected_rpm = self.sample_data['rpm_rev_min'] / np.sqrt(self.sample_data['tamb_k'])
        expected_corrected_fuel = self.sample_data['fuel_flow_kg_s'] / (self.sample_data['pamb_pa'] * np.sqrt(self.sample_data['tamb_k']))
        expected_p3_p2_ratio = self.sample_data['p3_pa'] / self.sample_data['p2_pa']
        expected_p4_p3_ratio = self.sample_data['p4_pa'] / self.sample_data['p3_pa']

        self.assertAlmostEqual(df_feats.loc[0, 'p2_ratio'], expected_p2_ratio, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 't2_ratio'], expected_t2_ratio, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 't3_t4_ratio'], expected_t3_t4_ratio, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 'corrected_rpm'], expected_corrected_rpm, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 'corrected_fuel_flow'], expected_corrected_fuel, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 'p3_p2_ratio'], expected_p3_p2_ratio, places=5)
        self.assertAlmostEqual(df_feats.loc[0, 'p4_p3_ratio'], expected_p4_p3_ratio, places=5)

    def test_compute_features_dict(self):
        feats_dict = compute_features_dict(self.sample_data)
        
        expected_p2_ratio = self.sample_data['p2_pa'] / self.sample_data['pamb_pa']
        expected_corrected_fuel = self.sample_data['fuel_flow_kg_s'] / (self.sample_data['pamb_pa'] * np.sqrt(self.sample_data['tamb_k']))
        
        self.assertAlmostEqual(feats_dict['p2_ratio'], expected_p2_ratio, places=5)
        self.assertAlmostEqual(feats_dict['corrected_fuel_flow'], expected_corrected_fuel, places=5)
