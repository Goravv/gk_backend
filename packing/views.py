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
                client = Client.objects.get(client_name=client_name, marka=marka,user=self.request.user if self.request.user.is_staff else self.request.user.parent_id,)
                return Packing.objects.select_related("client").filter(client=client)
            except Client.DoesNotExist:
                return Packing.objects.none()
        return Packing.objects.filter(client__user=self.request.user if self.request.user.is_staff else self.request.user.parent_id,)

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
                    client = Client.objects.get(client_name=client_name, marka=marka, user=request.user if request.user.is_staff else request.user.parent_id)
                except Client.DoesNotExist:
                    return Response({"error": f"Invalid client or marka for item with part_no '{part_no}'"}, status=400)

                try:
                    stock = Stock.objects.get(part_no=part_no, user=request.user if request.user.is_staff else request.user.parent_id,client=client)
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
                client = Client.objects.get(client_name=client_name, marka=marka, user=request.user if request.user.is_staff else request.user.parent_id)
            except Client.DoesNotExist:
                return Response({"error": "Invalid client name or marka"}, status=400)

            try:
                stock = Stock.objects.get(part_no=part_no, user=request.user if request.user.is_staff else request.user.parent_id,client=client)
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
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user if request.user.is_staff else request.user.parent_id)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        try:
            packing = Packing.objects.get(part_no=part_no, client=client)
        except Packing.DoesNotExist:
            return Response({"error": "Packing item not found"}, status=404)

        try:
            stock = Stock.objects.get(part_no=part_no, user=request.user if request.user.is_staff else request.user.parent_id,client=client)
            stock.qty = max(stock.qty - qty, 0)
            if stock.qty == 0:
                stock.delete()
            else:
                stock.save()
        except Stock.DoesNotExist:
            pass

        try:
            packing.stock_qty = Stock.objects.get(part_no=part_no, user=request.user if request.user.is_staff else request.user.parent_id,client=client).qty
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
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user if request.user.is_staff else request.user.parent_id)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=400)

        merged_items = list(MergedItem.objects.filter(client=client))
        part_nos = [item.part_no for item in merged_items]

    # Fetch stock in one query
        stock_map = {
            s.part_no: s.qty for s in Stock.objects.filter(part_no__in=part_nos, user=request.user if request.user.is_staff else request.user.parent_id,client=client)
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
    # Filter only packings that belong to this user (through client)
        if request.user.is_staff:
            all_packing = Packing.objects.filter(client__user=request.user)
        else:
            all_packing = Packing.objects.filter(client__user=request.user.parent_id)

    # Collect all (client_id, part_no) pairs from packing
        packing_pairs = [(p.client_id, p.part_no) for p in all_packing if p.part_no]

    # Fetch relevant stocks
        stocks = Stock.objects.filter(
            user=request.user if request.user.is_staff else request.user.parent_id,
            client_id__in=[c for c, _ in packing_pairs],
            part_no__in=[p for _, p in packing_pairs]
        )

    # Build a map: (client_id, part_no) -> stock.qty
        stock_map = {(s.client_id, s.part_no): s.qty for s in stocks}

        to_update = []
        not_found = []

        for packing in all_packing:
            key = (packing.client_id, packing.part_no)
            if key in stock_map:
                packing.stock_qty = stock_map[key]
                to_update.append(packing)
            else:
                not_found.append({"client": packing.client_id, "part_no": packing.part_no})

    # Bulk update stock_qty field
        if to_update:
            Packing.objects.bulk_update(to_update, ['stock_qty'])

        return Response({
            "message": "Stock quantities synced.",
            "updated_count": len(to_update),
            "not_found": not_found
        }, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['post'], url_path='update_row_list')
    def update_row_list(self, request):
        client_name = request.data.get('client_name')
        marka = request.data.get('marka')
        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name.strip(), marka=marka.strip(), user=request.user if request.user.is_staff else request.user.parent_id)
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
            s.part_no: s.qty for s in Stock.objects.filter(part_no__in=part_nos, user=request.user if request.user.is_staff else request.user.parent_id,client=client)
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
    

    @action(detail=False, methods=['post'], url_path='netwt_upload')
    def netwt_upload(self,request):
        file=request.FILES.get('file')
        try:
            df = pd.read_excel(BytesIO(file.read()))
        except:
            pass
        objs_to_create = []
        for _, row in df.iterrows():
            part_no = str(row["part_no"]).strip()
            net_wt= str(row["net_wt"]).strip()
            count = 1
            objs_to_create.append(NetWeight(
                part_no=part_no,
                net_wt=net_wt,
                count=count
            ))
        NetWeight.objects.bulk_create(objs_to_create, ignore_conflicts=True)
        return Response({"message": "Data uploaded successfully"}, status=200)
class StockViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Stock.objects.filter(user=self.request.user)
        else:
            return Stock.objects.filter(user=self.request.user.parent_id)



    @action(detail=False, methods=["post"], url_path="upload-single")
    def upload_single(self, request):
        client_id = request.data.get("client_id")
        part_no = request.data.get("part_no")
        description = request.data.get("description")
        qty = request.data.get("qty")
        brand_name = request.data.get("brand_name")

        if not client_id or not part_no or not description or not qty or not brand_name:
            return Response({"error": "All fields (client_id, part_no, description, qty, brand_name) are required"}, status=400)

        try:
            client = Client.objects.get(
                id=client_id,
                user=request.user if request.user.is_staff else request.user.parent_id
            )
        except Client.DoesNotExist:
            return Response({"error": "Invalid client"}, status=400)

        # check if stock already exists
        stock, created = Stock.objects.get_or_create(
            user=request.user,
            client=client,
            part_no=part_no,
            defaults={
                "description": description,
                "qty": qty,
                "brand_name": brand_name
            }
        )

        if created:
            message = "Stock created successfully"
        else:
            # update existing stock
            stock.qty += int(qty)
            stock.description = description
            stock.brand_name = brand_name
            stock.save()
            message = "Stock updated successfully"

        return Response({
            "message": message,
            "part_no": stock.part_no,
            "qty": stock.qty,
            "description": stock.description,
            "brand_name": stock.brand_name
        }, status=200)


    @action(detail=False, methods=["post"], url_path="upload")
    def upload_excel(self, request):
        file = request.FILES.get("file")
        client_id = request.data.get("client_id")

        if not file:
            return Response({"error": "No file uploaded"}, status=400)
        if not client_id:
            return Response({"error": "No client provided"}, status=400)

        try:
            client = Client.objects.get(id=client_id, user=request.user if request.user.is_staff else request.user.parent_id)  # ensure client belongs to user
        except Client.DoesNotExist:
            return Response({"error": "Invalid client"}, status=400)

        try:
            df = pd.read_excel(BytesIO(file.read()))
        except Exception as e:
            return Response({"error": f"Failed to read Excel file: {str(e)}"}, status=400)

        required_columns = ["part_no", "description", "qty", "brand_name"]
        if not set(required_columns).issubset(df.columns):
            return Response({"error": f"Missing required columns: {required_columns}"}, status=400)

        # Clean data
        df = df[required_columns]
        df.dropna(subset=["part_no", "description", "qty", "brand_name"], inplace=True)
        df["part_no"] = df["part_no"].astype(str).str.strip()
        df["description"] = df["description"].astype(str).str.strip()
        df["brand_name"] = df["brand_name"].astype(str).str.strip()
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)

        part_nos = df["part_no"].unique()
        user = request.user

        # fetch existing stocks for this user+client+part_no
        existing_stocks = Stock.objects.filter(user=user, client=client, part_no__in=part_nos)
        existing_map = {stock.part_no: stock for stock in existing_stocks}

        stocks_to_create = []
        stocks_to_update = []

        for _, row in df.iterrows():
            part_no = row["part_no"]
            if part_no in existing_map:
                stock = existing_map[part_no]
                stock.qty += row["qty"]
                stock.description = row["description"]
                stock.brand_name = row["brand_name"]
                stocks_to_update.append(stock)
            else:
                stocks_to_create.append(Stock(
                    user=user,
                    client=client,  
                    part_no=row["part_no"],
                    description=row["description"],
                    qty=row["qty"],
                    brand_name=row["brand_name"]
                ))

        # Bulk DB operations
        if stocks_to_create:
            Stock.objects.bulk_create(stocks_to_create)

        if stocks_to_update:
            Stock.objects.bulk_update(stocks_to_update, ["qty", "description", "brand_name"])

        return Response({
            "message": "Stock uploaded successfully",
            "created": len(stocks_to_create),
            "updated": len(stocks_to_update)
        }, status=200)


    @action(detail=False, methods=['post'], url_path='update-qty')
    def update_quantity(self, request):
        part_no = request.data.get('part_no')
        qty_change = request.data.get('qty')
        client_id = request.data.get("client_id")
        if part_no is None or qty_change is None:
            return Response({"error": "Both 'part_no' and 'qty' are required."}, status=400)
        if not client_id:
            return Response({"error": "No client provided"}, status=400)
        try:
            qty_change = int(qty_change)
        except ValueError:
            return Response({"error": "'qty' must be an integer."}, status=400)
        try:
            client = Client.objects.get(id=client_id, user=request.user if request.user.is_staff else request.user.parent_id)  # ensure client belongs to user
        except Client.DoesNotExist:
            return Response({"error": "Invalid client"}, status=400)
        try:
            stock = Stock.objects.get(user=request.user if request.user.is_staff else request.user.parent_id, part_no=part_no,client=client)
        except Stock.DoesNotExist:
            return Response({"error": "Stock with this part number not found."}, status=404)

        stock.qty = qty_change

        if stock.qty <= 0:
            stock.delete()
            return Response({"message": "Stock deleted because qty <= 0."}, status=200)
        else:
            stock.save()
            return Response({"message": "Stock updated successfully.", "new_qty": stock.qty}, status=200)
        


class PackingDetailListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PackingDetailSerializer

    def get_queryset(self):
        client_name = self.request.query_params.get('client')
        marka = self.request.query_params.get('marka')
        if client_name and marka:
            try:
                client = Client.objects.get(client_name=client_name, marka=marka)
                packing=PackingDetail.objects.filter(client=client).order_by('case_no_start')
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
            main_user=request.user if request.user.is_staff else request.user.parent_id
            print(main_user)
            client = Client.objects.get(client_name=client_name, marka=marka, user=main_user)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        data['client'] = client.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



    def put(self, request, *args, **kwargs):
        
        client_name = request.data.get('client_name')
        marka = request.data.get('marka')
        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=status.HTTP_400_BAD_REQUEST)
        lookup_user = request.user if request.user.is_staff else request.user.parent_id

        try:
            if request.user.is_staff:
                client = Client.objects.get(client_name=client_name, marka=marka, user=request.user )
            else:
                client = Client.objects.get(client_name=client_name, marka=marka, user=request.user.parent_id)
        except Client.DoesNotExist:
            return Response({"error": "Invalid client name or marka"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        pk = request.data.get('id')
        if not pk:
            return Response({"error": "ID is required for update"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print(client)
            packing_detail = PackingDetail.objects.get(pk=pk, client_id=client.id)
        except PackingDetail.DoesNotExist:
            return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)

        
        data = request.data.copy()
        data['client'] = client.id

        # Ensure only model fields are updated
        allowed_fields = [f.name for f in PackingDetail._meta.fields]
        cleaned_data = {k: v for k, v in data.items() if k in allowed_fields}

        serializer = self.get_serializer(packing_detail, data=cleaned_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)



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
            client = Client.objects.get(client_name=client_name, marka=marka, user=request.user if request.user.is_staff else request.user.parent_id)
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

