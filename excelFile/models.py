from django.db import models
from django.conf import settings

class ExcelData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    part_no = models.CharField(max_length=100)
    description = models.TextField()
    mrp_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    hsn_code = models.IntegerField()
    gst_percent = models.IntegerField()
    brand_name = models.CharField(max_length=20)


    class Meta:
        # enforce uniqueness on (user, part_no)
        unique_together = ('user', 'part_no')

    def __str__(self):
        return f"{self.part_no} ({self.user})"
