"""
Create Mixin for User Management
Handles POST requests for creating new users and addresses
"""
from typing import Any, cast
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.settings import api_settings

from helper.auth_decorators import jwt_authentication, role_required, rate_limit, captcha_guard
from ...models import User


class CreateMixin:
    """Mixin to handle creation (POST) for users and addresses"""

    @rate_limit(limit=10, window=3600, prefix='cstaff', scope='ip+user')
    @captcha_guard()
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        POST /api/users/
        Create a customer account (open, no auth required).
        The role is always forced to 'customer' — cannot be overridden here.
        """
        serializer = self.get_serializer(data=request.data)  # type: ignore
        serializer.is_valid(raise_exception=True)
        serializer.save(role='customer')   # enforce customer role regardless of input
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer: Any) -> None:
        instance = serializer.save()
        # Write-through: warm detail cache ngay sau khi tạo
        # → nếu ai GET /users/:pk/ ngay sau đó sẽ là cache HIT, không query DB
        try:
            from django.core.cache import cache
            from ...serializers import UserSerializer
            pk = getattr(instance, 'pk', None) or getattr(instance, 'id', None)
            if pk:
                cache.set(f"users_detail:{pk}", UserSerializer(instance).data, 120)
        except Exception:
            pass  # cache warm thất bại không ảnh hưởng đến response
        # Invalidate list cache (pagination/filter/sort thay đổi khi có user mới)
        from helper.cache_helpers import invalidate_users_cache
        invalidate_users_cache()

    def get_success_headers(self, data: dict) -> dict:
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    # ------------------------------------------------------------------ staff

    @action(
        detail=False,
        methods=['post'],
        url_path='create-staff',
        permission_classes=[],
    )
    @jwt_authentication
    @role_required(["admin", "manager"])
    # @rate_limit(limit=10, window=3600, prefix='cstaff', scope='ip+user')  # Disabled for testing
    # @captcha_guard()  # Disabled for testing
    def create_staff(self, request: Request) -> Response:
        """
        POST /api/users/create-staff/
        Create a staff/manager account.  Admin or manager only.
        @jwt_authentication validates token + auto-refresh.
        @role_required(["admin", "manager"]) checks has_mgmt_access / is_staff.

        Body: { username, email, password, first_name?, last_name?, phone_number?, role }
        Allowed roles: staff (manager), staff + manager (admin)
        """
        caller = cast(User, request.user)
        requested_role = cast(dict, request.data).get('role', 'staff')

        if requested_role == 'customer':
            return Response(
                {'error': 'Use the standard register endpoint to create customer accounts'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No one can create admin accounts via this endpoint
        if requested_role == 'admin':
            return Response(
                {'error': 'Admin accounts cannot be created via this endpoint'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Managers can only create staff, not other managers
        if caller.role == 'manager' and requested_role != 'staff':
            return Response(
                {'error': 'Managers can only create staff accounts'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from ...serializers import StaffUserSerializer
        serializer = StaffUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


