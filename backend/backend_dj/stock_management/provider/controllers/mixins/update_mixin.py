# provider/controllers/mixins/update_mixin.py
from __future__ import annotations
from typing import Any, cast
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.models import Provider
from stock_management.provider.validators import validate_provider_data
from stock_management.provider.serializers import ProviderSerializer
from rest_framework.request import Request
from helper.auth_decorators import jwt_authentication, role_required


class UpdateMixin:
    """
    Mixin to handle PUT/PATCH requests for updating providers.
    
    Pattern: Like inventory.UpdateMixin - direct DB access
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Full update (PUT) of provider (Admin/Manager only).
        PUT /api/provider/{id}/
        
        All fields can be updated.
        """
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Provider.objects.get(pk=pk)
        except Provider.DoesNotExist:
            return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Use serializer for validation (handles exclude for partial updates)
        serializer = ProviderSerializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partial update (PATCH) of provider.
        PATCH /api/provider/{id}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def _validate_partial_update(self, data: dict, instance: Provider) -> None:
        """Validate partial update by merging with existing data"""
        merged_data = {
            'name': data.get('name', instance.name),
            'category': data.get('category', instance.category),
            'phone': data.get('phone', instance.phone),
            'email': data.get('email', instance.email),
            'address': data.get('address', instance.address),
            'is_active': data.get('is_active', instance.is_active),
        }
        validate_provider_data(merged_data)
    
    def perform_update(self, serializer: Any) -> None:
        """Save updated provider"""
        serializer.save()
    
    @action(detail=False, methods=['patch'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update_many(self, request: Request) -> Response:
        """
        Update multiple providers by IDs (Admin/Manager only).
        PATCH /api/provider/update-many/
        
        Request body:
        {
            "ids": [1, 2, 3],
            "name": "new name",
            "category": "new category",
            ...
        }
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
        
        try:
            # Validate data by checking against first provider or generic validation
            first_provider = Provider.objects.filter(id__in=ids).first()
            if first_provider:
                # Use serializer to validate with proper exclude context
                temp_serializer = ProviderSerializer(
                    first_provider,
                    data=update_data,
                    partial=True
                )
                temp_serializer.is_valid(raise_exception=True)
            else:
                # If no providers found with those IDs, validate anyway
                validate_provider_data(update_data)
        except (DjangoValidationError, DRFValidationError) as e:
            error_msg = str(e.detail) if isinstance(e, DRFValidationError) else str(e)
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update all matching providers
        updated_count = 0
        updated_providers = []
        
        for provider in Provider.objects.filter(id__in=ids):
            serializer = ProviderSerializer(
                provider,
                data=update_data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                updated_providers.append(serializer.data)
                updated_count += 1
        
        return Response({
            'message': f'{updated_count} provider(s) updated',
            'count': updated_count,
            'updated_providers': updated_providers
        })
    
    @action(detail=False, methods=['patch'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update_all(self, request: Request) -> Response:
        """
        Update all providers with the same data.
        PATCH /api/provider/update-all/
        
        Request body:
        {
            "name": "new name",
            "is_active": true,
            ...
        }
        """
        update_data = cast(dict[str, Any], request.data)
        
        if not update_data:
            return Response(
                {'error': 'No fields to update provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate by checking against first existing provider
            first_provider = Provider.objects.first()
            if first_provider:
                # Use serializer to validate with proper exclude context
                temp_serializer = ProviderSerializer(
                    first_provider,
                    data=update_data,
                    partial=True
                )
                temp_serializer.is_valid(raise_exception=True)
            else:
                # If no providers exist yet, validate anyway
                validate_provider_data(update_data)
        except (DjangoValidationError, DRFValidationError) as e:
            error_msg = str(e.detail) if isinstance(e, DRFValidationError) else str(e)
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update all providers
        updated_count = 0
        updated_providers = []
        
        for provider in Provider.objects.all():
            serializer = ProviderSerializer(
                provider,
                data=update_data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                updated_providers.append(serializer.data)
                updated_count += 1
        
        return Response({
            'message': f'All {updated_count} provider(s) updated',
            'count': updated_count,
            'updated_providers': updated_providers
        })
