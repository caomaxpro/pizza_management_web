#!/bin/bash
# Test Update User endpoints

echo "=== Testing Update User ==="
TOKEN="your_jwt_token_here"
USER_ID=1

curl -X PATCH http://localhost:8000/api/users/$USER_ID/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "phone_number": "+0987654321"
  }'

echo "\n"

echo "=== Testing Change Password ==="
curl -X POST http://localhost:8000/api/users/$USER_ID/set_password/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPass123",
    "new_password": "NewPass456"
  }'

echo "\n"
