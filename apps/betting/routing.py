from django.urls import path

from apps.betting.consumers import EventoOddsConsumer

websocket_urlpatterns = [
    path("ws/eventos/<int:evento_id>/odds/", EventoOddsConsumer.as_asgi()),
]
