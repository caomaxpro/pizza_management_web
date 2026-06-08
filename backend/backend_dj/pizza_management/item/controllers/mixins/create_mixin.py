import json
import logging
import uuid
import traceback
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pizza_management.item.model import Item
from pizza_management.ingredient.model import Ingredient
from pizza_management.item.validators import ItemCreateRequest
from pizza_management.item.serializers import ItemSerializer
from pizza_management.shared.image_processor import ImageProcessor
from pizza_management.item.tasks import process_item_import_async, cancel_item_import
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import invalidate_items_cache, invalidate_cache

logger = logging.getLogger(__name__)


class CreateMixin:
    """Mixin for CREATE operations: create, import_json"""
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def create(self, request, *args, **kwargs):
        """POST /items/ - Create with optional image upload (ADMIN ONLY)"""
        try:
            print("\n=== CREATE ITEM REQUEST ===")
            print(f"Request data: {request.data}")
            print(f"Request FILES: {request.FILES}")
            
            image_file = request.FILES.get('image_file')
            print(f"Image file: {image_file}")

            # Flatten QueryDict (multipart) before passing to Pydantic
            if hasattr(request.data, 'dict'):
                data = request.data.dict()
                for list_field in ('toppings', 'extras'):
                    vals = request.data.getlist(list_field)
                    if vals:
                        try:
                            data[list_field] = [int(v) for v in vals]
                        except (ValueError, TypeError):
                            data[list_field] = vals
            else:
                data = dict(request.data)
            valid_data = ItemCreateRequest(**data)
            print(f"Validation passed ✓")
            
            item_dict = valid_data.model_dump(exclude_none=True)
            
            # Extract relationships
            dough_id = item_dict.pop("dough", None)
            sauce_id = item_dict.pop("sauce", None)
            cheese_id = item_dict.pop("cheese", None)
            toppings_ids = item_dict.pop("toppings", None)
            extras_ids = item_dict.pop("extras", None)
            
            # Remove stock management fields (reserved for future inventory module)
            # These are validated but not persisted on Item model
            item_dict.pop("lead_time_days", None)
            item_dict.pop("safety_stock_days", None)
            item_dict.pop("stock_quantity", None)
            item_dict.pop("reorder_level", None)
            
            # Upload images
            if image_file:
                image_url = ImageProcessor.upload_image(image_file, "items")
                if image_url:
                    item_dict['image_url'] = image_url
    
            # Create item (with only fields that Item model recognizes)
            item = Item.objects.create(**item_dict)
            print(f"Item created ✓ ID: {item.id}")

            # Set FK relationships
            self._set_fks_for_create(item, dough_id, sauce_id, cheese_id)
            item.save()

            # Set M2M relationships
            if toppings_ids:
                item.toppings.set(toppings_ids)
            if extras_ids:
                item.extras.set(extras_ids)

            print("=== CREATE SUCCESS ===\n")
            
            # Invalidate cache when new item is created
            invalidate_items_cache()
            logger.debug("[CACHE] Invalidated all items cache")
            
            return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            print(f"❌ ValueError: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _set_fks_for_create(self, item, dough_id, sauce_id, cheese_id):
        """Set FK relationships, delete item if validation fails"""
        if dough_id:
            try:
                item.dough = Ingredient.objects.get(id=dough_id)
                print(f"  Set dough: {item.dough.name}")
            except Ingredient.DoesNotExist:
                print(f"  ❌ Dough ingredient ID {dough_id} not found")
                item.delete()
                raise ValueError(f"Dough ingredient with ID {dough_id} does not exist")
                    
        if sauce_id:
            try:
                item.sauce = Ingredient.objects.get(id=sauce_id)
                print(f"  Set sauce: {item.sauce.name}")
            except Ingredient.DoesNotExist:
                print(f"  ❌ Sauce ingredient ID {sauce_id} not found")
                item.delete()
                raise ValueError(f"Sauce ingredient with ID {sauce_id} does not exist")
                    
        if cheese_id:
            try:
                item.cheese = Ingredient.objects.get(id=cheese_id)
                print(f"  Set cheese: {item.cheese.name}")
            except Ingredient.DoesNotExist:
                print(f"  ❌ Cheese ingredient ID {cheese_id} not found")
                item.delete()
                raise ValueError(f"Cheese ingredient with ID {cheese_id} does not exist")

    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def import_json(self, request):
        """POST /items/import-json/ - Import items from JSON file (ADMIN ONLY) - ASYNC"""
        try:
            print("\n=== IMPORT JSON REQUEST ===")
            print(f"Request data type: {type(request.data)}")
            print(f"Request data keys: {list(request.data.keys()) if isinstance(request.data, dict) else 'N/A'}")
            
            items_data = self._load_json_data(request)
            
            # Log sample item for debugging
            if items_data and len(items_data) > 0:
                print(f"First item keys: {list(items_data[0].keys())}")
                print(f"First item image_url: {items_data[0].get('image_url')}")
                print(f"First item image_source_url: {items_data[0].get('image_source_url')}")
            
            if not isinstance(items_data, list):
                return Response(
                    {"error": "items must be a list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Generate unique import_id for WebSocket tracking
            import_id = str(uuid.uuid4())
            
            print(f"[Import] Starting async import with import_id={import_id}, total_items={len(items_data)}")
            
            # Queue async Celery task - returns immediately!
            process_item_import_async.delay(items_data, import_id)  # type: ignore[misc]
            
            print(f"[Import] Queued async task")
            print("=== IMPORT ACCEPTED (ASYNC) ===\n")
            
            # Return HTTP 202 Accepted with import_id for WebSocket connection
            return Response(
                {"import_id": import_id, "message": "Import started in background"},
                status=status.HTTP_202_ACCEPTED,
            )
        
        except Exception as e:
            print(f"❌ Import failed to start: {str(e)}")
            import_id = str(uuid.uuid4())
            self._broadcast_import_error(import_id, str(e))
            return Response(
                {"error": f"Import failed to start: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _load_json_data(self, request):
        """Load JSON data from file or request body"""
        json_file = request.FILES.get('json_file')
        if json_file:
            print(f"Reading JSON file: {json_file.name}")
            file_content = json_file.read().decode('utf-8')
            data = json.loads(file_content)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data
        
        if isinstance(request.data, list):
            return request.data
        elif isinstance(request.data, dict) and "items" in request.data:
            return request.data["items"]
        
        raise ValueError("No valid JSON data provided")

    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def cancel_import(self, request):
        """POST /items/cancel-import/ - Cancel ongoing item import (ADMIN ONLY)"""
        try:
            import_id = request.data.get("import_id")
            if not import_id:
                return Response(
                    {"error": "import_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cancel_item_import(import_id)

            print(f"[Import] Cancellation request sent for import_id={import_id}")
            return Response(
                {"message": f"Import {import_id} cancelled"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"❌ Cancel failed: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _broadcast_import_error(self, import_id, error_msg):
        """Broadcast import error via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            async_to_sync(channel_layer.group_send)(
                f"item_import_{import_id}",
                {
                    "type": "import.error",
                    "error": error_msg,
                    "message": f"Import failed: {error_msg}",
                }
            )
            logger.error(f"[WS] Error: {error_msg}")
        except Exception as e:
            logger.error(f"[WS] Failed to broadcast error: {str(e)}")