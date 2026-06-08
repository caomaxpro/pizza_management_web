from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from pizza_management.ingredient.model import Ingredient
from pizza_management.ingredient.validators import IngredientUpdateRequest
from pizza_management.ingredient.serializers import IngredientSerializer
from pizza_management.shared.firebase_service import FirebaseStorageService
from pizza_management.shared.image_processor import ImageProcessor
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import write_through_cache, invalidate_cache, invalidate_ingredients_list_cache
import logging

logger = logging.getLogger(__name__)


class UpdateMixin:
    """Mixin for UPDATE operations: update, update_many, update_all, adjust_prices, rollback_prices"""
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    @write_through_cache(
        detail_key_prefix="ingredients_detail",
        list_invalidator=invalidate_ingredients_list_cache,
    )
    def update(self, request, *args, **kwargs):
        """PUT/PATCH /ingredients/{id}/ - Update ingredient (ADMIN ONLY)"""
        print("[Ingredient Update]: Running")
        print(f"[Update] raw request.data: {request.data}")
        try:
            ingredient_id = kwargs.get('pk')
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                return Response({"error": "Ingredient not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Log current ingredient state
            print(f"[Update] Current ingredient - price: {ingredient.price}, original_price: {ingredient.original_price}")
            
            # Handle image replacement
            image_file = request.FILES.get('image_file')
            if image_file:
                if ingredient.image_url:
                    try:
                        FirebaseStorageService.delete_image(ingredient.image_url)
                        logger.info(f"[UPDATE] Deleted old image_url: {ingredient.image_url}")
                    except Exception as e:
                        logger.warning(f"[UPDATE] Failed to delete old image_url: {e}")
                        # Continue with upload anyway
                image_url = ImageProcessor.upload_image(image_file, "ingredients")
                if image_url:
                    ingredient.image_url = image_url

            piece_file = request.FILES.get('piece_file')
            if piece_file:
                if ingredient.piece_image_url:
                    try:
                        FirebaseStorageService.delete_image(ingredient.piece_image_url)
                        logger.info(f"[UPDATE] Deleted old piece_image_url: {ingredient.piece_image_url}")
                    except Exception as e:
                        logger.warning(f"[UPDATE] Failed to delete old piece_image_url: {e}")
                        # Continue with upload anyway
                piece_url = ImageProcessor.upload_image(piece_file, "ingredients")
                if piece_url:
                    ingredient.piece_image_url = piece_url

            # Validate other fields
            form_data = self._normalize_form_data(request.data)
            print(f"[Update] form_data after normalize: {form_data}")
            valid_data = IngredientUpdateRequest(**form_data)
            print(f"[Update] valid_data: {valid_data}")
            print(f"[Update] valid_data.price: {valid_data.price}, valid_data.original_price: {valid_data.original_price}")
            
            update_dict = valid_data.model_dump(exclude_none=True)
            print(f"[Update] update_dict before pop: {update_dict}")

            update_dict.pop('image_url', None)
            update_dict.pop('piece_image_url', None)
            
            print(f"[Update] update_dict after pop: {update_dict}")

            # Update model
            for attr, value in update_dict.items():
                print(f"[Update] Setting {attr} = {value}")
                setattr(ingredient, attr, value)

            ingredient.save()
            print(f"[Update] After save - price: {ingredient.price}, original_price: {ingredient.original_price}")
            print(f"✓ Ingredient {ingredient.id} updated")
            return Response(IngredientSerializer(ingredient).data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print(f"❌ Exception: {str(e)}")
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_ingredients_list_cache)
    def update_many(self, request):
        """PATCH /ingredients/update-many/ - Update multiple ingredients (ADMIN ONLY)"""
        print("[Ingredient Update Many]: Running")
        ingredients_data = request.data.get("ingredients", [])
        if not ingredients_data:
            return Response(
                {"error": "ingredients list required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
        results = {"updated": [], "errors": []}
    
        for item in ingredients_data:
            try:
                ingredient_id = item.get("id")
                if not ingredient_id:
                    raise ValueError("id is required")
            
                ingredient = Ingredient.objects.get(pk=ingredient_id)
            
                form_data = self._normalize_form_data(item)
                print(f"[Update Many] form_data: {form_data}")
                valid_data = IngredientUpdateRequest(**form_data)
                print(f"[Update Many] valid_data: {valid_data}")
                update_dict = valid_data.model_dump(exclude_none=True)
                print(f"[Update Many] update_dict: {update_dict}")
            
                for attr, value in update_dict.items():
                    setattr(ingredient, attr, value)
                
                ingredient.save()
                results["updated"].append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                })
            
            except Exception as e:
                results["errors"].append({
                    "id": item.get("id", "Unknown"),
                    "error": str(e)
                })
    
        print(f"✓ Updated {len(results['updated'])} ingredients")
        return Response(results, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_ingredients_list_cache)
    def update_all(self, request):
        """PATCH /ingredients/update-all/ - Update all ingredients (ADMIN ONLY)"""
        try:
            form_data = self._normalize_form_data(request.data)
            print(f"[Update All] form_data: {form_data}")
            valid_data = IngredientUpdateRequest(**form_data)
            print(f"[Update All] valid_data: {valid_data}")
            update_dict = valid_data.model_dump(exclude_none=True)
            print(f"[Update All] update_dict: {update_dict}")
            
            if not update_dict:
                return Response(
                    {"error": "At least one field required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            all_ingredients = Ingredient.objects.all()
            updated_count = 0
            
            for ingredient in all_ingredients:
                for attr, value in update_dict.items():
                    setattr(ingredient, attr, value)
                ingredient.save()
                updated_count += 1

            print(f"✓ Updated {updated_count} ingredients")
            return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_ingredients_list_cache)
    def adjust_prices(self, request):
        """PATCH /ingredients/adjust-prices/ - Adjust prices by percentage (ADMIN ONLY)"""
        try:
            percent = request.data.get("percent")
            if percent is None:
                return Response(
                    {"error": "percent required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            percent = float(percent)
            all_ingredients = Ingredient.objects.all()
            updated = []
            
            for ingredient in all_ingredients:
                old_price = ingredient.price
                ingredient.price = round(old_price * (1 + percent / 100), 2)
                ingredient.save()

                updated.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "old_price": old_price,
                    "new_price": ingredient.price,
                    "change": round(ingredient.price - old_price, 2),
                })

            print(f"✓ Adjusted prices for {len(updated)} ingredients by {percent}%")
            return Response(
                {"updated_count": len(updated), "percent_change": percent, "items": updated},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['patch'])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_ingredients_list_cache)
    def rollback_prices(self, request):
        """PATCH /ingredients/rollback-prices/ - Rollback prices to original (ADMIN ONLY)"""
        try:
            all_ingredients = Ingredient.objects.all()
            updated = []
            
            for ingredient in all_ingredients:
                if ingredient.original_price:
                    old_price = ingredient.price
                    ingredient.price = ingredient.original_price
                    ingredient.save()
                    updated.append({
                        "id": ingredient.id,
                        "name": ingredient.name,
                        "original_price": ingredient.original_price,
                        "reverted_from": old_price,
                    })

            print(f"✓ Rolled back {len(updated)} ingredients")
            return Response(
                {"updated_count": len(updated), "message": f"Rolled back {len(updated)} ingredients", "items": updated},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _normalize_form_data(self, data):
        """Extract single values from form data"""
        normalized = {}
        excluded_fields = {'image_url', 'piece_image_url'}
        
        for key, value in data.items():
            if key in excluded_fields:
                continue
            if isinstance(value, list) and len(value) > 0:
                val = value[0]
            else:
                val = value
            normalized[key] = None if val == '' else val
        
        return normalized