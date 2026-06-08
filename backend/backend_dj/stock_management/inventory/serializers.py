from typing import Any, Optional, Dict
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers
from stock_management.models import Inventory, InventoryLog
from stock_management.inventory.validators import validate_inventory_data


class ProviderDetailSerializer(serializers.Serializer):
    """Nested provider details for Inventory"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    category_display = serializers.SerializerMethodField(read_only=True)
    
    def get_category_display(self, obj: Any) -> str:
        """Get category display label"""
        return obj.get_category_display() if hasattr(obj, 'get_category_display') else obj.category


class InventorySerializer(serializers.ModelSerializer):
    """
    Serializer for Inventory model.
    
    Uses Pydantic validators for data validation.
    
    Fields:
    - name: unique, max 255 chars
    - unit: choice field
    - current_stock: float >= 0
    - min_threshold: reorder point
    - max_threshold: optional max capacity
    - provider_id: write_only (assign supplier)
    - provider: read_only nested provider details
    """
    
    stock_percentage = serializers.SerializerMethodField()
    needs_reorder = serializers.SerializerMethodField()
    
    # Accept provider_id for input, return nested provider for output
    provider_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    provider = ProviderDetailSerializer(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'name', 'description', 'unit',
            'current_stock', 'min_threshold', 'max_threshold',
            'provider_id', 'provider',
            'is_active', 'stock_percentage', 'needs_reorder',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate using Pydantic validator"""
        try:
            exclude_id = None
            validation_data = attrs
            
            # For partial updates (PATCH), merge with existing instance data
            if self.partial and self.instance:
                exclude_id = self.instance.id
                # Build merged data with all required fields
                validation_data = {
                    'name': attrs.get('name', self.instance.name),
                    'description': attrs.get('description', self.instance.description),
                    'unit': attrs.get('unit', self.instance.unit),
                    'current_stock': float(attrs.get('current_stock', self.instance.current_stock)),
                    'min_threshold': float(attrs.get('min_threshold', self.instance.min_threshold)),
                    'max_threshold': float(attrs.get('max_threshold', self.instance.max_threshold)) if attrs.get('max_threshold') is not None or self.instance.max_threshold else None,
                    'is_active': attrs.get('is_active', self.instance.is_active),
                }
            
            validate_inventory_data(validation_data, exclude_id=exclude_id)
        except PydanticValidationError as e:
            raise serializers.ValidationError(str(e))
        return attrs
    
    def get_stock_percentage(self, obj: Any) -> Optional[float]:
        """Calculate stock as percentage of max"""
        if obj.max_threshold:
            return round((obj.current_stock / obj.max_threshold) * 100, 2)
        return None
    
    def get_needs_reorder(self, obj: Any) -> bool:
        """Check if stock is below minimum threshold"""
        return obj.current_stock <= obj.min_threshold


class InventoryLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for InventoryLog (audit trail).
    
    Shows:
    - What was changed (quantity_change)
    - Why (reason)
    - When (created_at)
    - Which inventory item (nested data)
    """
    
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    inventory_unit = serializers.CharField(source='inventory.unit', read_only=True)
    reason_type_display = serializers.CharField(source='get_reason_type_display', read_only=True)
    
    class Meta:
        model = InventoryLog
        fields = [
            'id',
            'inventory',
            'inventory_name',
            'inventory_unit',
            'quantity_change',
            'reason_type',
            'reason_type_display',
            'reason_detail',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'inventory',
            'inventory_name',
            'inventory_unit',
            'quantity_change',
            'reason_type',
            'reason_type_display',
            'reason_detail',
            'created_at'
        ]