#!/bin/bash

# Test BULK UPDATE provider operations
# Tests PATCH /api/provider/update-many/ and /api/provider/update-all/

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing BULK UPDATE Provider Operations"
echo "=========================================="

# Setup: Create test providers
echo -e "\n📦 Setting up test data..."
PROVIDER_1=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Provider 1 '$TIMESTAMP'",
    "category": "fresh",
    "email": "p1@example.com",
    "phone": "1111111111",
    "address": "Address 1"
  }' | jq '.id')

PROVIDER_2=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Provider 2 '$TIMESTAMP'",
    "category": "frozen",
    "email": "p2@example.com",
    "phone": "2222222222",
    "address": "Address 2"
  }' | jq '.id')

PROVIDER_3=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Provider 3 '$TIMESTAMP'",
    "category": "dairy",
    "email": "p3@example.com",
    "phone": "3333333333",
    "address": "Address 3"
  }' | jq '.id')

echo "✅ Test providers created: ID1=$PROVIDER_1, ID2=$PROVIDER_2, ID3=$PROVIDER_3"

# Test 1: Update many - update multiple providers
echo -e "\n1️⃣ UPDATE MANY - update 2 providers..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$PROVIDER_1', '$PROVIDER_2'],
    "category": "premium"
  }' | jq '{
    message: .message,
    count: .count,
    updated_names: [.updated_providers[].name]
  }'

# Test 2: Verify providers were updated
echo -e "\n2️⃣ VERIFY - read updated providers..."
curl -s -X GET "$BASE_URL/provider/$PROVIDER_1/" | jq '{id, name, category}'
echo ""
curl -s -X GET "$BASE_URL/provider/$PROVIDER_2/" | jq '{id, name, category}'

# Test 3: Update many - with phone and email
echo -e "\n3️⃣ UPDATE MANY - update multiple fields..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$PROVIDER_2', '$PROVIDER_3'],
    "phone": "9999999999",
    "email": "bulk@example.com"
  }' | jq '{
    message: .message,
    count: .count
  }'

# Test 4: Update all - update ALL providers
echo -e "\n4️⃣ UPDATE ALL - activate all providers..."
curl -s -X PATCH "$BASE_URL/provider/update-all/" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true
  }' | jq '{
    message: .message,
    count: .count
  }'

# Test 5: Verify all were updated
echo -e "\n5️⃣ VERIFY - list all providers..."
curl -s -X GET "$BASE_URL/provider/" | jq '. | map({id, name, is_active}) | .[0:3]'

# Test 6: Update all - change all addresses
echo -e "\n6️⃣ UPDATE ALL - change all addresses..."
curl -s -X PATCH "$BASE_URL/provider/update-all/" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main Street, City"
  }' | jq '{
    message: .message,
    count: .count,
    sample_address: .updated_providers[0].address
  }'

# Test 7: ERROR - Update many without IDs
echo -e "\n❌ ERROR TEST: UPDATE MANY without ids (should fail)..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "new"
  }' | jq '.'

# Test 8: ERROR - Update many with empty IDs list
echo -e "\n❌ ERROR TEST: UPDATE MANY with empty ids (should fail)..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": [],
    "category": "new"
  }' | jq '.'

# Test 9: ERROR - Update many without fields
echo -e "\n❌ ERROR TEST: UPDATE MANY without fields (should fail)..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$PROVIDER_1']
  }' | jq '.'

# Test 10: ERROR - Update all without fields
echo -e "\n❌ ERROR TEST: UPDATE ALL without fields (should fail)..."
curl -s -X PATCH "$BASE_URL/provider/update-all/" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

# Test 11: Update many with invalid category (should fail)
echo -e "\n❌ ERROR TEST: UPDATE MANY with invalid category..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$PROVIDER_1'],
    "category": "invalid_category"
  }' | jq '.error // .'

# Test 12: Update many - partial names (invalid duplicates)
echo -e "\n❌ ERROR TEST: UPDATE MANY - set duplicate names..."
curl -s -X PATCH "$BASE_URL/provider/update-many/" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ['$PROVIDER_2'],
    "name": "'$(curl -s -X GET "$BASE_URL/provider/$PROVIDER_1/" | jq -r '.name')'"
  }' | jq '.error // .'

echo -e "\n✅ BULK UPDATE tests completed!"
