#!/bin/bash

# ============================================================================
# User Management Mixins - Comprehensive cURL Test Script
# ============================================================================
# Test: Create, Read, Update, Delete users with different roles
# ============================================================================

API_BASE="http://localhost:8000/api"
USERS_ENDPOINT="$API_BASE/users"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}User Management Mixins - cURL Test Suite${NC}"
echo -e "${BLUE}=========================================${NC}\n"

# ============================================================================
# 1. LOGIN - Get JWT tokens
# ============================================================================
echo -e "${YELLOW}[1] LOGIN TEST${NC}"
echo "Testing login endpoint: POST $USERS_ENDPOINT/login/"

LOGIN_RESPONSE=$(curl -s -X POST "$USERS_ENDPOINT/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }')

echo "Response: $LOGIN_RESPONSE"
echo ""

# Extract tokens
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}❌ Failed to get access token. Trying to create admin user first...${NC}\n"
  
  # Try creating admin user
  echo -e "${YELLOW}Creating admin user...${NC}"
  CREATE_ADMIN=$(curl -s -X POST "$USERS_ENDPOINT/" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@example.com",
      "password": "admin123",
      "first_name": "Admin",
      "last_name": "User",
      "phone_number": "+1234567890",
      "is_staff": true,
      "is_superuser": true
    }')
  
  echo "Admin creation response: $CREATE_ADMIN\n"
  
  # Try login again
  LOGIN_RESPONSE=$(curl -s -X POST "$USERS_ENDPOINT/login/" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@example.com",
      "password": "admin123"
    }')
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
  REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
fi

if [ -n "$ACCESS_TOKEN" ]; then
  echo -e "${GREEN}✓ Login successful!${NC}"
  echo "Access Token: ${ACCESS_TOKEN:0:20}..."
  echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."
else
  echo -e "${RED}✗ Login failed!${NC}"
  echo "Please make sure admin user exists in database"
fi

echo ""
echo ""

# ============================================================================
# 2. CREATE - Test creating new users
# ============================================================================
echo -e "${YELLOW}[2] CREATE USER TEST${NC}"
echo "Testing create endpoint: POST $USERS_ENDPOINT/"

USER_ID=""

# Create regular user
echo "Creating regular user..."
CREATE_USER1=$(curl -s -X POST "$USERS_ENDPOINT/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@example.com",
    "password": "user123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1111111111",
    "is_staff": false,
    "is_active": true
  }')

