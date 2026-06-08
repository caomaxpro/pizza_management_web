"""
WebSocket consumer for real-time inventory updates.

Broadcasts inventory changes (create, update, delete) to all connected clients
in the "inventory_updates" group.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class InventoryUpdateConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "inventory_updates"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        try:
            data = json.loads(text_data)
            if data.get("type") == "subscribe":
                await self.send(text_data=json.dumps({
                    "type": "subscription_confirmed",
                    "message": "Subscribed to inventory updates",
                }))
        except json.JSONDecodeError:
            pass

    async def inventory_created(self, event):
        await self.send(text_data=json.dumps({
            "type": "inventory_created",
            "inventory": event["inventory"],
        }))

    async def inventory_updated(self, event):
        await self.send(text_data=json.dumps({
            "type": "inventory_updated",
            "inventory": event["inventory"],
        }))

    async def inventory_deleted(self, event):
        await self.send(text_data=json.dumps({
            "type": "inventory_deleted",
            "inventory_id": event["inventory_id"],
        }))
