# Custom Authentication Decorator - Implementation Summary

## 📋 Tổng quan triển khai

Đã tạo custom `@require_token` decorator cho validation token và auto-refresh function-based views.

---

## 📁 Files Tạo/Cập Nhật

### 1. **Core Decorator** 
- **File**: `backend_dj/helper/auth_decorators.py`
- **Nội dung**:
  - `TokenValidator` class: Helper để validate/refresh token
  - `@require_token` decorator: Wrapper cho views
  
- **Luồng**:
  ```
  Token từ cookies/header 
    → Validate access token
    → Nếu hết hạn: Refresh token
    → Validate user (active, exists)
    → Cho view chạy hoặc trả lỗi
  ```

### 2. **Helper Module Export**
- **File**: `backend_dj/helper/__init__.py`
- **Export**: `require_token`, `TokenValidator`

### 3. **Usage Documentation**
- **File**: `backend_dj/helper/AUTH_DECORATOR_USAGE.md`
- **Nội dung**: Hướng dẫn chi tiết, error responses, logging, comparison

### 4. **Example Views**
- **File**: `backend_dj/pizza_management/item/views_example.py`
- **Examples**:
  - Get user items
  - Get item by ID
  - Create item hỗ trợ auth
  - List with pagination
  - Protected endpoint

### 5. **Example URLs**
- **File**: `backend_dj/pizza_management/item/urls_example.py`
- **Integration guide**: Cách mount example routes

---

## 🚀 Quick Start

### Import & Use
```python
from helper import require_token

@require_token
def my_protected_view(request):
    user = request.user  # Tự động set bởi decorator
    # View logic...
    return Response(data)
```

### Request Flow
```
Client Request
    ↓
@require_token decorator (validate token)
    ├─ Token valid? → Continue
    ├─ Token expired? → Try refresh
    │   ├─ Refresh OK? → Continue + attach X-New-Access-Token header
    │   └─ Refresh fail? → 401 error
    └─ User invalid? → 403 error
    ↓
View executes (request.user = authenticated user)
    ↓
Response (with X-New-Access-Token if refreshed)
```

---

## 🔐 Token Handling

| Scenario | Action |
|----------|--------|
| Access token valid | View chạy bình thường |
| Access token expired, refresh token valid | Refresh token, update access token, view chạy |
| Access token + refresh token expired | 401 error |
| User not active | 403 error |
| No token provided | 401 error |

---

## 📝 Response Headers

Nếu token được refresh:
```
X-New-Access-Token: eyJ0eXAiOiJKV1QiLCJhbGc...
```

Frontend sẽ:
1. Đọc header này
2. Update token được lưu
3. Dùng token mới cho request tiếp theo

---

## 🛠️ Integration Steps

### Step 1: Use on specific views
```python
# views.py
from helper import require_token
from rest_framework.response import Response

@require_token
def my_api_endpoint(request):
    user = request.user
    # Your logic here
    return Response({'data': ...})
```

### Step 2: Add to URLs (optional routing)
```python
# urls.py
from . import views

urlpatterns = [
    path('api/protected-endpoint/', views.my_api_endpoint),
]
```

### Step 3: Test with token
```bash
# Get token from login endpoint first
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response contains access_token, refresh_token

# Use token to call protected endpoint
curl http://localhost:8000/api/protected-endpoint/ \
  -H "Authorization: Bearer {access_token}"

# Or use cookies
curl http://localhost:8000/api/protected-endpoint/ \
  -H "Cookie: access_token={token}; refresh_token={token}"
```

---

## ⚙️ Configuration

Token lifetimes (in `settings.py`):
- Access token: **15 minutes**
- Refresh token: **7 days**

Để đổi, update settings:
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    ...
}
```

---

## 📊 Logging

Enable logs để debug token flow:
```python
import logging

logger = logging.getLogger('user_management')
logger.setLevel(logging.DEBUG)

# Output sẽ show:
# [require_token] Decorator called for /api/endpoint/
# [TokenValidator] Token found in cookies
# [TokenValidator] Access token valid for user: user@example.com
# ...
```

---

## 🔄 Comparison: Decorator vs DRF Auth Class

| Feature | `@require_token` | `CookieJWTAuthentication` |
|---------|-----------------|--------------------------|
| Usage | View wrapper | Global auth class |
| Granular | ✓ | ✗ |
| Auto-refresh | ✓ | ✓ |
| User validation | ✓ | Basic |
| Response header | ✓ | Via middleware |

**Use together:**
- Global auth: `CookieJWTAuthentication` (default)
- Specific endpoints: `@require_token` (extra validation)

---

## 🎯 Error Examples

### No token
```json
{
  "detail": "No token provided"
}
```
**HTTP 401**

### Token expired, refresh failed
```json
{
  "detail": "Token expired and refresh failed"
}
```
**HTTP 401**

### User not active
```json
{
  "detail": "User is not valid or inactive"
}
```
**HTTP 403 (actually raised as AuthenticationFailed)**

---

## 📌 Notes

- Decorator extract token từ **cookies** trước, sau đó **Authorization header**
- Auto-refresh chỉ làm việc khi **refresh token còn hạn**
- Middleware tự động attach new token vào response nếu cần
- Decorator validate user **exists** và **active**
- Logging giúp debug token flow (enable DEBUG level)

---

## ✅ Status

- ✓ Decorator tạo + đầy đủ chức năng
- ✓ Usage docs + examples
- ✓ Ready to integrate
- ⏳ Waiting bạn test trên endpoints thực

---

## 🔗 Files Reference

- Core: [`backend_dj/helper/auth_decorators.py`](backend_dj/helper/auth_decorators.py)
- Init: [`backend_dj/helper/__init__.py`](backend_dj/helper/__init__.py)
- Docs: [`backend_dj/helper/AUTH_DECORATOR_USAGE.md`](backend_dj/helper/AUTH_DECORATOR_USAGE.md)
- Examples: [`pizza_management/item/views_example.py`](pizza_management/item/views_example.py)
- URLs: [`pizza_management/item/urls_example.py`](pizza_management/item/urls_example.py)
