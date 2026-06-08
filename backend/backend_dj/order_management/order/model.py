from django.db import models
from django.conf import settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from order_management.order.orderitem_model import OrderItem as OrderItemType


class Order(models.Model):
    """
    Customer order model for tracking customer pizza orders.
    One Order has Many OrderItems (1:N relationship).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField()
    
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    # Cancellation tracking
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Fee charged for cancellation (20% of total for preparing orders)")
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for order cancellation")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Type hint for reverse relation from OrderItem
    if TYPE_CHECKING:
        items: "models.Manager[OrderItemType]"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order {self.order_number} - {self.status}"
