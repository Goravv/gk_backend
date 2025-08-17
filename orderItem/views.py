from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Item
from .serializers import ItemSerializer
from .excel_parser import parse_excel_file
from client.models import Client
import json
from django.db import transaction
import pandas as pd 


# class UploadExcelView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         file = request.FILES.get('file')
#         client_name = request.POST.get('client_name')
#         marka = request.POST.get('marka')

#         if not file or not client_name or not marka:
#             return Response({"error": "File, client name, and marka are required"}, status=400)

#         # Get or create client ONLY for the current user
#         client, created = Client.objects.get_or_create(
#             user=request.user,
#             client_name=client_name,
#             marka=marka
#         )

#         try:
#             items_data = parse_excel_file(file)
#         except ValueError as e:
#             return Response({"error": str(e)}, status=400)

#         for item_data in items_data:
#             item_data['client'] = client
#             Item.objects.update_or_create(
#                 part_no=item_data['part_no'],
#                 client=client,
#                 defaults=item_data
#             )

#         return Response({"message": "Excel data uploaded successfully"}, status=200)

class UploadExcelView(APIView):
    permission_classes = [permissions.IsAuthenticated]                                                                                                                                                                                                                     
    def post(self, request):
        file = request.FILES.get('file')
        client_name = request.data.get('client_name')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka are required"}, status=400)

        # Get or create the client
        client = Client.objects.get(
            user=request.user,
            client_name=client_name.strip(),
            marka=marka.strip()
        )

        # Parse data from Excel file or JSON
        if file:
            try:
                df = pd.read_excel(file)
                items_data = df.to_dict(orient='records')
            except Exception as e:
                return Response({"error": f"Failed to parse Excel file: {str(e)}"}, status=400)
        else:
            raw_data = request.data.get('data')
            if not raw_data:
                return Response({"error": "No data provided"}, status=400)

            # Handle JSON string or dict/list
            if isinstance(raw_data, str):
                try:
                    parsed_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON string in 'data'"}, status=400)
            else:
                parsed_data = raw_data

            if isinstance(parsed_data, dict):
                items_data = [parsed_data]
            elif isinstance(parsed_data, list):
                items_data = parsed_data
            else:
                return Response({"error": "Invalid data format. Must be list or dict."}, status=400)

        if not items_data:
            return Response({"error": "No items found to process"}, status=400)

        part_nos = [item.get('part_no') or item.get('partNo') for item in items_data if item.get('part_no') or item.get('partNo')]

        existing_items_qs = Item.objects.filter(client=client, part_no__in=part_nos)
        existing_items_dict = {item.part_no: item for item in existing_items_qs}

        items_to_create = []
        items_to_update = []

        for data in items_data:
            part_no = data.get('part_no') or data.get('partNo')
            description = data.get('description', '')
            qty = data.get('qty', 0)

            try:
                qty = int(qty)
            except:
                qty = 0

            if not part_no:
                continue

            if part_no in existing_items_dict:
                item = existing_items_dict[part_no]
                item.description = description
                item.qty += qty
                items_to_update.append(item)
            else:
                items_to_create.append(Item(
                    client=client,
                    part_no=part_no,
                    description=description,
                    qty=qty
                ))

        # Save to DB
        with transaction.atomic():
            if items_to_create:
                Item.objects.bulk_create(items_to_create, batch_size=100)
            if items_to_update:
                Item.objects.bulk_update(items_to_update, ['description', 'qty'], batch_size=100)

        return Response({"message": "Data uploaded successfully"}, status=200)
class ItemListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka required"}, status=400)

        try:
            client = Client.objects.get( client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        items = Item.objects.filter(client=client)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)


class ItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, part_no):
        try:
            item = Item.objects.get(part_no=part_no, client__user=request.user)
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

        serializer = ItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request, part_no):
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka required"}, status=400)

        try:
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
            item = Item.objects.get(part_no=part_no, client=client)
            item.delete()
            return Response({"message": "Item deleted"})
        except (Client.DoesNotExist, Item.DoesNotExist):
            return Response({"error": "Item not found for this client"}, status=404)


class DeleteAllItemsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka required"}, status=400)

        try:
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        Item.objects.filter(client=client).delete()
        return Response({"message": "All items for client deleted"})





class UpdateItemQtyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        part_no = request.data.get("partNo")
        qty = request.data.get("qty")
        client_name = request.data.get("client_name")
        marka = request.data.get("marka")

        # Validate input
        if not part_no or qty is None:
            return Response({"error": "partNo and qty are required"}, status=status.HTTP_400_BAD_REQUEST)
        if not client_name or not marka:
            return Response({"error": "client_name and marka are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qty = int(qty)
        except ValueError:
            return Response({"error": "qty must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure this client belongs to the logged-in user
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Find the item for that client
            item = Item.objects.get(part_no=part_no, client=client)
        except Item.DoesNotExist:
            return Response({"error": "Item not found for this client"}, status=status.HTTP_404_NOT_FOUND)

        # Update qty
        item.qty = qty
        item.save()

        return Response({
            "message": f"Quantity updated for part {part_no}",
            "part_no": item.part_no,
            "qty": item.qty
        }, status=status.HTTP_200_OK)