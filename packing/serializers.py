from rest_framework import serializers
from .models import Packing, Stock, PackingDetail, NetWeight

class PackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packing
        fields = '__all__'

    def validate_client(self, client):
        request = self.context.get('request')
        if client.user != request.user:
            raise serializers.ValidationError("You do not own this client.")
        return client


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'
        read_only_fields = ['user']  # user is set from request

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PackingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackingDetail
        fields = '__all__'
        extra_kwargs = {
        'part_no': {'validators': []}
    }
    def validate_client(self, client):
        request = self.context.get('request')
        main_user =request.user.id if request.user.is_staff else request.user.parent_id
        if client.user.id != main_user:
            raise serializers.ValidationError("You do not own this client.")
        return client


class NetWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetWeight
        fields = '__all__'
