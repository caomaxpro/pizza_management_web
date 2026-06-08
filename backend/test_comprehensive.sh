#!/bin/bash

# ============================================================================
# User Management Mixins - Comprehensive cURL Test
# ============================================================================
# Test Auth, Create, Read, Update, Delete with proper endpoints
# ============================================================================

API="http://localhost:8000/api"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║ User Management Mixins - cURL Test (Proper Endpoints) ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ====================
# [1] CREATE USER - POST /api/auth/register/
# ====================
echo -e "${YELLOW}[1] CREATE USER - Registration${NC}"
echo "POST $API/auth/register/"
echo ""

CREATE_RESPONSE=$(curl -s -X POST "$API/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser123@mail.com",
    "username": "testuser123",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
  }')

echo "$CREATE_RESPONSE" | python -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"
echo ""
echo ""

# ====================
# [2] LOGIN USER - POST /api/auth/login/
# ====================
echo -e "${YELLOW}[2] LOGIN USER - Get JWT Tokens${NC}"
echo "POST $API/auth/login/"
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser123",
    "password": "TestPass123!"
  }')

echo "$LOGIN_RESPONSE" | python -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo ""
echo -e "${GREEN}Token extracted: ${TOKEN:0:30}...${NC}"
echo ""
echo ""

if [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Could not get token! Skipping authenticated tests${NC}"
  exit 1
fi

# ====================
# [3] GET CURRENT USER PROFILE - GET /api/users/me/
# ====================
echo -e "${YELLOW}[3] GET CURRENT USER PROFILE${NC}"
echo "GET $API/users/me/ (with token)"
echo ""

curl -s -X GET "$API/users/me/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool 2>/dev/null || echo "Error getting profile"

echo ""
echo ""

# ====================
# [4] LIST ALL USERS - GET /api/users/
# ====================
echo -e "${YELLOW}[4] LIST ALL USERS${NC}"
echo "GET $API/users/ (with token)"
echo ""

# Without token (should fail)
echo -e "${RED}❌ Without authentication:${NC}"
curl -s -X GET "$API/users/" \
  -H "Content-Type: application/json" \
  | head -1

echo ""

# With token (should work)
echo -e "${GREEN}✓ With authentication:${NC}"
curl -s -X GET "$API/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool 2>/dev/null | head -30

echo ""
echo ""

# ====================
# [5] CREATE ANOTHER USER (for testing) - POST /api/auth/register/
# ====================
echo -e "${YELLOW}[5] CREATE ANOTHER USER FOR TESTING${NC}"
echo "POST $API/auth/register/"
echo ""

ANOTHER_USER=$(curl -s -X POST "$API/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user2test@mail.com",
    "username": "user2test",
    "password": "TestPass123!",
    "first_name": "User",
    "last_name": "Two",
    "phone_number": "+9876543210"
  }')

USER2_ID=$(echo "$ANOTHER_USER" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "$ANOTHER_USER" | python -m json.tool 2>/dev/null | head -20
echo ""
echo -e "${GREEN}✓ User 2 ID: $USER2_ID${NC}"
echo ""
echo ""

# ====================
# [6] RETRIEVE SINGLE USER - GET /api/users/{id}/
# ====================
if [ -n "$USER2_ID" ]; then
  echo -e "${YELLOW}[6] RETRIEVE SINGLE USER${NC}"
  echo "GET $API/users/$USER2_ID/ (with token)"
  echo ""

  curl -s -X GET "$API/users/$USER2_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    | python -m json.tool 2>/dev/null || echo "Error"

  echo ""
  echo ""

  # ====================
  # [7] UPDATE USER - PATCH /api/users/{id}/
  # ====================
  echo -e "${YELLOW}[7] UPDATE USER (PATCH)${NC}"
  echo "PATCH $API/users/$USER2_ID/"
  echo ""

  UPDATE_RESPONSE=$(curl -s -X PATCH "$API/users/$USER2_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "first_name": "UpdatedName",
      "last_name": "ModifiedUser"
    }')

  echo "$UPDATE_RESPONSE" | python -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"

  echo ""
  echo ""

  # ====================
  # [8] DELETE USER -DELETE /api/users/{id}/
  # ====================
  echo -e "${YELLOW}[8] DELETE USER${NC}"
  echo "DELETE $API/users/$USER2_ID/"
  echo ""

  # Try without admin (should fail)
  echo -e "${RED}❌ Regular user trying to delete (should fail with 403):${NC}"
  DELETE_NO_ADMIN=$(curl -s -w "\nStatus: %{http_code}" -X DELETE "$API/users/$USER2_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "$DELETE_NO_ADMIN"

  echo ""
fi

# ====================
# [9] LOGOUT - POST /api/auth/logout/
# ====================
echo -e "${YELLOW}[9] LOGOUT${NC}"
echo "POST $API/auth/logout/"
echo ""

curl -s -X POST "$API/auth/logout/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool 2>/dev/null || echo "Logged out"

echo ""
echo ""

# ====================
# Summary
# ====================
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              Test Summary                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Tests Completed:${NC}"
echo "  1. CREATE MIXIN: User registration via /api/auth/register/"
echo "  2. AUTH MIXIN: Login via /api/auth/login/"
echo "  3. READ MIXIN: Current user profile via /api/users/me/"
echo "  4. READ MIXIN: List all users via /api/users/ (requires auth)"
echo "  5. CREATE MIXIN: Create another user"
echo "  6. READ MIXIN: Retrieve single user"
echo "  7. UPDATE MIXIN: PATCH user update (requires auth)"
echo "  8. DELETE MIXIN: DELETE user (admin only)"
echo "  9. AUTH MIXIN: Logout"
echo ""
echo -e "${YELLOW}Expected Status Codes:${NC}"
echo "  201: Created successfully"
echo "  200: OK / Success"
echo "  401: Unauthorized (not authenticated)"
echo "  403: Forbidden (non-admin trying to delete)"
echo "  204: No Content (successful delete)"
echo ""
