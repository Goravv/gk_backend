from django.db import models
from django.contrib.auth.models import User
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stock_items")
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()
    brand_name = models.CharField(max_length=100)

    def __str__(self):
        return self.part_no


class PackingDetail(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="packings")
    part_no = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    hsn_no = models.CharField(max_length=20, blank=True, null=True)
    gst = models.CharField(blank=True, null=True)
    brand_name = models.CharField(max_length=100, blank=True, null=True)

    total_packing_qty = models.IntegerField(blank=True, null=True)
    mrp_invoice = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mrp_box = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_mrp = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    npr = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    nsr = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    packed_in_plastic_bag = models.IntegerField(blank=True, null=True)

    case_no_start = models.IntegerField(blank=True, null=True)
    case_no_end = models.IntegerField(blank=True, null=True)
    total_case = models.IntegerField(blank=True, null=True)

    net_wt = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    total_net_wt = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    total_gross_wt = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)

    length = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    cbm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)

    def __str__(self):
        return f"{self.client.client_name} - {self.part_no}"


class NetWeight(models.Model):
    part_no = models.CharField(max_length=100)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('part_no', 'net_wt')

    def __str__(self):
        return f"{self.part_no} - {self.net_wt} ({self.count})"
