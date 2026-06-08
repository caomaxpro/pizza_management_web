"""
Django signals for broadcasting inventory changes via WebSocket.

Fires when an Inventory model instance is saved or deleted,
then broadcasts the serialized data to the "inventory_updates" channel group.
"""

import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.renderers import JSONRenderer

from stock_management.models import Inventory
from stock_management.inventory.serializers import InventorySerializer


def _serialize_inventory(instance: Inventory) -> dict:
    """Return a fully JSON-serializable dict for the given Inventory instance."""
    data_bytes = JSONRenderer().render(InventorySerializer(instance).data)
    return json.loads(data_bytes)


def _broadcast(event: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)("inventory_updates", event)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            "Failed to broadcast inventory WebSocket event: %s", e
        )


@receiver(post_save, sender=Inventory)
def broadcast_inventory_save(sender, instance, created, **kwargs):
    event_type = "inventory_created" if created else "inventory_updated"

    def send():
        data = _serialize_inventory(instance)
        _broadcast({"type": event_type, "inventory": data})

    # Wait until the DB transaction commits so clients get consistent data
    transaction.on_commit(send)


@receiver(post_delete, sender=Inventory)
def broadcast_inventory_delete(sender, instance, **kwargs):
    def send():
        _broadcast({
            "type": "inventory_deleted",
            "inventory_id": instance.id,
        })

    transaction.on_commit(send)
