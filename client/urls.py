from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet

router = DefaultRouter()
router.register('clients', ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
