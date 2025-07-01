from rest_framework import serializers
from .models import MergedItem
from client.models import Client

class MergedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergedItem
        fields = '__all__'

    def validate_client(self, client):
        request = self.context.get('request')
        if client.user != request.user:
            raise serializers.ValidationError("You do not own this client.")
        return client
