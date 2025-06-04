from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Item
from .serializers import ItemSerializer
from .excel_parser import parse_excel_file


class UploadExcelView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            items_data = parse_excel_file(file)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        for item_data in items_data:
            # Upsert logic
            Item.objects.update_or_create(
                part_no=item_data['part_no'],
                defaults=item_data
            )

        return Response({"message": "Excel data uploaded successfully"})

class ItemListView(APIView):
    def get(self, request):
        items = Item.objects.all()
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
        try:
            item = Item.objects.get(part_no=part_no)
            item.delete()
            return Response({"message": "Item deleted"})
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteAllItemsView(APIView):
    def delete(self, request):
        Item.objects.all().delete()
        return Response({"message": "All items deleted"})



