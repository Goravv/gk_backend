from django.db import models
from client.models import Client

class invoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    part_no = models.CharField(max_length=100)
    description = models.TextField()
    hsn = models.CharField(max_length=50, null=True, blank=True)
    qty = models.IntegerField()
    per_unit_rupees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_unit_dollar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amt_dollar = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    taxable_amt = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    gst=models.IntegerField()
    gst_amt=models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_net_wt=models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['client', 'part_no'], name='unique_client_part_invoice')
        ]

    def __str__(self):
        return f"{self.client} - {self.part_no}"
