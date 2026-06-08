# provider/controllers/mixins/read_mixin.py
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.models import Provider
from stock_management.provider.validators import validate_provider_filter
from stock_management.provider.serializers import ProviderSerializer
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request


class ReadMixin:
    """
    Mixin to handle GET requests for retrieving providers.
    """
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List all providers with custom filtering (Admin/Staff only).
        GET /api/provider/
        
        Query params:
        - category: fresh, canned, bottled, dairy, equipment, other
        - search: search in name
        - is_active: true/false filter active status
        - ordering: name, created_at (prepend - for desc)
        """
        try:
            filters = validate_provider_filter(dict(request.query_params))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Provider.objects.all()
        
        # Filter by category
        if filters.get('category'):
            queryset = queryset.filter(category=filters['category'])
        
        # Filter by active status
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        
        # Search in name, email, phone
        if filters.get('search'):
            queryset = queryset.filter(
                models.Q(name__icontains=filters['search']) |
                models.Q(email__icontains=filters['search']) |
                models.Q(phone__icontains=filters['search'])
            )
        
        # Ordering
        ordering = filters.get('ordering', 'name')
        queryset = queryset.order_by(ordering)
        
        serializer = ProviderSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve single provider by ID (Admin/Staff only).
        GET /api/provider/{id}/
        """
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Provider.objects.get(pk=pk)
        except Provider.DoesNotExist:
            return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProviderSerializer(instance)
        return Response(serializer.data)
