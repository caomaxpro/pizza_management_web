# inventory/urls.py
from django.urls import path

from .controllers import InventoryViewSet, InventoryLogViewSet

inventory_list = InventoryViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

inventory_detail = InventoryViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

inventory_low_stock = InventoryViewSet.as_view({
    'get': 'low_stock',
})

inventory_history = InventoryViewSet.as_view({
    'get': 'history',
})

inventory_delete_all = InventoryViewSet.as_view({
    'delete': 'delete_all',
})

inventory_delete_many = InventoryViewSet.as_view({
    'post': 'delete_many',
})

inventory_delete_by_provider = InventoryViewSet.as_view({
    'post': 'delete_by_provider',
})

inventory_revert_logs = InventoryViewSet.as_view({
    'post': 'revert_logs',
})

inventory_log_list = InventoryLogViewSet.as_view({
    'get': 'list',
})

# bulk_create moved to InventoryViewSet (UpdateMixin) with proper auth
inventory_log_bulk_create = InventoryViewSet.as_view({
    'post': 'bulk_create',
})

inventory_log_detail = InventoryLogViewSet.as_view({
    'get': 'retrieve',
})

urlpatterns = [
    # Custom actions PHẢI trước detail routes
    path('inventory/low-stock/', inventory_low_stock, name='inventory-low-stock'),
    path('inventory/<int:pk>/history/', inventory_history, name='inventory-history'),
    path('inventory/delete-all/', inventory_delete_all, name='inventory-delete-all'),
    path('inventory/delete-many/', inventory_delete_many, name='inventory-delete-many'),
    path('inventory/delete-by-provider/', inventory_delete_by_provider, name='inventory-delete-by-provider'),
    path('inventory/revert-logs/', inventory_revert_logs, name='inventory-revert-logs'),
    
    # Inventory endpoints
    path('inventory/', inventory_list, name='inventory-list'),
    path('inventory/<int:pk>/', inventory_detail, name='inventory-detail'),
    
    # Inventory Log endpoints
    path('inventory-log/bulk-create/', inventory_log_bulk_create, name='inventory-log-bulk-create'),
    path('inventory-log/', inventory_log_list, name='inventory-log-list'),
    path('inventory-log/<int:pk>/', inventory_log_detail, name='inventory-log-detail'),
]