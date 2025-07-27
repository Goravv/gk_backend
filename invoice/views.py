from decimal import Decimal, InvalidOperation, DivisionUndefined
from .models import invoice
from .serializers import invoiceSerializer
from client.models import Client
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
            try:
                if not item.mrp:  # covers None and empty string or 0
                    skipped_items.append(item.part_no)
                    continue
                mrp = Decimal(item.mrp)
                if mrp == 0:
                    skipped_items.append(item.part_no)
                    continue

                amt = round(mrp / doller, 2)
                total_amt = amt * item.qty

                if item.part_no in invoice_map:
                # Update existing invoice
                    inv = invoice_map[item.part_no]
                    inv.description = item.description
                    inv.hsn = item.hsn
                    inv.qty = item.qty
                    inv.per_unit = amt
                    inv.total_amt = total_amt
                    invoice_objs_to_update.append(inv)
                else:
                # Create new invoice
                    invoice_objs_to_create.append(invoice(
                        client=item.client,
                        part_no=item.part_no,
                        description=item.description,
                        hsn=item.hsn,
                        qty=item.qty,
                        per_unit=amt,
                        total_amt=total_amt
                    ))
            except (InvalidOperation, DivisionUndefined, ZeroDivisionError):
                skipped_items.append(item.part_no)
                continue

    # Perform bulk operations
        if invoice_objs_to_create:
            invoice.objects.bulk_create(invoice_objs_to_create, ignore_conflicts=True)
        if invoice_objs_to_update:
            invoice.objects.bulk_update(invoice_objs_to_update, ['description', 'hsn', 'qty', 'per_unit', 'total_amt'])

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
