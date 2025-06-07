# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import MergedItem
from .serializers import MergedItemSerializer
from .utils import populate_merged_items
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

class MergedItemListView(APIView):
    def get(self, request):
        client_name = request.GET.get('client')
        if not client_name:
            return Response({"error": "Client name required"}, status=400)
        estimates = MergedItem.objects.filter(client__client_name=client_name)
        serializer = MergedItemSerializer(estimates, many=True)
        return Response(serializer.data)
    


class MergeOrderItemWithExcel(APIView):
    
    def post(self, request):
        client_name = request.data.get('client')
        if not client_name:
            return Response({"error": "Client name is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            populate_merged_items(client_name)
            return Response({"message": "Estimate generated successfully!"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@ensure_csrf_cookie
def set_csrf_cookie(request):
    return JsonResponse({'message': 'CSRF cookie set'})