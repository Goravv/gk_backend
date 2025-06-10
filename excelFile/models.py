from django.db import models

class ExcelData(models.Model):
    item_code = models.CharField(primary_key=True, max_length=100)
    item_description = models.TextField()
    item_segment = models.CharField(max_length=100)
    mrp_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    hsn_code = models.IntegerField()
    gst_percent = models.DecimalField(max_digits=3, decimal_places=0)

    def __str__(self):
        return self.item_description
