#!/bin/bash

# ============================================================================
# User Management Mixins - Simple cURL Test
# ============================================================================

API="http://localhost:8000/api"
echo "🚀 Testing User Management Mixins with cURL"
echo "================================================"
echo ""

# Test 1: Check if server is running
echo "📌 [TEST 1] Server Health Check"
curl -s "$API/users/login/" | head -1
echo ""
echo ""

# Test 2: Try to create a user WITHOUT auth (should work for public registration)
echo "📌 [TEST 2] CREATE User (Public Registration)"
echo "POST $API/users/"
curl -s -X POST "$API/users/" \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@mail.com","password":"pass123","first_name":"Test","last_name":"User","phone_number":"+1234567890"}' \
  | python -m json.tool
echo ""
echo ""

# Test 3: Try to LOGIN
echo "📌 [TEST 3] LOGIN (Get JWT Tokens)"
echo "POST $API/users/login/"
LOGIN_RESPONSE=$(curl -s -X POST "$API/users/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@mail.com","password":"pass123"}')

echo "$LOGIN_RESPONSE" | python -m json.tool

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo ""
echo "Extracted Token: ${TOKEN:0:20}..."
echo ""
echo ""

# Test 4: Try LIST without token (should get 401)
echo "📌 [TEST 4] LIST Users WITHOUT Authentication"
echo "GET $API/users/ (no token)"
curl -s -X GET "$API/users/" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# Test 5: Try LIST with token
if [ -n "$TOKEN" ]; then
  echo "📌 [TEST 5] LIST Users WITH Authentication"
  echo "GET $API/users/ (with token)"
  curl -s -X GET "$API/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    | python -m json.tool | head -30
  echo ""
  echo ""

  # Test 6: Try GET ME endpoint
  echo "📌 [TEST 6] Get Current User Profile"
  echo "GET $API/users/me/"
  curl -s -X GET "$API/users/me/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    | python -m json.tool
  echo ""
  echo ""
else
  echo "❌ Could not extract token, skipping authenticated tests"
fi

echo ""
echo "================================================"
echo "✅ Test Suite Complete!"
echo "================================================"
