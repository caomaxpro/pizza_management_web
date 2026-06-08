#!/bin/bash

# Test script for Stock Management Module
# Flow: Provider → Inventory → PurchaseOrder → PurchaseOrderItems → confirm_receipt → view logs

BASE_URL="http://127.0.0.1:8000/api"
TIMESTAMP=$(date +%s%N)  # Unique timestamp to avoid duplicate provider names

echo "=========================================="
echo "Testing Stock Management Full Flow"
echo "=========================================="

# 1. Create Provider (with unique name to avoid duplicates)
echo ""
echo "1️⃣ Creating Provider..."
PROVIDER_NAME="Fresh Farms Suppliers $TIMESTAMP"
PROVIDER_RESPONSE=$(curl -s -X POST $BASE_URL/provider/ \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$PROVIDER_NAME\",
    \"category\": \"fresh\",
    \"phone\": \"+1-555-0123\",
    \"email\": \"contact@freshfarms.com\",
    \"address\": \"123 Farm Road\"
  }")

PROVIDER_ID=$(echo "$PROVIDER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$PROVIDER_ID" ]; then
  echo "❌ Provider creation failed!"
  echo "Response: $PROVIDER_RESPONSE"
  exit 1
fi

echo "✅ Provider created: ID=$PROVIDER_ID (Name: $PROVIDER_NAME)"

# 2. Create Inventory Items (catalog) linked to Provider
echo ""
echo "2️⃣ Creating Inventory Items..."

INVENTORY_1=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Organic Tomatoes\",
    \"unit\": \"kg\",
    \"current_stock\": 0,
    \"min_threshold\": 10,
    \"max_threshold\": 100,
    \"provider_id\": $PROVIDER_ID
  }")

INVENTORY_1_ID=$(echo "$INVENTORY_1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$INVENTORY_1_ID" ]; then
  echo "❌ Inventory 1 creation failed!"
  echo "Response: $INVENTORY_1"
  exit 1
fi

echo "✅ Inventory 1 created: ID=$INVENTORY_1_ID (Organic Tomatoes)"

INVENTORY_2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Fresh Onions\",
    \"unit\": \"kg\",
    \"current_stock\": 0,
    \"min_threshold\": 5,
    \"max_threshold\": 50,
    \"provider_id\": $PROVIDER_ID
  }")

INVENTORY_2_ID=$(echo "$INVENTORY_2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$INVENTORY_2_ID" ]; then
  echo "❌ Inventory 2 creation failed!"
  echo "Response: $INVENTORY_2"
  exit 1
fi

echo "✅ Inventory 2 created: ID=$INVENTORY_2_ID (Fresh Onions)"

# 3. Create Purchase Order
echo ""
echo "3️⃣ Creating Purchase Order..."
PO_RESPONSE=$(curl -s -X POST "$BASE_URL/purchase-order/" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_number\": \"PO-2026-$(date +%s)\",
    \"provider_id\": $PROVIDER_ID,
    \"expected_delivery_date\": \"2026-04-20\",
    \"notes\": \"Weekly delivery from Fresh Farms\"
  }")

PO_ID=$(echo "$PO_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$PO_ID" ]; then
  echo "❌ PO creation failed!"
  echo "Response: $PO_RESPONSE"
  exit 1
fi

echo "✅ Purchase Order created: ID=$PO_ID"

# 4. Add Items to Purchase Order
echo ""
echo "4️⃣ Adding items to Purchase Order..."

ITEM_1=$(curl -s -X POST "$BASE_URL/purchase-order-item/" \
  -H "Content-Type: application/json" \
  -d "{
    \"purchase_order\": $PO_ID,
    \"inventory_id\": $INVENTORY_1_ID,
    \"quantity\": 50,
    \"actual_unit_price\": 2.5
  }")

ITEM_1_ID=$(echo "$ITEM_1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$ITEM_1_ID" ]; then
  echo "❌ Item 1 addition failed!"
  echo "Response: $ITEM_1"
  exit 1
