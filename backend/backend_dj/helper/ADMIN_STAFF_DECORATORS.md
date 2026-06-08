# Admin/Staff Permission Decorators - Usage Guide

## Decorators Added

### 1. `@require_admin` - Admin-Only Access
Requires authenticated user with `is_staff=True`

```python
from helper import require_admin

@require_admin
def admin_dashboard(request):
    """Only accessible to staff/admin users"""
    user = request.user
    # Admin logic here
    return Response(data)
```

### 2. `@require_staff` - Staff-Only Access
Alias for `@require_admin` (checks same `is_staff` flag)

```python
from helper import require_staff

@require_staff
def staff_moderation(request):
    """Only accessible to staff users"""
    user = request.user
    # Staff logic here
    return Response(data)
```

### 3. `@require_permission` - Flexible Permission Check
Check any user attribute or permission

```python
from helper import require_permission

@require_permission('is_superuser')
def superuser_only(request):
    """Only accessible to superusers"""
    return Response(data)

@require_permission('is_staff')
def staff_endpoint(request):
    """Same as @require_staff"""
    return Response(data)

@require_permission('can_edit_items')
def edit_items(request):
    """Check custom permission"""
    return Response(data)
```

---

## Usage Examples

### Admin Dashboard
```python
from helper import require_admin

@require_admin
def admin_dashboard(request):
    """
    Admin-only dashboard view
    - Requires valid token
    - Requires is_staff=True
    """
    user = request.user
    return JsonResponse({
        'message': f'Welcome Admin {user.email}',
        'is_admin': user.is_staff,
        'is_superuser': user.is_superuser,
    })
```

### Admin-Only Delete
```python
from helper import require_admin

@api_view(['DELETE'])
@require_admin
def delete_item_admin(request, item_id):
    """
    Admin can delete any item (not just own)
    - Requires token + is_staff=True
    """
    item = Item.objects.get(id=item_id)
    item.delete()
    return Response({'message': 'Item deleted'})
```

### Staff Moderation Panel
```python
from helper import require_staff

@require_staff
def moderation_panel(request):
    """Staff-only moderation panel"""
    items = Item.objects.all()
    return Response({
        'items': ItemSerializer(items, many=True).data,
        'total': items.count()
    })
```

### Flexible Custom Permission
```python
from helper import require_permission

@require_permission('is_superuser')
def system_admin_endpoint(request):
    """Only superusers can access"""
    return Response({'data': 'system info'})

# Or check custom permission from User model
@require_permission('can_manage_prices')
def manage_prices(request):
    """Check custom boolean field on User"""
    return Response({'prices': []})
```

---

## How They Work

### `@require_admin` / `@require_staff` Flow

```
1. Extract token
   ↓
2. Validate token (expired? → refresh)
   ↓
3. Validate user (active? exists?)
   ↓
4. ⭐ Check user.is_staff == True
   ├─ YES → Continue to view
   └─ NO → Raise "Admin access required" (401/403)
   ↓
5. Execute view
```

### `@require_permission(permission_name)` Flow

```
1. Extract token
   ↓
2. Validate token (expired? → refresh)
   ↓
3. Validate user (active? exists?)
   ↓
4. ⭐ Check hasattr(user, permission_name) and getattr(user, permission_name)
   ├─ YES → Continue to view
   └─ NO → Raise "Permission '{name}' required" (401/403)
   ↓
5. Execute view
```

---

## User Fields Checked

### Standard Django User Fields

| Field | Type | Checked By |
|-------|------|-----------|
| `is_staff` | bool | `@require_admin`, `@require_staff`, `@require_permission('is_staff')` |
| `is_superuser` | bool | `@require_permission('is_superuser')` |
| `is_active` | bool | All decorators (via `TokenValidator.validate_user`) |

### Custom User Fields

If you have custom boolean fields on your User model:

```python
# models.py
class User(AbstractUser):
    is_staff = models.BooleanField(default=False)  # Django standard
    can_edit_items = models.BooleanField(default=False)  # Custom
    can_manage_prices = models.BooleanField(default=False)  # Custom
    can_delete_users = models.BooleanField(default=False)  # Custom
```

Then use `@require_permission`:

```python
@require_permission('can_edit_items')
def edit_items_view(request):
    ...

@require_permission('can_manage_prices')
def pricing_view(request):
    ...

@require_permission('can_delete_users')
def delete_user_view(request):
    ...
```

