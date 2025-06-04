from django.urls import path
from .views import MergedItemListView, MergeOrderItemWithExcel, set_csrf_cookie

urlpatterns = [
    path('', MergedItemListView.as_view(), name='merged-items'),
    path('genrate/', MergeOrderItemWithExcel.as_view(), name='merge-order'),
    path('set-csrf-cookie/', set_csrf_cookie, name='set_csrf_cookie'),
]
