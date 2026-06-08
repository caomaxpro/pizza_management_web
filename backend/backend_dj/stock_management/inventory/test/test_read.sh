#!/bin/bash

# Test READ inventory items
# Tests GET /api/inventory/ endpoints

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing READ Inventory Items"
echo "==============================="

# Setup: Create test data
echo -e "\n📦 Setting up test data..."

# Create provider
PROVIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Read Test Provider '$TIMESTAMP'",
    "category": "fresh",
    "email": "test@example.com",
    "phone": "1234567890",
    "address": "123 Test St"
  }')
PROVIDER_ID=$(echo "$PROVIDER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

# Create test items
echo "Creating test inventory items..."
ITEM_1=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item A '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "max_threshold": 100,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item B '$TIMESTAMP'",
    "unit": "litre",
    "current_stock": 30,
    "min_threshold": 5,
    "max_threshold": 50,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

ITEM_3=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Item C Inactive '$TIMESTAMP'",
    "unit": "pcs",
    "current_stock": 0,
    "min_threshold": 10,
    "is_active": false
  }' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

echo "✅ Test items created: ID1=$ITEM_1, ID2=$ITEM_2, ID3=$ITEM_3"

# Test 1: List all inventory
echo -e "\n1️⃣ READ ALL inventory items..."
curl -s -X GET "$BASE_URL/inventory/" | jq 'length as $count | "Total items: \($count)"'

# Test 2: Retrieve single item by ID
echo -e "\n2️⃣ READ single item (ID=$ITEM_1)..."
curl -s -X GET "$BASE_URL/inventory/$ITEM_1/" | jq '.'

# Test 3: Filter by is_active=true
echo -e "\n3️⃣ READ items filtered by is_active=true..."
curl -s -X GET "$BASE_URL/inventory/?is_active=true" | jq 'length as $count | "Active items: \($count)"'

# Test 4: Filter by is_active=false
echo -e "\n4️⃣ READ items filtered by is_active=false..."
curl -s -X GET "$BASE_URL/inventory/?is_active=false" | jq 'length as $count | "Inactive items: \($count)"'

# Test 5: Search by name
echo -e "\n5️⃣ READ items with search query (name contains 'Item A')..."
curl -s -X GET "$BASE_URL/inventory/" -G --data-urlencode 'search=Item A' | jq '. | map(select(.name | contains("Item A"))) | .[0]'

# Test 6: Filter by stock range (min_stock)
echo -e "\n6️⃣ READ items with minimum stock >= 30..."
curl -s -X GET "$BASE_URL/inventory/?min_stock=30" | jq 'length as $count | "Items with stock >= 30: \($count)"'

# Test 7: Filter by stock range (max_stock)
echo -e "\n7️⃣ READ items with maximum stock <= 50..."
curl -s -X GET "$BASE_URL/inventory/?max_stock=50" | jq 'length as $count | "Items with stock <= 50: \($count)"'

# Test 8: Filter by stock range (both min and max)
echo -e "\n8️⃣ READ items with stock between 25-60..."
curl -s -X GET "$BASE_URL/inventory/?min_stock=25&max_stock=60" | jq 'length as $count | "Items in range 25-60: \($count)"'

# Test 9: Test ordering (default is -created_at)
echo -e "\n9️⃣ READ items with default ordering (by -created_at)..."
curl -s -X GET "$BASE_URL/inventory/" | jq '.[0] | {id, name, created_at}'

# Test 10: Read with pagination/limit (just show first 2)
echo -e "\n🔟 READ items (first 2)..."
curl -s -X GET "$BASE_URL/inventory/" | jq '.[0:2] | length as $count | "Showing items: \($count)"'

# Test 11: ERROR - Non-existent item
echo -e "\n❌ ERROR TEST: READ non-existent item (should return 404)..."
curl -s -X GET "$BASE_URL/inventory/99999/" -w "\nStatus: %{http_code}\n" | jq '.'

# Test 12: Read low stock items (if endpoint exists)
echo -e "\n1️⃣2️⃣ READ low stock items..."
curl -s -X GET "$BASE_URL/inventory/low-stock/" | jq 'length as $count | "Low stock items: \($count)"' || echo "Endpoint might not exist or no low stock items"

echo -e "\n✅ READ tests completed!"
