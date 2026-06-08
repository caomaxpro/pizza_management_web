#!/bin/bash
# Test Register endpoint

echo "=== Testing Register ==="

curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }' | jq '.'

echo "\n"
