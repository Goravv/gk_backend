# serializers.py
from rest_framework import serializers
from .models import Packing, Stock,PackingDetail,NetWeight

class PackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packing
        fields = '__all__'

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class PackingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackingDetail
        fields = '__all__'




class NetWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetWeight
        fields = '__all__'
