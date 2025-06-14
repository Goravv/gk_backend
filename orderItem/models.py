from django.db import models
from client.models import Client

class Item(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    part_no = models.CharField(max_length=100)
    description = models.TextField()
    qty = models.IntegerField()
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amt_mrp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hsn = models.CharField(max_length=50, null=True, blank=True)
    billed_qty = models.IntegerField(null=True, blank=True)
    total_amt_billed_qty = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['client', 'part_no'], name='unique_client_part')
        ]

    def __str__(self):
        return f"{self.client} - {self.part_no}"
