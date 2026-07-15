import json
import os
import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from engine_data.models import EngineCycleRecord
from digitaltwin.models_ml import run_twin_inference, get_metrics

@api_view(['GET'])
def list_engines(request):
    """
    GET /api/engines/
    Returns list of engine IDs, latest cycle, and latest overall health.
    """
    distinct_ids = sorted(list(set(EngineCycleRecord.objects.values_list('engine_id', flat=True))))
    engines_list = []
    
    for eid in distinct_ids:
        latest_record = EngineCycleRecord.objects.filter(engine_id=eid).order_by('-cycle').first()
        if latest_record:
            engines_list.append({
                'engine_id': eid,
                'latest_cycle': latest_record.cycle,
                'latest_overall_health': latest_record.overall_health,
                'latest_thrust': latest_record.thrust_n,
                'latest_tsfc': latest_record.tsfc_g_n_s
            })
            
    return Response(engines_list)

@api_view(['GET'])
def engine_history(request, engine_id):
    """
    GET /api/engines/{id}/history/
    Returns full cycle-by-cycle history (true vs predicted) for a specific engine.
    """
    records = EngineCycleRecord.objects.filter(engine_id=engine_id).order_by('cycle')
    if not records.exists():
        return Response({'error': f"Engine {engine_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
    history_data = []
    for rec in records:
        sensor_payload = {
            'altitude_m': rec.altitude_m,
            'mach': rec.mach,
            'tamb_k': rec.tamb_k,
            'pamb_pa': rec.pamb_pa,
            'rpm_rev_min': rec.rpm_rev_min,
            'fuel_flow_kg_s': rec.fuel_flow_kg_s,
            'p2_pa': rec.p2_pa,
            't2_k': rec.t2_k,
            'p3_pa': rec.p3_pa,
            't3_k': rec.t3_k,
            'p4_pa': rec.p4_pa,
            't4_k': rec.t4_k,
            'cycle': rec.cycle
        }
        twin_res = run_twin_inference(sensor_payload)
        
        history_data.append({
            'cycle': rec.cycle,
            'operating_conditions': {
                'altitude_m': rec.altitude_m,
                'mach': rec.mach,
                'tamb_k': rec.tamb_k,
                'pamb_pa': rec.pamb_pa,
                'rpm_rev_min': rec.rpm_rev_min,
                'fuel_flow_kg_s': rec.fuel_flow_kg_s
            },
            'raw_sensors': {
                'p2_pa': rec.p2_pa,
                't2_k': rec.t2_k,
                'p3_pa': rec.p3_pa,
                't3_k': rec.t3_k,
                'p4_pa': rec.p4_pa,
                't4_k': rec.t4_k
            },
            'engineered_features': twin_res['engineered_features'],
            'true_health': {
                'compressor': rec.compressor_health,
                'combustor': rec.combustor_health,
                'turbine': rec.turbine_health,
                'overall': rec.overall_health
            },
            'predicted_health': {
                'compressor': twin_res['predicted_compressor_health'],
                'combustor': twin_res['predicted_combustor_health'],
                'turbine': twin_res['predicted_turbine_health'],
                'overall': twin_res['predicted_overall_health']
            },
            'true_performance': {
                'thrust': rec.thrust_n,
                'tsfc': rec.tsfc_g_n_s
            },
            'predicted_performance': twin_res['predicted_thrust'],
            'predicted_tsfc': twin_res['predicted_tsfc']
        })
        
    return Response(history_data)

@api_view(['GET'])
def engine_latest(request, engine_id):
    """
    GET /api/engines/{id}/latest/
    Returns current cycle snapshot, predictions, and degradation trend extrapolation.
    """
    records = EngineCycleRecord.objects.filter(engine_id=engine_id).order_by('cycle')
    if not records.exists():
        return Response({'error': f"Engine {engine_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
    latest_rec = records.last()
    
    sensor_payload = {
        'altitude_m': latest_rec.altitude_m,
        'mach': latest_rec.mach,
        'tamb_k': latest_rec.tamb_k,
        'pamb_pa': latest_rec.pamb_pa,
        'rpm_rev_min': latest_rec.rpm_rev_min,
        'fuel_flow_kg_s': latest_rec.fuel_flow_kg_s,
        'p2_pa': latest_rec.p2_pa,
        't2_k': latest_rec.t2_k,
        'p3_pa': latest_rec.p3_pa,
        't3_k': latest_rec.t3_k,
        'p4_pa': latest_rec.p4_pa,
        't4_k': latest_rec.t4_k,
        'cycle': latest_rec.cycle
    }
    
    twin_res = run_twin_inference(sensor_payload)
    
    # Fit degradation trend line
    cycles = [rec.cycle for rec in records]
    overall_healths = [rec.overall_health for rec in records]
    
    if len(cycles) > 1:
        slope, intercept = np.polyfit(cycles, overall_healths, 1)
    else:
        slope = 0.0
        intercept = latest_rec.overall_health
        
    # Extrapolate for next 5 cycles
    extrapolations = []
    for c in range(latest_rec.cycle + 1, latest_rec.cycle + 6):
        projected = slope * c + intercept
        # Clamp health to [0, 1]
        projected = max(0.0, min(1.0, projected))
        extrapolations.append({
            'cycle': c,
            'projected_health': projected
        })
        
    response_data = {
        'engine_id': latest_rec.engine_id,
        'cycle': latest_rec.cycle,
        'operating_conditions': {
            'altitude_m': latest_rec.altitude_m,
            'mach': latest_rec.mach,
            'tamb_k': latest_rec.tamb_k,
            'pamb_pa': latest_rec.pamb_pa,
            'rpm_rev_min': latest_rec.rpm_rev_min,
            'fuel_flow_kg_s': latest_rec.fuel_flow_kg_s
        },
        'raw_sensors': {
            'p2_pa': latest_rec.p2_pa,
            't2_k': latest_rec.t2_k,
            'p3_pa': latest_rec.p3_pa,
            't3_k': latest_rec.t3_k,
            'p4_pa': latest_rec.p4_pa,
            't4_k': latest_rec.t4_k
        },
        'engineered_features': twin_res['engineered_features'],
        'true_health': {
            'compressor': latest_rec.compressor_health,
            'combustor': latest_rec.combustor_health,
            'turbine': latest_rec.turbine_health,
            'overall': latest_rec.overall_health
        },
        'predicted_health': {
            'compressor': twin_res['predicted_compressor_health'],
            'combustor': twin_res['predicted_combustor_health'],
            'turbine': twin_res['predicted_turbine_health'],
            'overall': twin_res['predicted_overall_health']
        },
        'true_performance': {
            'thrust': latest_rec.thrust_n,
            'tsfc': latest_rec.tsfc_g_n_s
        },
        'predicted_performance': twin_res['predicted_thrust'],
        'predicted_tsfc': twin_res['predicted_tsfc'],
        'degradation_slope': slope,
        'extrapolations': extrapolations
    }
    
    return Response(response_data)

@api_view(['POST'])
def predict_twin(request):
    """
    POST /api/predict/
    Accepts raw sensor payload (case-insensitive keys) and returns digital twin predictions.
    """
    raw_payload = request.data
    # Map camelCase or PascalCase to snake_case
    mapped_payload = {}
    
    key_mapping = {
        'engineid': 'engine_id',
        'engine_id': 'engine_id',
        'cycle': 'cycle',
        'altitude_m': 'altitude_m',
        'mach': 'mach',
        'tamb_k': 'tamb_k',
        'pamb_pa': 'pamb_pa',
        'rpm_rev_min': 'rpm_rev_min',
        'fuelflow_kg_s': 'fuel_flow_kg_s',
        'fuel_flow_kg_s': 'fuel_flow_kg_s',
        'p2_pa': 'p2_pa',
        't2_k': 't2_k',
        'p3_pa': 'p3_pa',
        't3_k': 't3_k',
        'p4_pa': 'p4_pa',
        't4_k': 't4_k',
    }
    
    # Fill mapped_payload with standard keys
    for k, v in raw_payload.items():
        k_lower = k.lower()
        if k_lower in key_mapping:
            mapped_payload[key_mapping[k_lower]] = float(v)
        else:
            # Try to match sub-parts
            for map_k, map_v in key_mapping.items():
                if map_k in k_lower:
                    mapped_payload[map_v] = float(v)
                    break
                    
    # Fill defaults if missing
    defaults = {
        'engine_id': 1,
        'cycle': 1,
        'altitude_m': 0.0,
        'mach': 0.0,
        'tamb_k': 288.15,
        'pamb_pa': 101325.0,
        'rpm_rev_min': 50000.0,
        'fuel_flow_kg_s': 1.0,
        'p2_pa': 101325.0,
        't2_k': 288.15,
        'p3_pa': 101325.0,
        't3_k': 1000.0,
        'p4_pa': 101325.0,
        't4_k': 900.0
    }
    
    for def_k, def_v in defaults.items():
        if def_k not in mapped_payload:
            mapped_payload[def_k] = def_v
            
    # Run twin inference cascade
    try:
        results = run_twin_inference(mapped_payload)
        return Response(results)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def model_metrics(request):
    """
    GET /api/model-metrics/
    Returns the metrics from metrics.json (accuracy, latency, size, feature importances).
    """
    metrics = get_metrics()
    return Response(metrics)
