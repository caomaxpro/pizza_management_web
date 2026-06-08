#!/bin/bash

# Inventory API curl test script
# Run this to test the inventory endpoints

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing Inventory API Endpoints"
echo "=================================="

# 1. Create Provider first
echo -e "\n1️⃣ Creating Provider..."
PROVIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Provider '$TIMESTAMP'",
    "category": "fresh",
    "email": "test@example.com",
    "phone": "1234567890",
    "address": "123 Test St"
  }')

PROVIDER_ID=$(echo "$PROVIDER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo "Provider created: ID=$PROVIDER_ID"
echo "Response: $PROVIDER_RESPONSE"

# 2. Create Inventory
echo -e "\n2️⃣ Creating Inventory Item..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Basil '$TIMESTAMP'",
    "description": "Organic basil leaves",
    "unit": "g",
    "current_stock": 100,
    "min_threshold": 20,
    "max_threshold": 500,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }')

ITEM_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo "Item created: ID=$ITEM_ID"
echo "Response: $CREATE_RESPONSE"

# 3. List Inventory
echo -e "\n3️⃣ Fetching Inventory List..."
curl -s -X GET "$BASE_URL/inventory/" | jq '.'

# 4. Retrieve Single Item
echo -e "\n4️⃣ Retrieving Single Item (ID=$ITEM_ID)..."
curl -s -X GET "$BASE_URL/inventory/$ITEM_ID/" | jq '.'

# 5. Update Inventory (PATCH)
echo -e "\n5️⃣ Updating Inventory Item (PATCH)..."
curl -s -X PATCH "$BASE_URL/inventory/$ITEM_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": 150,
    "description": "Updated description"
  }' | jq '.'

# 6. Delete Inventory
echo -e "\n6️⃣ Deleting Inventory Item (ID=$ITEM_ID)..."
curl -s -X DELETE "$BASE_URL/inventory/$ITEM_ID/" -w "\nStatus: %{http_code}\n"

# 7. Verify Deletion
echo -e "\n7️⃣ Verifying Deletion..."
curl -s -X GET "$BASE_URL/inventory/$ITEM_ID/" 2>&1 | jq '.' || echo "Item not found (expected)"

# 8. Test Bulk Operations
echo -e "\n8️⃣ Testing Bulk Operations..."
echo "Creating 3 items for bulk tests..."

for i in {1..3}; do
  curl -s -X POST "$BASE_URL/inventory/" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Bulk Item '$i' '$TIMESTAMP'",
      "unit": "kg",
      "current_stock": '$((i*10))',
      "min_threshold": 5,
      "provider_id": '$PROVIDER_ID'
    }' > /dev/null
done

echo "✅ Bulk items created"

# 9. Test delete-all
echo -e "\n9️⃣ Testing DELETE /api/inventory/delete-all/..."
curl -s -X DELETE "$BASE_URL/inventory/delete-all/" | jq '.'

echo -e "\n✅ All tests completed!"
