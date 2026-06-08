from typing import TYPE_CHECKING
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from simple_history.models import HistoricalRecords

if TYPE_CHECKING:
    from stock_management.purchase_order.model import PurchaseOrder

# Provider category choices
PROVIDER_CATEGORY = [
    ('fresh', 'Fresh Ingredients'),
    ('canned', 'Canned/Packaged'),
    ('bottled', 'Beverages/Oils'),
    ('dairy', 'Dairy Products'),
    ('equipment', 'Equipment/Supplies'),
    ('other', 'Other'),
]


class Provider(models.Model):
    """
    Supplier/Vendor master data.
    
    Purpose:
    - Store supplier contact information
    - Track supplier categories (fresh, canned, beverages, etc.)
    - Reference in PurchaseOrder for traceability
    """
    id = models.AutoField(primary_key=True)
    
    # Supplier name (must be unique)
    name = models.CharField(max_length=255, unique=True)
    
    # Category of products supplied
    category = models.CharField(
        max_length=50,
        choices=PROVIDER_CATEGORY,
        default='other'
    )
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit trail
    history = HistoricalRecords()
    
    # Type hint for reverse relation from PurchaseOrder.provider
    purchase_orders: QuerySet["PurchaseOrder"]
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        category_display = dict(PROVIDER_CATEGORY).get(self.category, self.category)
        return f"{self.name} ({category_display})"