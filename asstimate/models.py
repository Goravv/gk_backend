from django.db import models
from client.models import Client

class MergedItem(models.Model):
    part_no = models.CharField(max_length=100)
    description = models.TextField()
    qty = models.IntegerField()

    # Joined fields from ExcelData
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amt_mrp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hsn = models.CharField(max_length=100, null=True, blank=True)

    # Foreign key to Client model
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="merged_items")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["part_no", "client"], name="unique_mergeditem_per_client")
        ]

    def __str__(self):
        return f"{self.part_no} ({self.client.client_name} - {self.client.marka})"
