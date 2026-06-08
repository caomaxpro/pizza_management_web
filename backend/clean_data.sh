#!/bin/bash

# Clean data script for Stock Management Module
# Clears only stock_management app data (Provider, Inventory, InventoryLog, PurchaseOrder, PurchaseOrderItem)

echo "=========================================="
echo "🧹 Cleaning Stock Management Data"
echo "=========================================="

# Paths
BACKEND_DIR="/home/cao-le/Flutter Projects/pizza_ordering_app/backend/backend_dj"
VENV_DIR="/home/cao-le/Flutter Projects/pizza_ordering_app/backend/.venv"

# Activate virtual environment
echo ""
echo "1️⃣ Activating virtual environment..."
source "$VENV_DIR/bin/activate" || {
  echo "❌ Failed to activate venv"
  exit 1
}

cd "$BACKEND_DIR" || {
  echo "❌ Failed to change directory"
  exit 1
}

echo "✅ Virtual environment activated"

# Clear only stock_management tables
echo ""
echo "2️⃣ Clearing stock_management data..."
python manage.py shell << END
from stock_management.models import (
    Provider, Inventory, InventoryLog, 
    PurchaseOrder, PurchaseOrderItem
)

# Get counts before deletion
before_counts = {
    'Provider': Provider.objects.count(),
    'Inventory': Inventory.objects.count(),
    'InventoryLog': InventoryLog.objects.count(),
    'PurchaseOrder': PurchaseOrder.objects.count(),
    'PurchaseOrderItem': PurchaseOrderItem.objects.count(),
}

# Delete data (respects foreign key constraints automatically)
PurchaseOrderItem.objects.all().delete()
PurchaseOrder.objects.all().delete()
InventoryLog.objects.all().delete()
Inventory.objects.all().delete()
Provider.objects.all().delete()

print("✅ Data cleared:")
for model, count in before_counts.items():
    print(f"   - {model}: {count} records deleted")
END

echo ""
echo "=========================================="
echo "✅ Stock Management Cleanup Completed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- All Provider records cleared"
echo "- All Inventory records cleared"
echo "- All InventoryLog records cleared"
echo "- All PurchaseOrder records cleared"
echo "- All PurchaseOrderItem records cleared"
echo ""
echo "📌 Next steps:"
echo "1. Run: cd backend_dj && python manage.py runserver"
echo "2. Test: ./test_full_flow.sh"
echo ""
echo "2. Test: ./test_full_flow.sh"
echo ""
