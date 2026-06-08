import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from pizza_management.item.model import Item
from pizza_management.ingredient.model import Ingredient
from pizza_management.item.validators import ItemUpdateRequest
from pizza_management.item.serializers import ItemSerializer
from pizza_management.shared.firebase_service import FirebaseStorageService
from pizza_management.shared.image_processor import ImageProcessor
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import invalidate_items_cache, write_through_cache, invalidate_cache

logger = logging.getLogger(__name__)


class UpdateMixin:
    """Mixin for UPDATE operations: update, update_many, update_all, adjust_prices
    
    Note: This mixin must be used with a ViewSet class that provides get_object() method.
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    @write_through_cache(detail_key_prefix="items_detail", list_invalidator=invalidate_items_cache)
    def update(self, request, *args, **kwargs):
        """PUT/PATCH /items/{id}/ - Update with optional image replacement (ADMIN ONLY)"""
        try:
            logger.info("=== UPDATE ITEM REQUEST ===")
            
            item_id = kwargs.get('pk')
            try:
                item = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"Item found: {item.id} - {item.name}")

            # Handle image replacement
            image_file = request.FILES.get('image_file')
            if image_file:
                logger.info("Uploading new image_file...")
                if item.image_url:
                    logger.info(f"Deleting old image: {item.image_url}")
                    try:
                        FirebaseStorageService.delete_image(item.image_url)
                    except Exception as e:
                        logger.warning(f"Failed to delete old image: {e}")
                        # Continue with upload anyway

                item.image_url = ImageProcessor.upload_image(image_file, "items")

            # Validate data
            # request.data may be a QueryDict (multipart) where **unpacking gives lists.
            # Use .dict() to flatten to single values, then re-add multi-value list fields.
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
            valid_data = ItemUpdateRequest(**data)
            update_dict = valid_data.model_dump(exclude_none=True)

            dough_id = update_dict.pop("dough", None)
            sauce_id = update_dict.pop("sauce", None)
            cheese_id = update_dict.pop("cheese", None)
            toppings_ids = update_dict.pop("toppings", None)
            extras_ids = update_dict.pop("extras", None)
            
            # Remove stock management fields (reserved for future inventory module)
            # These are validated but not persisted on Item model
            update_dict.pop("lead_time_days", None)
            update_dict.pop("safety_stock_days", None)
            update_dict.pop("stock_quantity", None)
            update_dict.pop("reorder_level", None)

            # Update fields (only those that Item model recognizes)
            for attr, value in update_dict.items():
                setattr(item, attr, value)

            item.save()

            # Update FKs
            self._update_fks(item, dough_id, sauce_id, cheese_id)
            item.save()

            # Update M2Ms
            if toppings_ids is not None:
                item.toppings.set(toppings_ids)
            if extras_ids is not None:
                item.extras.set(extras_ids)

            logger.info("=== UPDATE SUCCESS ===")
            
            # Invalidate cache when item is updated
            invalidate_items_cache()
            logger.debug("[CACHE] Invalidated all items cache")
            
            return Response(ItemSerializer(item).data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Exception in update_item: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def update_many(self, request):
        """POST /items/update-many/ - Update multiple items (ADMIN ONLY)"""
        logger.info("=== UPDATE MANY ITEMS REQUEST ===")
        updates = request.data if isinstance(request.data, list) else [request.data]
        results, errors = [], []
        
        for idx, update_data in enumerate(updates):
            try:
                item_id = update_data.get("id")
                if not item_id:
                    errors.append({"error": "id required"})
                    continue
                
                item = Item.objects.get(id=item_id)
                
                # Process images
                update_for_validation = dict(update_data)
                self._process_update_images(update_for_validation)
                
                # Validate
                valid_data = ItemUpdateRequest(**update_for_validation)
                update_dict = valid_data.model_dump(exclude_none=True)
                
                dough_id = update_dict.pop("dough", None)
                sauce_id = update_dict.pop("sauce", None)
                cheese_id = update_dict.pop("cheese", None)
                toppings_ids = update_dict.pop("toppings", None)
                extras_ids = update_dict.pop("extras", None)
                
                # Update fields
                for attr, value in update_dict.items():
                    setattr(item, attr, value)
                
                self._update_fks(item, dough_id, sauce_id, cheese_id)
                item.save()
                
                if toppings_ids is not None:
                    item.toppings.set(toppings_ids)
                if extras_ids is not None:
                    item.extras.set(extras_ids)
                
                results.append(ItemSerializer(item).data)
            except Exception as e:
                errors.append({"id": update_data.get("id"), "error": str(e)})
        
        logger.info("=== UPDATE MANY SUCCESS ===")
        
        # Invalidate cache when items are updated
        if results:
            invalidate_items_cache()
            logger.debug("[CACHE] Invalidated all items cache")
        
        return Response({"updated": results, "errors": errors}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def update_all(self, request):
        """PATCH /items/update-all/ - Update all items with same values (ADMIN ONLY)"""
        try:
            form_data = request.data.copy()
            valid_data = ItemUpdateRequest(**form_data)
            update_dict = valid_data.model_dump(exclude_none=True)
            
            if not update_dict:
                return Response(
                    {"error": "At least one field required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            updated_count = 0
            for item in Item.objects.all():
                dough_id = update_dict.get("dough")
                sauce_id = update_dict.get("sauce")
                cheese_id = update_dict.get("cheese")
                toppings_ids = update_dict.get("toppings")
                extras_ids = update_dict.get("extras")
                
                for attr, value in update_dict.items():
                    if attr not in ["dough", "sauce", "cheese", "toppings", "extras"]:
                        setattr(item, attr, value)
                
                self._update_fks(item, dough_id, sauce_id, cheese_id)
                item.save()
                
                if toppings_ids:
                    item.toppings.set(toppings_ids)
                if extras_ids:
                    item.extras.set(extras_ids)
                
                updated_count += 1
            
            # Invalidate cache when items are updated
            if updated_count > 0:
                invalidate_items_cache()
                logger.debug("[CACHE] Invalidated all items cache")
            
            return Response(
                {"updated_count": updated_count},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def adjust_prices(self, request):
        """PATCH /items/adjust-prices/ - Adjust prices by percentage (ADMIN ONLY)"""
        try:
            percent = request.data.get("percent")
            if percent is None:
                return Response(
                    {"error": "percent parameter required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            percent = float(percent)
            updated = []
            
            for item in Item.objects.all():
                old_price = item.price
                item.price = round(old_price * (1 + percent / 100), 2)
                item.save()
                updated.append({
                    "id": item.id,
                    "name": item.name,
                    "old_price": old_price,
                    "new_price": item.price,
                    "change": round(item.price - old_price, 2)
                })
            
            # Invalidate cache when prices are adjusted
            if updated:
                invalidate_items_cache()
                logger.debug("[CACHE] Invalidated all items cache")
            
            return Response(
                {
                    "updated_count": len(updated),
                    "percent_change": percent,
                    "items": updated
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _process_update_images(self, update_data):
        """Process images from filesystem paths"""
        image_url = update_data.get("image_url")
        
        if image_url and isinstance(image_url, str) and image_url.startswith('/'):
            update_data['image_url'] = ImageProcessor.process_image_path(image_url, "items")

    def _update_fks(self, item, dough_id, sauce_id, cheese_id):
        """Update FK relationships"""
        if dough_id is not None:
            try:
                item.dough = Ingredient.objects.get(id=dough_id)
            except Ingredient.DoesNotExist:
                logger.warning(f"Dough ingredient {dough_id} not found")
        
        if sauce_id is not None:
            try:
                item.sauce = Ingredient.objects.get(id=sauce_id)
            except Ingredient.DoesNotExist:
                logger.warning(f"Sauce ingredient {sauce_id} not found")
        
        if cheese_id is not None:
            try:
                item.cheese = Ingredient.objects.get(id=cheese_id)
            except Ingredient.DoesNotExist:
                logger.warning(f"Cheese ingredient {cheese_id} not found")