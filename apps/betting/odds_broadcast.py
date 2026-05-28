"""Envío de actualizaciones de cuotas por Django Channels."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_odds_evento(evento_id: int, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"evento_{evento_id}",
        {"type": "odds.update", "payload": payload},
    )
