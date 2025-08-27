from django.db import models
from django.conf import settings

class ExcelData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    part_no = models.CharField(primary_key=True, max_length=100)
    description = models.TextField()
    mrp_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    hsn_code = models.IntegerField(null=False, blank=False)
    gst_percent = models.IntegerField()
    brand_name=models.CharField(max_length=20)

    def __str__(self):
        return self.item_description
