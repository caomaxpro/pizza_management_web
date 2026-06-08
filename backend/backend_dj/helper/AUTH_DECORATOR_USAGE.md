# Authentication Decorator Usage Guide

## Overview
Custom `@require_token` decorator cho token validation và auto-refresh.

### Luồng xử lý:
```
1. Extract token (từ cookies hoặc Authorization header)
2. Validate access token
   ✓ Valid → Validate user → Cho phép view chạy
   ✗ Invalid/Expired → Bước 3
3. Nếu token hết hạn:
   - Kiểm tra refresh token
   - Nếu refresh OK → Cấp lại access token → Validate user → Cho phép view chạy
   - Nếu refresh fail → Trả lỗi 401
4. Validate user (active, exists)
   ✓ Valid → Cho phép view chạy
   ✗ Invalid → Trả lỗi 403
5. Nếu có new access token → Attach vào response header "X-New-Access-Token"
```

---

## Usage Example

### Basic Function View
```python
from django.http import JsonResponse
from helper import require_token

@require_token
def get_user_profile(request):
    """
    Get user profile - requires valid token
    request.user will be automatically set to authenticated user
    """
    user = request.user
    return JsonResponse({
        'id': user.id,
        'email': user.email,
        'phone_number': user.phone_number,
    })
```

### ViewSet with require_token
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from helper import require_token

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    
    # DRF action decorator + custom require_token decorator
    @action(detail=False, methods=['get'])
    @require_token
    def my_items(self, request):
        """Get items for authenticated user"""
        user = request.user
        items = Item.objects.filter(created_by=user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
```

### Protecting specific endpoints
```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints (no token required)
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    
    # Protected endpoints (token required via decorator)
    path('api/profile/', views.get_user_profile, name='get_profile'),
    path('api/items/', views.list_items_view, name='list_items'),
]

# views.py
from helper import require_token

@require_token
def list_items_view(request):
    """Only accessible with valid token"""
    items = Item.objects.all()
    return Response(ItemSerializer(items, many=True).data)
```

---

## How Tokens are Handled

### 1. Access Token (15 minutes)
- Extracted from:
  - `request.COOKIES.get('access_token')` (preferred)
  - `Authorization: Bearer {token}` header (fallback)
- If valid → User authenticated, view executes
- If invalid/expired → Attempt refresh (step 2)

### 2. Refresh Token (7 days)
- Stored in `request.COOKIES.get('refresh_token')`
- Used to generate new access token if current one expired
- New token attached to response as `X-New-Access-Token` header
- Frontend should update its token storage with new token

### 3. User Validation
- Check if user exists in database
- Check if user is active (`is_active=True`)
- If not valid → Return 403 Forbidden

---

## Error Responses

| Scenario | HTTP Status | Response |
|----------|------------|----------|
| No token provided | 401 | `{"detail": "No token provided"}` |
| Token invalid/malformed | 401 | `{"detail": "Invalid or expired access token: ..."}` |
| Token expired, refresh failed | 401 | `{"detail": "Token expired and refresh failed"}` |
| User not active/invalid | 403 | `{"detail": "User is not valid or inactive"}` |

---

## Response Header

When token is refreshed, response includes:
```
X-New-Access-Token: eyJ0eXAiOiJKV1QiLCJhbGc...
```

Frontend should:
1. Read this header from response
2. Update stored token (localStorage, sessionStorage, state)
3. Use new token for future requests

---

## Logging

Decorator logs all token validation steps to `user_management` logger:
```python
import logging
logger = logging.getLogger('user_management')

# Enable debug logs to see token validation flow
logger.setLevel(logging.DEBUG)
```

Debug output example:
```
[require_token] Decorator called for /api/items/
[TokenValidator] Token found in cookies
[TokenValidator] Access token valid for user: user@example.com
[require_token] ✓ Authentication successful for user@example.com
```

---

## Comparison: Decorator vs DRF Authentication Class

| Feature | `@require_token` | `CookieJWTAuthentication` |
|---------|-----------------|--------------------------|
| Usage | Function/view wrapper | Permission class |
| Token validation | ✓ | ✓ |
| Auto-refresh | ✓ | ✓ |
| User validation | ✓ | ✗ (basic) |
| Response header | ✓ | Middleware required |
| Granular control | ✓ | Less control |
| Best for | Specific endpoints | Global auth |

**Recommendation:**
- Use `@require_token` on specific endpoints that need strict validation
- Use `CookieJWTAuthentication` as default auth class for consistent handling
- Combine both for defense-in-depth authentication
