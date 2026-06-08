#!/bin/bash

# Test script for DELETE endpoints
# Tests: delete single, delete-all, delete-many, delete-by-provider

BASE_URL="http://127.0.0.1:8000/api"
TIMESTAMP=$(date +%s%N)  # Unique timestamp to avoid duplicate names

echo "=========================================="
echo "🚀 Testing DELETE Endpoints"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1️⃣ CREATE TEST DATA - Providers
echo "1️⃣ Creating providers..."
PROVIDER1=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Pizza Supplier A $TIMESTAMP\", \"category\": \"supplier\", \"email\": \"supplier_a@example.com\", \"phone\": \"1234567890\", \"address\": \"123 Main St\"}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

PROVIDER2=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Pizza Supplier B $TIMESTAMP\", \"category\": \"supplier\", \"email\": \"supplier_b@example.com\", \"phone\": \"0987654321\", \"address\": \"456 Oak Ave\"}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

echo -e "✅ Provider 1 ID: ${GREEN}${PROVIDER1}${NC}"
echo -e "✅ Provider 2 ID: ${GREEN}${PROVIDER2}${NC}"
echo ""

# 2️⃣ CREATE INVENTORY ITEMS
echo "2️⃣ Creating inventory items..."
ITEM1=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Mozzarella $TIMESTAMP\", \"description\": \"Fresh mozzarella\", \"unit\": \"kg\", \"min_threshold\": 10, \"max_threshold\": 100, \"current_stock\": 100, \"provider_id\": ${PROVIDER1}}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

ITEM2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Tomato Sauce $TIMESTAMP\", \"description\": \"Italian tomato sauce\", \"unit\": \"litre\", \"min_threshold\": 5, \"max_threshold\": 50, \"current_stock\": 50, \"provider_id\": ${PROVIDER1}}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

ITEM3=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Pepperoni $TIMESTAMP\", \"description\": \"Sliced pepperoni\", \"unit\": \"kg\", \"min_threshold\": 8, \"max_threshold\": 100, \"current_stock\": 30, \"provider_id\": ${PROVIDER2}}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

ITEM4=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Mushrooms $TIMESTAMP\", \"description\": \"Fresh mushrooms\", \"unit\": \"kg\", \"min_threshold\": 6, \"max_threshold\": 100, \"current_stock\": 25, \"provider_id\": ${PROVIDER2}}" \
  | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

echo -e "✅ Item 1 ID: ${GREEN}${ITEM1}${NC} (Mozzarella - Provider A)"
echo -e "✅ Item 2 ID: ${GREEN}${ITEM2}${NC} (Tomato Sauce - Provider A)"
echo -e "✅ Item 3 ID: ${GREEN}${ITEM3}${NC} (Pepperoni - Provider B)"
echo -e "✅ Item 4 ID: ${GREEN}${ITEM4}${NC} (Mushrooms - Provider B)"
echo ""

# LIST ALL BEFORE DELETION
echo "3️⃣ All inventory items (BEFORE deletion):"
curl -s "$BASE_URL/inventory/" | python3 -m json.tool | head -30
echo ""

echo "=========================================="
echo "🧪 Testing DELETE Endpoints"
echo "=========================================="
echo ""

# TEST 1: DELETE SINGLE ITEM
echo "TEST 1️⃣: Delete single item (DELETE /api/inventory/{id}/)"
echo "Command: DELETE /api/inventory/${ITEM1}/"
RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/inventory/${ITEM1}/")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
echo -e "Status: ${GREEN}${HTTP_CODE}${NC}"
echo ""

# TEST 2: DELETE MANY ITEMS
echo "TEST 2️⃣: Delete multiple items (POST /api/inventory/delete-many/)"
echo "Command: POST /api/inventory/delete-many/"
echo "Body: {\"ids\": [${ITEM2}, ${ITEM3}]}"
curl -s -X POST "$BASE_URL/inventory/delete-many/" \
  -H "Content-Type: application/json" \
  -d "{\"ids\": [${ITEM2}, ${ITEM3}]}" | python3 -m json.tool
echo ""

# TEST 3: DELETE BY PROVIDER
echo "TEST 3️⃣: Delete by provider (POST /api/inventory/delete-by-provider/)"
echo "Command: POST /api/inventory/delete-by-provider/"
echo "Body: {\"provider_id\": ${PROVIDER2}}"
curl -s -X POST "$BASE_URL/inventory/delete-by-provider/" \
  -H "Content-Type: application/json" \
  -d "{\"provider_id\": ${PROVIDER2}}" | python3 -m json.tool
echo ""

# LIST ALL AFTER SOME DELETIONS
echo "4️⃣ Remaining inventory items (after deletions):"
curl -s "$BASE_URL/inventory/" | python3 -m json.tool
echo ""

# TEST 4: DELETE ALL
echo "TEST 4️⃣: Delete ALL items (DELETE /api/inventory/delete-all/)"
echo "Command: DELETE /api/inventory/delete-all/"
curl -s -X DELETE "$BASE_URL/inventory/delete-all/" | python3 -m json.tool
echo ""

# LIST ALL AFTER DELETE-ALL
echo "5️⃣ Final inventory list (should be empty):"
curl -s "$BASE_URL/inventory/" | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ DELETE Endpoints Testing Complete!"
echo "=========================================="
echo ""
