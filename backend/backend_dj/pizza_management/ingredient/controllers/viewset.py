from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from pizza_management.ingredient.model import Ingredient
from pizza_management.ingredient.serializers import IngredientSerializer
from pizza_management.ingredient.controllers.mixins import (
    CreateMixin, ReadMixin, UpdateMixin, DeleteMixin
)


@method_decorator(csrf_exempt, name='dispatch')
class IngredientViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """Ingredient ViewSet with modular CRUD mixins"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)