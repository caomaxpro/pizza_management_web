# provider/serializers.py
from rest_framework import serializers
from stock_management.models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider (Supplier/Vendor) model.
    
    Fields:
    - name: unique, max 255 chars
    - category: choice field (fresh, canned, bottled, dairy, equipment, other)
    - phone: optional contact number
    - email: optional email address
    - address: optional supplier address
    - is_active: boolean status
    - created_at, updated_at: audit timestamps
    """
    
    # Category display (show label instead of code)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    # Count of purchase orders from this provider
    purchase_order_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id',
            'name',
            'category',
            'category_display',
            'phone',
            'email',
            'address',
            'is_active',
            'purchase_order_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate provider name uniqueness (exclude current instance on update)"""
        instance = self.instance
        queryset = Provider.objects.filter(name=value)
        
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A provider with this name already exists")
        
        return value
    
    def validate_email(self, value):
        """Validate email format if provided"""
        if value and len(value) > 254:
            raise serializers.ValidationError("Email address too long")
        return value
    
    def get_purchase_order_count(self, obj):
        """Return count of purchase orders from this provider"""
        return obj.purchase_orders.count()
