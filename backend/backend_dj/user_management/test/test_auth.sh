#!/bin/bash
# Test User Authentication endpoints

echo "========================================="
echo "User Authentication API - Test Suite"
echo "========================================="

BASE_URL="http://localhost:8000/api"

echo ""
echo "=== 1. Register New User ==="
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser123@example.com",
    "username": "testuser123",
    "password": "SecurePassword123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
  }')

echo "$REGISTER_RESPONSE" | jq '.'

echo ""
echo "=== 2. Login User ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser123@example.com",
    "password": "SecurePassword123"
  }')

echo "$LOGIN_RESPONSE" | jq '.'

# Extract tokens from login response
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access' 2>/dev/null)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh' 2>/dev/null)

echo ""
echo "=== 3. Get Current User Profile (using access token) ==="
curl -s -X GET $BASE_URL/users/me/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

echo ""
echo "=== 4. List Users (staff view) ==="
curl -s -X GET $BASE_URL/users/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

echo ""
echo "=== 5. Logout User ==="
curl -s -X POST $BASE_URL/auth/logout/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}" | jq '.'

echo ""
echo "========================================="
echo "Authentication tests completed!"
echo "========================================="
