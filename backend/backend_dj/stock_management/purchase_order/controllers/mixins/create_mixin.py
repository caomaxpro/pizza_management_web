# purchase_order/controllers/mixins/create_mixin.py
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

from stock_management.purchase_order.validators import validate_purchase_order_data
from stock_management.purchase_order.serializers import PurchaseOrderSerializer
from helper.auth_decorators import jwt_authentication, role_required


class CreateMixin:
    """
    Mixin to handle POST requests for creating purchase orders.
    
    Pattern: Like inventory.CreateMixin - direct DB access
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new purchase order (Admin/Manager only).
        POST /api/purchase-order/
        
        Required fields:
        - order_number: str (PO-001, PO-002, ...)
        - provider_id: int
        
        Optional fields:
        - expected_delivery_date: date
        - notes: str
        
        Note: Items are added via separate PurchaseOrderItem endpoint
        """
        try:
            validate_purchase_order_data(dict(request.data))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PurchaseOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer: Any) -> None:
        """Save new purchase order"""
        serializer.save()
