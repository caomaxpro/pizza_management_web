from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from pizza_management.ingredient.model import Ingredient
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import CacheHelper
import logging

logger = logging.getLogger(__name__)


class DeleteMixin:
    """Mixin for DELETE operations: destroy, delete_many, delete_all"""
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request, *args, **kwargs):
        """DELETE /ingredients/{id}/ - Delete single ingredient (ADMIN ONLY)"""
        print("\n=== DELETE INGREDIENT REQUEST ===")
        
        ingredient_id = kwargs.get('pk')
        print(f"Ingredient ID: {ingredient_id}")
        
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
            print(f"Deleting ingredient: {ingredient.id} - {ingredient.name}")
            logger.info(f"[DELETE] Starting deletion of ingredient ID {ingredient_id}: {ingredient.name}")
            
            # Log image URLs for deletion tracking
            if ingredient.image_url:
                logger.info(f"[FIREBASE] Deleting image_url: {ingredient.image_url}")
                CacheHelper.clear_image_cache_for_url(ingredient.image_url)
            if ingredient.piece_image_url:
                logger.info(f"[FIREBASE] Deleting piece_image_url: {ingredient.piece_image_url}")
                CacheHelper.clear_image_cache_for_url(ingredient.piece_image_url)
            
            ingredient.delete()
            
            print("✓ Ingredient deleted successfully")
            logger.info(f"[SUCCESS] Ingredient {ingredient_id} and its Firebase images deleted successfully")
            
            # Invalidate ingredients cache
            CacheHelper.cache_clear_pattern("ingredients_*")
            print("[CACHE] Invalidated all ingredients cache")
            
            print("=== DELETE SUCCESS ===\n")
            return Response(
                {"message": "Ingredient deleted successfully", "id": ingredient_id},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except Ingredient.DoesNotExist:
            print(f"❌ Ingredient {ingredient_id} not found")
            logger.warning(f"[DELETE] Ingredient {ingredient_id} not found")
            return Response(
                {"error": "Ingredient not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            logger.error(f"[DELETE] Error deleting ingredient {ingredient_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def bulk_delete(self, request):
        """POST /ingredients/bulk_delete/ - Delete multiple ingredients (ADMIN ONLY)"""
        print("\n=== BULK DELETE INGREDIENTS REQUEST ===")
        
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "ids list required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"Deleting {len(ids)} ingredients: {ids}")
        logger.info(f"[BULK DELETE] Starting bulk deletion of {len(ids)} ingredients: {ids}")
        deleted_count = 0
        errors = []
        
        for item_id in ids:
            try:
                ingredient = Ingredient.objects.get(id=item_id)
                print(f"Deleting ingredient: {ingredient.name} (id={ingredient.id})")
                logger.info(f"[BULK DELETE] Deleting {ingredient.name} (ID: {item_id})")
                
                if ingredient.image_url:
                    logger.info(f"[FIREBASE] Removing image_url: {ingredient.image_url}")
                    CacheHelper.clear_image_cache_for_url(ingredient.image_url)
                if ingredient.piece_image_url:
                    logger.info(f"[FIREBASE] Removing piece_image_url: {ingredient.piece_image_url}")
                    CacheHelper.clear_image_cache_for_url(ingredient.piece_image_url)
                
                ingredient.delete()
                deleted_count += 1
                logger.info(f"[BULK DELETE] Successfully deleted ingredient {item_id}")
            except Ingredient.DoesNotExist:
                print(f"❌ Ingredient {item_id} not found")
                logger.warning(f"[BULK DELETE] Ingredient {item_id} not found")
                errors.append({"id": item_id, "error": "Ingredient not found"})
            except Exception as e:
                print(f"❌ Error deleting {item_id}: {str(e)}")
                logger.error(f"[BULK DELETE] Error deleting ingredient {item_id}: {str(e)}", exc_info=True)
                errors.append({"id": item_id, "error": str(e)})
        
        print(f"✓ Deleted {deleted_count} ingredients")
        
        # Invalidate ingredients cache
        if deleted_count > 0:
            CacheHelper.cache_clear_pattern("ingredients_*")
            print("[CACHE] Invalidated all ingredients cache")
        
        print("=== BULK DELETE SUCCESS ===\n")
        return Response(
            {"deleted_count": deleted_count, "errors": errors},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_all(self, request):
        """POST /ingredients/delete-all/ - Delete all ingredients (ADMIN ONLY)"""
        print("\n=== DELETE ALL INGREDIENTS REQUEST ===")
        
        total_count = Ingredient.objects.count()
        print(f"Total ingredients before delete: {total_count}")
        logger.info(f"[DELETE ALL] Starting deletion of ALL {total_count} ingredients")
        
        deleted_count = 0
        errors = []
        
        for ingredient in Ingredient.objects.all():
            try:
                print(f"Deleting ingredient: {ingredient.name} (id={ingredient.id})")
                logger.info(f"[DELETE ALL] Deleting {ingredient.name} (ID: {ingredient.id})")
                
                if ingredient.image_url:
                    logger.info(f"[FIREBASE] Removing image_url: {ingredient.image_url}")
                    CacheHelper.clear_image_cache_for_url(ingredient.image_url)
                if ingredient.piece_image_url:
                    logger.info(f"[FIREBASE] Removing piece_image_url: {ingredient.piece_image_url}")
                    CacheHelper.clear_image_cache_for_url(ingredient.piece_image_url)
                
                ingredient.delete()
                deleted_count += 1
                logger.info(f"[DELETE ALL] Successfully deleted ingredient {ingredient.id}")
            except Exception as e:
                print(f"❌ Error deleting {ingredient.id}: {str(e)}")
                logger.error(f"[DELETE ALL] Error deleting ingredient {ingredient.id}: {str(e)}", exc_info=True)
                errors.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "error": str(e)
                })
        
        print(f"✓ Deleted {deleted_count} ingredients")
        logger.info(f"[DELETE ALL] Completed: {deleted_count}/{total_count} ingredients deleted")
        
        # Invalidate ingredients cache
        if deleted_count > 0:
            CacheHelper.cache_clear_pattern("ingredients_*")
            print("[CACHE] Invalidated all ingredients cache")
            logger.info("[CACHE] Invalidated all ingredients cache pattern")
        
        print("=== DELETE ALL SUCCESS ===\n")
        logger.info(f"[SUCCESS] DELETE ALL operation completed: {deleted_count} deleted, {len(errors)} errors")
        return Response(
            {
                "deleted_count": deleted_count,
                "errors": errors,
                "message": f"{deleted_count}/{total_count} ingredients deleted"
            },
            status=status.HTTP_200_OK
        )