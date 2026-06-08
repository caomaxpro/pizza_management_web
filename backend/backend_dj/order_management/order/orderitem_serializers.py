from rest_framework import serializers
from order_management.order.orderitem_model import OrderItem
from pizza_management.item.serializers import ItemSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items with nested item info"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_info = ItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order',
            'item',
            'item_name',
            'item_info',
            'quantity',
            'unit_price',
            'subtotal',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'subtotal', 'created_at', 'updated_at']
