from django.urls import path
from api import views

urlpatterns = [
    path('engines/', views.list_engines, name='list_engines'),
    path('engines/<int:engine_id>/history/', views.engine_history, name='engine_history'),
    path('engines/<int:engine_id>/latest/', views.engine_latest, name='engine_latest'),
    path('predict/', views.predict_twin, name='predict_twin'),
    path('model-metrics/', views.model_metrics, name='model_metrics'),
]
