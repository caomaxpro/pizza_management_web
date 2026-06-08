# provider/controllers/mixins/delete_mixin.py
from __future__ import annotations
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from stock_management.models import Provider
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request


class DeleteMixin:
    """
    Mixin to handle DELETE requests for removing providers.
    
    Pattern: Hard delete with validation
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete provider (Admin/Manager only).
        DELETE /api/provider/{id}/
        
        Rules:
        - Can only delete providers with no purchase orders
        - If provider has orders, must soft-delete (set is_active=False)
        """
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Provider.objects.get(pk=pk)
        except Provider.DoesNotExist:
            return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if provider has associated purchase orders
        if instance.purchase_orders.exists():
            return Response(
                {
                    'error': 'Cannot delete provider with existing purchase orders',
                    'suggestion': 'Set is_active=False to deactivate instead'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_all(self, request: Request) -> Response:
        """
        Delete all providers without purchase orders (Admin/Manager only).
        DELETE /api/provider/delete-all/
        
        Rules:
        - Only deletes providers with no purchase orders
        - Providers with orders are skipped (returned in skipped list)
        - Returns count of deleted and skipped providers
        """
        deleted_count = 0
        skipped_providers = []
        
        for provider in Provider.objects.all():
            if provider.purchase_orders.exists():
                skipped_providers.append({
                    'id': provider.id,
                    'name': provider.name,
                    'reason': 'Has purchase orders'
                })
            else:
                provider.delete()
                deleted_count += 1
        
        return Response({
            'message': f'{deleted_count} provider(s) deleted',
            'deleted_count': deleted_count,
            'skipped_count': len(skipped_providers),
            'skipped_providers': skipped_providers
        })
    
    @action(detail=False, methods=['delete'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_many(self, request: Request) -> Response:
        """
        Delete multiple providers by IDs (Admin/Manager only).
        DELETE /api/provider/delete-many/
        
        Request body:
        {
            "ids": [1, 2, 3]
        }
        
        Rules:
        - Only deletes providers with no purchase orders
        - Providers with orders are skipped (returned in skipped list)
        - Returns count of deleted and skipped providers
        """
        data = dict(request.data)
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list) or len(ids) == 0:
            return Response(
                {'error': 'ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = 0
        skipped_providers = []
        
        for provider in Provider.objects.filter(id__in=ids):
            if provider.purchase_orders.exists():
                skipped_providers.append({
                    'id': provider.id,
                    'name': provider.name,
                    'reason': 'Has purchase orders'
                })
            else:
                provider.delete()
                deleted_count += 1
        
        return Response({
            'message': f'{deleted_count} provider(s) deleted',
            'deleted_count': deleted_count,
            'skipped_count': len(skipped_providers),
            'skipped_providers': skipped_providers
        })
