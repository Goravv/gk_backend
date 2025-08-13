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


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'address',
            'bank_name', 'account_name', 'account_number',
            'ifsc_code', 'ad_code', 'swift_code',
            'exporter_reference_number', 'pan', 'iec',
            'parent_id'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)
