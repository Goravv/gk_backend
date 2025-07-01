from rest_framework import viewsets, permissions
from .models import Client
from .serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show only data belonging to the logged-in user
        return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Auto-assign the user to the new Client
        serializer.save(user=self.request.user)
    