from rest_framework import serializers
from pizza_management.ingredient.model import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"
    
    def validate_image_url(self, value):
        # Allow empty/None URLs
        if value is None or value == '':
            return None
        return value
    
    def validate_piece_image_url(self, value):
        # Allow empty/None URLs
        if value is None or value == '':
            return None
        return value