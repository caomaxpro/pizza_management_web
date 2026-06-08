from typing import Any
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.inventory.validators import validate_inventory_data
from stock_management.inventory.serializers import InventorySerializer
from helper.auth_decorators import jwt_authentication, role_required


class CreateMixin:
    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request, *args, **kwargs) -> Response:
        """
        Create a new inventory item (Admin/Manager only).
        POST /api/inventory/
        """
        try:
            validate_inventory_data(dict(request.data))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = InventorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer) -> None:
        """Save inventory item"""
        serializer.save()