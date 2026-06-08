from django.db import models
from django.utils import timezone
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError

from stock_management.provider.model import Provider
from stock_management.inventory.model import Inventory

# Purchase order status choices
PURCHASE_ORDER_STATUS = [
    ('pending', 'Pending'),        # Waiting for delivery
    ('received', 'Received'),      # Delivery confirmed, stock updated
    ('cancelled', 'Cancelled'),    # Order cancelled
]


class PurchaseOrder(models.Model):
    """
    Purchase order (inbound delivery ticket) from suppliers.
    Tracks: supplier, delivery dates, status, total cost.
    When confirmed, automatically updates inventory stock.
    """
    id = models.AutoField(primary_key=True)
    
    # Purchase order number (PO-001, PO-002, ...)
    order_number = models.CharField(max_length=100, unique=True)
    
    # Foreign key to Provider - PROTECT prevents accidental deletion
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,  # ❌ Cannot delete provider if orders reference it
        related_name="purchase_orders"  # Reverse: provider.purchase_orders.all()
    )
    
    # Order creation date (auto = today)
    order_date = models.DateTimeField(default=timezone.now)
    
    # Expected delivery date (manual input)
    expected_delivery_date = models.DateField(null=True, blank=True)
    
    # Actual delivery date (auto-updated on confirm_receipt)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Order status: pending, received, or cancelled
    status = models.CharField(
        max_length=20,
        choices=PURCHASE_ORDER_STATUS,
        default='pending'
    )
    
    # Total cost = sum of all PurchaseOrderItem.total_price
    # Auto-calculated in calculate_total()
    total_cost = models.FloatField(default=0)
    
    # Optional notes/comments
    notes = models.TextField(null=True, blank=True)
    
    # Receipt/proof files (JSON array of file URLs)
    receipt_files = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of receipt file URLs/paths for proof of purchase"
    )
    # Example: ["receipts/PO-001_receipt.pdf", "receipts/PO-001_invoice.jpg"]
    
    # Keep current JSONField just for reference URLs (optional)
    # For actual files, use separate model:
    
    # Metadata timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  # Auto-updates on each save
    
    # Audit trail (change history)
    history = HistoricalRecords()
    
    # Type hint for related manager
    items: QuerySet["PurchaseOrderItem"]
    
    class Meta:
        ordering = ['-order_date']  # Show newest orders first
        indexes = [
            models.Index(fields=['order_number']),  # Fast lookup by PO number
            models.Index(fields=['status', '-order_date']),  # Filter by status + sort
            models.Index(fields=['provider', 'status']),  # Find orders by provider
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.provider.name}"
    
    def calculate_total(self):
        """
        Calculate total cost by summing all items in this order.
        Called automatically whenever an item is added/deleted/modified.
        
        Returns:
            float: Total cost of the order
        """
        total = sum(item.total_price for item in self.items.all())
        self.total_cost = total
        self.save()
        return total
    
    def confirm_receipt(self):
        """
        Confirm delivery and update stock levels.
        
        Process:
        1. Validate order has at least one item
        2. For each item: increase material stock by quantity
        3. Create StockLog entries for audit trail
        4. Set status to 'received' and record actual delivery date
        
        Raises:
            ValidationError: If order already received or has no items
        """
        # Skip if already confirmed
        if self.status == 'received':
            return
        
        # Validate: cannot confirm empty order
        if not self.items.exists():
            raise ValidationError("Cannot receive PO without items")
        
        # Process each ordered item
        for item in self.items.all():
            # Increase stock (add to existing quantity)
            item.inventory.current_stock += item.quantity
            item.inventory.save()
            
            # Create audit log entry (who, what, when)
            from stock_management.inventory.model import InventoryLog
            InventoryLog.objects.create(
                inventory=item.inventory,
                quantity_change=item.quantity,  # Positive = incoming stock
                reason_type='receipt',
                reason_detail=f"PO {self.order_number} from {self.provider.name}"
            )
        
        # Mark order as received
        self.status = 'received'
        
        # Record actual delivery timestamp
        self.actual_delivery_date = timezone.now().date()
        self.save()
    
    def cancel(self):
        """
        Cancel the purchase order.
        Only pending orders can be cancelled.
        Received orders cannot be cancelled (stock already updated).
        
        Raises:
            ValidationError: If order is not in pending status
        """
        if self.status != 'pending':
            raise ValidationError("Can only cancel pending orders")
        self.status = 'cancelled'
        self.save()


class PurchaseOrderItem(models.Model):
    """
    Line item detail within a purchase order.
    
    Flow:
    1. Create: only quantity (price unknown yet)
    2. Receive: add actual_unit_price from invoice
    3. Calculate total_price when confirmed
    """
    id = models.AutoField(primary_key=True)
    
    # Foreign key to PurchaseOrder - CASCADE (delete PO → delete items)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,  # Deleting PO automatically deletes items
        related_name="items"  # Reverse: po.items.all()
    )
    
    # Foreign key to Inventory - CASCADE (delete inventory → delete related items)
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,  # ✅ Deleting inventory automatically deletes related PurchaseOrderItems
        related_name="purchase_items"  # Reverse: inventory.purchase_items.all()
    )
    
    # Step 1: Required at creation
    quantity = models.FloatField()  # 10 bags
    
    # Step 2: Added when receive (from supplier invoice)
    actual_unit_price = models.FloatField(
        null=True,
        blank=True,
        help_text="Actual price from supplier invoice"
    )
    
    # Step 3: Auto-calculated when saved with actual_unit_price
    total_price = models.FloatField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']  # Order by creation time
        indexes = [
            models.Index(fields=['purchase_order', 'inventory']),  # Fast lookup
        ]
        # Ensure no duplicate items in same PO (one inventory item per order)
        unique_together = ['purchase_order', 'inventory']
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.inventory.name}"
    
    def save(self, *args, **kwargs):
        # Only calculate if actual_unit_price is provided
        if self.actual_unit_price:
            self.total_price = self.quantity * self.actual_unit_price
        
        super().save(*args, **kwargs)
        
        # Only update PO total if all items have prices
        if self.purchase_order.items.filter(actual_unit_price__isnull=True).count() == 0:
            self.purchase_order.calculate_total()
    
    def delete(self, *args, **kwargs):
        po = self.purchase_order
        result = super().delete(*args, **kwargs)
        po.calculate_total()
        return result


class PurchaseOrderReceipt(models.Model):
    """Uploaded proof documents (receipts, invoices, photos)"""
    id = models.AutoField(primary_key=True)
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="receipts"
    )
    
    # This ACTUALLY stores the file
    file = models.FileField(
        upload_to='purchase_orders/receipts/%Y/%m/',  # receipts/2026/04/...
        help_text="Receipt, invoice, or proof document"
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('receipt', 'Receipt'),
            ('invoice', 'Invoice'),
            ('photo', 'Photo'),
        ]
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.file.name}"