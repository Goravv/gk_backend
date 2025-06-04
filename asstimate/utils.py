# orderItem/utils.py

from orderItem.models import Item
from excelFile.models import ExcelData
from .models import MergedItem  # Adjust import as needed

def populate_merged_items():
    MergedItem.objects.all().delete()  # optional: clear previous data

    for item in Item.objects.all():
        try:
            excel = ExcelData.objects.get(item_code=item.part_no)
            mrp = excel.mrp_per_unit
            total_amt = mrp * item.qty
            tax = excel.gst_percent
            hsn = excel.hsn_code
        except ExcelData.DoesNotExist:
            mrp = None
            total_amt = None
            tax = None
            hsn = None

        MergedItem.objects.create(
            part_no=item.part_no,
            description=item.description,
            qty=item.qty,
            mrp=mrp,
            total_amt_mrp=total_amt,
            tax_percent=tax,
            hsn=hsn
        )
