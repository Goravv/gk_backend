from django.urls import path
from .views import (
    UploadExcelView, ExcelDataListView, ExcelDataDetailView, DeleteAllExcelDataView
)

urlpatterns = [
    path('upload/', UploadExcelView.as_view(), name='upload-excel'),
    path('data/', ExcelDataListView.as_view(), name='data-list'),
    path('delete-all/', DeleteAllExcelDataView.as_view(), name='delete-all'),  # move this up
    path('data/<str:pk>/', ExcelDataDetailView.as_view(), name='data-detail'),
]
    