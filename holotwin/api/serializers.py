from rest_framework import serializers
from engine_data.models import EngineCycleRecord

class EngineCycleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineCycleRecord
        fields = '__all__'
