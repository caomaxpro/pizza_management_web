"""
WebSocket consumers for real-time ingredient updates.

Handles WebSocket connections for broadcasting ingredient changes
(create, update, delete) to all connected clients.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class IngredientUpdateConsumer(AsyncWebsocketConsumer):
    """
    Consumer that handles WebSocket connections for ingredient updates.

    Clients subscribe to the "ingredients_updates" group and receive
    notifications when ingredients are created, updated, or deleted.
    """

    async def connect(self):
        await self.channel_layer.group_add(
            "ingredients_updates",
            self.channel_name
        )
        await self.accept()
        print(f"✅ Ingredient WS client connected: {self.channel_name}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            "ingredients_updates",
            self.channel_name
        )
        print(f"❌ Ingredient WS client disconnected: {self.channel_name}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return

        try:
            data = json.loads(text_data)
            if data.get("type") == "subscribe":
                await self.send(text_data=json.dumps({
                    "type": "subscription_confirmed",
                    "message": "Subscribed to ingredient updates"
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))

    async def ingredient_created(self, event):
        await self.send(text_data=json.dumps({
            "type": "ingredient_created",
            "ingredient_id": event["ingredient_id"],
            "ingredient_name": event.get("ingredient_name", ""),
            "message": f"New ingredient created: {event.get('ingredient_name', 'Unknown')}"
        }))

    async def ingredient_updated(self, event):
        await self.send(text_data=json.dumps({
            "type": "ingredient_updated",
            "ingredient_id": event["ingredient_id"],
            "ingredient_name": event.get("ingredient_name", ""),
            "message": f"Ingredient updated: {event.get('ingredient_name', 'Unknown')}"
        }))

    async def ingredient_deleted(self, event):
        await self.send(text_data=json.dumps({
            "type": "ingredient_deleted",
            "ingredient_id": event["ingredient_id"],
            "message": f"Ingredient deleted: ID {event['ingredient_id']}"
        }))


class IngredientImportProgressConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time ingredient import progress tracking.
    
    Clients subscribe with an import_id and receive progress updates 
    as ingredients are processed during bulk import.
    """

    async def connect(self):
        # Extract import_id from URL: /ws/ingredients/import/{import_id}/
        if "url_route" in self.scope and isinstance(self.scope["url_route"], dict):
            url_route = self.scope["url_route"]
            kwargs = url_route.get("kwargs") if isinstance(url_route.get("kwargs"), dict) else {}
            self.import_id = kwargs.get("import_id")
        else:
            self.import_id = None

        if not self.import_id:
            await self.close()
            return

        self.group_name = f"ingredient_import_{self.import_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"✅ Import progress client connected: import_id={self.import_id}")

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"❌ Import progress client disconnected: import_id={self.import_id}")

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from client"""
        if text_data is None:
            return

        try:
            data = json.loads(text_data)
            if data.get("type") == "subscribe":
                await self.send(json.dumps({
                    "type": "import_subscription_confirmed",
                    "import_id": self.import_id,
                    "message": f"Connected to import {self.import_id}"
                }))
        except json.JSONDecodeError:
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))

    async def import_progress(self, event):
        """Receive progress updates and send to client"""
        payload = {
            "type": "import_progress",
            "current": event["current"],
            "total": event["total"],
            "percentage": event["percentage"],
            "message": event.get("message", ""),
        }
        # Include completed ingredient if available
        if "completed_ingredient" in event and event["completed_ingredient"]:
            payload["completed_ingredient"] = event["completed_ingredient"]
        await self.send(json.dumps(payload))

    async def import_completed(self, event):
        """Notify when import is complete"""
        await self.send(json.dumps({
            "type": "import_completed",
            "total_created": event["total_created"],
            "total_errors": event["total_errors"],
            "message": event.get("message", "Import completed")
        }))

    async def import_error(self, event):
        """Notify on import error"""
        await self.send(json.dumps({
            "type": "import_error",
            "error": event["error"],
            "message": event.get("message", "Import failed")
        }))

    async def import_cancelled(self, event):
        """Handle import cancellation"""
        print(f"🛑 import_cancelled called: {event.get('message')}")
        await self.send(json.dumps({
            "type": "import_cancelled",
            "message": event.get("message", "Import cancelled"),
        }))

    async def image_progress(self, event):
        """Notify when image batch processing makes progress"""
        await self.send(json.dumps({
            "type": "image_progress",
            "processed": event.get("processed", 0),
            "total": event.get("total", 0),
            "percentage": event.get("percentage", 0),
            "message": event.get("message", "Processing images..."),
        }))

    async def image_batch_completed(self, event):
        """Notify when image batch processing completes"""
        print(f"🖼️ Image batch completed: {event.get('message')}")
        await self.send(json.dumps({
            "type": "image_batch_completed",
            "processed": event.get("processed", 0),
            "cached": event.get("cached", 0),
            "failed": event.get("failed", 0),
            "message": event.get("message", "Image batch processing completed"),
        }))

    async def import_cancel_progress(self, event):
        """Notify of cancel progress during cancellation"""
        print(f"⏸️ Cancel progress {event.get('step')}/{event.get('total_steps')}: {event.get('action')}")
        await self.send(json.dumps({
            "type": "import_cancel_progress",
            "step": event.get("step", 0),
            "total_steps": event.get("total_steps", 0),
            "percentage": event.get("percentage", 0),
            "action": event.get("action", "Cancelling..."),
        }))
