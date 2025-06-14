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
from rest_framework.decorators import api_view
from decimal import Decimal


class PackingViewSet(viewsets.ModelViewSet):
    queryset = Packing.objects.all()
    serializer_class = PackingSerializer

    def get_queryset(self):
        client_name = self.request.query_params.get('client')
        marka = self.request.query_params.get('marka')

        if client_name and marka:
            try:
                client = Client.objects.get(client_name=client_name, marka=marka)
                return Packing.objects.select_related("client").filter(client=client)
            except Client.DoesNotExist:
                return Packing.objects.none()
        elif client_name:
            return Packing.objects.none()  # Require marka if client is given
        return Packing.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        part_no = data.get('part_no')
        qty = int(data.get('qty', 0))
        client_name = data.get('client')
        marka = data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        try:
            stock = Stock.objects.get(part_no=part_no)
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
            client = Client.objects.get(client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        try:
            packing = Packing.objects.get(part_no=part_no, client=client)
        except Packing.DoesNotExist:
            return Response({"error": "Packing item not found"}, status=404)

        try:
            stock = Stock.objects.get(part_no=part_no)
            stock.qty = max(stock.qty - qty, 0)
            if stock.qty == 0:
                stock.delete()
            else:
                stock.save()
        except Stock.DoesNotExist:
            pass

        try:
            packing.stock_qty = Stock.objects.get(part_no=part_no).qty
        except Stock.DoesNotExist:
            packing.stock_qty = 0

        packing.qty = max(packing.qty - qty, 0)
        if packing.qty == 0:
            packing.delete()
        else:
            packing.save()

        try:
            details = PackingDetail.objects.filter(part_no=part_no, client=client)
            for detail in details:
                detail.total_packing_qty = max(detail.total_packing_qty - qty, 0)
                if detail.total_packing_qty == 0:
                    detail.delete()
                else:
                    detail.save()
        except PackingDetail.DoesNotExist:
            pass

        return Response({"success": True}, status=204)

    @action(detail=False, methods=['post'], url_path='copy-from-estimate')
    def copy_from_estimate(self, request):
        client_name = request.data.get('client')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        merged_items = MergedItem.objects.all()
        created_or_updated = []

        for item in merged_items:
            if item.client == client:
                part_no = item.part_no
                description = item.description
                qty = item.qty

                try:
                    stock = Stock.objects.get(part_no=part_no)
                    stock_qty = stock.qty
                except Stock.DoesNotExist:
                    stock_qty = 0

                packing, _ = Packing.objects.update_or_create(
                    client=client,
                    part_no=part_no,
                    defaults={
                        'description': description,
                        'qty': qty,
                        'stock_qty': stock_qty
                    }
                )
                created_or_updated.append(packing)

        serializer = self.get_serializer(created_or_updated, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='sync-stock')
    def sync_stock_qty(self, request):
        updated = 0
        not_found = []

        all_packing = Packing.objects.all()
        for packing in all_packing:
            try:
                stock = Stock.objects.get(part_no=packing.part_no)
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


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

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

            part_nos = df["part_no"].astype(str).str.strip().tolist()
            existing_stocks = Stock.objects.in_bulk(part_nos)

            to_create = []
            to_update = []

            for _, row in df.iterrows():
                part_no = str(row["part_no"]).strip()
                description = str(row["description"]).strip()
                qty = int(row["qty"])
                brand_name = str(row["brand_name"]).strip()

                if part_no in existing_stocks:
                    stock = existing_stocks[part_no]
                    stock.qty += qty
                    stock.description = description
                    stock.brand_name = brand_name
                    to_update.append(stock)
                else:
                    stock = Stock(
                        part_no=part_no,
                        description=description,
                        qty=qty,
                        brand_name=brand_name
                    )
                    to_create.append(stock)

            if to_create:
                Stock.objects.bulk_create(to_create, batch_size=1000)
            if to_update:
                Stock.objects.bulk_update(to_update, ["qty", "description", "brand_name"], batch_size=1000)

            return Response({
                "message": "Stock Excel processed successfully",
                "created": len(to_create),
                "updated": len(to_update)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PackingDetailListCreateAPIView(generics.ListCreateAPIView):
    queryset = PackingDetail.objects.all()
    serializer_class = PackingDetailSerializer

    def get_queryset(self):
        client_name = self.request.query_params.get('client')
        marka = self.request.query_params.get('marka')

        if client_name and marka:
            try:
                client = Client.objects.get(client_name=client_name, marka=marka)
                return PackingDetail.objects.filter(client=client)
            except Client.DoesNotExist:
                return PackingDetail.objects.none()
        elif client_name:
            return PackingDetail.objects.none()
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        client_name = request.data.get('client')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['client'] = client.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PackingDetail
from client.models import Client


class UpdatePackingDetailByCase(APIView):
    def post(self, request):
        case_no_start = request.data.get('case_no_start')
        client_name = request.data.get('client')
        marka = request.data.get('marka')
        updates = request.data.get('updates', {})

        if not case_no_start or not client_name or  not marka or not updates :
            return Response({
                "error": "case_no_start, client, marka, and updates are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(client_name=client_name, marka=marka)
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
    


@api_view(['GET', 'POST'])
def net_weight_view(request):
    if request.method == 'GET':
        part_no = request.query_params.get('part_no')
        try:
            item = NetWeight.objects.get(part_no=part_no)
            return Response({'net_wt': item.net_wt}, status=status.HTTP_200_OK)
        except NetWeight.DoesNotExist:
            return Response({'net_wt': 0}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        part_no = request.data.get('part_no')
        net_wt = Decimal(str(request.data.get('net_wt')))

        try:
            item = NetWeight.objects.get(part_no=part_no)
            existing = item.net_wt
            lower_limit = existing * Decimal('0.90')
            upper_limit = existing * Decimal('1.10')

            if lower_limit <= net_wt <= upper_limit:
                return Response({'message': 'Net weight accepted (within ±10%)'}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Net weight differs not more than ±10% from {existing}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except NetWeight.DoesNotExist:
            new_item = NetWeight.objects.create(part_no=part_no, net_wt=net_wt)
            return Response({'message': 'New part number added'}, status=status.HTTP_201_CREATED)