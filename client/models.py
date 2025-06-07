from django.db import models

class Client(models.Model):
    client_name = models.CharField(max_length=100, primary_key=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.client_name