fi

echo "✅ Item 1 added: ID=$ITEM_1_ID (50 kg Tomatoes @ \$2.5/kg)"

ITEM_2=$(curl -s -X POST "$BASE_URL/purchase-order-item/" \
  -H "Content-Type: application/json" \
  -d "{
    \"purchase_order\": $PO_ID,
    \"inventory_id\": $INVENTORY_2_ID,
    \"quantity\": 30,
    \"actual_unit_price\": 1.5
  }")

ITEM_2_ID=$(echo "$ITEM_2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$ITEM_2_ID" ]; then
  echo "❌ Item 2 addition failed!"
  echo "Response: $ITEM_2"
  exit 1
fi

echo "✅ Item 2 added: ID=$ITEM_2_ID (30 kg Onions @ \$1.5/kg)"

# 5. View PO with all items
echo ""
echo "5️⃣ Viewing Purchase Order with items..."
curl -s -X GET "$BASE_URL/purchase-order/$PO_ID/" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Response parsing error"

# 6. Check Inventory BEFORE confirm_receipt (stock should still be 0)
echo ""
echo "6️⃣ Checking Inventory BEFORE confirm_receipt (stock = 0)..."
echo "Tomatoes:"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_1_ID/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null | grep -E "(current_stock|needs_reorder|name)" || echo "Response parsing error"
echo ""
echo "Onions:"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_2_ID/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null | grep -E "(current_stock|needs_reorder|name)" || echo "Response parsing error"

# 7. Confirm Receipt - THIS IS WHERE LOG IS CREATED
echo ""
echo "7️⃣ Confirming receipt of Purchase Order..."
CONFIRM=$(curl -s -X POST "$BASE_URL/purchase-order/$PO_ID/confirm-receipt/" \
  -H "Content-Type: application/json")
echo "$CONFIRM" | python3 -m json.tool 2>/dev/null | head -n 30 || echo "Confirm response: $CONFIRM"

# 8. Check Inventory AFTER confirm_receipt (stock should be updated)
echo ""
echo "8️⃣ Checking Inventory AFTER confirm_receipt (stock updated)..."
echo "Tomatoes (should be 50 kg):"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_1_ID/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null | grep -E "(current_stock|needs_reorder|name)" || echo "Response parsing error"
echo ""
echo "Onions (should be 30 kg):"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_2_ID/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null | grep -E "(current_stock|needs_reorder|name)" || echo "Response parsing error"

# 9. View Inventory Logs - PROOF THAT LOG WAS CREATED
echo ""
echo "9️⃣ Viewing Inventory Logs (audit trail)..."
echo "Tomatoes logs:"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_1_ID/history/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Response parsing error"
echo ""
echo "Onions logs:"
curl -s -X GET "$BASE_URL/inventory/$INVENTORY_2_ID/history/" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Response parsing error"

echo ""
echo "=========================================="
echo "✅ Full Flow Test Completed!"
echo "=========================================="

echo ""
echo "Summary:"
echo "- Provider ID: $PROVIDER_ID (Fresh Farms Suppliers)"
echo "- Inventory 1 ID: $INVENTORY_1_ID (Organic Tomatoes)"
echo "- Inventory 2 ID: $INVENTORY_2_ID (Fresh Onions)"
echo "- PO ID: $PO_ID (Order Number visible in responses)"
echo "- Item 1 ID: $ITEM_1_ID (50 kg Tomatoes)"
echo "- Item 2 ID: $ITEM_2_ID (30 kg Onions)"
echo ""
echo "Expected Results:"
echo "✅ Inventory stocks updated from 0 → 50 kg (Tomatoes), 30 kg (Onions)"
echo "✅ InventoryLog created for each item with reason \"Purchase Order received from...\""
echo "✅ PO status changed from 'pending' to 'received'"
