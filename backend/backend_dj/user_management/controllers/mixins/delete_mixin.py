"""
Delete Mixin for User Management
Handles DELETE requests for removing users and addresses
"""
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from helper.auth_decorators import jwt_authentication, role_required
from ...models import User


class DeleteMixin:
    """Mixin to handle deletion (DELETE) for users and addresses"""

    @jwt_authentication
    @role_required(["admin"])
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        DELETE /api/users/<id>/
        Admin only.
        @jwt_authentication handles token validation + auto-refresh.
        @role_required(["admin"]) checks is_admin_role / is_staff.
        """
        instance = self.get_object()  # type: ignore
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance: Any) -> None:
        pk = getattr(instance, 'pk', None) or getattr(instance, 'id', None)
        instance.delete()
        # Invalidate list + specific user detail cache
        from helper.cache_helpers import invalidate_users_cache
        from django.core.cache import cache
        if pk:
            cache.delete(f"users_detail:{pk}")
        invalidate_users_cache()
