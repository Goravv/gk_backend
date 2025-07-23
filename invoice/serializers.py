from rest_framework import serializers
from .models import invoice

class invoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = invoice
        fields = '__all__'
