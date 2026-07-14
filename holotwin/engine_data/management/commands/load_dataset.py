import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from engine_data.models import EngineCycleRecord

class Command(BaseCommand):
    help = 'Load turbojet complete dataset from CSV into database'

    def handle(self, *args, **options):
        # Look for the dataset path
        possible_paths = [
            os.path.join(settings.BASE_DIR, '..', 'Dataset', 'turbojet_complete_dataset.csv'),
            os.path.join(settings.BASE_DIR, 'Dataset', 'turbojet_complete_dataset.csv'),
            os.path.join('/home/cygnusvale/coding/projects/iiti-aerothon-regression/Dataset/turbojet_complete_dataset.csv')
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
                
        if not csv_path:
            self.stdout.write(self.style.ERROR("Could not find turbojet_complete_dataset.csv in expected locations."))
            return
            
        self.stdout.write(f"Reading data from {csv_path}...")
        
        with open(csv_path, mode='r') as f:
            reader = csv.DictReader(f)
            records = []
            for row in reader:
                records.append(EngineCycleRecord(
                    engine_id=int(row['EngineID']),
                    cycle=int(row['Cycle']),
                    altitude_m=float(row['Altitude_m']),
                    mach=float(row['Mach']),
                    tamb_k=float(row['Tamb_K']),
                    pamb_pa=float(row['Pamb_Pa']),
                    rpm_rev_min=float(row['RPM_rev_min']),
                    fuel_flow_kg_s=float(row['FuelFlow_kg_s']),
                    p2_pa=float(row['P2_Pa']),
                    t2_k=float(row['T2_K']),
                    p3_pa=float(row['P3_Pa']),
                    t3_k=float(row['T3_K']),
                    p4_pa=float(row['P4_Pa']),
                    t4_k=float(row['T4_K']),
                    compressor_health=float(row['CompressorHealth']),
                    combustor_health=float(row['CombustorHealth']),
                    turbine_health=float(row['TurbineHealth']),
                    overall_health=float(row['OverallHealth']),
                    thrust_n=float(row['Thrust_N']),
                    tsfc_g_n_s=float(row['TSFC_g_N_s'])
                ))
            
            self.stdout.write(f"Parsed {len(records)} rows from CSV. Loading to database...")
            
            # bulk_create with update_conflicts requires Django 4.2+ & SQLite 3.24.0+
            EngineCycleRecord.objects.bulk_create(
                records,
                update_conflicts=True,
                unique_fields=['engine_id', 'cycle'],
                update_fields=[
                    'altitude_m', 'mach', 'tamb_k', 'pamb_pa', 'rpm_rev_min', 'fuel_flow_kg_s',
                    'p2_pa', 't2_k', 'p3_pa', 't3_k', 'p4_pa', 't4_k',
                    'compressor_health', 'combustor_health', 'turbine_health', 'overall_health',
                    'thrust_n', 'tsfc_g_n_s'
                ]
            )
            
        self.stdout.write(self.style.SUCCESS(f"Successfully loaded/upserted {len(records)} records."))
