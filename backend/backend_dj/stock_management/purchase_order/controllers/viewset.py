# purchase_order/controllers/viewset.py
from rest_framework import viewsets, permissions
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from stock_management.purchase_order.controllers.mixins import (
    CreateMixin,
    ReadMixin,
    UpdateMixin,
    DeleteMixin,
)
from stock_management.purchase_order.serializers import PurchaseOrderSerializer
from stock_management.models import PurchaseOrder


@method_decorator(csrf_exempt, name='dispatch')
class PurchaseOrderViewSet(
    CreateMixin,
    ReadMixin,
    UpdateMixin,
    DeleteMixin,
    viewsets.ModelViewSet
):
    """
    API ViewSet for Purchase Order management - pattern like inventory.InventoryViewSet
    All endpoints require authentication and admin/staff role.
    
    Endpoints (Admin/Staff only):
    - POST   /api/purchase-order/                 - Create new PO
    - GET    /api/purchase-order/                 - List with filtering
    - GET    /api/purchase-order/{id}/            - Retrieve single PO
    - PUT    /api/purchase-order/{id}/            - Full update (expected_delivery_date, notes)
    - PATCH  /api/purchase-order/{id}/            - Partial update
    - DELETE /api/purchase-order/{id}/            - Delete (pending only)
    - PATCH  /api/purchase-order/update-many/     - Update multiple POs
    - POST   /api/purchase-order/{id}/confirm-receipt/  - Confirm delivery, update inventory
    - POST   /api/purchase-order/{id}/cancel/           - Cancel pending order
    - DELETE /api/purchase-order/delete-many/     - Delete multiple POs
    - DELETE /api/purchase-order/delete-all/      - Delete all non-received POs
    
    Filtering:
    - ?status=pending|received|cancelled
    - ?provider_id=1
    - ?search=PO-001
    - ?ordering=order_date|-order_date
    """
    
    queryset = PurchaseOrder.objects.all().prefetch_related('items', 'provider')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.AllowAny]  # Checks enforced in mixins via is_staff/is_superuser
    parser_classes = (JSONParser, MultiPartParser, FormParser)
