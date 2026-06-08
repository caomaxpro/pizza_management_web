from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from pizza_management.ingredient.model import Ingredient
from pizza_management.ingredient.validators import IngredientFilterRequest
from pizza_management.ingredient.serializers import IngredientSerializer
from helper.cache_helpers import cache_response
import logging

logger = logging.getLogger(__name__)


class IngredientPagination(PageNumberPagination):
    """Custom pagination for ingredients"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ReadMixin:
    """Mixin for READ operations: list, get_all_items, get_many_items, get_item, filter_ingredients"""

    @cache_response(key_prefix="ingredients_list", use_query_params=True)
    def list(self, request, *args, **kwargs):
        """GET /ingredients/ - List all ingredients with filtering (PUBLIC)"""
        logger.debug("=== LIST INGREDIENTS REQUEST ===")
        logger.debug(f"Query params: {request.GET}")

        try:
            is_active_param = request.GET.get("is_active")
            if is_active_param and isinstance(is_active_param, str):
                is_active_param = is_active_param.lower() in ("true", "1", "yes")
            else:
                is_active_param = None

            filters = IngredientFilterRequest(
                name=request.GET.get("name"),
                type=request.GET.get("type"),
                is_active=is_active_param,
            )
        except Exception:
            filters = IngredientFilterRequest()

        queryset = Ingredient.objects.all()

        if filters.name:
            queryset = queryset.filter(name__icontains=filters.name)
        if filters.type:
            queryset = queryset.filter(type=filters.type)
        if filters.is_active is not None:
            queryset = queryset.filter(is_active=filters.is_active)

        logger.debug(f"Total ingredients: {queryset.count()}")
        logger.debug("=== LIST SUCCESS ===")
        return Response(IngredientSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    @cache_response(key_prefix="ingredients_all_items", use_query_params=False)
    def get_all_items(self, request):
        """GET /ingredients/get-all-items/ - Get all ingredients (PUBLIC)"""
        logger.debug("[get_all_items] Called")
        ingredients = Ingredient.objects.all()
        logger.debug(f"[get_all_items] Returned {ingredients.count()} ingredients")
        return Response(IngredientSerializer(ingredients, many=True).data)

    @cache_response(key_prefix="ingredients_paginated", use_query_params=True)
    def get_paginated_items(self, request):
        """GET /ingredients/get-paginated-items/?page=1&page_size=20&search=xxx&type=dough&sub_type=xxx&status=active&price_min=5&price_max=20
        Get paginated ingredients with optional filtering (PUBLIC)"""
        logger.debug("[get_paginated_items] Called")
        logger.debug(f"[get_paginated_items] Query params: {request.GET}")

        queryset = Ingredient.objects.all().order_by('-created_at')
        
        # Apply filters from query parameters
        search = request.GET.get('search', '').strip()
        ingredient_type = request.GET.get('type', '').strip()
        sub_type = request.GET.get('sub_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        price_min = request.GET.get('price_min', '').strip()
        price_max = request.GET.get('price_max', '').strip()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        if ingredient_type:
            queryset = queryset.filter(type=ingredient_type)
            
        if sub_type:
            queryset = queryset.filter(sub_type=sub_type)
            
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

        paginator = IngredientPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request) or []
        paginated_response = paginator.get_paginated_response(
            IngredientSerializer(paginated_queryset, many=True).data
        )
        logger.debug(f"[get_paginated_items] Returned {len(paginated_queryset)} items")
        return paginated_response

    def get_many_items(self, request):
        """GET /ingredients/get-many-items?ids=1,2,3 - Get multiple ingredients (PUBLIC)"""
        ids = request.query_params.getlist('ids')
        if not ids:
            return Response(
                {"error": "ids parameter required (e.g., ?ids=1,2,3)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = Ingredient.objects.filter(id__in=ids)
        serializer = IngredientSerializer(queryset, many=True)
        logger.debug(f"[get_many_items] Returned {queryset.count()} ingredients")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @cache_response(key_prefix="ingredients_detail", pk_in_key=True, use_query_params=False)
    def get_item(self, request, pk=None):
        """GET /ingredients/{id}/get-item/ - Get single ingredient (PUBLIC)"""
        logger.debug(f"[get_item] Called with pk={pk}")
        try:
            ingredient = Ingredient.objects.get(pk=pk)
            logger.debug(f"[get_item] Found ingredient: {ingredient.name}")
            return Response(IngredientSerializer(ingredient).data)
        except Ingredient.DoesNotExist:
            logger.warning(f"[get_item] Ingredient with id {pk} not found")
            return Response(
                {"error": f"Ingredient with id {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @cache_response(key_prefix="ingredients_filter", use_query_params=True)
    def filter_ingredients(self, request):
        """GET /ingredients/filter-ingredients/?name=xxx&type=dough&price_min=5&price_max=20 (PUBLIC)"""
        try:
            filters = IngredientFilterRequest(
                name=request.GET.get("name"),
                type=request.GET.get("type"),
                is_active=self._parse_bool(request.GET.get("is_active")),
            )
        except Exception:
            filters = IngredientFilterRequest()
    
        price_min = request.GET.get("price_min")
        price_max = request.GET.get("price_max")
    
        queryset = Ingredient.objects.all()
    
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
    
        serializer = IngredientSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _parse_bool(self, value):
        """Helper to parse boolean query parameters"""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)