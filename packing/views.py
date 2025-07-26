from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Packing, Stock, PackingDetail,NetWeight
from .serializers import PackingSerializer, StockSerializer, PackingDetailSerializer,NetWeightSerializer
from asstimate.models import MergedItem
from rest_framework import generics
from client.models import Client
import pandas as pd
from io import BytesIO
from decimal import Decimal
from rest_framework.views import APIView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import pandas as pd
import json




class PackingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PackingSerializer

    def get_queryset(self):
        client_name = self.request.query_params.get('client')
        marka = self.request.query_params.get('marka')

        if client_name and marka:
            try:
                client = Client.objects.get(client_name=client_name, marka=marka, user=self.request.user)
                return Packing.objects.select_related("client").filter(client=client)
            except Client.DoesNotExist:
                return Packing.objects.none()
        return Packing.objects.filter(client__user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data

        if isinstance(data, list):
            created_packing = []

            for item in data:
                part_no = item.get('part_no')
                qty = int(item.get('qty', 0))
                client_name = item.get('client')
                marka = item.get('marka')
                if qty <= 0:
                    continue

                if not client_name or not marka:
                    return Response({"error": "Both client_name and marka are required for all items"}, status=400)

                try:
                    client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
                except Client.DoesNotExist:
                    return Response({"error": f"Invalid client or marka for item with part_no '{part_no}'"}, status=400)

                try:
                    stock = Stock.objects.get(part_no=part_no, user=request.user)
                    stock_qty = stock.qty
                except Stock.DoesNotExist:
                    stock_qty = 0

                created_packing.append(Packing(
                    client=client,
                    part_no=part_no,
                    description=item.get('description', ''),
                    qty=qty,
                    stock_qty=stock_qty
                ))

            Packing.objects.bulk_create(created_packing)
            serializer = self.get_serializer(created_packing, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            part_no = data.get('part_no')
            qty = int(data.get('qty', 0))
            client_name = data.get('client')
            marka = data.get('marka')

            if qty <= 0:
                return Response({"error": "qty must be greater than 0"}, status=400)

            if not client_name or not marka:
                return Response({"error": "Both client_name and marka are required"}, status=400)

            try:
                client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
            except Client.DoesNotExist:
                return Response({"error": "Invalid client name or marka"}, status=400)

            try:
                stock = Stock.objects.get(part_no=part_no, user=request.user)
                stock_qty = stock.qty
            except Stock.DoesNotExist:
                stock_qty = 0

            data['stock_qty'] = stock_qty
            data['client'] = client.id

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='delete-by-partno')
    def delete_by_partno(self, request):
        part_no = request.data.get("part_no")
        qty = int(request.data.get("qty", 0))
        client_name = request.data.get("client")
        marka = request.data.get("marka")

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        try:
            packing = Packing.objects.get(part_no=part_no, client=client)
        except Packing.DoesNotExist:
            return Response({"error": "Packing item not found"}, status=404)

        try:
            stock = Stock.objects.get(part_no=part_no, user=request.user)
            stock.qty = max(stock.qty - qty, 0)
            if stock.qty == 0:
                stock.delete()
            else:
                stock.save()
        except Stock.DoesNotExist:
            pass

        try:
            packing.stock_qty = Stock.objects.get(part_no=part_no, user=request.user).qty
        except Stock.DoesNotExist:
            packing.stock_qty = 0

        packing.qty = max(packing.qty - qty, 0)
        if packing.qty == 0:
            packing.delete()
        else:
            packing.save()


        return Response({"success": True}, status=204)

    @action(detail=False, methods=['post'], url_path='copy-from-estimate')
  
    def copy_from_estimate(self, request):
        client_name = request.data.get('client')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        merged_items = list(MergedItem.objects.filter(client=client))
        part_nos = [item.part_no for item in merged_items]

    # Fetch stock in one query
        stock_map = {
            s.part_no: s.qty for s in Stock.objects.filter(part_no__in=part_nos, user=request.user)
        }

    # Fetch existing packing in one query
        existing_packing_map = {
            (p.part_no): p for p in Packing.objects.filter(client=client, part_no__in=part_nos)
        }

        new_packings = []
        updated_packings = []

        for item in merged_items:
            part_no = item.part_no
            description = item.description
            qty = item.qty
            stock_qty = stock_map.get(part_no, 0)

            if part_no in existing_packing_map:
                packing = existing_packing_map[part_no]
                packing.description = description
                packing.qty = qty
                packing.stock_qty = stock_qty
                updated_packings.append(packing)
            else:
                new_packings.append(Packing(
                    client=client,
                    part_no=part_no,
                    description=description,
                    qty=qty,
                    stock_qty=stock_qty
                ))

    # Perform bulk DB operations
        with transaction.atomic():
            if new_packings:
                Packing.objects.bulk_create(new_packings)
            if updated_packings:
                Packing.objects.bulk_update(updated_packings, ['description', 'qty', 'stock_qty'])

        serializer = self.get_serializer(new_packings + updated_packings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'], url_path='sync-stock')
    def sync_stock_qty(self, request):
        updated = 0
        not_found = []

        all_packing = Packing.objects.filter(client__user=request.user)
        for packing in all_packing:
            try:
                stock = Stock.objects.get(part_no=packing.part_no, user=request.user)
                packing.stock_qty = stock.qty
                packing.save()
                updated += 1
            except Stock.DoesNotExist:
                not_found.append(packing.part_no)

        return Response({
            "message": "Stock quantities synced.",
            "updated_count": updated,
            "not_found_part_nos": not_found
        }, status=status.HTTP_200_OK)
   

   
    @action(detail=False, methods=['post'], url_path='update_row_list')
    def update_row_list(self, request):
        client_name = request.data.get('client_name')
        marka = request.data.get('marka')
        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name.strip(), marka=marka.strip(), user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

    # Handle data from file or request body
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                df = pd.read_excel(file)
                merged_items = df.to_dict(orient='records')
            except Exception as e:
                return Response({"error": f"Failed to read Excel file: {str(e)}"}, status=400)
        else:
            raw_data = request.data.get('data')

        # If data is a string, try to parse as JSON
            if isinstance(raw_data, str):
                try:
                    parsed_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON string in 'data'"}, status=400)
            else:
                parsed_data = raw_data

        # Normalize into a list of dicts
            if isinstance(parsed_data, list):
                merged_items = parsed_data
            elif isinstance(parsed_data, dict):
                merged_items = [parsed_data]
            else:
                return Response({"error": "No valid data source found (expected file, list or dict in 'data')"}, status=400)

        if not merged_items:
            return Response({"error": "No items to process"}, status=400)

    # Extract part numbers
        part_nos = [item.get('partNo') or item.get('part_no') for item in merged_items if item.get('partNo') or item.get('part_no')]

    # Fetch stock and existing packing
        stock_map = {
            s.part_no: s.qty for s in Stock.objects.filter(part_no__in=part_nos, user=request.user)
        }

        existing_packing_map = {
            p.part_no: p for p in Packing.objects.filter(client=client, part_no__in=part_nos)
        }

        new_packings = []
        updated_packings = []

        for item in merged_items:
            part_no = item.get('partNo') or item.get('part_no')
            description = item.get('description', '')
            qty = item.get('qty', 0)

            try:
                qty = int(qty)
            except:
                qty = 0

            stock_qty = stock_map.get(part_no, 0)

            if not part_no:
                continue  # Skip invalid rows

            if part_no in existing_packing_map:
                packing = existing_packing_map[part_no]
                packing.description = description
                packing.qty += qty
                packing.stock_qty = stock_qty
                updated_packings.append(packing)
            else:
                new_packings.append(Packing(
                    client=client,
                    part_no=part_no,
                    description=description,
                    qty=qty,
                    stock_qty=stock_qty
                ))

    # Bulk save
        print(new_packings)
        print(updated_packings)
        with transaction.atomic():
            if new_packings:
                Packing.objects.bulk_create(new_packings)
            if updated_packings:
                Packing.objects.bulk_update(updated_packings, ['description', 'qty', 'stock_qty'])

        serializer = self.get_serializer(new_packings + updated_packings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StockViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockSerializer

    def get_queryset(self):
        return Stock.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload_excel(self, request):
        excel_file = request.FILES.get("file")
        if not excel_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(BytesIO(excel_file.read()))
            required_columns = {"part_no", "description", "qty", "brand_name"}

            if not required_columns.issubset(df.columns):
                return Response({"error": f"Missing columns. Required: {required_columns}"}, status=400)

            created_count = 0
            updated_count = 0

            for _, row in df.iterrows():
                part_no = str(row["part_no"]).strip()
                description = str(row["description"]).strip()
                qty = int(row["qty"])
                brand_name = str(row["brand_name"]).strip()

                stock, created = Stock.objects.get_or_create(part_no=part_no, user=request.user, defaults={
                    "description": description,
                    "qty": qty,
                    "brand_name": brand_name,
                })

                if not created:
                    stock.qty += qty
                    stock.description = description
                    stock.brand_name = brand_name
                    stock.save()
                    updated_count += 1
                else:
                    created_count += 1

            return Response({
                "message": "Stock Excel processed successfully",
                "created": created_count,
                "updated": updated_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PackingDetailListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PackingDetailSerializer

    def get_queryset(self):
        client_name = self.request.query_params.get('client')
        marka = self.request.query_params.get('marka')

        if client_name and marka:
            try:
                client = Client.objects.get(client_name=client_name, marka=marka, user=self.request.user)
                packing=PackingDetail.objects.filter(client=client).order_by('id')
                return packing
            except Client.DoesNotExist:
                return PackingDetail.objects.none()
        return PackingDetail.objects.filter(client__user=self.request.user)

    def create(self, request, *args, **kwargs):
        client_name = request.data.get('client')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['client'] = client.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UpdatePackingDetailByCase(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        case_no_start = request.data.get('case_no_start')
        client_name = request.data.get('client')
        marka = request.data.get('marka')
        updates = request.data.get('updates', {})

        if not case_no_start or not client_name or not marka:
            return Response({
                "error": "case_no_start, client, marka, and updates are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        queryset = PackingDetail.objects.filter(case_no_start=case_no_start, client=client)

        if not queryset.exists():
            return Response({"error": "No matching PackingDetail found"}, status=404)

        for entry in queryset:
            for field, value in updates.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)
            entry.save()

        return Response({
            "message": "PackingDetail entries updated successfully",
            "updated_count": queryset.count()
        }, status=200)



class NetWeightView(APIView):
    def get(self, request):
        part_no = request.query_params.get("part_no")

        if not part_no:
            return Response({"error": "part_no query parameter is required"}, status=400)

        net_weights = NetWeight.objects.filter(part_no=part_no)

        serializer = NetWeightSerializer(net_weights, many=True)
        return Response(serializer.data, status=200)

    def post(self, request):
        part_no = request.data.get("part_no")
        net_wt = request.data.get("net_wt")

        if not part_no or net_wt is None:
            return Response({"error": "part_no and net_wt are required"}, status=400)

        obj, created = NetWeight.objects.get_or_create(
            part_no=part_no,
            net_wt=net_wt,
            defaults={"count": 1}
        )

        if not created:
            obj.count += 1
            obj.save()

        return Response({
            "message": "Net weight updated successfully",
            "part_no": obj.part_no,
            "net_wt": obj.net_wt,
            "count": obj.count,
            "created": created
        }, status=201 if created else 200)
    
@ensure_csrf_cookie
def set_csrf_cookie(request):
    return JsonResponse({"message": "CSRF cookie set"})