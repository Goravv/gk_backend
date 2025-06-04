# models.py

from django.db import models

class MergedItem(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()

    # Joined fields from ExcelData
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amt_mrp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hsn = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.part_no
