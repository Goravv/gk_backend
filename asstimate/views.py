from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import MergedItem
from .serializers import MergedItemSerializer
from .utils import populate_merged_items
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from client.models import Client

class MergedItemListView(APIView):
    def get(self, request):
        client_name = request.GET.get('client_name')
        marka = request.GET.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name.strip(), marka=marka.strip())
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        items = MergedItem.objects.filter(client=client)
        serializer = MergedItemSerializer(items, many=True)
        return Response(serializer.data)

class MergeOrderItemWithExcel(APIView):
    def post(self, request):
        client_name = request.data.get('client_name')
        marka = request.data.get('marka')

        if not client_name or not marka:
            return Response({"error": "Both client_name and marka are required"}, status=400)

        try:
            client = Client.objects.get(client_name=client_name.strip(), marka=marka.strip())
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        try:
            populate_merged_items(client)
            return Response({"message": "Estimate generated successfully!"}, status=200)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

@ensure_csrf_cookie
def set_csrf_cookie(request):
    return JsonResponse({'message': 'CSRF cookie set'})
