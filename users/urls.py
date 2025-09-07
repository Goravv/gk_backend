from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet
from .views import RegistrationView,UserPermissionView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='customuser')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegistrationView.as_view(), name='register'),
    path('permissions/',UserPermissionView.as_view(),name='permission')

]
