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
        items = MergedItem.objects.all()
        serializer = MergedItemSerializer(items, many=True)
        return Response(serializer.data)
    


class MergeOrderItemWithExcel(APIView):
    def post(self, request):
        populate_merged_items()
        return Response({"message": "Asstimate genrated succesfully!!!"}, status=status.HTTP_200_OK)
    

@ensure_csrf_cookie
def set_csrf_cookie(request):
    return JsonResponse({'message': 'CSRF cookie set'})