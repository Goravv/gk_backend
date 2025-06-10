from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ExcelData
from .serializers import ExcelDataSerializer
import pandas as pd
from django.core.files.storage import default_storage

class UploadExcelView(APIView):
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        path = default_storage.save('temp.xlsx', file)
        df = pd.read_excel(default_storage.path(path))

        # Normalize column names
        df.columns = [col.strip() for col in df.columns]

        required_columns = [
            'Item Code', 'Item Description', 'Item Segment',
            'MRP - per unit', 'HSN Code', 'GST %'
        ]

        if not all(col in df.columns for col in required_columns):
            return Response({"error": "Missing one or more required columns."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Drop rows without item code
        df = df.dropna(subset=['Item Code'])

        # Optional: convert HSN code to int
        try:
            df['HSN Code'] = df['HSN Code'].fillna(0).astype(int)
        except Exception as e:
            return Response({"error": f"HSN Code conversion failed: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Save to database
        for _, row in df.iterrows():
            ExcelData.objects.update_or_create(
                item_code=row['Item Code'],
                defaults={
                    'item_description': row['Item Description'],
                    'item_segment': row['Item Segment'],
                    'mrp_per_unit': row['MRP - per unit'],
                    'hsn_code': row['HSN Code'],
                    'gst_percent': row['GST %'],
                }
            )

        return Response({"message": "Excel data imported successfully."},
                        status=status.HTTP_201_CREATED)


class ExcelDataListView(APIView):
    def get(self, request):
        data = ExcelData.objects.all()
        serializer = ExcelDataSerializer(data, many=True)
        return Response(serializer.data)


class ExcelDataDetailView(APIView):
    def get(self, request, pk):
        try:
            obj = ExcelData.objects.get(pk=pk)
            serializer = ExcelDataSerializer(obj)
            return Response(serializer.data)
        except ExcelData.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class DeleteAllExcelDataView(APIView):
    def delete(self, request):
        ExcelData.objects.all().delete()
        return Response({"message": "All data deleted"},
                        status=status.HTTP_204_NO_CONTENT)