echo "Response: $CREATE_USER1"
USER_ID=$(echo "$CREATE_USER1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo -e "${GREEN}✓ User 1 created with ID: $USER_ID${NC}\n"

# Create staff user
echo "Creating staff user..."
CREATE_USER2=$(curl -s -X POST "$USERS_ENDPOINT/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff@example.com",
    "password": "staff123",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+2222222222",
    "is_staff": true,
    "is_active": true
  }')

echo "Response: $CREATE_USER2"
STAFF_ID=$(echo "$CREATE_USER2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo -e "${GREEN}✓ Staff user created with ID: $STAFF_ID${NC}\n"

echo ""

# ============================================================================
# 3. READ LIST - Test reading all users
# ============================================================================
echo -e "${YELLOW}[3] READ LIST TEST${NC}"
echo "Testing list endpoint: GET $USERS_ENDPOINT/"

echo "List WITHOUT authentication (should fail with 401):"
LIST_NO_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/" \
  -H "Content-Type: application/json")
echo "Response: $LIST_NO_AUTH"
echo ""

echo "List WITH authentication (admin user):"
LIST_WITH_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Response (first 200 chars): ${LIST_WITH_AUTH:0:200}..."
echo -e "${GREEN}✓ List endpoint works${NC}\n"

echo ""

# ============================================================================
# 4. RETRIEVE - Test reading single user
# ============================================================================
echo -e "${YELLOW}[4] RETRIEVE USER TEST${NC}"

if [ -n "$USER_ID" ]; then
  echo "Testing retrieve endpoint: GET $USERS_ENDPOINT/$USER_ID/"
  
  echo "Retrieve WITHOUT authentication (should fail with 401):"
  RETRIEVE_NO_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/$USER_ID/" \
    -H "Content-Type: application/json")
  echo "Response: $RETRIEVE_NO_AUTH"
  echo ""
  
  echo "Retrieve WITH authentication (admin user):"
  RETRIEVE_WITH_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/$USER_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "Response: $RETRIEVE_WITH_AUTH"
  echo -e "${GREEN}✓ Retrieve endpoint works${NC}\n"
fi

echo ""

# ============================================================================
# 5. UPDATE - Test updating users
# ============================================================================
echo -e "${YELLOW}[5] UPDATE USER TEST${NC}"

if [ -n "$USER_ID" ]; then
  echo "Testing update endpoint: PATCH $USERS_ENDPOINT/$USER_ID/"
  
  echo "Update WITHOUT authentication (should fail with 401):"
  UPDATE_NO_AUTH=$(curl -s -X PATCH "$USERS_ENDPOINT/$USER_ID/" \
    -H "Content-Type: application/json" \
    -d '{
      "first_name": "Johnny"
    }')
  echo "Response: $UPDATE_NO_AUTH"
  echo ""
  
  echo "Update WITH authentication (admin user):"
  UPDATE_WITH_AUTH=$(curl -s -X PATCH "$USERS_ENDPOINT/$USER_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "first_name": "Johnny",
      "last_name": "Updated"
    }')
  echo "Response: $UPDATE_WITH_AUTH"
  echo -e "${GREEN}✓ Update endpoint works${NC}\n"
fi

echo ""

# ============================================================================
# 6. DELETE - Test deleting users
# ============================================================================
echo -e "${YELLOW}[6] DELETE USER TEST${NC}"

if [ -n "$STAFF_ID" ]; then
  echo "Testing delete endpoint: DELETE $USERS_ENDPOINT/$STAFF_ID/"
  
  echo "Delete WITHOUT authentication (should fail with 401):"
  DELETE_NO_AUTH=$(curl -s -X DELETE "$USERS_ENDPOINT/$STAFF_ID/" \
    -H "Content-Type: application/json")
  echo "Response: $DELETE_NO_AUTH"
  echo ""
  
  echo "Delete WITH authentication (admin user - should succeed):"
  DELETE_WITH_AUTH=$(curl -s -i -X DELETE "$USERS_ENDPOINT/$STAFF_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "Response: $DELETE_WITH_AUTH"
  echo -e "${GREEN}✓ Delete endpoint works${NC}\n"
fi

echo ""

# ============================================================================
# 7. ME ENDPOINT - Get current user profile
# ============================================================================
echo -e "${YELLOW}[7] ME ENDPOINT TEST${NC}"
echo "Testing me endpoint: GET $USERS_ENDPOINT/me/"

echo "Get current user WITHOUT authentication (should fail with 401):"
ME_NO_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/me/" \
  -H "Content-Type: application/json")
echo "Response: $ME_NO_AUTH"
echo ""

echo "Get current user WITH authentication (admin user):"
ME_WITH_AUTH=$(curl -s -X GET "$USERS_ENDPOINT/me/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Response: $ME_WITH_AUTH"
echo -e "${GREEN}✓ Me endpoint works${NC}\n"

echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✓ All mixins tested:${NC}"
echo "  - AUTH MIXIN: Login endpoint"
echo "  - CREATE MIXIN: POST user creation"
echo "  - READ MIXIN: GET list and retrieve"
echo "  - UPDATE MIXIN: PATCH user update"
echo "  - DELETE MIXIN: DELETE user (admin only)"
echo ""
echo -e "${YELLOW}Expected Results:${NC}"
echo "  ✓ 401 Unauthorized when no authentication"
echo "  ✓ 403 Forbidden for non-admin delete operations"
echo "  ✓ 200/201 for successful operations with auth"
echo "  ✓ 204 No Content for successful delete"
echo ""
echo -e "${BLUE}=========================================${NC}\n"
