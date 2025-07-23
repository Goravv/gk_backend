from django.urls import path
from .views import invoiceGenrate

urlpatterns = [
    path('invoiceGenrate/', invoiceGenrate.as_view()),
]
