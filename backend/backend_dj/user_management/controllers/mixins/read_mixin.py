"""
Read Mixin for User Management
Handles GET requests for retrieving users and addresses
"""
import hashlib
import json
from typing import Any
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.cache import cache

from rest_framework.pagination import PageNumberPagination
from helper.auth_decorators import jwt_authentication, role_required
from ...throttles import UserListUserThrottle, UserListIpThrottle


class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200

# Cache TTL for user list/detail (seconds)
_USERS_LIST_TTL = 60    # 1 min — short enough to reflect changes quickly
_USERS_DETAIL_TTL = 120  # 2 min


def _users_list_cache_key(params: dict) -> str:
    params_str = json.dumps(params, sort_keys=True)
    h = hashlib.md5(params_str.encode()).hexdigest()[:12]
    return f"users_list:{h}"


def _users_detail_cache_key(pk: Any) -> str:
    return f"users_detail:{pk}"


class ReadMixin:
    """Mixin to handle retrieval (GET) for users and addresses"""

    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        GET /api/users/
        Supports query params:  search, role, status, ordering, page, page_size
        Throttled: 60/min per user · 30/min per IP.
        Cached in Redis for 60 s (key includes all query params).
        """
        # --- throttle check ---
        for throttle_cls in (UserListIpThrottle, UserListUserThrottle):
            throttle = throttle_cls()
            if not throttle.allow_request(request, self):  # type: ignore
                wait = throttle.wait()
                return Response(
                    {"detail": f"Request was throttled. Try again in {int(wait or 0)} seconds."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        # --- cache lookup ---
        params = dict(request.query_params)
        cache_key = _users_list_cache_key(params)
        cached = cache.get(cache_key)
        if cached is not None:
            print(f"[CACHE HIT] {cache_key}")
            return Response(cached)

        # --- queryset with server-side filtering ---
        queryset = self.filter_queryset(self.get_queryset())  # type: ignore

        # search: email or username substring
        search = request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(username__icontains=search)
            )

        # role filter
        role = request.query_params.get("role", "").strip()
        if role and role != "all":
            queryset = queryset.filter(role=role)

        # status filter: active / inactive
        user_status = request.query_params.get("status", "").strip()
        if user_status == "active":
            queryset = queryset.filter(is_active=True)
        elif user_status == "inactive":
            queryset = queryset.filter(is_active=False)

        # ordering
        ordering = request.query_params.get("ordering", "username")
        allowed_ordering = {"username", "-username", "email", "-email",
                            "role", "-role", "date_joined", "-date_joined",
                            "is_active", "-is_active"}
        if ordering not in allowed_ordering:
            ordering = "username"
        queryset = queryset.order_by(ordering)

        page = self.paginate_queryset(queryset)  # type: ignore
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # type: ignore
            response = self.get_paginated_response(serializer.data)  # type: ignore
            cache.set(cache_key, response.data, _USERS_LIST_TTL)
            print(f"[CACHE MISS] Cached {cache_key} for {_USERS_LIST_TTL}s")
            return response

        serializer = self.get_serializer(queryset, many=True)  # type: ignore
        cache.set(cache_key, serializer.data, _USERS_LIST_TTL)
        print(f"[CACHE MISS] Cached {cache_key} for {_USERS_LIST_TTL}s")
        return Response(serializer.data)

    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        GET /api/users/<id>/
        Cached per-user-id for 2 min.
        """
        pk = kwargs.get(getattr(self, 'lookup_field', 'pk'), kwargs.get('pk'))  # type: ignore
        cache_key = _users_detail_cache_key(pk)
        cached = cache.get(cache_key)
        if cached is not None:
            print(f"[CACHE HIT] {cache_key}")
            return Response(cached)

        instance = self.get_object()  # type: ignore
        serializer = self.get_serializer(instance)  # type: ignore
        cache.set(cache_key, serializer.data, _USERS_DETAIL_TTL)
        print(f"[CACHE MISS] Cached {cache_key} for {_USERS_DETAIL_TTL}s")
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='employees', permission_classes=[])
    @jwt_authentication
    @role_required(['admin', 'manager', 'staff'])
    def employees(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        GET /api/users/employees/

        Return all non-customer users (admin, manager, staff).
        Used for general employee listing across the application.

        Accessible to: admin, manager, staff.
        """
        from ...models import User
        qs = User.objects.filter(role__in=['admin', 'manager', 'staff']).order_by('username')
        serializer = self.get_serializer(qs, many=True)  # type: ignore
        return Response(serializer.data)
