import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class EventoOddsConsumer(AsyncJsonWebsocketConsumer):
    """Canal por evento: recibe actualizaciones de cuotas y suspensiones."""

    async def connect(self):
        self.evento_id = self.scope["url_route"]["kwargs"]["evento_id"]
        self.group_name = f"evento_{self.evento_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "tipo": "conectado",
                "evento_id": int(self.evento_id),
                "mensaje": "Suscripción a cuotas en vivo activa.",
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def odds_update(self, event):
        await self.send_json(event["payload"])
