# purchase_order/controllers/item_viewset.py
from rest_framework import viewsets, permissions
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError as DjangoValidationError
from typing import cast, Any

from stock_management.purchase_order.serializers import PurchaseOrderItemSerializer
from stock_management.models import PurchaseOrderItem, PurchaseOrder, Inventory
from stock_management.purchase_order.validators import validate_purchase_order_item_data
from user_management.models import User


@method_decorator(csrf_exempt, name='dispatch')
class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for PurchaseOrderItem (line items in PO).
    All endpoints require authentication and admin/staff role.
    
    Endpoints (Admin/Staff only):
    - POST   /api/purchase-order-item/              - Add item to PO
    - GET    /api/purchase-order-item/              - List all items
    - GET    /api/purchase-order-item/{id}/         - Retrieve single item
    - PUT    /api/purchase-order-item/{id}/         - Full update (quantity, price)
    - PATCH  /api/purchase-order-item/{id}/         - Partial update
    - DELETE /api/purchase-order-item/{id}/         - Remove item from PO
    
    Validation:
    - Inventory must belong to PO's provider
    - Quantity must be > 0
    - Price must be >= 0
    
    Query params:
    - ?purchase_order_id=1  - Filter by PO
    - ?inventory_id=1       - Filter by inventory
    """
    
    queryset = PurchaseOrderItem.objects.all().select_related('purchase_order', 'inventory', 'inventory__provider')
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.AllowAny]  # Checks enforced in CRUD methods via is_staff/is_superuser
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def list(self, request, *args, **kwargs):
        """List all PO items with optional filtering (Admin/Staff only)"""
        # Check if user is authenticated
        if not request.user.is_authenticated:  # type: ignore
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is admin or staff
        user = cast(User, request.user)  # type: ignore
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Only admins/staff can view purchase order items'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.queryset
        
        # Filter by purchase_order_id
        po_id = request.query_params.get('purchase_order_id')
        if po_id:
            queryset = queryset.filter(purchase_order_id=po_id)
        
        # Filter by inventory_id
        inv_id = request.query_params.get('inventory_id')
        if inv_id:
            queryset = queryset.filter(inventory_id=inv_id)
        
        serializer = PurchaseOrderItemSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Add item to purchase order (Admin/Staff only).
        POST /api/purchase-order-item/
        
        Required:
        - purchase_order: int (PO ID)
        - inventory_id: int (Item ID - must belong to PO's supplier)
        - quantity: float (> 0)
        
        Optional:
        - actual_unit_price: float (from invoice)
        """
        # Check if user is authenticated
        if not request.user.is_authenticated:  # type: ignore
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is admin or staff
        user = cast(User, request.user)  # type: ignore
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Only admins/staff can add purchase order items'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            validate_purchase_order_item_data(dict(request.data))
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get PO for context
        po_id = request.data.get('purchase_order')
        try:
            po = PurchaseOrder.objects.get(id=po_id)
        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': f'Purchase Order ID {po_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Pass PO context to serializer for provider validation
        serializer = PurchaseOrderItemSerializer(
            data=request.data,
            context={'po_id': po_id, 'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer) -> None:
        """Save new item"""
        serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        """Get single item (Admin/Staff only)"""
        # Check if user is authenticated
        if not request.user.is_authenticated:  # type: ignore
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is admin or staff
        user = cast(User, request.user)  # type: ignore
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Only admins/staff can view purchase order items'},
                status=status.HTTP_403_FORBIDDEN
            )
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = PurchaseOrderItem.objects.select_related(
                'purchase_order', 'inventory', 'inventory__provider'
            ).get(pk=pk)
        except PurchaseOrderItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PurchaseOrderItemSerializer(item)
        return Response(serializer.data)
    
    def update(self, request, *args: Any, **kwargs: Any) -> Response:
        """Update item in PO (Admin/Staff only)"""
        # Check if user is authenticated
        if not request.user.is_authenticated:  # type: ignore
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is admin or staff
        user = cast(User, request.user)  # type: ignore
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Only admins/staff can update purchase order items'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        partial = kwargs.pop('partial', False)
        return super().update(request, *args, partial=partial, **kwargs)
    
    def partial_update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """Partial update item in PO (Admin/Staff only)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete item from PO (Admin/Staff only)"""
        # Check if user is authenticated
        if not request.user.is_authenticated:  # type: ignore
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is admin or staff
        user = cast(User, request.user)  # type: ignore
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Only admins/staff can delete purchase order items'},
                status=status.HTTP_403_FORBIDDEN
            )
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = PurchaseOrderItem.objects.get(pk=pk)
        except PurchaseOrderItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if PO is already received
        if item.purchase_order.status == 'received':
            return Response(
                {'error': 'Cannot delete item from received order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po = item.purchase_order
        item.delete()
        
        # Recalculate PO total
        po.calculate_total()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
