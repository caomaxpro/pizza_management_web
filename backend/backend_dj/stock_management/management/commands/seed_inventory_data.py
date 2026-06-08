"""
Django management command to seed dummy data for stock management testing.
Usage: python manage.py seed_inventory_data
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from stock_management.inventory.model import Inventory, InventoryLog
from stock_management.provider.model import Provider


class Command(BaseCommand):
    help = "Seed dummy inventory data for testing reports"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting inventory data seeding...")
        
        # Clear existing data (optional - comment out if you want to append)
        count_inv, _ = Inventory.objects.all().delete()
        count_logs, _ = InventoryLog.objects.all().delete()
        self.stdout.write(f"✅ Cleared {count_inv} inventory items and logs")
        
        # Create or get providers
        providers_data = [
            {"name": "Local Fresh Co", "category": "fresh", "email": "fresh@example.com"},
            {"name": "Global Imports Ltd", "category": "bottled", "email": "imports@example.com"},
            {"name": "Dairy Direct", "category": "dairy", "email": "dairy@example.com"},
            {"name": "Equipment Plus", "category": "equipment", "email": "equip@example.com"},
            {"name": "Bulk Foods Inc", "category": "canned", "email": "bulk@example.com"},
        ]
        
        providers = {}
        for data in providers_data:
            provider, created = Provider.objects.get_or_create(
                name=data["name"],
                defaults={
                    "category": data["category"],
                    "email": data["email"],
                    "is_active": True,
                }
            )
            providers[data["name"]] = provider
            if created:
                self.stdout.write(f"  ✓ Created provider: {provider.name}")
        
        # Inventory items with diverse units and stock levels
        inventory_data = [
            # Fresh Produce
            {"name": "Pork Meat", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 15.5, "min_threshold": 10, "max_threshold": 50},
            {"name": "Chicken Breast", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 8.2, "min_threshold": 10, "max_threshold": 40},
            {"name": "Beef Mince", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 3.5, "min_threshold": 8, "max_threshold": 35},
            {"name": "Fresh Tomatoes", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 25.0, "min_threshold": 5, "max_threshold": 50},
            {"name": "Onions", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 40.0, "min_threshold": 20, "max_threshold": 100},
            {"name": "Bell Peppers", "unit": "kg", "provider": "Local Fresh Co", "current_stock": 12.5, "min_threshold": 8, "max_threshold": 30},
            
            # Dairy Products
            {"name": "Mozzarella Cheese", "unit": "kg", "provider": "Dairy Direct", "current_stock": 5.0, "min_threshold": 5, "max_threshold": 25},
            {"name": "Parmesan Cheese", "unit": "kg", "provider": "Dairy Direct", "current_stock": 2.8, "min_threshold": 3, "max_threshold": 15},
            {"name": "Fresh Milk", "unit": "l", "provider": "Dairy Direct", "current_stock": 45.0, "min_threshold": 30, "max_threshold": 100},
            {"name": "Cream", "unit": "l", "provider": "Dairy Direct", "current_stock": 8.5, "min_threshold": 5, "max_threshold": 20},
            
            # Sauces & Oils
            {"name": "Olive Oil", "unit": "l", "provider": "Global Imports Ltd", "current_stock": 30.0, "min_threshold": 10, "max_threshold": 60},
            {"name": "Tomato Sauce", "unit": "l", "provider": "Global Imports Ltd", "current_stock": 50.0, "min_threshold": 20, "max_threshold": 100},
            {"name": "Pesto", "unit": "ml", "provider": "Global Imports Ltd", "current_stock": 800.0, "min_threshold": 500, "max_threshold": 2000},
            {"name": "Balsamic Vinegar", "unit": "ml", "provider": "Global Imports Ltd", "current_stock": 250.0, "min_threshold": 200, "max_threshold": 1000},
            
            # Canned Goods
            {"name": "Canned Tuna", "unit": "pcs", "provider": "Bulk Foods Inc", "current_stock": 120.0, "min_threshold": 50, "max_threshold": 300},
            {"name": "Canned Olives", "unit": "pcs", "provider": "Bulk Foods Inc", "current_stock": 85.0, "min_threshold": 30, "max_threshold": 200},
            {"name": "Canned Mushrooms", "unit": "pcs", "provider": "Bulk Foods Inc", "current_stock": 45.0, "min_threshold": 20, "max_threshold": 150},
            {"name": "Canned Corn", "unit": "pcs", "provider": "Bulk Foods Inc", "current_stock": 200.0, "min_threshold": 80, "max_threshold": 400},
            
            # Dry Goods
            {"name": "Flour", "unit": "kg", "provider": "Bulk Foods Inc", "current_stock": 50.0, "min_threshold": 25, "max_threshold": 100},
            {"name": "Sugar", "unit": "kg", "provider": "Bulk Foods Inc", "current_stock": 30.0, "min_threshold": 15, "max_threshold": 75},
            {"name": "Salt", "unit": "kg", "provider": "Bulk Foods Inc", "current_stock": 20.0, "min_threshold": 10, "max_threshold": 50},
            {"name": "Pasta - Spaghetti", "unit": "box", "provider": "Bulk Foods Inc", "current_stock": 45.0, "min_threshold": 20, "max_threshold": 100},
            {"name": "Rice", "unit": "kg", "provider": "Bulk Foods Inc", "current_stock": 35.0, "min_threshold": 15, "max_threshold": 80},
            
            # Spices & Seasonings
            {"name": "Oregano", "unit": "g", "provider": "Global Imports Ltd", "current_stock": 500.0, "min_threshold": 200, "max_threshold": 1000},
            {"name": "Basil", "unit": "g", "provider": "Global Imports Ltd", "current_stock": 300.0, "min_threshold": 150, "max_threshold": 800},
            {"name": "Black Pepper", "unit": "g", "provider": "Global Imports Ltd", "current_stock": 250.0, "min_threshold": 150, "max_threshold": 500},
            {"name": "Garlic Powder", "unit": "g", "provider": "Global Imports Ltd", "current_stock": 400.0, "min_threshold": 200, "max_threshold": 1000},
            
            # Beverages
            {"name": "Tomato Juice", "unit": "bottle", "provider": "Global Imports Ltd", "current_stock": 50.0, "min_threshold": 20, "max_threshold": 100},
            {"name": "Orange Juice", "unit": "bottle", "provider": "Global Imports Ltd", "current_stock": 75.0, "min_threshold": 30, "max_threshold": 150},
            {"name": "Sparkling Water", "unit": "bottle", "provider": "Global Imports Ltd", "current_stock": 200.0, "min_threshold": 100, "max_threshold": 500},
            
            # Packaging & Supplies
            {"name": "Pizza Boxes - Large", "unit": "box", "provider": "Equipment Plus", "current_stock": 300.0, "min_threshold": 150, "max_threshold": 1000},
            {"name": "Pizza Boxes - Medium", "unit": "box", "provider": "Equipment Plus", "current_stock": 250.0, "min_threshold": 150, "max_threshold": 800},
            {"name": "Napkins", "unit": "packet", "provider": "Equipment Plus", "current_stock": 50.0, "min_threshold": 20, "max_threshold": 100},
            {"name": "Plastic Bags", "unit": "bag", "provider": "Equipment Plus", "current_stock": 100.0, "min_threshold": 50, "max_threshold": 200},
            
            # Some inactive items
            {"name": "Expired Spice Mix", "unit": "g", "provider": "Global Imports Ltd", "current_stock": 0, "min_threshold": 100, "max_threshold": 500, "is_active": False},
            {"name": "Old Menu Item", "unit": "pouch", "provider": "Bulk Foods Inc", "current_stock": 2.0, "min_threshold": 5, "max_threshold": 30, "is_active": False},
        ]
        
        # Create inventory items
        inventories = {}
        for data in inventory_data:
            provider = providers.get(data.pop("provider"))
            is_active = data.pop("is_active", True)
            
            inventory, created = Inventory.objects.get_or_create(
                name=data["name"],
                defaults={
                    **data,
                    "provider": provider,
                    "is_active": is_active,
                    "description": f"Inventory item for {data['name']}"
                }
            )
            inventories[data["name"]] = inventory
            if created:
                self.stdout.write(f"  ✓ Created inventory: {inventory.name} ({inventory.current_stock} {inventory.unit})")
        
        self.stdout.write(f"\n✅ Created {len(inventories)} inventory items\n")
        
        # Create inventory logs with realistic time-series data
        self.stdout.write("📊 Generating inventory logs (time-series data)...")
        
        now = timezone.now()
        log_count = 0
        
        for inventory in inventories.values():
            # Generate 15-30 log entries per item spanning the last 60 days
            num_logs = 15 + (hash(inventory.name) % 15)
            
            for i in range(num_logs):
                days_ago = 60 - (i * 4)  # Space logs roughly 4 days apart
                log_datetime = now - timedelta(days=days_ago)
                
                # Alternate between receipt and stock_take
                reason_type = "receipt" if i % 2 == 0 else "stock_take"
                
                # Vary quantities
                if reason_type == "receipt":
                    quantity = 10 + (hash(inventory.name + str(i)) % 40)  # 10-50 units incoming
                    reason_detail = f"PO#{1000 + i} from {inventory.provider.name if inventory.provider else 'Unknown'}"
                else:
                    quantity = -(5 + (hash(inventory.name + str(i)) % 20))  # 5-25 units outgoing
                    reason_detail = f"Stock adjustment - {['Damaged', 'Expired', 'Usage', 'Transfer', 'Audit correction'][i % 5]}"
                
                log = InventoryLog.objects.create(
                    inventory=inventory,
                    quantity_change=quantity,
                    reason_type=reason_type,
                    reason_detail=reason_detail,
                )
                # auto_now_add=True prevents .save() from updating created_at,
                # so use QuerySet.update() to bypass the field's pre_save hook
                InventoryLog.objects.filter(pk=log.pk).update(created_at=log_datetime)
                log_count += 1
        
        self.stdout.write(f"✅ Created {log_count} inventory log entries\n")
        
        # Summary statistics
        total_items = Inventory.objects.count()
        active_items = Inventory.objects.filter(is_active=True).count()
        low_stock_items = sum(1 for inv in Inventory.objects.all() if inv.needs_reorder)
        total_logs = InventoryLog.objects.count()
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📈 DUMMY DATA SUMMARY")
        self.stdout.write("="*60)
        self.stdout.write(f"  Total Inventory Items:    {total_items}")
        self.stdout.write(f"  Active Items:             {active_items}")
        self.stdout.write(f"  Items Below Min Stock:    {low_stock_items}")
        self.stdout.write(f"  Total Log Entries:        {total_logs}")
        self.stdout.write(f"  Providers:                {Provider.objects.count()}")
        self.stdout.write("="*60)
        
        self.stdout.write("\n✨ Seeding complete! Your FE reports should have plenty of data to display.\n")
