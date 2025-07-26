from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'address',
            'bank_name', 'account_name', 'account_number',
            'ifsc_code', 'ad_code', 'swift_code',
            'exporter_reference_number', 'pan', 'iec',
            'is_active', 'is_staff', 'date_joined'
        ]
        read_only_fields = ['is_staff', 'date_joined', 'is_active']
