from rest_framework.routers import DefaultRouter
from .views import PackingViewSet, StockViewSet,PackingDetailListCreateAPIView
from django.urls import path, include

router = DefaultRouter()
router.register(r'packing', PackingViewSet)
router.register(r'stock', StockViewSet)

urlpatterns = [
    path("packing-details/", PackingDetailListCreateAPIView.as_view(), name="packing-details"),
    path('', include(router.urls)),  
]
