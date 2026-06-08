"""
Channels routing configuration for WebSocket URLs.

Maps WebSocket URL patterns to their corresponding consumers.
"""

from django.urls import path, re_path
from channels.routing import URLRouter
from pizza_management.item.consumers import ItemUpdateConsumer, ItemImportProgressConsumer
from pizza_management.ingredient.consumers import IngredientUpdateConsumer, IngredientImportProgressConsumer
from stock_management.inventory.consumers import InventoryUpdateConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/items/updates/", ItemUpdateConsumer.as_asgi(), name="ws_item_updates"),
    path("ws/ingredients/updates/", IngredientUpdateConsumer.as_asgi(), name="ws_ingredient_updates"),
    path("ws/inventory/updates/", InventoryUpdateConsumer.as_asgi(), name="ws_inventory_updates"),
    re_path(r"ws/items/import/(?P<import_id>[^/]+)/$", ItemImportProgressConsumer.as_asgi(), name="ws_item_import_progress"),
    re_path(r"ws/ingredients/import/(?P<import_id>[^/]+)/$", IngredientImportProgressConsumer.as_asgi(), name="ws_ingredient_import_progress"),
]
