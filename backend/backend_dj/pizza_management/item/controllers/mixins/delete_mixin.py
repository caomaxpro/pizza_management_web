import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from pizza_management.item.model import Item
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import invalidate_items_cache, invalidate_cache, CacheHelper

logger = logging.getLogger(__name__)


class DeleteMixin(ModelViewSet):
    """Mixin for DELETE operations: destroy, delete_many, delete_all"""
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def destroy(self, request, *args, **kwargs):
        """DELETE /items/{id}/ - Delete single item (ADMIN ONLY)"""
        logger.info("[DELETE] Single item delete request")
        
        item_id = kwargs.get('pk')
        logger.debug(f"[DELETE] Item ID: {item_id}")
        
        try:
            item = Item.objects.get(id=item_id)
            logger.debug(f"[DELETE] Deleting item: {item.id} - {item.name}")
            
            # Clear image cache before deletion
            if item.image_url:
                CacheHelper.clear_image_cache_for_url(item.image_url)
            if item.piece_image_url:
                CacheHelper.clear_image_cache_for_url(item.piece_image_url)
            
            item.delete()
            
            logger.info(f"[DELETE] Item {item_id} deleted successfully")
            
            # Cache invalidation handled by @invalidate_cache decorator
            return Response(
                {"message": "Item deleted successfully", "id": item_id},
                status=status.HTTP_200_OK
            )
        
        except Item.DoesNotExist:
            logger.warning(f"[DELETE] Item {item_id} not found")
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"[DELETE] Error deleting item {item_id}: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def delete_many(self, request):
        """POST /items/delete-many/ - Delete multiple items by IDs (ADMIN ONLY)"""
        logger.info("[DELETE] Bulk delete request")
        ids = request.data.get("ids", [])
        if not ids:
            logger.warning("[DELETE] Bulk delete: no IDs provided")
            return Response({"error": "ids list required"}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = 0
        errors = []
        
        for item_id in ids:
            try:
                item = Item.objects.get(id=item_id)
                logger.debug(f"[DELETE] Deleting item: {item.id} - {item.name}")
                
                # Clear image cache before deletion
                if item.image_url:
                    CacheHelper.clear_image_cache_for_url(item.image_url)
                if item.piece_image_url:
                    CacheHelper.clear_image_cache_for_url(item.piece_image_url)
                
                item.delete()
                deleted_count += 1
            except Item.DoesNotExist:
                errors.append({"id": item_id, "error": "Item not found"})
                logger.warning(f"[DELETE] Item {item_id} not found")
            except Exception as e:
                errors.append({"id": item_id, "error": str(e)})
                logger.error(f"[DELETE] Error deleting item {item_id}: {str(e)}")
        
        logger.info(f"[DELETE] Bulk delete: {deleted_count} deleted, {len(errors)} errors")
        
        # Cache invalidation handled by @invalidate_cache decorator
        return Response({"deleted_count": deleted_count, "errors": errors}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"])
    @jwt_authentication
    @role_required(["admin", "manager"])
    @invalidate_cache(invalidate_items_cache)
    def delete_all(self, request):
        """POST /items/delete-all/ - Delete all items (ADMIN ONLY)"""
        logger.warning("[DELETE] Delete all items request")
        total_count = Item.objects.count()
        logger.info(f"[DELETE] Total items to delete: {total_count}")
        
        deleted_count = 0
        errors = []
        
        for item in Item.objects.all():
            try:
                logger.debug(f"[DELETE] Deleting item: {item.id} - {item.name}")
                
                # Clear image cache before deletion
                if item.image_url:
                    CacheHelper.clear_image_cache_for_url(item.image_url)
                if item.piece_image_url:
                    CacheHelper.clear_image_cache_for_url(item.piece_image_url)
                
                item.delete()
                deleted_count += 1
            except Exception as e:
                errors.append({"id": item.id, "name": item.name, "error": str(e)})
                logger.error(f"[DELETE] Error deleting item {item.id}: {str(e)}")
        
        logger.info(f"[DELETE] Delete all: {deleted_count} deleted, {len(errors)} errors")
        
        # Cache invalidation handled by @invalidate_cache decorator
        return Response(
            {"deleted_count": deleted_count, "errors": errors},
            status=status.HTTP_200_OK,
        )