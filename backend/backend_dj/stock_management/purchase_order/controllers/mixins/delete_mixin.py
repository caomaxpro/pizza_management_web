# purchase_order/controllers/mixins/delete_mixin.py
from __future__ import annotations
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from stock_management.models import PurchaseOrder
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request


class DeleteMixin:
    """
    Mixin to handle DELETE requests for removing purchase orders.
    
    Pattern: Hard delete only
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete purchase order (Admin/Manager only).
        DELETE /api/purchase-order/{id}/
        
        Rules:
        - Can only delete pending orders (not received/cancelled)
        - Received orders cannot be deleted (inventory already updated)
        """
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = PurchaseOrder.objects.get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Prevent deletion of received orders (inventory already updated)
        if instance.status == 'received':
            return Response(
                {'error': 'Cannot delete received orders (inventory already updated)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_many(self, request: Request) -> Response:
        """
        Delete multiple purchase orders by IDs (Admin/Manager only).
        DELETE /api/purchase-order/delete-many/
        
        Request body:
        {
            "ids": [1, 2, 3]
        }
        
        Rules:
        - Can only delete pending/cancelled orders (not received)
        - Received orders cannot be deleted (inventory already updated)
        """
        data = dict(request.data)
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list) or len(ids) == 0:
            return Response(
                {'error': 'ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = 0
        skipped_orders = []
        
        for order in PurchaseOrder.objects.filter(id__in=ids):
            if order.status == 'received':
                skipped_orders.append({
                    'id': order.id,
                    'reason': 'Cannot delete received orders (inventory already updated)'
                })
            else:
                order.delete()
                deleted_count += 1
        
        return Response({
            'message': f'{deleted_count} order(s) deleted',
            'deleted_count': deleted_count,
            'skipped_count': len(skipped_orders),
            'skipped_orders': skipped_orders
        })
    
    @action(detail=False, methods=['delete'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def delete_all(self, request: Request) -> Response:
        """
        Delete all non-received purchase orders (Admin/Manager only).
        DELETE /api/purchase-order/delete-all/
        
        Rules:
        - Only deletes pending/cancelled orders
        - Received orders are skipped (inventory already updated)
        """
        deleted_count = 0
        skipped_orders = []
        
        for order in PurchaseOrder.objects.all():
            if order.status == 'received':
                skipped_orders.append({
                    'id': order.id,
                    'reason': 'Cannot delete received orders (inventory already updated)'
                })
            else:
                order.delete()
                deleted_count += 1
        
        return Response({
            'message': f'{deleted_count} order(s) deleted',
            'deleted_count': deleted_count,
            'skipped_count': len(skipped_orders),
            'skipped_orders': skipped_orders
        })
