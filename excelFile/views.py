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
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            return Response({"error": f"Failed to read Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Strip column names
        df.columns = [col.strip() for col in df.columns]

        required_columns = [
            'Item Code', 'Item Description', 
            'MRP - per unit', 'HSN Code', 'GST %'
        ]

        # Check for missing columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({"error": f"Missing columns: {', '.join(missing_columns)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Drop rows with empty Item Code
        df = df.dropna(subset=['Item Code'])

        # Convert HSN Code to integer
        try:
            df['HSN Code'] = df['HSN Code'].fillna(0).astype(int)
        except Exception as e:
            return Response({"error": f"HSN Code conversion failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Clean GST % field for CharField, store as string like "18%"
        def clean_gst(val):
            if pd.isna(val):
                return "0%"
            if isinstance(val, str):
                val = val.strip().replace('%', '')
            try:
                return f"{float(val):.0f}%"
            except ValueError:
                return "0%"

        df['GST %'] = df['GST %'].apply(clean_gst)

        # Create a mapping of Item Code to row
        incoming_data = {
            str(row['Item Code']).strip(): row for _, row in df.iterrows()
        }

        # Fetch existing items
        existing_items = ExcelData.objects.filter(item_code__in=incoming_data.keys())
        existing_map = {item.item_code: item for item in existing_items}

        items_to_create = []
        items_to_update = []

        for item_code, row in incoming_data.items():
            if item_code in existing_map:
                obj = existing_map[item_code]
                obj.item_description = row['Item Description']
                obj.mrp_per_unit = row['MRP - per unit']
                obj.hsn_code = row['HSN Code']
                obj.gst_percent = row['GST %']
                items_to_update.append(obj)
            else:
                items_to_create.append(
                    ExcelData(
                        item_code=item_code,
                        item_description=row['Item Description'],
                        mrp_per_unit=row['MRP - per unit'],
                        hsn_code=row['HSN Code'],
                        gst_percent=row['GST %']
                    )
                )

        with transaction.atomic():
            if items_to_create:
                ExcelData.objects.bulk_create(items_to_create, batch_size=1000)
            if items_to_update:
                ExcelData.objects.bulk_update(
                    items_to_update,
                    ['item_description', 'mrp_per_unit', 'hsn_code', 'gst_percent'],
                    batch_size=1000
                )

        return Response({
            "message": f"{len(items_to_create)} created, {len(items_to_update)} updated."
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
