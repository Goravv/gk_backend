from rest_framework.routers import DefaultRouter
from .views import PackingViewSet, StockViewSet,PackingDetailListCreateAPIView,UpdatePackingDetailByCase,net_weight_view
from django.urls import path, include

router = DefaultRouter()
router.register(r'packing', PackingViewSet)
router.register(r'stock', StockViewSet)

urlpatterns = [
    path("packing-details/", PackingDetailListCreateAPIView.as_view(), name="packing-details"),
     path('packingdetail/update-by-case/', UpdatePackingDetailByCase.as_view(), name='update-packingdetail-case'),
    path('', include(router.urls)),  
    path('net-weight/', net_weight_view),
]
