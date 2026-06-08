# purchase_order/urls.py
from django.urls import path

from .controllers import PurchaseOrderViewSet, PurchaseOrderItemViewSet

# PurchaseOrder views
purchase_order_list = PurchaseOrderViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

purchase_order_detail = PurchaseOrderViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

purchase_order_confirm_receipt = PurchaseOrderViewSet.as_view({
    'post': 'confirm_receipt',
})

purchase_order_cancel = PurchaseOrderViewSet.as_view({
    'post': 'cancel',
})

# Bulk Update operations
purchase_order_update_many = PurchaseOrderViewSet.as_view({
    'patch': 'update_many',
})

purchase_order_update_all = PurchaseOrderViewSet.as_view({
    'patch': 'update_all',
})

# Bulk Delete operations
purchase_order_delete_many = PurchaseOrderViewSet.as_view({
    'delete': 'delete_many',
})

purchase_order_delete_all = PurchaseOrderViewSet.as_view({
    'delete': 'delete_all',
})

# PurchaseOrderItem views
purchase_order_item_list = PurchaseOrderItemViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

purchase_order_item_detail = PurchaseOrderItemViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    # Bulk operations MUST come before detail routes (Django route matching order)
    path('purchase-orders/update-many/', purchase_order_update_many, name='purchase-orders-update-many'),
    path('purchase-orders/update-all/', purchase_order_update_all, name='purchase-orders-update-all'),
    path('purchase-orders/delete-many/', purchase_order_delete_many, name='purchase-orders-delete-many'),
    path('purchase-orders/delete-all/', purchase_order_delete_all, name='purchase-orders-delete-all'),

    # Custom actions PHẢI trước detail routes (Django route matching order)
    path('purchase-orders/<int:pk>/confirm-receipt/', purchase_order_confirm_receipt, name='purchase-orders-confirm-receipt'),
    path('purchase-orders/<int:pk>/cancel/', purchase_order_cancel, name='purchase-orders-cancel'),

    # PO items CRUD
    path('purchase-order-items/', purchase_order_item_list, name='purchase-order-items-list'),
    path('purchase-order-items/<int:pk>/', purchase_order_item_detail, name='purchase-order-items-detail'),

    # PO CRUD
    path('purchase-orders/', purchase_order_list, name='purchase-orders-list'),
    path('purchase-orders/<int:pk>/', purchase_order_detail, name='purchase-orders-detail'),
]
