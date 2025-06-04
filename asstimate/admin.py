# admin.py

from django.contrib import admin
from .models import MergedItem

@admin.register(MergedItem)
class MergedItemAdmin(admin.ModelAdmin):
    list_display = ['part_no', 'description', 'qty', 'mrp', 'total_amt_mrp', 'tax_percent', 'hsn']
