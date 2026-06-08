# inventory/controllers/viewset.py
import json
from rest_framework import viewsets, permissions, status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pydantic import ValidationError as PydanticValidationError

from stock_management.inventory.controllers.mixins import CreateMixin, ReadMixin, UpdateMixin, DeleteMixin
from stock_management.inventory.serializers import InventorySerializer, InventoryLogSerializer
from stock_management.inventory.validators import BulkLogCreateValidator
from stock_management.inventory.services import InventoryService
from stock_management.models import Inventory, InventoryLog


@method_decorator(csrf_exempt, name='dispatch')
class InventoryViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """
    API ViewSet for Inventory management - pattern like pizza_management.ingredient
    All endpoints require authentication and admin/staff role.
    
    Endpoints (Admin/Staff only):
    - POST   /api/inventory/              - Create inventory item
    - GET    /api/inventory/              - List with filtering
    - GET    /api/inventory/{id}/         - Retrieve item details
    - PUT    /api/inventory/{id}/         - Full update
    - PATCH  /api/inventory/{id}/         - Partial update
    - DELETE /api/inventory/{id}/         - Delete single item
    - DELETE /api/inventory/delete-all/   - Delete all items
    - POST   /api/inventory/delete-many/  - Delete multiple items by IDs
    - POST   /api/inventory/delete-by-provider/ - Delete by provider
    - GET    /api/inventory/low_stock/    - Low stock items report
    - GET    /api/inventory/{id}/history/ - Stock change history
    """
    
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.AllowAny]  # Checks enforced in mixins via is_staff/is_superuser
    parser_classes = (JSONParser, MultiPartParser, FormParser)


class InventoryLogViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for InventoryLog (audit trail) - read-only.

    Endpoints:
    - GET  /api/inventory-log/              - List all logs (filterable by ?inventory=<id>)
    - GET  /api/inventory-log/{id}/         - Retrieve a single log
    """

    queryset = InventoryLog.objects.select_related("inventory").order_by("-created_at")
    serializer_class = InventoryLogSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Skip global CookieJWTAuthentication; auth handled per-method

    def list(self, request, *args, **kwargs):
        from helper.auth_decorators import TokenValidator

        user, error = TokenValidator.validate_admin_request(request)
        if error:
            return error

        inventory_id = request.query_params.get("inventory")
        queryset = self.queryset
        if inventory_id:
            queryset = queryset.filter(inventory_id=inventory_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        from helper.auth_decorators import TokenValidator

        user, error = TokenValidator.validate_admin_request(request)
        if error:
            return error

        return super().retrieve(request, *args, **kwargs)
