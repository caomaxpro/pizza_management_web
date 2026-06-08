# pizza_management/signals.py
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Item, Ingredient
from .shared.firebase_service import FirebaseStorageService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@receiver(post_delete, sender=Item)
def delete_item_images(sender, instance, **kwargs):
    """Delete Firebase image when item is deleted"""
    if instance.image_url:
        try:
            FirebaseStorageService.delete_image(instance.image_url)
        except Exception as e:
            print(f"Error deleting item image: {e}")


@receiver(post_save, sender=Item)
def broadcast_item_update(sender, instance, created, **kwargs):
    """
    Broadcast item changes to all connected WebSocket clients.
    Triggers when an item is created or updated.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        # Channel layer not configured, skip broadcast
        return
    
    event_data = {
        "item_id": instance.id,
        "item_name": instance.name,
    }
    
    try:
        if created:
            # Item was created
            async_to_sync(channel_layer.group_send)(
                "items_updates",
                {
                    "type": "item_created",
                    **event_data,
                }
            )
        else:
            # Item was updated
            async_to_sync(channel_layer.group_send)(
                "items_updates",
                {
                    "type": "item_updated",
                    **event_data,
                }
            )
    except Exception as e:
        # Log but don't fail if broadcast fails
        print(f"⚠️  Failed to broadcast item update: {e}")


@receiver(post_delete, sender=Item)
def broadcast_item_delete(sender, instance, **kwargs):
    """
    Broadcast item deletion to all connected WebSocket clients.
    Triggers when an item is deleted.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        # Channel layer not configured, skip broadcast
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            "items_updates",
            {
                "type": "item_deleted",
                "item_id": instance.id,
            }
        )
    except Exception as e:
        # Log but don't fail if broadcast fails
        print(f"⚠️  Failed to broadcast item deletion: {e}")


# ─── Ingredient signals ───────────────────────────────────────────────────────
# Note: Image deletion for Ingredient is handled in Ingredient.delete() (model.py).
# No post_delete signal needed here to avoid double-deletion.

@receiver(post_save, sender=Ingredient)
def broadcast_ingredient_update(sender, instance, created, **kwargs):
    """
    Broadcast ingredient changes to all connected WebSocket clients.
    Triggers when an ingredient is created or updated.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    event_data = {
        "ingredient_id": instance.id,
        "ingredient_name": instance.name,
    }

    try:
        if created:
            async_to_sync(channel_layer.group_send)(
                "ingredients_updates",
                {
                    "type": "ingredient_created",
                    **event_data,
                }
            )
        else:
            async_to_sync(channel_layer.group_send)(
                "ingredients_updates",
                {
                    "type": "ingredient_updated",
                    **event_data,
                }
            )
    except Exception as e:
        print(f"⚠️  Failed to broadcast ingredient update: {e}")


@receiver(post_delete, sender=Ingredient)
def broadcast_ingredient_delete(sender, instance, **kwargs):
    """
    Broadcast ingredient deletion to all connected WebSocket clients.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    try:
        async_to_sync(channel_layer.group_send)(
            "ingredients_updates",
            {
                "type": "ingredient_deleted",
                "ingredient_id": instance.id,
            }
        )
    except Exception as e:
        print(f"⚠️  Failed to broadcast ingredient deletion: {e}")
