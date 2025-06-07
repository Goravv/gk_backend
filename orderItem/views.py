from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Item
from .serializers import ItemSerializer
from .excel_parser import parse_excel_file
from client.models import Client


class UploadExcelView(APIView):
    
    def post(self, request):
        file = request.FILES.get('file')
        client_name = request.POST.get('client')

        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        if not client_name:
            return Response({"error": "No client name provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create the client instance
        client, created = Client.objects.get_or_create(client_name=client_name)

        try:
            items_data = parse_excel_file(file)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        for item_data in items_data:
           item_data['client_name'] = client  # Attach the client
           Item.objects.update_or_create(
           part_no=item_data['part_no'],
           client_name=client,
           defaults=item_data 
           )


        return Response({"message": "Excel data uploaded successfully"}, status=status.HTTP_200_OK)


class ItemListView(APIView):
    
    def get(self, request):
        client_name = request.GET.get('client')
        if not client_name:
            return Response({"error": "Client name required"}, status=400)

        # FIXED FK lookup
        items = Item.objects.filter(client_name__client_name=client_name)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

class ItemDetailView(APIView):
    def get(self, request, part_no):
        try:
            item = Item.objects.get(part_no=part_no)
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ItemSerializer(item)
        return Response(serializer.data)

    
    def delete(self, request, part_no):
        client_name = request.GET.get('client')
        if not client_name:
            return Response({"error": "Client name required"}, status=400)
        
        try:
            item = Item.objects.get(part_no=part_no, client__client_name=client_name)
            item.delete()
            return Response({"message": "Item deleted"})
        except Item.DoesNotExist:
            return Response({"error": "Item not found for this client"}, status=404)

class DeleteAllItemsView(APIView):
    
    def delete(self, request):
        client_name = request.GET.get('client')
        if not client_name:
            return Response({"error": "Client name required"}, status=400)
        
        Item.objects.filter(client__client_name=client_name).delete()
        return Response({"message": "All items for client deleted"})



