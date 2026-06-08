#!/bin/bash
# ============================================================
# Test: Role assignment, staff creation, and task listing
# Endpoints covered:
#   POST   /api/users/                    - Customer self-register (no auth)
#   POST   /api/users/create-staff/       - Create staff/manager (admin/manager only)
#   PATCH  /api/users/<id>/assign-role/   - Change user role (admin/manager only)
#   GET    /api/users/<id>/tasks/         - List tasks for a user's role
# ============================================================

BASE_URL="http://localhost:8000/api"
PASS="\e[32mPASS\e[0m"
FAIL="\e[31mFAIL\e[0m"

# ── helpers ──────────────────────────────────────────────────────────────────

check_status() {
  local label="$1"
  local expected="$2"
  local actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo -e "[$PASS] $label (HTTP $actual)"
  else
    echo -e "[$FAIL] $label — expected HTTP $expected, got HTTP $actual"
  fi
}

login() {
  local email="$1"
  local password="$2"
  local resp
  resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$email\", \"password\": \"$password\"}")
  local body; body=$(echo "$resp" | head -n -1)
  echo "$body" | jq -r '.access // empty'
}

# ── seed credentials (adjust if your admin user differs) ─────────────────────

ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="AdminPass123"
MANAGER_EMAIL="manager@example.com"
MANAGER_PASSWORD="ManagerPass123"

TIMESTAMP=$(date +%s)

echo ""
echo "============================================="
echo " User Management — Roles & Staff Test Suite"
echo "============================================="

# ===========================================================================
# 1. Customer self-registration (no auth, role forced to 'customer')
# ===========================================================================
echo ""
echo "--- 1. Customer self-registration ---"

CUST_EMAIL="customer_${TIMESTAMP}@test.com"
CUST_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"customer_${TIMESTAMP}\",
    \"email\": \"$CUST_EMAIL\",
    \"password\": \"CustomerPass123\",
    \"first_name\": \"John\",
    \"last_name\": \"Doe\"
  }")

CUST_BODY=$(echo "$CUST_RESP" | head -n -1)
CUST_CODE=$(echo "$CUST_RESP" | tail -n 1)
CUST_ID=$(echo "$CUST_BODY" | jq -r '.id // empty')
CUST_ROLE=$(echo "$CUST_BODY" | jq -r '.role // "customer"')

check_status "Customer self-register returns 201" "201" "$CUST_CODE"
echo "       Created user id=$CUST_ID  role=$CUST_ROLE"

# Verify role cannot be overridden to admin via public endpoint
HIJACK_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"hijack_${TIMESTAMP}\",
    \"email\": \"hijack_${TIMESTAMP}@test.com\",
    \"password\": \"HijackPass123\",
    \"role\": \"admin\"
  }")
HIJACK_BODY=$(echo "$HIJACK_RESP" | head -n -1)
HIJACK_ROLE=$(echo "$HIJACK_BODY" | jq -r '.role // empty')
if [ "$HIJACK_ROLE" = "admin" ]; then
  echo -e "[$FAIL] Role escalation via public register — role should NOT be admin"
else
  echo -e "[$PASS] Role escalation blocked (role='$HIJACK_ROLE', not 'admin')"
fi

# ===========================================================================
# 2. Obtain admin token
# ===========================================================================
echo ""
echo "--- 2. Obtain admin token ---"

ADMIN_TOKEN=$(login "$ADMIN_EMAIL" "$ADMIN_PASSWORD")
if [ -z "$ADMIN_TOKEN" ]; then
  echo -e "[$FAIL] Could not log in as admin ($ADMIN_EMAIL). Remaining tests may fail."
else
  echo -e "[$PASS] Admin login successful"
fi

# ===========================================================================
# 3. Admin creates a staff account
# ===========================================================================
echo ""
echo "--- 3. Admin creates staff account ---"

STAFF_EMAIL="staff_${TIMESTAMP}@test.com"
STAFF_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"staff_${TIMESTAMP}\",
    \"email\": \"$STAFF_EMAIL\",
    \"password\": \"StaffPass123\",
    \"first_name\": \"Alice\",
    \"last_name\": \"Smith\",
    \"role\": \"staff\"
  }")

STAFF_BODY=$(echo "$STAFF_RESP" | head -n -1)
STAFF_CODE=$(echo "$STAFF_RESP" | tail -n 1)
STAFF_ID=$(echo "$STAFF_BODY" | jq -r '.id // empty')
STAFF_ROLE=$(echo "$STAFF_BODY" | jq -r '.role // empty')

