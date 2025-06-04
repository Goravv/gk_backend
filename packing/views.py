from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Packing, Stock,PackingDetail
from .serializers import PackingSerializer, StockSerializer,PackingDetailSerializer
from asstimate.models import MergedItem  # Your estimate app
from rest_framework import generics

class PackingViewSet(viewsets.ModelViewSet):
    queryset = Packing.objects.all()
    serializer_class = PackingSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        part_no = data.get('part_no')
        qty = int(data.get('qty', 0))

        try:
            stock = Stock.objects.get(part_no=part_no)
            stock_qty = stock.qty
        except Stock.DoesNotExist:
            stock_qty = 0

        data['stock_qty'] = stock_qty
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     part_no = instance.part_no
    #     qty_to_remove = instance.qty

    #     try:
    #         stock = Stock.objects.get(part_no=part_no)
    #         stock.qty = max(stock.qty - qty_to_remove, 0)
    #         stock.save()
    #     except Stock.DoesNotExist:
    #         pass

    #     self.perform_destroy(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)
    

    # def destroy(self, request, *args, **kwargs):
    #     part_no = request.data.get("part_no")
    #     qty = int(request.data.get("qty", 0))

    #     try:
    #         packing = Packing.objects.get(part_no=part_no)
    #     except Packing.DoesNotExist:
    #         return Response({"error": "Packing item not found"}, status=404)

    # # Adjust stock quantity
    #     try:
    #         stock = Stock.objects.get(part_no=part_no)
    #         stock.qty = max(stock.qty - qty, 0)

    #         if stock.qty == 0:
    #             stock.delete()
    #         else:
    #             stock.save()
    #     except Stock.DoesNotExist:
    #         pass

    # # Update packing stock_qty based on new stock (if exists)
    #     try:
    #        packing.stock_qty = Stock.objects.get(part_no=part_no).qty
    #     except Stock.DoesNotExist:
    #         packing.stock_qty = 0

    # # Adjust packing qty
    #     packing.qty = max(packing.qty - qty, 0)

    #     if packing.qty == 0:
    #         packing.delete()
    #     else:
    #         packing.save()

    # # Update or delete related PackingDetail
    #     try:
    #         detail = PackingDetail.objects.get(part_no=part_no)
    #         detail.total_qty = max(detail.total_qty - qty, 0)

    #         if detail.total_qty == 0:
    #            detail.delete()
    #         else:
    #             detail.save()
    #     except PackingDetail.DoesNotExist:
    #         pass

    #     return Response({"success": True}, status=204)


    @action(detail=False, methods=['post'], url_path='delete-by-partno')
    def delete_by_partno(self, request):
        part_no = request.data.get("part_no")
        qty = int(request.data.get("qty", 0))

        try:
            packing = Packing.objects.get(part_no=part_no)
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
        merged_items = MergedItem.objects.all()
        created_or_updated = []

        for item in merged_items:
            part_no = item.part_no
            description = item.description
            qty = item.qty

            try:
                stock = Stock.objects.get(part_no=part_no)
                stock_qty = stock.qty
            except Stock.DoesNotExist:
                stock_qty = 0

            packing, _ = Packing.objects.update_or_create(
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

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        part_no = data.get('part_no')
        qty = int(data.get('qty', 0))

        stock, _ = Stock.objects.update_or_create(
            part_no=part_no,
            defaults={
                'description': data.get('description'),
                'qty': qty
            }
        )

        # Update Packing if exists
        try:
            packing = Packing.objects.get(part_no=part_no)
            packing.stock_qty = qty
            packing.save()
        except Packing.DoesNotExist:
            pass

        serializer = self.get_serializer(stock)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class PackingDetailListCreateAPIView(generics.ListCreateAPIView):
    queryset = PackingDetail.objects.all()
    serializer_class = PackingDetailSerializer