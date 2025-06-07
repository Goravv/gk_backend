from django.db import models
from client.models import Client


class Packing(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    part_no = models.CharField(max_length=100)
    description = models.TextField()
    qty = models.IntegerField()
    stock_qty = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['client', 'part_no'], name='unique_client_partno')
            ]
    def __str__(self):
        return self.part_no
class Stock(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()
    
    def __str__(self):
        return self.part_no


class PackingDetail(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="packings")
    part_no = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    hsn_no = models.CharField(max_length=20, blank=True, null=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    total_packing_qty = models.IntegerField(blank=True, null=True)
    box_mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    update_box_mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_mrp = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    npr = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    nsr = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    packed_in_plastic_bag = models.IntegerField(blank=True, null=True)

    case_no_start = models.IntegerField(blank=True, null=True)
    case_no_end = models.IntegerField(blank=True, null=True)
    total_case = models.IntegerField(blank=True, null=True)

    net_wt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_net_wt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_gross_wt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cbm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)

    class Meta:
        unique_together = ('client', 'part_no')

    def __str__(self):
        return f"{self.client.name} - {self.part_no}"