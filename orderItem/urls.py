from django.urls import path
from .views import UploadExcelView, ItemListView, ItemDetailView, DeleteAllItemsView,UpdateItemQtyView

urlpatterns = [
    path('upload-excel/', UploadExcelView.as_view()),
    path('items/', ItemListView.as_view()),
    path('items/delete-all/', DeleteAllItemsView.as_view()), 
    path("items/update-qty/", UpdateItemQtyView.as_view(), name="update-item-qty"), 
    path('items/<str:part_no>/', ItemDetailView.as_view()),
    
]
