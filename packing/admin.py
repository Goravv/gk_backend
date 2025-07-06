from django.contrib import admin
from .models import PackingDetail

# Register your models here.
@admin.register(PackingDetail)
class packingList(admin.ModelAdmin):
    list_display = [field.name for field in PackingDetail._meta.fields]