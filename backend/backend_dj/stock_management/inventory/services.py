# inventory/services.py
from collections import defaultdict
from django.db import transaction
from django.db.models import F, Case, When, FloatField

from .model import Inventory, InventoryLog


class InventoryService:
    """
    Business logic layer for inventory operations.
    
    Handles:
    - Stock adjustments with audit trail
    - Batch operations
    - Report generation
    """
    
    @staticmethod
    @transaction.atomic
    def adjust_stock(inventory_id, quantity, reason_type="stock_take", reason_detail=None):
        """
        Adjust inventory stock and create audit log.
        
        Args:
            inventory_id (int): Inventory item ID
            quantity (float): Positive (add) or negative (remove)
            reason_type (str): 'receipt' or 'stock_take'
            reason_detail (str|None): Optional extra context
            
        Returns:
            Inventory: Updated inventory object
            
        Raises:
            ValueError: If inventory not found
        """
        try:
            inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise ValueError(f"Inventory {inventory_id} not found")
        
        # Update stock
        inventory.current_stock += quantity
        inventory.save()
        
        # Create audit log
        InventoryLog.objects.create(
            inventory=inventory,
            quantity_change=quantity,
            reason_type=reason_type,
            reason_detail=reason_detail,
        )
        
        return inventory

    @staticmethod
    @transaction.atomic
    def create_logs_and_apply(log_entries):
        """
        Bulk create InventoryLog entries and update stock atomically.

        Logs are created first (source of truth), then stock is aggregated
        and applied in a single transaction.

        Args:
            log_entries (list[dict]): Each dict has:
                - inventory_id (int)
                - quantity_change (float, nonzero)
                - reason_type (str): 'receipt' | 'stock_take'
                - reason_detail (str|None): Optional free text

        Returns:
            list[InventoryLog]: Created log objects

        Raises:
            ValueError: If any inventory_id is not found
        """
        inventory_ids = [e['inventory_id'] for e in log_entries]
        inventories = {
            inv.id: inv
            for inv in Inventory.objects.select_for_update().filter(id__in=inventory_ids)
        }

        missing = set(inventory_ids) - set(inventories.keys())
        if missing:
            raise ValueError(f"Inventory IDs not found: {sorted(missing)}")

        # Create all log rows first
        logs = InventoryLog.objects.bulk_create([
            InventoryLog(
                inventory=inventories[e['inventory_id']],
                quantity_change=e['quantity_change'],
                reason_type=e['reason_type'],
                reason_detail=e.get('reason_detail'),
            )
            for e in log_entries
        ])

        # Aggregate deltas per inventory and apply
        delta = defaultdict(float)
        for e in log_entries:
            delta[e['inventory_id']] += e['quantity_change']

        for inv_id, qty in delta.items():
            inv = inventories[inv_id]
            inv.current_stock += qty
            inv.save()

        return logs
    
    @staticmethod
    def get_low_stock_items():
        """Get all items below minimum threshold"""
        return Inventory.objects.filter(
            is_active=True,
            current_stock__lt=F('min_threshold')
        )
    
    @staticmethod
    def get_overstock_items():
        """Get all items above maximum threshold"""
        return Inventory.objects.filter(
            is_active=True,
            current_stock__gt=F('max_threshold')
        )
    
    @staticmethod
    def generate_stock_report():
        """Generate inventory status report"""
        return {
            'total_items': Inventory.objects.filter(is_active=True).count(),
            'low_stock': Inventory.objects.filter(
                current_stock__lt=F('min_threshold'),
                is_active=True
            ).count(),
            'overstock': Inventory.objects.filter(
                current_stock__gt=F('max_threshold'),
                is_active=True
            ).count(),
        }