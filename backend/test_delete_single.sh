#!/bin/bash

# Quick test for DELETE single endpoint only

BASE_URL="http://127.0.0.1:8000/api"
TIMESTAMP=$(date +%s%N)

echo "=========================================="
echo "🧪 Testing DELETE Single Item"
echo "=========================================="
echo ""

# Create provider
echo "1️⃣ Creating provider..."
PROVIDER=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Provider $TIMESTAMP\", \"category\": \"fresh\", \"email\": \"test@example.com\", \"phone\": \"1234567890\", \"address\": \"123 Main\"}")

PROVIDER_ID=$(echo "$PROVIDER" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Provider ID: $PROVIDER_ID"
echo "$PROVIDER" | python3 -m json.tool
echo ""

# Create inventory
echo "2️⃣ Creating inventory item..."
INVENTORY=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Item $TIMESTAMP\", \"unit\": \"kg\", \"current_stock\": 50, \"min_threshold\": 10, \"max_threshold\": 100, \"provider_id\": $PROVIDER_ID}")

ITEM_ID=$(echo "$INVENTORY" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Item ID: $ITEM_ID"
echo "$INVENTORY" | python3 -m json.tool
echo ""

# Test DELETE
echo "3️⃣ Testing DELETE /api/inventory/$ITEM_ID/"
curl -s -w "\nHTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/inventory/$ITEM_ID/" | python3 -m json.tool
echo ""

# Verify deletion
echo "4️⃣ Verifying item was deleted..."
curl -s -w "\nHTTP Status: %{http_code}\n" -X GET "$BASE_URL/inventory/$ITEM_ID/" | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ Test Complete!"
echo "=========================================="