check_status "Admin creates staff — returns 201" "201" "$STAFF_CODE"
echo "       Created staff id=$STAFF_ID  role=$STAFF_ROLE"

# ===========================================================================
# 4. Admin creates a manager account
# ===========================================================================
echo ""
echo "--- 4. Admin creates manager account ---"

MGR_EMAIL="manager_${TIMESTAMP}@test.com"
MGR_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"manager_${TIMESTAMP}\",
    \"email\": \"$MGR_EMAIL\",
    \"password\": \"ManagerPass123\",
    \"role\": \"manager\"
  }")

MGR_BODY=$(echo "$MGR_RESP" | head -n -1)
MGR_CODE=$(echo "$MGR_RESP" | tail -n 1)
MGR_ID=$(echo "$MGR_BODY" | jq -r '.id // empty')
MGR_ROLE=$(echo "$MGR_BODY" | jq -r '.role // empty')

check_status "Admin creates manager — returns 201" "201" "$MGR_CODE"
echo "       Created manager id=$MGR_ID  role=$MGR_ROLE"

# ===========================================================================
# 4b. Admin cannot create another admin (403 expected)
# ===========================================================================
echo ""
echo "--- 4b. Admin cannot create another admin (403 expected) ---"

ADMIN2_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"admin2_${TIMESTAMP}\",
    \"email\": \"admin2_${TIMESTAMP}@test.com\",
    \"password\": \"Admin2Pass123\",
    \"role\": \"admin\"
  }")
ADMIN2_CODE=$(echo "$ADMIN2_RESP" | tail -n 1)
check_status "Admin blocked from creating another admin" "403" "$ADMIN2_CODE"

# ===========================================================================
# 5. Customer must not create staff (403)
# ===========================================================================
echo ""
echo "--- 5. Customer cannot create staff (403 expected) ---"

CUST_TOKEN=$(login "$CUST_EMAIL" "CustomerPass123")
UNAUTH_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $CUST_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"evil_${TIMESTAMP}\",
    \"email\": \"evil_${TIMESTAMP}@test.com\",
    \"password\": \"EvilPass123\",
    \"role\": \"staff\"
  }")
UNAUTH_CODE=$(echo "$UNAUTH_RESP" | tail -n 1)
check_status "Customer blocked from create-staff" "403" "$UNAUTH_CODE"

# ===========================================================================
# 6. Unauthenticated request to create-staff (401 expected)
# ===========================================================================
echo ""
echo "--- 6. Unauthenticated create-staff (401 expected) ---"

NO_AUTH_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"anon\", \"email\": \"anon@test.com\", \"password\": \"Pass1234\", \"role\": \"staff\"}")
NO_AUTH_CODE=$(echo "$NO_AUTH_RESP" | tail -n 1)
check_status "Unauthenticated blocked from create-staff" "401" "$NO_AUTH_CODE"

# ===========================================================================
# 7. Admin assigns role to the newly created customer
# ===========================================================================
echo ""
echo "--- 7. Admin assigns 'staff' role to customer (id=$CUST_ID) ---"

if [ -n "$CUST_ID" ]; then
  ASSIGN_RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/users/$CUST_ID/assign-role/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"role": "staff"}')
  ASSIGN_BODY=$(echo "$ASSIGN_RESP" | head -n -1)
  ASSIGN_CODE=$(echo "$ASSIGN_RESP" | tail -n 1)
  NEW_ROLE=$(echo "$ASSIGN_BODY" | jq -r '.role // empty')
  check_status "Admin assigns role — returns 200" "200" "$ASSIGN_CODE"
  echo "       User $CUST_ID new role=$NEW_ROLE"
else
  echo "       (skipped — no customer id)"
fi

# ===========================================================================
# 8. Manager cannot assign 'admin' role (403 expected)
# ===========================================================================
echo ""
echo "--- 8. Manager cannot promote to admin (403 expected) ---"

if [ -n "$STAFF_ID" ]; then
  MGR_TOKEN=$(login "$MGR_EMAIL" "ManagerPass123")
  MGR_PROMOTE_RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/users/$STAFF_ID/assign-role/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"role": "admin"}')
  MGR_PROMOTE_CODE=$(echo "$MGR_PROMOTE_RESP" | tail -n 1)
  check_status "Manager blocked from assigning admin role" "403" "$MGR_PROMOTE_CODE"
else
  echo "       (skipped — no staff id)"
fi
# ===========================================================================
# 8b. Staff cannot create any accounts (403 expected)
# ===========================================================================
echo ""
echo "--- 8b. Staff cannot use create-staff (403 expected) ---"

