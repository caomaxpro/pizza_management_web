# purchase_order/controllers/mixins/update_mixin.py
from __future__ import annotations
from typing import Any, cast
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.models import PurchaseOrder
from stock_management.purchase_order.validators import validate_purchase_order_data
from stock_management.purchase_order.serializers import PurchaseOrderSerializer
from rest_framework.request import Request
from helper.auth_decorators import jwt_authentication, role_required


class UpdateMixin:
    """
    Mixin to handle PUT/PATCH requests for updating purchase orders.
    
    Pattern: Like inventory.UpdateMixin - direct DB access
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Full update (PUT) of purchase order (Admin/Manager only).
        PUT /api/purchase-order/{id}/
        
        Updatable fields (for pending orders only):
        - expected_delivery_date
        - notes
        
        Cannot update order_number or provider once created.
        Cannot update received/cancelled orders.
        """
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = PurchaseOrder.objects.get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Prevent updates to received/cancelled orders
        if instance.status != 'pending':
            return Response(
                {'error': f'Can only update pending orders. Current status: {instance.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if not partial:
                # Full update requires all fields
                validate_purchase_order_data(dict(request.data))
            else:
                # Partial update - merge with existing
                self._validate_partial_update(dict(request.data), instance)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PurchaseOrderSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def partial_update(self, request: "Request", *args: Any, **kwargs: Any) -> Response:
        """
        Partial update (PATCH) of purchase order.
        PATCH /api/purchase-order/{id}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def _validate_partial_update(self, data: dict, instance: PurchaseOrder) -> None:
        """Validate partial update by merging with existing data"""
        merged_data = {
            'order_number': data.get('order_number', instance.order_number),
            'provider_id': data.get('provider_id', instance.provider.id),
            'expected_delivery_date': data.get('expected_delivery_date', instance.expected_delivery_date),
            'notes': data.get('notes', instance.notes),
        }
        validate_purchase_order_data(merged_data)
    
    def perform_update(self, serializer: Any) -> None:
        """Save updated purchase order"""
        serializer.save()
    
    @action(detail=False, methods=['patch'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update_many(self, request: Request) -> Response:
        """
        Update multiple purchase orders by IDs (Admin/Manager only).
        PATCH /api/purchase-order/update-many/
        
        Request body:
        {
            "ids": [1, 2, 3],
            "expected_delivery_date": "2024-12-31",
            "notes": "new notes"
        }
        
        Rules:
        - Can only update pending orders
        - Only updatable fields: expected_delivery_date, notes
        """
        data = cast(dict[str, Any], request.data)
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list) or len(ids) == 0:
            return Response(
                {'error': 'ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract update data (everything except 'ids')
        update_data = {k: v for k, v in data.items() if k != 'ids'}
        
        if not update_data:
            return Response(
                {'error': 'No fields to update provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = 0
        skipped_orders = []
        updated_orders = []
        
        for order in PurchaseOrder.objects.filter(id__in=ids):
            if order.status != 'pending':
                skipped_orders.append({
                    'id': order.id,
                    'reason': f'Not pending (status: {order.status})'
                })
            else:
                try:
                    serializer = PurchaseOrderSerializer(
                        order,
                        data=update_data,
                        partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()
                        updated_orders.append(serializer.data)
                        updated_count += 1
                    else:
                        skipped_orders.append({
                            'id': order.id,
                            'reason': f'Validation error: {serializer.errors}'
                        })
                except (DjangoValidationError, DRFValidationError) as e:
                    error_msg = str(e.detail) if isinstance(e, DRFValidationError) else str(e)
                    skipped_orders.append({
                        'id': order.id,
                        'reason': f'Error: {error_msg}'
                    })
        
        return Response({
            'message': f'{updated_count} order(s) updated',
            'updated_count': updated_count,
            'skipped_count': len(skipped_orders),
            'updated_orders': updated_orders,
            'skipped_orders': skipped_orders
        })
    
    @action(detail=False, methods=['patch'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update_all(self, request: Request) -> Response:
        """
        Update all pending purchase orders.
        PATCH /api/purchase-order/update-all/
        
        Request body:
        {
            "expected_delivery_date": "2024-12-31",
            "notes": "new notes"
        }
        
        Rules:
        - Only updates pending orders
        - Only updatable fields: expected_delivery_date, notes
        """
        update_data = cast(dict[str, Any], request.data)
        
        if not update_data:
            return Response(
                {'error': 'No fields to update provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = 0
        skipped_orders = []
        updated_orders = []
        
        for order in PurchaseOrder.objects.filter(status='pending'):
            try:
                serializer = PurchaseOrderSerializer(
                    order,
                    data=update_data,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    updated_orders.append(serializer.data)
                    updated_count += 1
                else:
                    skipped_orders.append({
                        'id': order.id,
                        'reason': f'Validation error: {serializer.errors}'
                    })
            except (DjangoValidationError, DRFValidationError) as e:
                error_msg = str(e.detail) if isinstance(e, DRFValidationError) else str(e)
                skipped_orders.append({
                    'id': order.id,
                    'reason': f'Error: {error_msg}'
                })
        
        return Response({
            'message': f'All {updated_count} pending order(s) updated',
            'updated_count': updated_count,
            'skipped_count': len(skipped_orders),
            'updated_orders': updated_orders,
            'skipped_orders': skipped_orders
        })
