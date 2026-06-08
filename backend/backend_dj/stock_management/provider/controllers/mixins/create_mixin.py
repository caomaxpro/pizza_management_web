# provider/controllers/mixins/create_mixin.py
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.provider.validators import validate_provider_data
from stock_management.provider.serializers import ProviderSerializer
from helper.auth_decorators import jwt_authentication, role_required


class CreateMixin:
    """
    Mixin to handle POST requests for creating providers.
    
    Pattern: Like inventory.CreateMixin - direct DB access
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new provider/supplier (Admin/Manager only).
        POST /api/provider/
        
        Required fields:
        - name: str (unique)
        
        Optional fields:
        - category: fresh, canned, bottled, dairy, equipment, other (default: other)
        - phone: str
        - email: str
        - address: str
        - is_active: bool (default: true)
        """
        try:
            validate_provider_data(dict(request.data))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer: Any) -> None:
        """Save new provider"""
        serializer.save()
