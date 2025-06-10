from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Packing, Stock,PackingDetail
from .serializers import PackingSerializer, StockSerializer,PackingDetailSerializer
from asstimate.models import MergedItem  # Your estimate app
from rest_framework import generics
from client.models import Client
import pandas as pd
from io import BytesIO

class PackingViewSet(viewsets.ModelViewSet):
    queryset=Packing.objects.all()
    serializer_class = PackingSerializer
    def get_queryset(self):
        client_name = self.request.query_params.get('client')

        if client_name:
            try:
                client = Client.objects.get(client_name=client_name)
                return Packing.objects.select_related("client").filter(client=client)
            except Client.DoesNotExist:
                return Packing.objects.none()
        return Packing.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        part_no = data.get('part_no')
        qty = int(data.get('qty', 0))
        client_name = data.get('client')

        if not client_name:
            return Response({"error": "Client name is required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name"}, status=400)

        try:
            stock = Stock.objects.get(part_no=part_no)
            stock_qty = stock.qty
        except Stock.DoesNotExist:
            stock_qty = 0

        data['stock_qty'] = stock_qty
        data['client'] = client.id  # set client ID for serializer

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='delete-by-partno')
    def delete_by_partno(self, request):
        part_no = request.data.get("part_no")
        qty = int(request.data.get("qty", 0))
        client_name = request.data.get("client")

        if not client_name:
            return Response({"error": "Client name is required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name"}, status=400)

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
            details = PackingDetail.objects.filter(part_no=part_no)
            for detail in details:
                detail.total_qty = max(detail.total_qty - qty, 0)
                if detail.total_qty == 0:
                    detail.delete()
                else:
                    detail.save()
        except PackingDetail.DoesNotExist:
            pass

        return Response({"success": True}, status=204)

    @action(detail=False, methods=['post'], url_path='copy-from-estimate')
    def copy_from_estimate(self, request):
        client_name = request.data.get('client')

        if not client_name:
            return Response({"error": "Client name is required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name"}, status=400)

        merged_items = MergedItem.objects.all()
        created_or_updated = []

        for item in merged_items:
            if item.client==client:
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
            existing_stocks = Stock.objects.in_bulk(part_nos)  # Returns dict: {part_no: Stock instance}

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

        # Perform bulk operations
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
        if client_name:
            try:
                client = Client.objects.get(client_name=client_name)
                return PackingDetail.objects.filter(client=client)
            except Client.DoesNotExist:
                return PackingDetail.objects.none()
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        client_name = request.data.get('client')
        if not client_name:
            return Response({"error": "Client name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(client_name=client_name)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['client'] = client.client_name  

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)