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

        merged_items = MergedItem.objects.filter(client=client)
        if not merged_items.exists():
            return Response({"error": "No merged items found for this client"}, status=404)

        doller = None

        # Find valid conversion rate
        for item in merged_items:
            try:
                effective_price = Decimal(item.effective_price)
                if effective_price > 0:
                    doller_candidate = Decimal(item.doller_effective_price) / effective_price
                    if doller_candidate > 0:
                        doller = doller_candidate
                        break
            except (InvalidOperation, DivisionUndefined, ZeroDivisionError):
                continue

        if not doller:
            return Response({
                "error": "Unable to determine valid conversion rate (doller). All items may have 0 effective price or invalid data."
            }, status=400)

        invoice_objs = []
        skipped_items = []

        for item in merged_items:
            try:
                mrp = Decimal(item.mrp)
                if mrp == 0:
                    skipped_items.append(item.part_no)
                    continue

                per_unit = mrp / doller
                invoice_objs.append(invoice(
                    client=item.client,
                    part_no=item.part_no,
                    description=item.description,
                    hsn=item.hsn,
                    qty=item.qty,
                    per_unit=per_unit,
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
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka required"}, status=400)

        try:
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        items = invoice.objects.filter(client=client)
        serializer = invoiceSerializer(items, many=True)
        return Response(serializer.data)
