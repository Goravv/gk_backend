from client.models import Client
from orderItem.models import Item
from excelFile.models import ExcelData
from .models import MergedItem

def populate_merged_items(client_name):
    try:
        client = Client.objects.get(client_name=client_name)
    except Client.DoesNotExist:
        raise ValueError("Client not found")

    # Delete existing MergedItem records only for this client
    MergedItem.objects.filter(client=client).delete()

    # Fetch items associated with this client
    for item in Item.objects.filter(client_name=client):
        try:
            excel = ExcelData.objects.get(item_code=item.part_no)
            mrp = excel.mrp_per_unit
            total_amt = mrp * item.qty if mrp is not None else None
            tax = excel.gst_percent
            hsn = excel.hsn_code
        except ExcelData.DoesNotExist:
            mrp = total_amt = tax = hsn = None

        # Create the merged item
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
