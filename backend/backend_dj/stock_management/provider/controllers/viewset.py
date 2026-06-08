# provider/controllers/viewset.py
from rest_framework import viewsets, permissions
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from stock_management.provider.controllers.mixins import (
    CreateMixin,
    ReadMixin,
    UpdateMixin,
    DeleteMixin,
)
from stock_management.provider.serializers import ProviderSerializer
from stock_management.models import Provider


@method_decorator(csrf_exempt, name='dispatch')
class ProviderViewSet(
    CreateMixin,
    ReadMixin,
    UpdateMixin,
    DeleteMixin,
    viewsets.ModelViewSet
):
    """
    API ViewSet for Provider (Supplier/Vendor) management - pattern like inventory.InventoryViewSet
    All endpoints require authentication and admin/staff role.
    
    Endpoints (Admin/Staff only):
    - POST   /api/provider/              - Create new provider
    - GET    /api/provider/              - List with filtering & search
    - GET    /api/provider/{id}/         - Retrieve single provider
    - PUT    /api/provider/{id}/         - Full update
    - PATCH  /api/provider/{id}/         - Partial update
    - DELETE /api/provider/{id}/         - Delete (only if no purchase orders)
    - PATCH  /api/provider/update-many/  - Update multiple providers
    - DELETE /api/provider/delete-all/   - Delete all providers without orders
    - DELETE /api/provider/delete-many/  - Delete multiple providers by IDs
    
    Filtering:
    - ?category=fresh|canned|bottled|dairy|equipment|other
    - ?is_active=true|false
    - ?search=supplier_name
    - ?ordering=name|-name|created_at|-created_at
    """
    
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    permission_classes = [permissions.AllowAny]  # Checks enforced in mixins via is_staff/is_superuser
    parser_classes = (JSONParser, MultiPartParser, FormParser)
