from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ExcelData
from .serializers import ExcelDataSerializer
import pandas as pd
from collections import defaultdict
from django.db import transaction


class UploadExcelView(APIView):
    def post(self, request, format=None):
        file = request.FILES.get('file')
        brand_name = request.data.get('brand_name')

        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        if not brand_name:
            return Response({"error": "No brand_name found"}, status=status.HTTP_400_BAD_REQUEST)

        # Read Excel
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            return Response({"error": f"Failed to read Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Clean column names
        df.columns = [col.strip() for col in df.columns]

        required_columns = ['part_no', 'description', 'mrp_per_unit', 'hsn_code', 'gst']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({"error": f"Missing columns: {', '.join(missing_columns)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Drop empty part_no
        df = df.dropna(subset=['part_no'])

        # Convert hsn_code safely
        def safe_hsn(val):
            try:
                return int(str(val).strip())
            except (ValueError, TypeError):
                return 0

        df['hsn_code'] = df['hsn_code'].apply(safe_hsn)

        # Keep valid GST
        def is_valid_gst(val):
            try:
                int(str(val).strip())
                return True
            except (ValueError, TypeError):
                return False

        df = df[df['gst'].apply(is_valid_gst)]
        df['gst'] = df['gst'].apply(lambda val: int(str(val).strip()))

        # Build objects
        items_to_create = [
            ExcelData(
                brand_name=brand_name,
                part_no=str(row['part_no']).strip(),
                description=row['description'],
                mrp_per_unit=row['mrp_per_unit'],
                hsn_code=row['hsn_code'],
                gst_percent=row['gst']
            )
            for _, row in df.iterrows()
        ]

        with transaction.atomic():
            # delete old records for this brand_name
            ExcelData.objects.filter(brand_name=brand_name).delete()

            # insert fresh ones
            ExcelData.objects.bulk_create(items_to_create, batch_size=1000)

        return Response({
            "message": f"{len(items_to_create)} records inserted for brand {brand_name}, old records deleted."
        }, status=status.HTTP_201_CREATED)

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
