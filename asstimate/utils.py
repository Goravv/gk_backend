from client.models import Client
from orderItem.models import Item
from excelFile.models import ExcelData
from .models import MergedItem

def populate_merged_items(client):
    if not isinstance(client, Client):
        raise ValueError("Expected a Client instance")

    # Delete existing merged items for this client
    MergedItem.objects.filter(client=client).delete()

    # Merge Item and ExcelData rows
    for item in Item.objects.filter(client=client):
        try:
            excel = ExcelData.objects.get(item_code=item.part_no)
            mrp = excel.mrp_per_unit
            tax = excel.gst_percent
            hsn = excel.hsn_code
        except ExcelData.DoesNotExist:
            mrp = None
            tax = None
            hsn = None

        # Handle potential None values for required fields
        if not item.part_no:
            raise ValueError(f"Missing part_no in item: {item}")
        if item.description is None:
            item.description = ""
        if item.qty is None:
            item.qty = 0

        total_amt = mrp * item.qty if mrp is not None else None

        # Create MergedItem safely
        MergedItem.objects.create(
            part_no=item.part_no,
            description=item.description,
            qty=item.qty,
            mrp=mrp,
            total_amt_mrp=total_amt,
            tax_percent=tax,
            hsn=hsn,
            client=client,
        )
