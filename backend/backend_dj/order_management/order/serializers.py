from rest_framework import serializers
from order_management.order.model import Order


class OrderItemNestedSerializer(serializers.Serializer):
    """Minimal nested serializer for order items in order context"""
    id = serializers.IntegerField()
    item = serializers.IntegerField()
    item_name = serializers.CharField(source='item.name')
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(allow_blank=True)


class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    items = OrderItemNestedSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_name', 'status',
            'total_price', 'delivery_address', 'order_date', 'delivery_date',
            'notes', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'order_date', 'items']
