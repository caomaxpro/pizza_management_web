"""
User Management ViewSet
REST API endpoints for user operations
"""
from typing import Any, cast

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.request import Request

from .mixins import CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, AuthMixin, ScheduleMixin
from .mixins.read_mixin import UserPagination
from ..models import User, Address, WorkSchedule
from helper.auth_decorators import jwt_authentication, role_required
from ..serializers import UserSerializer, StaffUserSerializer, AddressSerializer
from ..services import UserService
from ..permissions import AutoRoleTaskPermission


class IsOwnerOrStaff(BasePermission):
    """Permission to check if user is owner or staff"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user owns the object or is staff"""
        user: User = cast(User, request.user)
        return obj.id == user.id or user.is_staff


class UserViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """ViewSet for User operations"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserPagination
    lookup_field = 'id'
    # Actions that skip the AutoRoleTaskPermission check (open endpoints)
    task_bypass_actions = {'create', 'assignable', 'employees'}

    def get_permissions(self) -> list:
        """Customize permissions per-action.

        - `create` remains open for self-registration (AllowAny).
        - actions in `task_bypass_actions` (e.g. `assignable`) require only
          authentication and should skip the AutoRoleTaskPermission check.
        - all other actions require both authentication and the
          AutoRoleTaskPermission guard.
        """
        if self.action == 'create':
            return [AllowAny()]
        if self.action in getattr(self, 'task_bypass_actions', set()):
            return [IsAuthenticated()]
        return [IsAuthenticated(), AutoRoleTaskPermission()]

    def get_serializer_class(self) -> type:
        """Use StaffUserSerializer for admin/manager-facing write and detail views."""
        if self.action in ('create_staff', 'assign_role', 'list_tasks'):
            return StaffUserSerializer
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'has_mgmt_access', False):
            return StaffUserSerializer
        return UserSerializer

    def get_queryset(self) -> Any:
        """Filter users - own profile for regular users, all for staff/admin/manager"""
        user: User = cast(User, self.request.user)
        if user.is_staff or getattr(user, 'has_mgmt_access', False):
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request: Request) -> Response:
        """Get current user profile"""
        user: User = cast(User, request.user)
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_password(self, request: Request, id: int | None = None) -> Response:
        """Change user password"""
        user = self.get_object()
        
        if not request.data.get('old_password') or not request.data.get('new_password'):
            return Response(
                {'error': 'old_password and new_password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(request.data.get('old_password')):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(request.data.get('new_password'))
        user.save()
        return Response({'status': 'password changed'})

    @action(detail=False, methods=['get'], url_path='assignable', permission_classes=[])
    @jwt_authentication
    @role_required(['admin', 'manager', 'staff'])
    def assignable(self, request: Request) -> Response:
        """
        GET /api/users/assignable/

        Return all users whose role is 'admin', 'manager', or 'staff'
        (i.e. anyone who can be assigned a work schedule).
        Customers are excluded.

        Accessible to: admin, manager, staff.
        """
        qs = User.objects.filter(role__in=['admin', 'manager', 'staff']).order_by('username')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class AddressViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """ViewSet for Address operations"""
    
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self) -> Any:
        """Filter addresses - own addresses for regular users, all for staff"""
        user: User = cast(User, self.request.user)
        if user.is_staff:
            return Address.objects.all()
        return Address.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Set user when creating address"""
        user: User = cast(User, self.request.user)
        serializer.save(user=user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request: Request, id: int | None = None) -> Response:
        """Set address as default"""
        address = self.get_object()
        
        # Clear other defaults for this user
        Address.objects.filter(user=address.user).update(is_default=False)
        
        # Set this as default
        address.is_default = True
        address.save()
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)


class AuthViewSet(AuthMixin, viewsets.ViewSet):
    """ViewSet for authentication operations (login, logout, register)"""
    
    queryset = User.objects.none()
    serializer_class = UserSerializer
    lookup_field = 'id'


class WorkScheduleViewSet(ScheduleMixin, viewsets.ViewSet):
    """ViewSet for WorkSchedule CRUD operations."""

    lookup_field = 'pk'
