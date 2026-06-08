"""
Update Mixin for User Management
Handles PUT/PATCH requests for updating users and addresses
"""
from typing import Any, cast
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request

from helper.auth_decorators import (
    jwt_authentication, rate_limit, role_required
)
from ...models import User, RoleTask, RoleChangeLog, ROLE_CHOICES


class UpdateMixin:
    """Mixin to handle updates (PUT/PATCH) for users and addresses"""
    
    @jwt_authentication
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update an instance (requires authentication)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()  # type: ignore
        serializer = self.get_serializer(instance, data=request.data, partial=partial)  # type: ignore
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @jwt_authentication
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partial update of an instance"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer: Any) -> None:
        serializer.save()
        # Write-through: ghi data mới vào cache detail thay vì chỉ xóa
        # → lần đọc tiếp theo sẽ cache HIT ngay, không cần query DB
        from helper.cache_helpers import invalidate_users_cache
        from django.core.cache import cache
        pk = getattr(serializer.instance, 'pk', None) or getattr(serializer.instance, 'id', None)
        if pk:
            try:
                from ...serializers import UserSerializer
                fresh_data = UserSerializer(serializer.instance).data
                cache.set(f"users_detail:{pk}", fresh_data, 120)
            except Exception:
                cache.delete(f"users_detail:{pk}")
        # List cache vẫn phải invalidate vì thứ tự/filter có thể thay đổi
        invalidate_users_cache()

    # ------------------------------------------------------------------ role

    @action(detail=True, methods=['patch'], url_path='assign-role', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def assign_role(self, request: Request, **kwargs: Any) -> Response:
        """
        PATCH /api/users/<id>/assign-role/
        Assign a business role to a user.  Admin or manager only.
        @jwt_authentication validates token + auto-refresh.
        @role_required(["admin", "manager"]) checks has_mgmt_access / is_staff.

        Body: { "role": "staff" }
        """
        caller = cast(User, request.user)
        new_role = cast(dict, request.data).get('role')
        valid_roles = [r[0] for r in ROLE_CHOICES]
        if new_role not in valid_roles:
            return Response(
                {'error': f'Invalid role. Choices: {valid_roles}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Managers cannot promote to admin
        if caller.role == 'manager' and new_role == 'admin':
            return Response({'error': 'Managers cannot assign the admin role'}, status=status.HTTP_403_FORBIDDEN)

        target = self.get_object()  # type: ignore
        old_role = target.role
        target.role = new_role
        target.save(update_fields=['role'])

        RoleChangeLog.objects.create(
            changed_by=caller,
            target_user=target,
            old_role=old_role,
            new_role=new_role,
        )

        from ...serializers import StaffUserSerializer
        return Response(StaffUserSerializer(target).data)

    # ------------------------------------------------------------------ assign task

    @action(detail=True, methods=['patch'], url_path='assign-task', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def assign_task(self, request: Request, **kwargs: Any) -> Response:
        """
        PATCH /api/users/<id>/assign-task/
        Assign or revoke per-staff task permissions.  Admin or manager only.
        Target user must have role 'staff'.

        Body: { "can_stock_take": true, "can_receive_stock": false }
        """
        target = self.get_object()  # type: ignore
        if target.role != 'staff':
            return Response(
                {'error': 'Task permissions can only be assigned to staff users.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = cast(dict, request.data)
        updated_fields: list[str] = []

        if 'can_stock_take' in data:
            target.can_stock_take = bool(data['can_stock_take'])
            updated_fields.append('can_stock_take')

        if 'can_receive_stock' in data:
            target.can_receive_stock = bool(data['can_receive_stock'])
            updated_fields.append('can_receive_stock')

        if not updated_fields:
            return Response(
                {'error': 'No valid fields provided. Use can_stock_take or can_receive_stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target.save(update_fields=updated_fields)

        from helper.cache_helpers import invalidate_users_cache
        from django.core.cache import cache
        cache.delete(f"users_detail:{target.pk}")
        invalidate_users_cache()

        from ...serializers import StaffUserSerializer
        return Response(StaffUserSerializer(target, context={'request': request}).data)

    # ------------------------------------------------------------------ tasks

    @action(detail=True, methods=['get'], url_path='tasks', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list_tasks(self, request: Request, **kwargs: Any) -> Response:
        """
        GET /api/users/<id>/tasks/
        List the tasks allowed for the user's current role.
        @jwt_authentication validates token + auto-refresh (any authenticated user).
        """
        target = self.get_object()  # type: ignore
        tasks = list(
            RoleTask.objects.filter(role=target.role, allowed=True)
            .select_related('task')
            .values('task__codename', 'task__name', 'task__description')
        )
        return Response({'role': target.role, 'tasks': tasks})

    # ------------------------------------------------------------------ password

    @action(
        detail=False, methods=['post'], url_path='change-password',
        permission_classes=[],
    )
    @jwt_authentication
    @rate_limit(limit=5, window=900, prefix='chpwd', scope='user')
    def change_password(self, request: Request, **kwargs: Any) -> Response:
        """
        POST /api/users/change-password/
        Any authenticated user can change their own password.
        Body: { "old_password": "...", "new_password": "..." }
        """
        user = cast(User, request.user)
        data = cast(dict, request.data)
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'status': 'Password changed successfully.'})
