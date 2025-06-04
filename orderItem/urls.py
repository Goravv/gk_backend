from django.urls import path
from .views import UploadExcelView, ItemListView, ItemDetailView, DeleteAllItemsView

urlpatterns = [
    path('upload-excel/', UploadExcelView.as_view()),
    path('items/', ItemListView.as_view()),
    path('items/delete-all/', DeleteAllItemsView.as_view()),  # put this BEFORE <str:part_no>
    path('items/<str:part_no>/', ItemDetailView.as_view()),
    
]
