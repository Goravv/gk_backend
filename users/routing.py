from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/logout/<int:user_id>/", consumers.LogoutConsumer.as_asgi()),
]
