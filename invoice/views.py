from decimal import Decimal, InvalidOperation, DivisionUndefined
from .models import invoice
from .serializers import invoiceSerializer
from client.models import Client
from asstimate.models import MergedItem
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

        merged_items = MergedItem.objects.filter(client=client)
        if not merged_items.exists():
            return Response({"error": "No merged items found for this client"}, status=404)

        doller = int(client_detail.rupees)

        

        invoice_objs = []
        skipped_items = []

        for item in merged_items:
            
            try:
                mrp = Decimal(item.mrp)
                if mrp == 0:
                    skipped_items.append(item.part_no)
                    continue

                amt = round(mrp / doller,2)
                invoice_objs.append(invoice(
                    client=item.client,
                    part_no=item.part_no,
                    description=item.description,
                    hsn=item.hsn,
                    qty=item.qty,
                    per_unit=amt,
                    total_amt=item.doller_effective_price
                ))
            except (InvalidOperation, DivisionUndefined, ZeroDivisionError):
                skipped_items.append(item.part_no)
                continue

        invoice.objects.bulk_create(invoice_objs, ignore_conflicts=True)

        return Response({
            "message": "Invoice generated successfully",
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
