from django.db import models
from django.conf import settings

class Client(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_name = models.CharField(max_length=100)
    marka = models.CharField(max_length=100)
    address = models.TextField()
    vessel_no = models.CharField(max_length=100)
    port_of_loading = models.CharField(max_length=100)
    terms_of_payment = models.TextField()
    delivery_terms = models.TextField()
    port_of_discharge = models.CharField(max_length=100)
    final_destination = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'client_name', 'marka'], name='unique_client_per_user')
        ]
        ordering = ['-created_at']  

    def __str__(self):
        return f"{self.client_name} - {self.marka}"
