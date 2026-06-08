#!/bin/bash
# Test Create User endpoint

echo "=== Testing Create User ==="
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'

echo "\n"
