from django.urls import path

def get_patterns():
    """Defer import để tránh circular dependency"""
    from pizza_management.item.controllers.viewset import ItemViewSet
    
    return [
        # Items
        path('', ItemViewSet.as_view({'get': 'list', 'post': 'create'}), name='item-list'),
        path('create/', ItemViewSet.as_view({'post': 'create'}), name='item-create'),
        path('get-paginated-items/', ItemViewSet.as_view({'get': 'get_paginated_items'}), name='item-get-paginated'),
        path('filter-items/', ItemViewSet.as_view({'get': 'filter_items'}), name='item-filter'),
        path('update-all/', ItemViewSet.as_view({'patch': 'update_all'}), name='item-update-all'),
        path('adjust-prices/', ItemViewSet.as_view({'patch': 'adjust_prices'}), name='item-adjust-prices'),
        path('update-many/', ItemViewSet.as_view({'post': 'update_many'}), name='item-update-many'),
        path('delete-many/', ItemViewSet.as_view({'post': 'delete_many'}), name='item-delete-many'),
        path('delete-all/', ItemViewSet.as_view({'post': 'delete_all'}), name='item-delete-all'),
        path('import-json/', ItemViewSet.as_view({'post': 'import_json'}), name='item-import'),
        path('cancel-import/', ItemViewSet.as_view({'post': 'cancel_import'}), name='item-cancel-import'),
        path('<int:pk>/', ItemViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='item-detail'),
        path('<int:pk>/delete/', ItemViewSet.as_view({'delete': 'destroy'}), name='item-delete'),
    ]

urlpatterns = get_patterns()