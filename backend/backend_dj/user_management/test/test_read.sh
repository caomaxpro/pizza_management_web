#!/bin/bash
# Test Read User endpoints

echo "=== Testing Get Current User ==="
TOKEN="your_jwt_token_here"

curl http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n"

echo "=== Testing List Users ==="
curl http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n"

echo "=== Testing Get User Detail ==="
USER_ID=1

curl http://localhost:8000/api/users/$USER_ID/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n"
