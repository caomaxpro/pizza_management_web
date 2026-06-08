#!/bin/bash
# Test Login endpoint

echo "=== Testing Login ==="

curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "password123"
  }' | jq '.'

echo "\n"
