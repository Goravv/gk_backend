from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Item
from .serializers import ItemSerializer
from .excel_parser import parse_excel_file
from client.models import Client

class UploadExcelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        client_name = request.POST.get('client_name')
        marka = request.POST.get('marka')

        if not file or not client_name or not marka:
            return Response({"error": "File, client name, and marka are required"}, status=400)

        # Get or create client ONLY for the current user
        client, created = Client.objects.get_or_create(
            user=request.user,
            client_name=client_name,
            marka=marka
        )

        try:
            items_data = parse_excel_file(file)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        for item_data in items_data:
            item_data['client'] = client
            Item.objects.update_or_create(
                part_no=item_data['part_no'],
                client=client,
                defaults=item_data
            )

        return Response({"message": "Excel data uploaded successfully"}, status=200)


class ItemListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Client name and marka required"}, status=400)

        try:
            client = Client.objects.get(user=request.user, client_name=client_name, marka=marka)
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
