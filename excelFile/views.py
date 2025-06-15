from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ExcelData
from .serializers import ExcelDataSerializer
import pandas as pd


class UploadExcelView(APIView):
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file, engine='openpyxl')  # use in-memory, no disk
        except Exception as e:
            return Response({"error": f"Failed to read Excel file: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Normalize column names
        df.columns = [col.strip() for col in df.columns]

        required_columns = [
            'Item Code', 'Item Description', 'Item Segment',
            'MRP - per unit', 'HSN Code', 'GST %'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({"error": f"Missing columns: {', '.join(missing_columns)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        df = df.dropna(subset=['Item Code'])

        try:
            df['HSN Code'] = df['HSN Code'].fillna(0).astype(int)
        except Exception as e:
            return Response({"error": f"HSN Code conversion failed: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        count = 0
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
            count += 1

        return Response({"message": f"{count} rows imported successfully."},
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
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)


class DeleteAllExcelDataView(APIView):
    def delete(self, request):
        deleted_count, _ = ExcelData.objects.all().delete()
        return Response({"message": f"{deleted_count} entries deleted"},
                        status=status.HTTP_204_NO_CONTENT)