if [ -n "$STAFF_ID" ] && [ -n "$MGR_TOKEN" ]; then
  STAFF_TOKEN=$(login "$STAFF_EMAIL" "StaffPass123")
  STAFF_CREATE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
    -H "Authorization: Bearer $STAFF_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"x_${TIMESTAMP}\", \"email\": \"x_${TIMESTAMP}@test.com\", \"password\": \"Pass12345\", \"role\": \"staff\"}")
  STAFF_CREATE_CODE=$(echo "$STAFF_CREATE_RESP" | tail -n 1)
  check_status "Staff blocked from create-staff" "403" "$STAFF_CREATE_CODE"
else
  echo "       (skipped)"
fi
# ===========================================================================
# 9. Customer cannot assign roles (403 expected)
# ===========================================================================
echo ""
echo "--- 9. Customer cannot assign roles (403 expected) ---"

if [ -n "$STAFF_ID" ]; then
  CUST_ASSIGN_RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/users/$STAFF_ID/assign-role/" \
    -H "Authorization: Bearer $CUST_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"role": "staff"}')
  CUST_ASSIGN_CODE=$(echo "$CUST_ASSIGN_RESP" | tail -n 1)
  check_status "Customer blocked from assign-role" "403" "$CUST_ASSIGN_CODE"
else
  echo "       (skipped — no staff id)"
fi

# ===========================================================================
# 10. List tasks for a user (any authenticated user can view own tasks)
# ===========================================================================
echo ""
echo "--- 10. List tasks for staff user (id=$STAFF_ID) ---"

if [ -n "$STAFF_ID" ]; then
  TASKS_RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/users/$STAFF_ID/tasks/" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
  TASKS_BODY=$(echo "$TASKS_RESP" | head -n -1)
  TASKS_CODE=$(echo "$TASKS_RESP" | tail -n 1)
  check_status "List tasks returns 200" "200" "$TASKS_CODE"
  echo "       Response:"
  echo "$TASKS_BODY" | jq '.'
else
  echo "       (skipped — no staff id)"
fi

# ===========================================================================
# 11. create-staff must reject role='customer' (400 expected)
# ===========================================================================
echo ""
echo "--- 11. create-staff rejects role='customer' (400 expected) ---"

BAD_ROLE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"badcust_${TIMESTAMP}\",
    \"email\": \"badcust_${TIMESTAMP}@test.com\",
    \"password\": \"BadCustPass123\",
    \"role\": \"customer\"
  }")
BAD_ROLE_CODE=$(echo "$BAD_ROLE_RESP" | tail -n 1)
check_status "create-staff rejects customer role" "400" "$BAD_ROLE_CODE"

# ===========================================================================
# 11b. create-staff must reject role='admin' (403 expected for everyone)
# ===========================================================================
echo ""
echo "--- 11b. create-staff rejects role='admin' even for admin caller (403 expected) ---"

ADMIN_ROLE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"badadmin_${TIMESTAMP}\",
    \"email\": \"badadmin_${TIMESTAMP}@test.com\",
    \"password\": \"BadAdmin12345\",
    \"role\": \"admin\"
  }")
ADMIN_ROLE_CODE=$(echo "$ADMIN_ROLE_RESP" | tail -n 1)
check_status "Admin blocked from creating another admin" "403" "$ADMIN_ROLE_CODE"

# ===========================================================================
# 12. Manager can create staff, but not manager or admin
# ===========================================================================
echo ""
echo "--- 12. Manager creates staff (ok) and manager (forbidden) ---"

if [ -n "$MGR_TOKEN" ]; then
  # Should succeed: manager creates staff
  MGR_STAFF_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"mgr_staff_${TIMESTAMP}\",
      \"email\": \"mgr_staff_${TIMESTAMP}@test.com\",
      \"password\": \"MgrStaff123\",
      \"role\": \"staff\"
    }")
  MGR_STAFF_CODE=$(echo "$MGR_STAFF_RESP" | tail -n 1)
  check_status "Manager can create staff" "201" "$MGR_STAFF_CODE"

  # Should fail: manager tries to create a manager
  MGR_MGR_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"mgr_mgr_${TIMESTAMP}\",
      \"email\": \"mgr_mgr_${TIMESTAMP}@test.com\",
      \"password\": \"MgrMgr12345\",
      \"role\": \"manager\"
    }")
  MGR_MGR_CODE=$(echo "$MGR_MGR_RESP" | tail -n 1)
  check_status "Manager blocked from creating manager" "403" "$MGR_MGR_CODE"
else
  echo "       (skipped — manager token unavailable)"
fi

echo ""
echo "============================================="
echo " Tests complete"
echo "============================================="
echo ""
