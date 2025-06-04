# serializers.py

from rest_framework import serializers
from .models import MergedItem

class MergedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergedItem
        fields = '__all__'
