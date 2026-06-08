#!/bin/bash

# Test DELETE inventory items
# Tests DELETE /api/inventory/ endpoints (single and bulk)

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing DELETE Inventory Items"
echo "================================="

# Setup: Create test data
echo -e "\n📦 Setting up test data..."

# Create provider
PROVIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Delete Test Provider '$TIMESTAMP'",
    "category": "fresh",
    "email": "test@example.com",
    "phone": "1234567890",
    "address": "123 Test St"
  }')
PROVIDER_ID=$(echo "$PROVIDER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

# Create multiple test items
echo "Creating test inventory items..."
ITEM_1=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 1 '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 2 '$TIMESTAMP'",
    "unit": "litre",
    "current_stock": 30,
    "min_threshold": 5,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_3=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 3 '$TIMESTAMP'",
    "unit": "pcs",
    "current_stock": 100,
    "min_threshold": 20,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_4=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 4 '$TIMESTAMP'",
    "unit": "box",
    "current_stock": 15,
    "min_threshold": 3
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

echo "✅ Test items created: ID1=$ITEM_1, ID2=$ITEM_2, ID3=$ITEM_3, ID4=$ITEM_4"

# Test 1: Delete single item by ID
echo -e "\n1️⃣ DELETE single item (ID=$ITEM_1)..."
curl -s -X DELETE "$BASE_URL/inventory/$ITEM_1/" -w "\nStatus: %{http_code}\n"

# Test 2: Verify item is deleted
echo -e "\n2️⃣ VERIFY deletion - try to fetch deleted item (should be 404)..."
curl -s -X GET "$BASE_URL/inventory/$ITEM_1/" -w "\nStatus: %{http_code}\n" | jq '.'

# Test 3: Delete many items (bulk delete with IDs)
echo -e "\n3️⃣ DELETE many items (bulk delete with IDs)..."
curl -s -X POST "$BASE_URL/inventory/delete-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$ITEM_2', '$ITEM_3']
  }' | jq '.data // .'

# Test 4: Verify bulk deleted items are gone
echo -e "\n4️⃣ VERIFY bulk deletion - list remaining items..."
curl -s -X GET "$BASE_URL/inventory/" | jq '.data // . | length as $count | "Remaining items: \($count)"'

# Setup for delete-all test
echo -e "\n📦 Creating new items for delete-all test..."
ITEM_5=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 5 '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_6=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item 6 '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 30,
    "min_threshold": 5,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

# Test 5: Delete ALL items
echo -e "\n5️⃣ DELETE ALL items..."
curl -s -X DELETE "$BASE_URL/inventory/delete-all/" | jq '.data // .'

# Test 6: Verify all items are deleted
echo -e "\n6️⃣ VERIFY all deletion - list inventory (should be empty)..."
curl -s -X GET "$BASE_URL/inventory/" | jq '.data // . | length as $count | "Remaining items: \($count)"'

# Setup for delete-by-provider test
echo -e "\n📦 Creating items for delete-by-provider test..."
ITEM_7=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Provider Item 1 '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_8=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Provider Item 2 '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 30,
    "min_threshold": 5,
    "provider_id": '$PROVIDER_ID'
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_9=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "No Provider Item '$TIMESTAMP'",
    "unit": "pcs",
    "current_stock": 100,
    "min_threshold": 20
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

# Test 7: Delete by provider
echo -e "\n7️⃣ DELETE by provider (provider_id=$PROVIDER_ID)..."
curl -s -X POST "$BASE_URL/inventory/delete-by-provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": '$PROVIDER_ID'
  }' | jq '.data // .'

# Test 8: Verify items from provider deleted, others remain
echo -e "\n8️⃣ VERIFY delete-by-provider - item without provider should remain..."
curl -s -X GET "$BASE_URL/inventory/$ITEM_9/" | jq '.data // . | {id, name, provider_id}'

# Test 9: ERROR - Delete non-existent item
echo -e "\n❌ ERROR TEST: DELETE non-existent item (should return 404)..."
curl -s -X DELETE "$BASE_URL/inventory/99999/" -w "\nStatus: %{http_code}\n" | jq '.'

# Test 10: ERROR - delete-many with empty list
echo -e "\n1️⃣0️⃣ ERROR TEST: delete-many with empty IDs list..."
curl -s -X POST "$BASE_URL/inventory/delete-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": []
  }' | jq '.data // .'

# Test 11: ERROR - delete-many without ids param
echo -e "\n1️⃣1️⃣ ERROR TEST: delete-many without 'ids' param (should fail)..."
curl -s -X POST "$BASE_URL/inventory/delete-many/" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

# Test 12: ERROR - delete-by-provider without provider_id
echo -e "\n1️⃣2️⃣ ERROR TEST: delete-by-provider without 'provider_id' param (should fail)..."
curl -s -X POST "$BASE_URL/inventory/delete-by-provider/" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

echo -e "\n✅ DELETE tests completed!"