---

## Error Responses

### All Decorators (Token/User Issues)

| Issue | HTTP Status | Response |
|-------|------------|----------|
| No token provided | 401 | `{"detail": "No token provided"}` |
| Token invalid/expired | 401 | `{"detail": "Invalid or expired access token: ..."}` |
| Token + refresh expired | 401 | `{"detail": "Token expired and refresh failed"}` |
| User not active | 403 | `{"detail": "User is not valid or inactive"}` |

### Permission Errors

| Decorator | Condition | HTTP Status | Response |
|-----------|-----------|------------|----------|
| `@require_admin` | `user.is_staff != True` | 403 | `{"detail": "Admin access required"}` |
| `@require_staff` | `user.is_staff != True` | 403 | `{"detail": "Admin access required"}` |
| `@require_permission('field')` | `getattr(user, 'field') != True` | 403 | `{"detail": "Permission 'field' required"}` |

---

## URL Routing Examples

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('auth/login/', views.login, name='login'),
    
    # User endpoints (token required)
    path('api/profile/', views.get_profile, name='get_profile'),
    path('api/items/', views.get_items, name='get_items'),
    
    # Admin endpoints (token + is_staff)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.list_all_users, name='list_all_users'),
    path('admin/delete-item/<int:id>/', views.delete_item_admin, name='delete_item_admin'),
    
    # Staff endpoints (token + is_staff)
    path('staff/moderation/', views.moderation_panel, name='moderation_panel'),
    
    # Superuser endpoints
    path('system/admin/', views.system_admin, name='system_admin'),
]
```

---

## Decorator Stacking

You can combine decorators:

```python
from helper import require_admin
from rest_framework.decorators import api_view

@api_view(['POST', 'DELETE'])
@require_admin
def admin_operation(request):
    """Admin-only API endpoint"""
    if request.method == 'POST':
        # Create
        pass
    else:
        # Delete
        pass
    return Response(data)
```

Order matters:
- Inner decorator runs first: `@require_admin`
- Outer decorator runs after: `@api_view`

---

## Logging & Debugging

Enable debug logs to see permission checks:

```python
import logging

logger = logging.getLogger('user_management')
logger.setLevel(logging.DEBUG)

# Output will show:
# [require_admin] Decorator called for /admin/dashboard/
# [TokenValidator] Token found in cookies
# [TokenValidator] Access token valid for user: admin@example.com
# [require_admin] ✓ Admin authentication successful for admin@example.com
```

---

## Best Practices

### 1. Use Specific Decorators
```python
# Good ✓
@require_admin
def admin_view(request):
    pass

# Also good ✓
@require_permission('can_edit_items')
def edit_view(request):
    pass

# Less clear ✗
@require_permission('is_staff')  # Just use @require_admin instead
def admin_view(request):
    pass
```

### 2. Order Decorators Correctly
```python
# Good ✓
@api_view(['POST', 'DELETE'])
@require_admin
def admin_api(request):
    pass

# Avoid ✗ (decorators might conflict)
@require_admin
@api_view(['POST'])
def admin_api(request):
    pass
```

### 3. Document Requirements
```python
@require_admin
def admin_operation(request):
    """
    Admin-only operation
    
    Requires:
    - Valid JWT token
    - is_staff=True
    
    Returns:
    - 200: Operation successful
    - 401: No/invalid token
    - 403: Not admin
    """
    pass
```

---

## Testing

```python
# tests.py
from django.test import TestCase, Client
from user_management.models import User

class AdminDecoratorTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create regular user
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password'
        )
        # Create admin user
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='password',
            is_staff=True  # Make admin
        )
    
    def test_admin_endpoint_without_token(self):
        response = self.client.get('/admin/dashboard/')
        self.assertEqual(response.status_code, 401)
    
    def test_admin_endpoint_as_regular_user(self):
        # Login as regular user (get token)
        login_response = self.client.post('/auth/login/', {
            'email': 'user@example.com',
            'password': 'password'
        })
        token = login_response.json()['access_token']
        
        # Try to access admin endpoint
        response = self.client.get(
            '/admin/dashboard/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_admin_endpoint_as_admin(self):
        # Login as admin
        login_response = self.client.post('/auth/login/', {
            'email': 'admin@example.com',
            'password': 'password'
        })
        token = login_response.json()['access_token']
        
        # Access admin endpoint
        response = self.client.get(
            '/admin/dashboard/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
```
