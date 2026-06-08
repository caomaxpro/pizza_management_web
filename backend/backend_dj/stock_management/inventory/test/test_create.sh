#!/bin/bash

# Test CREATE inventory items
# Tests POST /api/inventory/ endpoint

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)

echo "🧪 Testing CREATE Inventory Items"
echo "=================================="

# Create Provider first for tests
echo -e "\n📦 Creating test provider..."
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
echo "✅ Provider created: ID=$PROVIDER_ID"

# Test 1: Create with full data
echo -e "\n1️⃣ CREATE with FULL data (all fields)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Basil '$TIMESTAMP'",
    "description": "Organic basil leaves from local farm",
    "unit": "g",
    "current_stock": 100,
    "min_threshold": 20,
    "max_threshold": 500,
    "provider_id": '$PROVIDER_ID',
    "is_active": true
  }' | jq '.data // .'

# Test 2: Create with minimal data
echo -e "\n2️⃣ CREATE with MINIMAL data (required fields only)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomato Sauce '$TIMESTAMP'",
    "unit": "litre",
    "current_stock": 30,
    "min_threshold": 5
  }' | jq '.data // .'

# Test 3: Create without provider (optional FK)
echo -e "\n3️⃣ CREATE without provider (optional FK)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Generic Item '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10
  }' | jq '.data // .'

# Test 4: Create with negative stock (adjustment)
echo -e "\n4️⃣ CREATE with NEGATIVE stock (adjustment scenario)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Adjustment Item '$TIMESTAMP'",
    "unit": "pcs",
    "current_stock": -5,
    "min_threshold": 10
  }' | jq '.data // .'

# Test 5: Create with float values
echo -e "\n5️⃣ CREATE with FLOAT values..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Precision Item '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 25.5,
    "min_threshold": 5.2,
    "max_threshold": 100.75
  }' | jq '.data // .'

# Test 6: Create with inactive status
echo -e "\n6️⃣ CREATE with INACTIVE status..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Inactive Item '$TIMESTAMP'",
    "unit": "box",
    "current_stock": 0,
    "min_threshold": 5,
    "is_active": false
  }' | jq '.data // .'

# Test 7: ERROR - Duplicate name
echo -e "\n❌ ERROR TEST: CREATE with DUPLICATE name (should fail)..."
DUPLICATE_NAME="Fresh Basil '$TIMESTAMP'"
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'$DUPLICATE_NAME'",
    "unit": "kg",
    "current_stock": 100,
    "min_threshold": 20
  }' | jq '.'

# Test 8: ERROR - Missing required field
echo -e "\n❌ ERROR TEST: CREATE without required field (should fail)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "unit": "kg",
    "current_stock": 50
  }' | jq '.'

# Test 9: ERROR - Invalid unit
echo -e "\n❌ ERROR TEST: CREATE with INVALID unit (should fail)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Unit '$TIMESTAMP'",
    "unit": "invalid_unit",
    "current_stock": 50,
    "min_threshold": 10
  }' | jq '.'

# Test 10: ERROR - Non-existent provider
echo -e "\n❌ ERROR TEST: CREATE with non-existent provider (should fail)..."
curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bad Provider Item '$TIMESTAMP'",
    "unit": "kg",
    "current_stock": 50,
    "min_threshold": 10,
    "provider_id": 99999
  }' | jq '.'

echo -e "\n✅ CREATE tests completed!"
