#!/bin/bash
# Test Delete User endpoint

echo "=== Testing Delete User ==="
TOKEN="your_jwt_token_here"
USER_ID=1

curl -X DELETE http://localhost:8000/api/users/$USER_ID/ \
  -H "Authorization: Bearer $TOKEN"

echo "\n"
