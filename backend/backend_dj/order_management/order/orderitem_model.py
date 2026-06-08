from django.db import models
from django.utils import timezone
from order_management.order.model import Order
from pizza_management.item.model import Item


class OrderItem(models.Model):
    """
    Individual item in an order (pizza/item + quantity + customizations).
    One-to-Many relationship: One Order has many OrderItems.
    """
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='order_items')
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customizations snapshot - for custom pizzas or modifications
    customizations = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        item_name = self.customizations.get('item_name', '') or (self.item.name if self.item else "Deleted Item")
        return f"Order {self.order.id} - {item_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Auto-snapshot item data and calculate subtotal"""
        # Snapshot item data into customizations if item exists
        if self.item and 'item_name' not in self.customizations:
            self.customizations['item_name'] = self.item.name
            self.customizations['base_price'] = float(self.item.price)
        
        # Auto-calculate subtotal
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
