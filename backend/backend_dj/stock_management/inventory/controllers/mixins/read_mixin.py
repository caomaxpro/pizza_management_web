from __future__ import annotations

from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.models import Inventory
from stock_management.inventory.validators import validate_inventory_filter
from stock_management.inventory.serializers import InventorySerializer, InventoryLogSerializer
from helper.auth_decorators import jwt_authentication, role_required

from rest_framework.request import Request


class ReadMixin:
    """
    Mixin to handle GET requests for retrieving inventory items.
    """
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List all inventory items with custom filtering (Admin/Staff only).
        GET /api/inventory/
        """
        try:
            filters = validate_inventory_filter(dict(request.query_params))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Inventory.objects.all()
        
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        
        if filters.get('search'):
            queryset = queryset.filter(
                models.Q(name__icontains=filters['search']) |
                models.Q(description__icontains=filters['search'])
            )
        
        if filters.get('min_stock') is not None:
            queryset = queryset.filter(current_stock__gte=filters['min_stock'])
        
        if filters.get('max_stock') is not None:
            queryset = queryset.filter(current_stock__lte=filters['max_stock'])
        
        ordering = filters.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve single inventory item by ID (Admin/Staff only).
        GET /api/inventory/{id}/
        """
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventorySerializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def low_stock(self, request: Request) -> Response:
        """
        Get items below minimum threshold (Admin/Staff only).
        GET /api/inventory/low_stock/
        """
        low_stock_items = Inventory.objects.filter(
            current_stock__lt=models.F('min_threshold'),
            is_active=True
        ).order_by('current_stock')
        
        serializer = InventorySerializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def history(self, request: Request, pk: Any = None) -> Response:
        """
        Get stock change history for this item (Admin/Staff only).
        GET /api/inventory/{id}/history/
        """
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        logs = inventory.logs.all().order_by('-created_at')  # type: ignore[attr-defined]
        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data)
