#!/bin/bash
# Test Logout endpoint

echo "=== Testing Logout ==="
TOKEN="your_jwt_token_here"
REFRESH="your_refresh_token_here"

curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}" | jq '.'

echo "\n"
