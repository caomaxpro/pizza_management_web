from django.db import models
from django.utils import timezone
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stock_management.provider.model import Provider

# Inventory unit choices
REASON_CHOICES = [
    ('receipt', 'Receipt'),
    ('stock_take', 'Stock Take'),
]

UNIT_CHOICES = [
    ('kg', 'Kilogram'),
    ('g', 'Gram'),
    ('ml', 'Milliliter'),
    ('l', 'Liter'),
    ('pcs', 'Piece'),
    ('box', 'Box'),
    ('bag', 'Bag'),
    ('pouch', 'Pouch'),
    ('packet', 'Packet'),
    ('bottle', 'Bottle'),
    ('dozen', 'Dozen'),
]

class Inventory(models.Model):
    """
    Inventory item catalog with current stock level.
    
    Purpose:
    - Master list of materials the restaurant can purchase
    - Track current quantity in stock
    - Alert when stock is low
    - Audit all stock movements
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)  # e.g., "Pork Meat", "Mozzarella Cheese"
    description = models.TextField(null=True, blank=True)
    
    # Supplier/Provider - optional (item might not have assigned supplier yet)
    provider = models.ForeignKey(
        'stock_management.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        help_text="Primary supplier for this item"
    )
    
    # Unit and pricing
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    
    # Stock management
    current_stock = models.FloatField(default=0)  # Current quantity in stock
    min_threshold = models.FloatField(default=5)  # Alert when stock < this value
    max_threshold = models.FloatField(null=True, blank=True)  # Optional max capacity
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit trail
    history = HistoricalRecords()
    
    # Type hint for related managers
    logs: QuerySet["InventoryLog"]  # From InventoryLog.related_name='logs'
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['current_stock']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"
    
    @property
    def needs_reorder(self):
        """Check if stock is below minimum threshold"""
        return self.current_stock < self.min_threshold
    
    @property
    def stock_percentage(self):
        """Stock as % of max capacity"""
        if self.max_threshold:
            return (self.current_stock / self.max_threshold) * 100
        return None
    
    def update_stock(self, quantity, reason_type="stock_take", reason_detail=None):
        """Update stock and create log entry"""
        self.current_stock += quantity
        self.save()
        
        return InventoryLog.objects.create(
            inventory=self,
            quantity_change=quantity,
            reason_type=reason_type,
            reason_detail=reason_detail,
        )


class InventoryLog(models.Model):
    """
    Inventory operation audit trail.
    
    Tracks all stock changes:
    - Incoming: +quantity from PO received
    - Outgoing: -quantity from usage
    - Adjustment: ±quantity from correction
    - Loss: -quantity from damage/expiry
    """
    id = models.AutoField(primary_key=True)
    
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="logs"
    )
    
    quantity_change = models.FloatField()  # Positive (add) or negative (remove)
    reason_type = models.CharField(max_length=20, choices=REASON_CHOICES, default='stock_take')
    reason_detail = models.TextField(null=True, blank=True)  # Optional: PO number, notes, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def get_reason_type_display(self) -> str:
        """
        Return the human-readable label for `reason_type`.
        Django dynamically provides `get_FOO_display()` for fields with `choices`,
        but static analyzers don't see it — provide a concrete implementation
        so type checkers (Pylance) are satisfied.
        """
        return dict(REASON_CHOICES).get(self.reason_type, str(self.reason_type))

    def __str__(self):
        sign = "+" if self.quantity_change >= 0 else ""
        detail = f" - {self.reason_detail}" if self.reason_detail else ""
        return f"{self.inventory.name}: {sign}{self.quantity_change} ({self.get_reason_type_display()}{detail})"