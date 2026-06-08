# purchase_order/serializers.py
from typing import Any, Optional, Dict
from rest_framework import serializers
from stock_management.models import PurchaseOrder, PurchaseOrderItem, Provider, Inventory


class ProviderDetailSerializer(serializers.ModelSerializer):
    """Nested provider details in PurchaseOrder"""
    
    class Meta:
        model = Provider
        fields = ['id', 'name', 'category', 'phone', 'email']
        read_only_fields = ['id']


class InventoryDetailSerializer(serializers.ModelSerializer):
    """Nested inventory details in PurchaseOrderItem"""
    
    provider_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = ['id', 'name', 'unit', 'current_stock', 'provider_details']
        read_only_fields = ['id', 'current_stock']
    
    def get_provider_details(self, obj: Any) -> Optional[Dict[str, Any]]:
        """Show provider info for this inventory item"""
        if obj.provider:
            return {
                'id': obj.provider.id,
                'name': obj.provider.name,
                'category': obj.provider.category,
            }
        return None


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for line items within a purchase order.
    
    Validates that inventory item's provider matches PO's provider.
    Returns nested inventory info with provider details.
    """
    
    inventory_details = InventoryDetailSerializer(
        source='inventory',
        read_only=True
    )
    
    # For input: accept inventory_id
    inventory_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id',
            'purchase_order',
            'inventory_id',  # Write-only for input
            'inventory',     # Read-only for output
            'inventory_details',
            'quantity',
            'actual_unit_price',
            'total_price',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'purchase_order',
            'inventory',     # Use inventory_id for input
            'total_price',
            'created_at',
        ]
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that:
        1. Inventory exists
        2. Inventory's provider matches PO's provider
        """
        inventory_id = attrs.get('inventory_id')
        po_id = self.context.get('po_id') or self.initial_data.get('purchase_order')  # type: ignore
        
        if not inventory_id:
            raise serializers.ValidationError({'inventory_id': 'This field is required.'})
        
        # Get inventory
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise serializers.ValidationError({'inventory_id': f'Inventory ID {inventory_id} not found'})
        
        # Get PO to check provider
        if po_id:
            try:
                po = PurchaseOrder.objects.get(id=po_id)
                
                # Check if inventory's provider matches PO's provider
                if inventory.provider and inventory.provider.id != po.provider.id:
                    raise serializers.ValidationError(
                        f"❌ Inventory '{inventory.name}' belongs to provider "
                        f"'{inventory.provider.name}' but this PO is for provider '{po.provider.name}'"
                    )
                
                # Add PO to validated_data for saving
                attrs['purchase_order'] = po
            except PurchaseOrder.DoesNotExist:
                raise serializers.ValidationError('Purchase Order not found')
        
        # Replace inventory_id with actual inventory object for save
        attrs['inventory'] = inventory
        attrs.pop('inventory_id', None)
        
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseOrder model.
    
    Includes:
    - Nested provider details
    - Nested items with inventory info
    - Status tracking
    - Timestamp audit trail
    
    Methods:
    - confirm_receipt: Mark as received, update inventory
    - cancel: Cancel pending order
    """
    
    items = PurchaseOrderItemSerializer(
        many=True,
        read_only=True
    )
    
    # Calculated field: item count
    item_count = serializers.SerializerMethodField()
    
    # Accept provider_id for input, but return nested provider for output
    provider_id = serializers.IntegerField(write_only=True)
    provider = ProviderDetailSerializer(read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'provider_id', 'provider',  # Note: both fields
            'order_date', 'expected_delivery_date', 'actual_delivery_date',
            'status', 'total_cost', 'notes', 'item_count', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id',
            'order_date',
            'actual_delivery_date',
            'total_cost',
            'items',
            'created_at',
            'updated_at',
        ]
    
    def get_item_count(self, obj: Any) -> int:
        """Return number of line items in order"""
        return obj.items.count()
    
    def validate_order_number(self, value: str) -> str:
        """Validate order number format and uniqueness"""
        if not value.startswith('PO-'):
            raise serializers.ValidationError("Order number must start with 'PO-'")
        return value
