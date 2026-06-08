from rest_framework import serializers
from pizza_management.item.model import Item
from pizza_management.ingredient.serializers import IngredientSerializer


class ItemSerializer(serializers.ModelSerializer):
    # Nested FK relationships - show full ingredient details
    dough = IngredientSerializer(read_only=True)
    sauce = IngredientSerializer(read_only=True)
    cheese = IngredientSerializer(read_only=True)

    # Nested M2M relationships - show full ingredient details
    toppings = IngredientSerializer(many=True, read_only=True)
    extras = IngredientSerializer(many=True, read_only=True)

    # Accept IDs when creating/updating
    dough_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    sauce_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    cheese_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    toppings_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    extras_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Item
        fields = "__all__"
    
    def to_internal_value(self, data):
        """Convert string boolean values from FormData to actual boolean.
        
        FormData converts boolean to string: True -> "1", False -> "0"
        This method converts them back before validation.
        """
        # Handle is_active field: "1" -> True, "0" -> False
        if 'is_active' in data:
            is_active_val = data['is_active']
            # Handle string from FormData
            if isinstance(is_active_val, str):
                data['is_active'] = is_active_val.lower() in ('true', '1', 'yes')
            # Handle list from multiple FormData appends (shouldn't happen, but safe)
            elif isinstance(is_active_val, list) and is_active_val:
                data['is_active'] = str(is_active_val[0]).lower() in ('true', '1', 'yes')
        
        return super().to_internal_value(data)