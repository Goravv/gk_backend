from rest_framework.routers import DefaultRouter
from .views import PackingViewSet, StockViewSet,PackingDetailListCreateAPIView,UpdatePackingDetailByCase,NetWeightView,set_csrf_cookie
from django.urls import path, include

router = DefaultRouter()
router.register(r'packing', PackingViewSet)
router.register(r'stock', StockViewSet)

urlpatterns = [
    path("packing-details/", PackingDetailListCreateAPIView.as_view(), name="packing-details"),
     path('packingdetail/update-by-case/', UpdatePackingDetailByCase.as_view(), name='update-packingdetail-case'),
    path('', include(router.urls)), 
    path("net-weight/", NetWeightView.as_view(), name="net_wt"),
    path("set-csrf-cookie/", set_csrf_cookie),
]
