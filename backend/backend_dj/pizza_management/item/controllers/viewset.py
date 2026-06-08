from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from pizza_management.item.model import Item
from pizza_management.item.serializers import ItemSerializer
from pizza_management.item.controllers.mixins import CreateMixin, ReadMixin, UpdateMixin, DeleteMixin


@method_decorator(csrf_exempt, name='dispatch')
class ItemViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """Item ViewSet with modular CRUD mixins"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)