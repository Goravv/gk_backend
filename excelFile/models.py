from django.db import models

class ExcelData(models.Model):
    item_code = models.CharField(primary_key=True, max_length=100)
    item_description = models.TextField()
    mrp_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    hsn_code = models.IntegerField(null=False, blank=False)
    gst_percent = models.CharField(max_length=10, null=False, blank=False)

    def __str__(self):
        return self.item_description
