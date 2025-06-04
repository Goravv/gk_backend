from django.db import models

class Packing(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()
    stock_qty = models.IntegerField()

    def __str__(self):
        return self.part_no
class Stock(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    qty = models.IntegerField()
    
    def __str__(self):
        return self.part_no


class PackingDetail(models.Model):
    part_no = models.CharField(max_length=100)
    total_qty = models.IntegerField()
    box_mrp = models.DecimalField(max_digits=10, decimal_places=2)
    qty_per_box = models.IntegerField()
    case_no_start = models.IntegerField()
    case_no_end = models.IntegerField()
    total_box = models.IntegerField()
    net_wt = models.FloatField()
    gross_wt = models.FloatField()
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    cbm = models.FloatField()

    def __str__(self):
        return self.part_no