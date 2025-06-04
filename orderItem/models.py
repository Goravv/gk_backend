from django.db import models

class Item(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amt_mrp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hsn = models.CharField(max_length=50, null=True, blank=True)
    billed_qty = models.IntegerField(null=True, blank=True)
    total_amt_billed_qty = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.part_no
