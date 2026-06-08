#!/bin/bash

# Test UPDATE inventory items
# Tests PUT/PATCH /api/inventory/{id}/ endpoints

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing UPDATE Inventory Items"
echo "=================================="

# Setup: Create test item
echo -e "\n📦 Setting up test data..."

# Create provider
PROVIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Update Test Provider '$TIMESTAMP'",
    "category": "fresh",
    "email": "test@example.com",
    "phone": "1234567890",
    "address": "123 Test St"
  }')
PROVIDER_ID=$(echo "$PROVIDER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

# Create test item
ITEM_ID=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mozzarella Cheese '$TIMESTAMP'",
    "description": "Fresh mozzarella",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "max_threshold": 100,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

echo "✅ Test item created: ID=$ITEM_ID"

# Test 1: Full UPDATE (PUT) - replace all fields
echo -e "\n1️⃣ FULL UPDATE (PUT) - replace all fields..."
curl -s -X PUT "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Mozzarella '$TIMESTAMP'",
    "description": "Premium mozzarella",
    "unit": "kg",
    "current_stock": 75,
    "min_threshold": 15,
    "max_threshold": 120,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }' | jq '.data // .'

# Test 2: Partial UPDATE (PATCH) - update only stock
echo -e "\n2️⃣ PARTIAL UPDATE (PATCH) - update current_stock only..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": 100
  }' | jq '.data // .'

# Test 3: Partial UPDATE (PATCH) - update description
echo -e "\n3️⃣ PARTIAL UPDATE (PATCH) - update description only..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Super premium mozzarella from Italy"
  }' | jq '.data // .'

# Test 4: Partial UPDATE (PATCH) - update thresholds
echo -e "\n4️⃣ PARTIAL UPDATE (PATCH) - update min/max thresholds..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "min_threshold": 20,
    "max_threshold": 150
  }' | jq '.data // .'

# Test 5: Partial UPDATE (PATCH) - update status
echo -e "\n5️⃣ PARTIAL UPDATE (PATCH) - deactivate item..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }' | jq '.data // .'

# Reactivate for next tests
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}' > /dev/null

# Test 6: Partial UPDATE (PATCH) - update to negative stock (adjustment)
echo -e "\n6️⃣ PARTIAL UPDATE (PATCH) - update to negative stock..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": -5
  }' | jq '.data // .'

# Test 7: Partial UPDATE (PATCH) - update with float values
echo -e "\n7️⃣ PARTIAL UPDATE (PATCH) - update with float values..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": 75.5,
    "min_threshold": 10.2
  }' | jq '.data // .'

# Test 8: Partial UPDATE (PATCH) - clear provider (set to null)
echo -e "\n8️⃣ PARTIAL UPDATE (PATCH) - clear provider..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": null
  }' | jq '.data // .'

# Set provider back for next tests
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{"provider_id": '$PROVIDER_ID'}' > /dev/null

# Test 9: Multiple field PATCH
echo -e "\n9️⃣ PARTIAL UPDATE (PATCH) - update multiple fields at once..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": 60,
    "description": "Regular mozzarella",
    "min_threshold": 12,
    "is_active": true
  }' | jq '.data // .'

# Test 10: ERROR - Invalid unit on update
echo -e "\n❌ ERROR TEST: UPDATE with invalid unit (should fail)..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "unit": "invalid_unit"
  }' | jq '.'

# Test 11: ERROR - Duplicate name on update
echo -e "\n1️⃣0️⃣ Create second item for duplicate test..."
ITEM_2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Other Item '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 25,
    "min_threshold": 5
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

echo -e "\n1️⃣1️⃣ ERROR TEST: UPDATE with duplicate name (should fail)..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_2/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Mozzarella '$TIMESTAMP'"
  }' | jq '.'

# Test 12: ERROR - Non-existent item
echo -e "\n1️⃣2️⃣ ERROR TEST: UPDATE non-existent item (should return 404)..."
curl -s -X PATCH "$BASE_URL/inventory/99999/" \
  -H "Content-Type: application/json" \
  -d '{"current_stock": 50}' -w "\nStatus: %{http_code}\n" | jq '.'

echo -e "\n✅ UPDATE tests completed!"
