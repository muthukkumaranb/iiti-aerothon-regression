from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from engine_data.models import EngineCycleRecord

class APITestCase(TestCase):
    def setUp(self):
        # Create a few test records
        self.record1 = EngineCycleRecord.objects.create(
            engine_id=1,
            cycle=1,
            altitude_m=5000.0,
            mach=0.4,
            tamb_k=250.0,
            pamb_pa=50000.0,
            rpm_rev_min=60000.0,
            fuel_flow_kg_s=0.5,
            p2_pa=100000.0,
            t2_k=300.0,
            p3_pa=100000.0,
            t3_k=1100.0,
            p4_pa=80000.0,
            t4_k=950.0,
            compressor_health=0.99,
            combustor_health=0.99,
            turbine_health=0.99,
            overall_health=0.99,
            thrust_n=30000.0,
            tsfc_g_n_s=0.015
        )
        self.record2 = EngineCycleRecord.objects.create(
            engine_id=1,
            cycle=2,
            altitude_m=5100.0,
            mach=0.42,
            tamb_k=249.0,
            pamb_pa=49500.0,
            rpm_rev_min=60500.0,
            fuel_flow_kg_s=0.51,
            p2_pa=101000.0,
            t2_k=301.0,
            p3_pa=101000.0,
            t3_k=1110.0,
            p4_pa=81000.0,
            t4_k=960.0,
            compressor_health=0.98,
            combustor_health=0.985,
            turbine_health=0.985,
            overall_health=0.983,
            thrust_n=29500.0,
            tsfc_g_n_s=0.0152
        )

    def test_list_engines(self):
        url = reverse('list_engines')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['engine_id'], 1)
        self.assertEqual(response.data[0]['latest_cycle'], 2)

    def test_engine_history(self):
        url = reverse('engine_history', kwargs={'engine_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['cycle'], 1)
        self.assertEqual(response.data[1]['cycle'], 2)

    def test_engine_latest(self):
        url = reverse('engine_latest', kwargs={'engine_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cycle'], 2)
        self.assertTrue('degradation_slope' in response.data)
        self.assertEqual(len(response.data['extrapolations']), 5)

    def test_predict_twin(self):
        url = reverse('predict_twin')
        payload = {
            'altitude_m': 7000.0,
            'mach': 0.5,
            'tamb_k': 240.0,
            'pamb_pa': 40000.0,
            'rpm_rev_min': 55000.0,
            'fuel_flow_kg_s': 0.45,
            'p2_pa': 80000.0,
            't2_k': 295.0,
            'p3_pa': 80000.0,
            't3_k': 1050.0,
            'p4_pa': 65000.0,
            't4_k': 910.0,
            'cycle': 10
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('predicted_compressor_health' in response.data)
        self.assertTrue('predicted_thrust' in response.data)

    def test_model_metrics(self):
        url = reverse('model_metrics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('compressor_health' in response.data)
