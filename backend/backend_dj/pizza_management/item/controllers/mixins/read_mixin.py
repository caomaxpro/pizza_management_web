import hashlib
import json
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from pizza_management.item.model import Item
from pizza_management.item.validators import ItemFilterRequest
from pizza_management.item.serializers import ItemSerializer
from helper.cache_helpers import CacheHelper, cache_response
from helper.auth_decorators import jwt_authentication

logger = logging.getLogger(__name__)


class ItemPagination(PageNumberPagination):
    """Custom pagination for items"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReadMixin:
    """Mixin for READ operations: list, retrieve, filter_items"""

    @jwt_authentication
    @cache_response(key_prefix="items_list", use_query_params=True, timeout=300)
    def list(self, request, *args, **kwargs):
        """GET /items/ - List all items with filtering (ADMIN ONLY)"""
        logger.info("=== LIST ITEMS REQUEST ===")
        
        # Build cache key from query params
        query_params = dict(request.GET)
        params_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()[:8]
        cache_key = f"items_list:all:params_{params_hash}"
        
        # Try to get from cache
        cached_data = CacheHelper.cache_get(cache_key)
        if cached_data is not None:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)
        
        logger.debug(f"Query params: {request.GET}")

        try:
            is_active_param = request.GET.get("is_active")
            if is_active_param and isinstance(is_active_param, str):
                is_active_param = is_active_param.lower() in ("true", "1", "yes")
            else:
                is_active_param = None

            filters = ItemFilterRequest(
                name=request.GET.get("name"),
                type=request.GET.get("type"),
                is_active=is_active_param,
            )
        except Exception:
            filters = ItemFilterRequest()

        queryset = Item.objects.all()

        if filters.name:
            queryset = queryset.filter(name__icontains=filters.name)
        if filters.type:
            queryset = queryset.filter(type=filters.type)
        if filters.is_active is not None:
            queryset = queryset.filter(is_active=filters.is_active)

        logger.debug(f"Total items: {queryset.count()}")
        serializer = ItemSerializer(queryset, many=True)
        
        # Cache the response
        CacheHelper.cache_set(cache_key, serializer.data, timeout=300)  # 5 minutes
        logger.debug(f"[CACHE MISS] Cached {cache_key} for 300s")
        logger.info("=== LIST SUCCESS ===")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @jwt_authentication
    @cache_response(key_prefix="items_detail", pk_in_key=True, use_query_params=False, timeout=30)
    def retrieve(self, request, *args, **kwargs):
        """GET /items/{id}/ - Get single item (ADMIN ONLY)"""
        logger.info("=== RETRIEVE ITEM REQUEST ===")
        item_id = kwargs.get("pk")
        logger.debug(f"Item ID: {item_id}")
        
        # Build cache key
        cache_key = f"items_detail:id_{item_id}"
        
        # Try to get from cache
        cached_data = CacheHelper.cache_get(cache_key)
        if cached_data is not None:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            item = Item.objects.get(id=item_id)
            logger.info(f"Item found: {item.id} - {item.name}")
            serializer = ItemSerializer(item)
            
            # Cache the response
            CacheHelper.cache_set(cache_key, serializer.data, timeout=30)  # 30 seconds (short TTL for frequently updated detail views)
            logger.debug(f"[CACHE MISS] Cached {cache_key} for 30s")
            logger.info("=== RETRIEVE SUCCESS ===")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Item.DoesNotExist:
            logger.warning(f"Item {item_id} not found")
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"])
    @jwt_authentication
    @cache_response(key_prefix="items_filter", use_query_params=True, timeout=300)
    def filter_items(self, request):
        """GET /items/filter-items/?name=xxx&category=pizza&type=pizza&price_min=10&price_max=20&is_active=true (ADMIN ONLY)"""
        # Build cache key from query params
        query_params = dict(request.GET)
        params_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()[:8]
        cache_key = f"items_filter:params_{params_hash}"
        
        # Try to get from cache
        cached_data = CacheHelper.cache_get(cache_key)
        if cached_data is not None:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)
        
        try:
            filters = ItemFilterRequest(
                name=request.GET.get("name"),
                type=request.GET.get("type"),
                is_active=self._parse_bool(request.GET.get("is_active")),
            )
        except Exception:
            filters = ItemFilterRequest()

        price_min = request.GET.get("price_min")
        price_max = request.GET.get("price_max")

        queryset = Item.objects.all()

        if filters.name:
            queryset = queryset.filter(name__icontains=filters.name)
        if filters.type:
            queryset = queryset.filter(type=filters.type)
        if filters.is_active is not None:
            queryset = queryset.filter(is_active=filters.is_active)
        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except ValueError:
                pass

        serializer = ItemSerializer(queryset, many=True)
        
        # Cache the response
        CacheHelper.cache_set(cache_key, serializer.data, timeout=300)  # 5 minutes
        logger.debug(f"[CACHE MISS] Cached {cache_key} for 300s")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    @jwt_authentication
    @cache_response(key_prefix="items_paginated", use_query_params=True, timeout=300)
    def get_paginated_items(self, request):
        """GET /items/get-paginated-items/?page=1&page_size=20&search=xxx&category=pizza&status=active&price_min=5&price_max=20
        Get paginated items with optional filtering"""

        logger.info("[get_paginated_items] Called")
        logger.debug(f"[get_paginated_items] Query params: {request.GET}")
        
        # Build cache key from query params (including page)
        query_params = dict(request.GET)
        params_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()[:8]
        cache_key = f"items_paginated:params_{params_hash}"
        
        # Try to get from cache
        cached_data = CacheHelper.cache_get(cache_key)
        if cached_data is not None:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)
        
        queryset = Item.objects.all().order_by('-created_at')
        
        # Apply filters from query parameters
        search = request.GET.get('search', '').strip()
        item_type = request.GET.get('type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        price_min = request.GET.get('price_min', '').strip()
        price_max = request.GET.get('price_max', '').strip()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        if item_type:
            queryset = queryset.filter(type=item_type)
            
        if status_filter and status_filter != 'all':
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
                
        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except (ValueError, TypeError):
                logger.warning(f"[get_paginated_items] Invalid price_min: {price_min}")
                
        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except (ValueError, TypeError):
                logger.warning(f"[get_paginated_items] Invalid price_max: {price_max}")
        
        logger.debug(f"[get_paginated_items] Total matching: {queryset.count()}")
        
        # Apply pagination
        paginator = ItemPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            paginated_queryset = []
        
        serializer = ItemSerializer(paginated_queryset, many=True)
        paginated_response = paginator.get_paginated_response(serializer.data)
        
        # Cache the response
        CacheHelper.cache_set(cache_key, paginated_response.data, timeout=300)  # 5 minutes
        logger.debug(f"[CACHE MISS] Cached {cache_key} for 300s")
        logger.info(f"[get_paginated_items] Returned {len(paginated_queryset)} items")
        return paginated_response

    def _parse_bool(self, value):
        """Helper to parse boolean query parameters"""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)