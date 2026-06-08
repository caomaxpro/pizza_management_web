"""
Cache helper utilities for Django views
Provides decorators and utility functions for caching API responses
"""

import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional
from django.core.cache import cache
from django.http import QueryDict
from rest_framework.response import Response


class CacheHelper:
    """Static methods for cache operations"""
    
    @staticmethod
    def make_cache_key(prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and params"""
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            if isinstance(arg, (int, str)):
                key_parts.append(str(arg))
            else:
                key_parts.append(json.dumps(arg, sort_keys=True, default=str))
        
        # Add kwargs (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (int, str, bool)):
                key_parts.append(f"{k}={v}")
            else:
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True, default=str)}")
        
        key = ":".join(key_parts)
        
        # Hash if too long (Redis key length limit is 512MB, but let's keep it reasonable)
        if len(key) > 200:
            hash_suffix = hashlib.md5(key.encode()).hexdigest()[:8]
            key = f"{prefix}:{hash_suffix}"
        
        return key
    
    @staticmethod
    def get_query_params_dict(request) -> dict:
        """Extract query parameters as dict"""
        if isinstance(request.GET, QueryDict):
            return request.GET.dict()
        return dict(request.GET)
    
    @staticmethod
    def cache_get(key: str, default: Any = None) -> Any:
        """Get from cache"""
        return cache.get(key, default)
    
    @staticmethod
    def cache_set(key: str, value: Any, timeout: int = 300) -> None:
        """Set cache"""
        cache.set(key, value, timeout)
    
    @staticmethod
    def cache_delete(key: str) -> None:
        """Delete from cache"""
        cache.delete(key)
    
    @staticmethod
    def cache_clear_pattern(pattern: str) -> None:
        """Clear all keys matching pattern using django-redis delete_pattern.
        Properly handles the Django cache key prefix (:1: version prefix).
        """
        try:
            cache.delete_pattern(pattern)  # type: ignore
        except Exception as e:
            print(f"Error clearing cache pattern {pattern}: {e}")

    @staticmethod
    def clear_image_cache_for_url(image_url: str) -> None:
        """Clear image processing cache for a specific image URL.
        Removes the cached Firebase URL associated with the source image URL.
        
        Args:
            image_url: The source image URL (before Firebase upload)
        """
        if not image_url:
            return
        
        # Generate cache key using same logic as image processor tasks
        cache_key = f"image_cache:{hashlib.sha256(image_url.encode()).hexdigest()[:16]}"
        CacheHelper.cache_delete(cache_key)
        print(f"[CACHE] Cleared image cache: {cache_key} for URL: {image_url}")


def cache_response(
    timeout: int = 300,
    key_prefix: str = "api",
    use_user: bool = False,
    use_query_params: bool = True,
    pk_in_key: bool = False,
    pk_kwarg: str = "pk",
):
    """
    Decorator to cache DRF view responses.

    Args:
        timeout: Cache timeout in seconds (default: 5 min)
        key_prefix: Prefix for cache key (e.g., "ingredients_list", "ingredients_detail")
        use_user: Include user ID in cache key (per-user caching)
        use_query_params: Hash query parameters into the cache key
        pk_in_key: Append ``id_<pk>`` to the key — use for detail views
        pk_kwarg: Name of the URL kwarg holding the primary key (default: "pk")

    Key patterns produced:
        list / filtered:  ``<prefix>:params_<hash>``
        detail:           ``<prefix>:id_<pk>``
        simple (no args): ``<prefix>``

    Example::

        @cache_response(key_prefix="ingredients_list", use_query_params=True)
        def list(self, request, *args, **kwargs): ...

        @cache_response(key_prefix="ingredients_detail", pk_in_key=True, use_query_params=False)
        def get_item(self, request, pk=None): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            cache_key_parts = [key_prefix]

            if use_user and request.user.is_authenticated:
                cache_key_parts.append(f"user_{request.user.id}")

            if pk_in_key:
                pk = kwargs.get(pk_kwarg)
                if pk is not None:
                    cache_key_parts.append(f"id_{pk}")

            if use_query_params:
                query_params = CacheHelper.get_query_params_dict(request)
                if query_params:
                    params_str = json.dumps(query_params, sort_keys=True)
                    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(f"params_{params_hash}")

            cache_key = ":".join(cache_key_parts)

            cached_response = cache.get(cache_key)
            if cached_response is not None:
                print(f"[CACHE HIT] {cache_key}")
                return Response(cached_response)

            response = view_func(self, request, *args, **kwargs)

            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                if hasattr(response, 'data'):
                    cache.set(cache_key, response.data, timeout)
                    print(f"[CACHE MISS] Cached {cache_key} for {timeout}s")

            return response

        return wrapper
    return decorator


def write_through_cache(
    detail_key_prefix: str,
    pk_kwarg: str = "pk",
    timeout: int = 300,
    list_invalidator: Optional[Callable] = None,
):
    """
    Decorator for write-through caching on single-item update views.

    After a successful response (2xx), pushes ``response.data`` into the detail
    cache at ``<detail_key_prefix>:id_<pk>`` so the next read is served from
    Redis without a DB roundtrip.  Optionally calls ``list_invalidator`` to
    keep list/filter/paginated caches consistent.

    Example::

        @write_through_cache(
            detail_key_prefix="ingredients_detail",
            list_invalidator=invalidate_ingredients_list_cache,
        )
        def update(self, request, *args, **kwargs): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)

            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                pk = kwargs.get(pk_kwarg)
                if pk is not None and hasattr(response, 'data'):
                    cache_key = f"{detail_key_prefix}:id_{pk}"
                    CacheHelper.cache_set(cache_key, response.data, timeout)
                    print(f"[CACHE] Write-through {cache_key}")
                if list_invalidator is not None:
                    list_invalidator()

            return response

        return wrapper
    return decorator


def invalidate_cache(*invalidators: Callable):
    """
    Decorator that calls each invalidator function after a successful write.

    Use on bulk-update views where per-item write-through is handled inside the
    view body but list/filter caches still need to be cleared.

    Example::

        @invalidate_cache(invalidate_ingredients_list_cache)
        def update_all(self, request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)

            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                for fn in invalidators:
                    fn()

            return response

        return wrapper
    return decorator


def invalidate_users_cache():
    """Clear all user-list-related cache entries"""
    try:
        for pattern in ["users_list:*", "users_detail:*"]:
            cache.delete_pattern(pattern)  # type: ignore
        print("[CACHE] Invalidated all users cache")
    except Exception as e:
        print(f"[CACHE ERROR] Failed to invalidate users cache: {e}")


def invalidate_items_cache():
    """Clear all item-related cache"""
    try:
        for pattern in ["items_list:*", "items_detail:*", "items_filter:*", "items_paginated:*"]:
            cache.delete_pattern(pattern)  # type: ignore
        print("[CACHE] Invalidated all items cache")
    except Exception as e:
        print(f"[CACHE ERROR] Failed to invalidate items cache: {e}")


def invalidate_ingredients_list_cache():
    """Clear ingredient list/filter/paginated caches only.
    
    Does NOT touch detail caches (ingredients_detail:id_*) so that
    write-through updates remain served from cache without a DB roundtrip.
    Call this after any write that modifies ingredient list query results.
    """
    try:
        for pattern in ["ingredients_list:*", "ingredients_paginated:*", "ingredients_filter:*"]:
            cache.delete_pattern(pattern)  # type: ignore
        # ingredients_all_items has no params suffix — delete directly
        cache.delete("ingredients_all_items")
        print("[CACHE] Invalidated ingredient list/filter/paginated caches")
    except Exception as e:
        print(f"[CACHE ERROR] Failed to invalidate ingredient list cache: {e}")
