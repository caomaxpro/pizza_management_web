#!/bin/bash
# Complete curl test suite for User Management API

echo "========================================="
echo "User Management API - Complete Test Suite"
echo "========================================="

TOKEN="your_jwt_token_here"
BASE_URL="http://localhost:8000/api"

echo "\n=== 1. List Users ==="
curl $BASE_URL/users/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n=== 2. Get Current User Profile ==="
curl $BASE_URL/users/me/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n=== 3. Get User Detail ==="
curl $BASE_URL/users/1/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n=== 4. Create User ==="
curl -X POST $BASE_URL/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User"
  }'

echo "\n\n=== 5. Update User ==="
curl -X PATCH $BASE_URL/users/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'

echo "\n\n=== 6. Change Password ==="
curl -X POST $BASE_URL/users/1/set_password/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPass123",
    "new_password": "NewPass456"
  }'

echo "\n\n=== 7. Create Address ==="
curl -X POST $BASE_URL/addresses/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "street": "123 Main St",
    "city": "Toronto",
    "state": "ON",
    "postal_code": "M5H 2N2",
    "country": "Canada",
    "latitude": 43.6629,
    "longitude": -79.3957
  }'

echo "\n\n=== 8. List Addresses ==="
curl $BASE_URL/addresses/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n=== 9. Set Default Address ==="
curl -X POST $BASE_URL/addresses/1/set_default/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n=== 10. Delete Address ==="
curl -X DELETE $BASE_URL/addresses/1/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n\n==========================================="
echo "Tests completed!"
echo "==========================================="
