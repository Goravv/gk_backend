from decimal import Decimal, InvalidOperation, DivisionUndefined
from .models import invoice
from .serializers import invoiceSerializer
from client.models import Client
from excelFile.models import ExcelData
from packing.models import PackingDetail
from orderItem.models import Item
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response


class invoiceGenrate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    
    def post(self, request):
        client_name = request.data.get('client')

        if not client_name:
            return Response({"error": "Client name is required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name, user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client"}, status=400)

        client_detail = Client.objects.filter(client_name=client_name, user=request.user).first()
        merged_items = Item.objects.filter(client=client)
        packing=PackingDetail.objects.filter(client=client)
        mrp_data=ExcelData.objects.all()

        if not merged_items.exists():
            return Response({"error": "No order items found for this client"}, status=404)

        doller = int(client_detail.rupees)

        invoice_objs_to_create = []
        invoice_objs_to_update = []
        skipped_items = []

    # Fetch existing invoices for these items
        existing_invoices = invoice.objects.filter(
            client=client,
            part_no__in=[item.part_no for item in merged_items]
        )    
        invoice_map = {inv.part_no: inv for inv in existing_invoices}

        for item in merged_items:
            print(item)
            try:
                related_mrp_data = mrp_data.filter(item_code=item.part_no).first()
                if not related_mrp_data:
                    skipped_items.append(item.part_no)
                    continue

                mrp = Decimal(related_mrp_data.mrp_per_unit or 0)
                if mrp == 0:
                    skipped_items.append(item.part_no)
                    continue
                

                amt = round(mrp / doller, 2)
                tax_amt=mrp*item.qty
                total_amt = max(amt * item.qty,round(tax_amt/doller,2))
                hsn=related_mrp_data.hsn_code
                related_packing = packing.filter(part_no=item.part_no).first()
                gst = related_packing.gst if related_packing else 0
                gst_amt = round(tax_amt * (Decimal(gst) / 100), 2) if gst else 0
                total_net_wt=related_packing.total_net_wt if related_packing else 0

                if item.part_no in invoice_map:
                # Update existing invoice
                    inv = invoice_map[item.part_no]
                    inv.description = item.description
                    inv.hsn = hsn
                    inv.qty = item.qty
                    inv.per_unit_rupees = mrp
                    inv.per_unit_dollar = amt
                    inv.total_amt_dollar = total_amt
                    inv.taxable_amt=tax_amt
                    inv.gst= gst
                    inv.gst_amt=gst_amt
                    inv.total_net_wt=total_net_wt
                    invoice_objs_to_update.append(inv)
                else:
                # Create new invoice
                    invoice_objs_to_create.append(invoice(
                        client=item.client,
                        part_no=item.part_no,
                        description=item.description,
                        hsn=item.hsn,
                        qty=item.qty,
                        per_unit_rupees=mrp,
                        per_unit_dollar=amt,
                        total_amt_dollar=total_amt,
                        taxable_amt=mrp*item.qty,
                        gst=gst,
                        gst_amt=gst_amt,
                        total_net_wt=total_net_wt
                    ))
            except (InvalidOperation, DivisionUndefined, ZeroDivisionError):
                skipped_items.append(item.part_no)
                continue

        print(invoice_objs_to_create)
        print(invoice_objs_to_update)
        print(skipped_items)
        if invoice_objs_to_create:
            invoice.objects.bulk_create(invoice_objs_to_create, ignore_conflicts=True)
        if invoice_objs_to_update:
            invoice.objects.bulk_update(invoice_objs_to_update, ['description', 'hsn', 'qty', 'per_unit_rupees', 'per_unit_dollar','total_amt_dollar','taxable_amt','gst','gst_amt','total_net_wt'])

        return Response({
            "message": "Invoice generated/updated successfully",
            "skipped_items": skipped_items
        })

    def get(self, request):
    # Extract and clean query params
        client_name = request.query_params.get('client', '').strip()
        marka = request.query_params.get('marka', '').strip()

        if not client_name or not marka:
            return Response({"error": "Client name and marka are required"}, status=400)

        try:
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        items = invoice.objects.filter(client=client)
        serializer = invoiceSerializer(items, many=True)
        return Response(serializer.data)
