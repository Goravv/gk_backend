from client.models import Client
from orderItem.models import Item
from excelFile.models import ExcelData
from .models import MergedItem
from decimal import Decimal


def populate_merged_items(client,client_detail):
    if not isinstance(client, Client):
        raise ValueError("Expected a Client instance")

    # Fetch items for this client
    items = list(Item.objects.filter(client=client))
    
    rupees=int(client_detail.rupees)
    gst = client_detail.gst  # This is a list of dicts
    print(gst)
    gst_discount = {}

    for obj in gst:
        gst_discount[int(obj['gst'])] = Decimal(obj['discount'])

    print(gst_discount)

    # Fetch all ExcelData rows needed in a single query
    part_nos = [item.part_no for item in items if item.part_no]
    excel_data_map = {
        e.item_code: e for e in ExcelData.objects.filter(item_code__in=part_nos)
    }

    # Fetch existing MergedItems for this client
    existing_merged_items = MergedItem.objects.filter(client=client, part_no__in=part_nos)
    existing_map = {(m.part_no): m for m in existing_merged_items}

    to_update = []
    to_create = []
    missing_part=[]

    for item in items:
        if not item.part_no:
            raise ValueError(f"Missing part_no in item: {item}")
        part_no=item.part_no
        excel = excel_data_map.get(part_no)
        if not excel:
            part_no='0'+part_no
            excel = excel_data_map.get(part_no)
            if not excel:
                part_no=part_no[1:]
                missing_part.append(part_no)
                continue


        description = item.description 
        mrp = excel.mrp_per_unit 
        tax = excel.gst_percent 
        hsn = excel.hsn_code 
        qty = item.qty 
        total_amt = mrp * qty
        effective_price = round((total_amt * (100 - gst_discount[tax]) / 100), 2) if tax else 0


        doller_effective_price = round(effective_price/rupees , 2) 

        existing = existing_map.get(part_no)

        if existing:
            # Update existing
            existing.description = description
            existing.qty = qty
            existing.mrp = mrp
            existing.total_amt_mrp = total_amt
            existing.tax_percent = tax
            existing.hsn = hsn
            existing.effective_price = effective_price
            existing.doller_effective_price = doller_effective_price
            to_update.append(existing)
        else:
            # Create new
            to_create.append(MergedItem(
                part_no=part_no,
                description=description,
                qty=qty,
                mrp=mrp,
                total_amt_mrp=total_amt,
                tax_percent=tax,
                hsn=hsn,
                effective_price=effective_price,
                doller_effective_price=doller_effective_price,
                client=client,
            ))
    print(missing_part,to_create,to_update)

    if to_update:
        MergedItem.objects.bulk_update(
            to_update,
            [
                "description", "qty", "mrp", "total_amt_mrp",
                "tax_percent", "hsn", "effective_price", "doller_effective_price"
            ]
        )

    if to_create:
        MergedItem.objects.bulk_create(to_create)
    return missing_part






























# # def populate_merged_items(client, gst_detail, rupees):
# #     if not isinstance(client, Client):
# #         raise ValueError("Expected a Client instance")

# #     # Delete existing merged items for this client
# #     MergedItem.objects.filter(client=client).delete()

# #     merged_items = []  # List to collect all MergedItem instances

# #     # Merge Item and ExcelData rows
# #     for item in Item.objects.filter(client=client):
# #         try:
# #             excel = ExcelData.objects.get(item_code=part_no)
# #             if item.description is None:
# #                 item.description = excel.description
# #             mrp = excel.mrp_per_unit
# #             tax = excel.gst_percent
# #             hsn = excel.hsn_code
# #         except ExcelData.DoesNotExist:
# #             mrp = 0
# #             tax = 0
# #             hsn = 0
        
# #         if not item.part_no:
# #             raise ValueError(f"Missing part_no in item: {item}")

# #         if item.qty is None:
# #             item.qty = 0

# #         total_amt = mrp * item.qty 
# #         effective_price = round((total_amt * (100 - gst_detail.get(int(tax), 0))) / 100, 2) if tax != 0 else 0
# #         doller_effective_price = round(effective_price / rupees, 2) if rupees else 0

# #         merged_items.append(MergedItem(
# #             part_no=item.part_no,
# #             description=item.description,
# #             qty=item.qty,
# #             mrp=mrp,
# #             total_amt_mrp=total_amt,
# #             tax_percent=tax,
# #             hsn=hsn,
# #             effective_price=effective_price,
# #             doller_effective_price=doller_effective_price,
# #             client=client,
# #         ))

# #     # Bulk insert all merged items at once
# #     if merged_items:
# #         MergedItem.objects.bulk_create(merged_items, ignore_conflicts=True)
# def populate_merged_items(client, gst_detail, rupees):
#     if not isinstance(client, Client):
#         raise ValueError("Expected a Client instance")

#     # Delete old merged items
#     MergedItem.objects.filter(client=client).delete()

#     # Fetch items for this client
#     items = list(Item.objects.filter(client=client))

#     # Fetch all ExcelData rows needed in a single query
#     part_nos = [item.part_no for item in items if item.part_no]
#     excel_data_map = {
#         e.item_code: e for e in ExcelData.objects.filter(item_code__in=part_nos)
#     }

#     merged_items = []

#     for item in items:
#         if not item.part_no:
#             raise ValueError(f"Missing part_no in item: {item}")

#         excel = excel_data_map.get(item.part_no)

#         description = item.description or (excel.description if excel else "")
#         mrp = excel.mrp_per_unit if excel else 0
#         tax = excel.gst_percent if excel else 0
#         hsn = excel.hsn_code if excel else 0

#         qty = item.qty or 0
#         total_amt = mrp * qty
#         effective_price = round((total_amt * (100 - gst_detail.get(int(tax), 0))) / 100, 2) if tax else 0
#         doller_effective_price = round(effective_price / rupees, 2) if rupees else 0

#         merged_items.append(MergedItem(
#             part_no=item.part_no,
#             description=description,
#             qty=qty,
#             mrp=mrp,
#             total_amt_mrp=total_amt,
#             tax_percent=tax,
#             hsn=hsn,
#             effective_price=effective_price,
#             doller_effective_price=doller_effective_price,
#             client=client,
#         ))

#     # Bulk insert
#     if merged_items:
#         MergedItem.objects.bulk_create(merged_items, ignore_conflicts=True)
