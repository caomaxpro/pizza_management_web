"""
Example URL configuration demonstrating how to use @require_token decorator
This file shows how to integrate decorated views into your URL routing
"""
from django.urls import path
from . import views_example

app_name = 'item_views_example'

urlpatterns = [
    # Protected endpoints - all require valid token via @require_token decorator
    path('user-items/', views_example.get_user_items, name='get_user_items'),
    path('item/<int:item_id>/', views_example.get_item_by_id, name='get_item_by_id'),
    path('create/', views_example.create_item_authenticated, name='create_item'),
    path('paginated/', views_example.list_items_paginated, name='list_paginated'),
    path('protected/', views_example.protected_endpoint, name='protected_endpoint'),
    
    # Admin-only endpoints - require token + is_staff=True
    path('admin/dashboard/', views_example.admin_dashboard, name='admin_dashboard'),
    path('admin/item/<int:item_id>/delete/', views_example.delete_item_admin, name='delete_item_admin'),
    
    # Staff-only endpoints - require token + is_staff=True (same as admin)
    path('staff/moderation/', views_example.staff_moderation_panel, name='staff_moderation_panel'),
    
    # Flexible permission endpoints
    path('superuser/endpoint/', views_example.superuser_only_endpoint, name='superuser_endpoint'),
    path('staff/permission/', views_example.staff_permission_endpoint, name='staff_permission_endpoint'),
]

"""
How to integrate into main urls.py:

In your_project/urls.py:
    from django.urls import path, include
    
    urlpatterns = [
        # ... other routes
        path('api/items-example/', include('pizza_management.item.urls_example')),
    ]

Then access via:
    # Basic auth (user endpoints)
    GET  /api/items-example/user-items/
    GET  /api/items-example/item/1/
    POST /api/items-example/create/
    GET  /api/items-example/paginated/?page=1&page_size=10
    GET  /api/items-example/protected/
    
    # Admin endpoints (requires is_staff=True)
    GET  /api/items-example/admin/dashboard/
    DELETE /api/items-example/admin/item/1/delete/
    
    # Staff endpoints (identical to admin)
    GET  /api/items-example/staff/moderation/
    
    # Flexible permission endpoints
    GET  /api/items-example/superuser/endpoint/
    GET  /api/items-example/staff/permission/

All endpoints require valid JWT token in:
    - Cookie: access_token
    - Or Header: Authorization: Bearer {token}

If token is expired but refresh token is valid:
    - Decorator automatically refreshes token
    - Response includes: X-New-Access-Token header with new token
    - Frontend should update stored token

Error responses:
    - 401: No token, token invalid/expired, user inactive
    - 403: Permission denied (not admin/staff/superuser)
"""
