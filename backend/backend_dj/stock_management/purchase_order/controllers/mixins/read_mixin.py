# purchase_order/controllers/mixins/read_mixin.py
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.models import PurchaseOrder
from stock_management.purchase_order.validators import validate_purchase_order_filter
from stock_management.purchase_order.serializers import PurchaseOrderSerializer
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request


class ReadMixin:
    """
    Mixin to handle GET requests for retrieving purchase orders.
    """
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List all purchase orders with custom filtering (Admin/Staff only).
        GET /api/purchase-order/
        
        Query params:
        - status: pending, received, cancelled
        - provider_id: filter by provider
        - search: search in order_number
        - ordering: order_number, order_date, status, total_cost (prepend - for desc)
        """
        try:
            filters = validate_purchase_order_filter(dict(request.query_params))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = PurchaseOrder.objects.all()
        
        # Filter by status
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Filter by provider
        if filters.get('provider_id'):
            queryset = queryset.filter(provider_id=filters['provider_id'])
        
        # Search in order_number
        if filters.get('search'):
            queryset = queryset.filter(order_number__icontains=filters['search'])
        
        # Ordering
        ordering = filters.get('ordering', '-order_date')
        queryset = queryset.order_by(ordering).prefetch_related('items', 'provider')
        
        serializer = PurchaseOrderSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve single purchase order by ID (Admin/Staff only).
        GET /api/purchase-order/{id}/
        """
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = PurchaseOrder.objects.prefetch_related('items', 'provider').get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PurchaseOrderSerializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def confirm_receipt(self, request: Request, pk: Any = None) -> Response:
        """
        Confirm delivery and update inventory stock (Admin/Manager only).
        POST /api/purchase-order/{id}/confirm-receipt/
        
        Process:
        1. Get purchase order by ID
        2. Call order.confirm_receipt() to:
           - Update inventory stock for each item
           - Create inventory logs for audit trail
           - Mark order as 'received'
           - Record actual_delivery_date
        
        Only pending orders can be confirmed.
        """
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = PurchaseOrder.objects.get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate order is pending
        if order.status != 'pending':
            return Response(
                {'error': f'Can only confirm pending orders. Current status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order.confirm_receipt()
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PurchaseOrderSerializer(order)
        return Response(
            {'message': 'Order received and inventory updated', 'data': serializer.data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def cancel(self, request: Request, pk: Any = None) -> Response:
        """
        Cancel a pending purchase order.
        POST /api/purchase-order/{id}/cancel/
        
        Only pending orders can be cancelled.
        Received orders cannot be cancelled (inventory already updated).
        """
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = PurchaseOrder.objects.get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            order.cancel()
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PurchaseOrderSerializer(order)
        return Response(
            {'message': 'Order cancelled', 'data': serializer.data},
            status=status.HTTP_200_OK
        )
