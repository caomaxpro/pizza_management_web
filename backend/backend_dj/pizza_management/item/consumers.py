"""
WebSocket consumers for real-time item updates.

Handles WebSocket connections for broadcasting item changes (create, update, delete)
to all connected clients.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser


class ItemUpdateConsumer(AsyncWebsocketConsumer):
    """
    Consumer that handles WebSocket connections for item updates.
    
    Broadcast events when items are created, updated, or deleted.
    Clients subscribe to the "items_updates" group and receive notifications.
    """
    
    async def connect(self):
        """
        Handle WebSocket connection.
        Join the items_updates group to receive broadcasts.
        """
        # Add this connection to the items_updates group
        await self.channel_layer.group_add(
            "items_updates",
            self.channel_name
        )
        
        # Accept the WebSocket connection
        await self.accept()
        
        # Log connection (optional - for debugging)
        print(f"✅ Client connected: {self.channel_name}")
    
    async def disconnect(self, code):
        """
        Handle WebSocket disconnection.
        Remove this connection from the items_updates group.
        """
        # Remove from group
        await self.channel_layer.group_discard(
            "items_updates",
            self.channel_name
        )
        
        # Log disconnection (optional - for debugging)
        print(f"❌ Client disconnected: {self.channel_name}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive message from WebSocket.
        
        Expected format: {"type": "subscribe"} or other control messages.
        """
        # Only handle text data
        if text_data is None:
            return
            
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                # Client is subscribing to item updates
                await self.send(text_data=json.dumps({
                    "type": "subscription_confirmed",
                    "message": "Subscribed to item updates"
                }))
                print(f"📥 Client subscribed: {self.channel_name}")
            else:
                # Handle other message types as needed
                pass
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
    
    async def item_created(self, event):
        """
        Handle item_created event from the channel layer.
        Broadcast to client.
        """
        await self.send(text_data=json.dumps({
            "type": "item_created",
            "item_id": event["item_id"],
            "item_name": event.get("item_name", ""),
            "message": f"New item created: {event.get('item_name', 'Unknown')}"
        }))
    
    async def item_updated(self, event):
        """
        Handle item_updated event from the channel layer.
        Broadcast to client.
        """
        await self.send(text_data=json.dumps({
            "type": "item_updated",
            "item_id": event["item_id"],
            "item_name": event.get("item_name", ""),
            "message": f"Item updated: {event.get('item_name', 'Unknown')}"
        }))
    
    async def item_deleted(self, event):
        """
        Handle item_deleted event from the channel layer.
        Broadcast to client.
        """
        await self.send(text_data=json.dumps({
            "type": "item_deleted",
            "item_id": event["item_id"],
            "message": f"Item deleted: ID {event['item_id']}"
        }))


class ItemImportProgressConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time item import progress tracking.
    
    Clients subscribe with an import_id and receive progress updates 
    as items are processed during bulk import.
    """

    async def connect(self):
        # Extract import_id from URL: /ws/items/import/{import_id}/
        if "url_route" in self.scope and isinstance(self.scope["url_route"], dict):
            url_route = self.scope["url_route"]
            kwargs = url_route.get("kwargs") if isinstance(url_route.get("kwargs"), dict) else {}
            self.import_id = kwargs.get("import_id")
        else:
            self.import_id = None

        if not self.import_id:
            await self.close()
            return

        self.group_name = f"item_import_{self.import_id}"

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
        # Include completed item if available
        if "completed_item" in event and event["completed_item"]:
            payload["completed_item"] = event["completed_item"]
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
