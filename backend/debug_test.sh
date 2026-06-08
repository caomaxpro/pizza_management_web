#!/bin/bash

BASE_URL="http://127.0.0.1:8000/api"

echo "Testing API responses..."
echo ""

echo "1️⃣ Creating a provider..."
RESPONSE=$(curl -s -X POST "$BASE_URL/provider/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Provider", "category": "supplier", "email": "test@example.com", "phone": "1234567890", "address": "123 Main"}')

echo "Raw response:"
echo "$RESPONSE"
echo ""

echo "Extracted ID:"
PROVIDER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Provider ID: $PROVIDER_ID"
echo ""

if [ -z "$PROVIDER_ID" ]; then
  echo "❌ Failed to extract ID - trying alternative extraction..."
  echo "$RESPONSE" | python3 -m json.tool
  exit 1
fi

echo "2️⃣ Creating inventory item..."
INVENTORY=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Item\", \"unit\": \"kg\", \"current_stock\": 50, \"min_threshold\": 10, \"max_threshold\": 100, \"provider_id\": $PROVIDER_ID}")

echo "Raw response:"
echo "$INVENTORY"
echo ""

ITEM_ID=$(echo "$INVENTORY" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Item ID: $ITEM_ID"
echo ""

echo "3️⃣ Testing DELETE single endpoint..."
echo "URL: DELETE $BASE_URL/inventory/$ITEM_ID/"
curl -s -w "\nHTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/inventory/$ITEM_ID/"
