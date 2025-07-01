from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clients")  # Per-user ownership
    client_name = models.CharField(max_length=100)
    marka = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'client_name', 'marka'], name='unique_client_per_user')
    ]
    def __str__(self):
        return self.client_name
