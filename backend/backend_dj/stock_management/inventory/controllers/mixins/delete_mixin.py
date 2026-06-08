from typing import Any, Dict, Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError as DjangoValidationError
from stock_management.models import Inventory
from stock_management.inventory.validators import validate_inventory_data
from stock_management.inventory.serializers import InventorySerializer
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request


class DeleteMixin:
    """
    Mixin to handle DELETE requests for removing inventory items.
    
    Endpoints:
    - DELETE /api/inventory/{id}/           - Delete single item
    - DELETE /api/inventory/delete-all/     - Delete ALL items
    - POST   /api/inventory/delete-many/    - Delete specific IDs
    - POST   /api/inventory/delete-by-provider/ - Delete by provider
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request, *args: Any, **kwargs: Any) -> Response:
        """Delete single inventory item - DELETE /api/inventory/{id}/"""
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Inventory.objects.get(pk=pk)
            instance.delete()
        except Inventory.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'], url_path='delete-all', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_all(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete ALL items - DELETE /api/inventory/delete-all/"""
        count, _ = Inventory.objects.all().delete()
        return Response(
            {'message': 'All inventory items deleted', 'count': count},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='delete-many', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_many(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete specific items - POST /api/inventory/delete-many/
        Body: {"ids": [1, 2, 3, ...]}
        """
        data: Dict[str, Any] = dict(request.data)  # type: ignore
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return Response(
                {'error': 'ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        existing_items = Inventory.objects.filter(id__in=ids)
        existing_ids = set(existing_items.values_list('id', flat=True))
        not_found_ids = list(set(ids) - existing_ids)
        deleted_count, _ = existing_items.delete()
        
        return Response(
            {
                'message': f'{deleted_count} items deleted successfully',
                'deleted_count': deleted_count,
                'not_found': not_found_ids or None,
                'count': deleted_count
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='delete-by-provider', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_by_provider(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete by provider - POST /api/inventory/delete-by-provider/
        Body: {"provider_id": 1}
        """
        data: Dict[str, Any] = dict(request.data)  # type: ignore
        provider_id = data.get('provider_id')
        
        if not provider_id:
            return Response(
                {'error': 'provider_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = Inventory.objects.filter(provider_id=provider_id)
        
        if not items.exists():
            return Response(
                {'message': f'No items found', 'count': 0},
                status=status.HTTP_200_OK
            )
        
        # Get first item and extract provider name
        first_item: Optional[Inventory] = items.first()
        provider_name = first_item.provider.name if (first_item and first_item.provider) else 'Unknown'
        count, _ = items.delete()
        
        return Response(
            {
                'message': f'All items from \'{provider_name}\' deleted',
                'provider_id': provider_id,
                'provider_name': provider_name,
                'count': count
            },
            status=status.HTTP_200_OK
        )