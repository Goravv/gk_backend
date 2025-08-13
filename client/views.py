from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Client
from .serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Client.objects.all()
        elif self.request.user.is_staff:
            return Client.objects.filter(user=self.request.user)
        else:
            return Client.objects.filter(user=self.request.user.parent_id)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=self.request.user.parent_id)
    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to edit this client.")
        serializer.save()
