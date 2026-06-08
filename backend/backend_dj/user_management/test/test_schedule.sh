#!/bin/bash
# ============================================================
# Test: WorkSchedule CRUD and slot assignment
# Endpoints covered:
#   GET    /api/schedules/                 - list schedules
#   POST   /api/schedules/                 - create schedule
#   GET    /api/schedules/<pk>/            - retrieve schedule
#   PATCH  /api/schedules/<pk>/            - partial update
#   DELETE /api/schedules/<pk>/            - destroy
#   POST   /api/schedules/assign_slot/     - assign single day slot (upsert)
#   POST   /api/schedules/remove_slot/     - remove single day slot
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

TIMESTAMP=$(date +%s)
# Monday 2026-05-04 — used throughout as a valid week_start
WEEK="2026-05-04"
# A second non-overlapping Monday
WEEK2="2026-05-11"

echo ""
echo "============================================="
echo " WorkSchedule — Comprehensive Test Suite"
echo "============================================="

# ===========================================================================
# 0. Setup — obtain admin token and pre-seed other users
# ===========================================================================
echo ""
echo "--- 0. Setup ---"

ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="AdminPass123"

ADMIN_TOKEN=$(login "$ADMIN_EMAIL" "$ADMIN_PASSWORD")
if [ -z "$ADMIN_TOKEN" ]; then
  echo -e "[$FAIL] Could not log in as admin ($ADMIN_EMAIL). Aborting."
  exit 1
fi
echo -e "[$PASS] Admin login successful"

# Create a manager via admin
MGR_EMAIL="sched_mgr_${TIMESTAMP}@test.com"
MGR_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"sched_mgr_${TIMESTAMP}\",
    \"email\": \"$MGR_EMAIL\",
    \"password\": \"ManagerPass123\",
    \"role\": \"manager\"
  }")
MGR_BODY=$(echo "$MGR_RESP" | head -n -1)
MGR_CODE=$(echo "$MGR_RESP" | tail -n 1)
MGR_ID=$(echo "$MGR_BODY" | jq -r '.id // empty')
check_status "Setup: admin creates manager" "201" "$MGR_CODE"
MGR_TOKEN=$(login "$MGR_EMAIL" "ManagerPass123")
[ -z "$MGR_TOKEN" ] && echo -e "[$FAIL] Manager login failed" || echo -e "[$PASS] Manager login successful (id=$MGR_ID)"

# Create a second manager (to test cross-manager restrictions)
MGR2_EMAIL="sched_mgr2_${TIMESTAMP}@test.com"
MGR2_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"sched_mgr2_${TIMESTAMP}\",
    \"email\": \"$MGR2_EMAIL\",
    \"password\": \"Manager2Pass123\",
    \"role\": \"manager\"
  }")
MGR2_BODY=$(echo "$MGR2_RESP" | head -n -1)
MGR2_CODE=$(echo "$MGR2_RESP" | tail -n 1)
MGR2_ID=$(echo "$MGR2_BODY" | jq -r '.id // empty')
check_status "Setup: admin creates second manager" "201" "$MGR2_CODE"
MGR2_TOKEN=$(login "$MGR2_EMAIL" "Manager2Pass123")
[ -z "$MGR2_TOKEN" ] && echo -e "[$FAIL] Manager2 login failed" || echo -e "[$PASS] Manager2 login successful (id=$MGR2_ID)"

# Create a staff member
STAFF_EMAIL="sched_staff_${TIMESTAMP}@test.com"
STAFF_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/create-staff/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"sched_staff_${TIMESTAMP}\",
    \"email\": \"$STAFF_EMAIL\",
    \"password\": \"StaffPass123\",
    \"role\": \"staff\"
  }")
STAFF_BODY=$(echo "$STAFF_RESP" | head -n -1)
STAFF_CODE=$(echo "$STAFF_RESP" | tail -n 1)
STAFF_ID=$(echo "$STAFF_BODY" | jq -r '.id // empty')
check_status "Setup: admin creates staff" "201" "$STAFF_CODE"
STAFF_TOKEN=$(login "$STAFF_EMAIL" "StaffPass123")
[ -z "$STAFF_TOKEN" ] && echo -e "[$FAIL] Staff login failed" || echo -e "[$PASS] Staff login successful (id=$STAFF_ID)"

# Create a customer (no staff endpoint; self-register)
CUST_EMAIL="sched_cust_${TIMESTAMP}@test.com"
CUST_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"sched_cust_${TIMESTAMP}\",
    \"email\": \"$CUST_EMAIL\",
    \"password\": \"CustomerPass123\",
    \"first_name\": \"Cust\",
    \"last_name\": \"Omer\"
  }")
CUST_CODE=$(echo "$CUST_RESP" | tail -n 1)
check_status "Setup: customer self-registers" "201" "$CUST_CODE"
CUST_TOKEN=$(login "$CUST_EMAIL" "CustomerPass123")
[ -z "$CUST_TOKEN" ] && echo -e "[$FAIL] Customer login failed" || echo -e "[$PASS] Customer login successful"

echo "       IDs — admin(admin), manager=$MGR_ID, manager2=$MGR2_ID, staff=$STAFF_ID"

# ===========================================================================
# 1. POST /api/schedules/ — create
# ===========================================================================
echo ""
echo "--- 1. Create schedule ---"

# 1a. Admin creates schedule for staff → 201
SCHED_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"entries\": {\"mon\": \"08:00-16:00\", \"wed\": \"09:00-17:00\"},
    \"notes\": \"admin-created\"
  }")
SCHED_BODY=$(echo "$SCHED_RESP" | head -n -1)
SCHED_CODE=$(echo "$SCHED_RESP" | tail -n 1)
SCHED_ID=$(echo "$SCHED_BODY" | jq -r '.id // empty')
check_status "Admin creates schedule for staff" "201" "$SCHED_CODE"
echo "       Schedule id=$SCHED_ID"

# 1b. Admin creates schedule for manager → 201
MGR_SCHED_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $MGR_ID,
    \"week_start\": \"$WEEK\",
    \"entries\": {\"fri\": \"08:00-16:00\"}
  }")
MGR_SCHED_CODE=$(echo "$MGR_SCHED_RESP" | tail -n 1)
MGR_SCHED_ID=$(echo "$MGR_SCHED_RESP" | head -n -1 | jq -r '.id // empty')
check_status "Admin creates schedule for manager" "201" "$MGR_SCHED_CODE"

# 1c. Admin tries to assign to customer → 400
CUST_SCHED_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $(echo "$CUST_RESP" | head -n -1 | jq -r '.id // 9999'),
    \"week_start\": \"$WEEK\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
CUST_SCHED_CODE=$(echo "$CUST_SCHED_RESP" | tail -n 1)
check_status "Admin blocked from assigning schedule to customer" "400" "$CUST_SCHED_CODE"

# 1d. Manager creates schedule for staff → 201
MGR_TO_STAFF_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $MGR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK2\",
    \"entries\": {\"tue\": \"10:00-18:00\"}
  }")
MGR_TO_STAFF_CODE=$(echo "$MGR_TO_STAFF_RESP" | tail -n 1)
MGR_CREATED_SCHED_ID=$(echo "$MGR_TO_STAFF_RESP" | head -n -1 | jq -r '.id // empty')
check_status "Manager creates schedule for staff" "201" "$MGR_TO_STAFF_CODE"

# 1e. Manager tries to assign to another manager → 403
MGR_TO_MGR_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $MGR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $MGR2_ID,
    \"week_start\": \"$WEEK\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
MGR_TO_MGR_CODE=$(echo "$MGR_TO_MGR_RESP" | tail -n 1)
check_status "Manager blocked from assigning schedule to another manager" "403" "$MGR_TO_MGR_CODE"

# 1f. Missing assigned_to → 400
MISSING_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"week_start\": \"$WEEK\", \"entries\": {\"mon\": \"08:00-16:00\"}}")
MISSING_CODE=$(echo "$MISSING_RESP" | tail -n 1)
check_status "Create: missing assigned_to returns 400" "400" "$MISSING_CODE"

# 1g. week_start not a Monday → 400 (2026-05-05 is a Tuesday)
BAD_WEEK_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-05\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
BAD_WEEK_CODE=$(echo "$BAD_WEEK_RESP" | tail -n 1)
check_status "Create: week_start not Monday returns 400" "400" "$BAD_WEEK_CODE"

# 1h. Customer cannot create → 403
CUST_CREATE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $CUST_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
CUST_CREATE_CODE=$(echo "$CUST_CREATE_RESP" | tail -n 1)
check_status "Customer blocked from creating schedule" "403" "$CUST_CREATE_CODE"

# 1i. Unauthenticated request → 401
UNAUTH_CREATE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
UNAUTH_CREATE_CODE=$(echo "$UNAUTH_CREATE_RESP" | tail -n 1)
check_status "Unauthenticated: create returns 401" "401" "$UNAUTH_CREATE_CODE"

# ===========================================================================
# 2. GET /api/schedules/ — list
# ===========================================================================
echo ""
echo "--- 2. List schedules ---"

# 2a. Unauthenticated → 401
UNAUTH_LIST=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/")
UNAUTH_LIST_CODE=$(echo "$UNAUTH_LIST" | tail -n 1)
check_status "Unauthenticated: list returns 401" "401" "$UNAUTH_LIST_CODE"

# 2b. Admin sees all schedules → 200
ADMIN_LIST_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
ADMIN_LIST_CODE=$(echo "$ADMIN_LIST_RESP" | tail -n 1)
ADMIN_LIST_COUNT=$(echo "$ADMIN_LIST_RESP" | head -n -1 | jq 'length')
check_status "Admin: list returns 200" "200" "$ADMIN_LIST_CODE"
echo "       Admin sees $ADMIN_LIST_COUNT schedule(s) total"

# 2c. Manager sees only schedules they created → 200
MGR_LIST_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $MGR_TOKEN")
MGR_LIST_CODE=$(echo "$MGR_LIST_RESP" | tail -n 1)
MGR_LIST_COUNT=$(echo "$MGR_LIST_RESP" | head -n -1 | jq 'length')
check_status "Manager: list returns 200" "200" "$MGR_LIST_CODE"
echo "       Manager sees $MGR_LIST_COUNT schedule(s) (own-created only)"

# 2d. Staff sees only own schedules → 200
STAFF_LIST_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $STAFF_TOKEN")
STAFF_LIST_CODE=$(echo "$STAFF_LIST_RESP" | tail -n 1)
STAFF_LIST_COUNT=$(echo "$STAFF_LIST_RESP" | head -n -1 | jq 'length')
check_status "Staff: list returns 200" "200" "$STAFF_LIST_CODE"
echo "       Staff sees $STAFF_LIST_COUNT schedule(s) (own-assigned only)"

# 2e. Customer → 403
CUST_LIST_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $CUST_TOKEN")
CUST_LIST_CODE=$(echo "$CUST_LIST_RESP" | tail -n 1)
check_status "Customer: list returns 403" "403" "$CUST_LIST_CODE"

# 2f. Valid ?week= filter → 200 and results match
WEEK_FILTER_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/?week=$WEEK" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
WEEK_FILTER_CODE=$(echo "$WEEK_FILTER_RESP" | tail -n 1)
check_status "Admin: list with valid ?week filter returns 200" "200" "$WEEK_FILTER_CODE"
WEEK_COUNT=$(echo "$WEEK_FILTER_RESP" | head -n -1 | jq 'length')
echo "       Results for week=$WEEK: $WEEK_COUNT schedule(s)"

# 2g. Invalid ?week= format → 400
BAD_WEEK_FILTER=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/?week=not-a-date" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
BAD_WEEK_FILTER_CODE=$(echo "$BAD_WEEK_FILTER" | tail -n 1)
check_status "List: invalid ?week format returns 400" "400" "$BAD_WEEK_FILTER_CODE"

# ===========================================================================
# 3. GET /api/schedules/<pk>/ — retrieve
# ===========================================================================
echo ""
echo "--- 3. Retrieve schedule ---"

# 3a. Admin retrieves any schedule → 200
if [ -n "$SCHED_ID" ]; then
  ADMIN_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
  ADMIN_RETRIEVE_CODE=$(echo "$ADMIN_RETRIEVE" | tail -n 1)
  check_status "Admin: retrieve any schedule returns 200" "200" "$ADMIN_RETRIEVE_CODE"
else
  echo -e "[$FAIL] Cannot test admin retrieve — SCHED_ID empty"
fi

# 3b. Staff retrieves own schedule → 200
if [ -n "$SCHED_ID" ]; then
  STAFF_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $STAFF_TOKEN")
  STAFF_RETRIEVE_CODE=$(echo "$STAFF_RETRIEVE" | tail -n 1)
  check_status "Staff: retrieve own schedule returns 200" "200" "$STAFF_RETRIEVE_CODE"
else
  echo -e "[$FAIL] Cannot test staff retrieve own — SCHED_ID empty"
fi

# 3c. Staff tries to retrieve a schedule not assigned to them (manager's schedule) → 404
if [ -n "$MGR_SCHED_ID" ]; then
  STAFF_RETRIEVE_OTHER=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$MGR_SCHED_ID/" \
    -H "Authorization: Bearer $STAFF_TOKEN")
  STAFF_RETRIEVE_OTHER_CODE=$(echo "$STAFF_RETRIEVE_OTHER" | tail -n 1)
  check_status "Staff: retrieve another user's schedule returns 404" "404" "$STAFF_RETRIEVE_OTHER_CODE"
else
  echo -e "[$FAIL] Cannot test staff retrieve other — MGR_SCHED_ID empty"
fi

# 3d. Manager sees own-created schedule → 200
if [ -n "$MGR_CREATED_SCHED_ID" ]; then
  MGR_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$MGR_CREATED_SCHED_ID/" \
    -H "Authorization: Bearer $MGR_TOKEN")
  MGR_RETRIEVE_CODE=$(echo "$MGR_RETRIEVE" | tail -n 1)
  check_status "Manager: retrieve own-created schedule returns 200" "200" "$MGR_RETRIEVE_CODE"
else
  echo -e "[$FAIL] Cannot test manager retrieve own — MGR_CREATED_SCHED_ID empty"
fi

# 3e. Manager2 cannot retrieve schedule created by Manager1 → 404
if [ -n "$MGR_CREATED_SCHED_ID" ]; then
  MGR2_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$MGR_CREATED_SCHED_ID/" \
    -H "Authorization: Bearer $MGR2_TOKEN")
  MGR2_RETRIEVE_CODE=$(echo "$MGR2_RETRIEVE" | tail -n 1)
  check_status "Manager2: retrieve schedule created by Manager1 returns 404" "404" "$MGR2_RETRIEVE_CODE"
else
  echo -e "[$FAIL] Cannot test manager2 retrieve — MGR_CREATED_SCHED_ID empty"
fi

# 3f. Customer retrieves any schedule → 403
if [ -n "$SCHED_ID" ]; then
  CUST_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $CUST_TOKEN")
  CUST_RETRIEVE_CODE=$(echo "$CUST_RETRIEVE" | tail -n 1)
  check_status "Customer: retrieve returns 403" "403" "$CUST_RETRIEVE_CODE"
else
  echo -e "[$FAIL] Cannot test customer retrieve — SCHED_ID empty"
fi

# 3g. Unauthenticated retrieve → 401
if [ -n "$SCHED_ID" ]; then
  UNAUTH_RETRIEVE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schedules/$SCHED_ID/")
  UNAUTH_RETRIEVE_CODE=$(echo "$UNAUTH_RETRIEVE" | tail -n 1)
  check_status "Unauthenticated: retrieve returns 401" "401" "$UNAUTH_RETRIEVE_CODE"
fi

# ===========================================================================
# 4. PATCH /api/schedules/<pk>/ — partial update
# ===========================================================================
echo ""
echo "--- 4. Partial update schedule ---"

# 4a. Admin patches any schedule → 200
if [ -n "$SCHED_ID" ]; then
  ADMIN_PATCH=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"notes": "updated-by-admin", "entries": {"mon": "09:00-17:00"}}')
  ADMIN_PATCH_CODE=$(echo "$ADMIN_PATCH" | tail -n 1)
  check_status "Admin: partial update returns 200" "200" "$ADMIN_PATCH_CODE"
else
  echo -e "[$FAIL] Cannot test admin patch — SCHED_ID empty"
fi

# 4b. Manager patches schedule they created → 200
if [ -n "$MGR_CREATED_SCHED_ID" ]; then
  MGR_PATCH=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$MGR_CREATED_SCHED_ID/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"notes": "updated-by-manager"}')
  MGR_PATCH_CODE=$(echo "$MGR_PATCH" | tail -n 1)
  check_status "Manager: patch own-created schedule returns 200" "200" "$MGR_PATCH_CODE"
else
  echo -e "[$FAIL] Cannot test manager patch own — MGR_CREATED_SCHED_ID empty"
fi

# 4c. Manager patches schedule they did NOT create → 404 (not visible in their qs)
if [ -n "$SCHED_ID" ]; then
  MGR_PATCH_OTHER=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"notes": "should-fail"}')
  MGR_PATCH_OTHER_CODE=$(echo "$MGR_PATCH_OTHER" | tail -n 1)
  check_status "Manager: patch schedule they didn't create returns 404" "404" "$MGR_PATCH_OTHER_CODE"
else
  echo -e "[$FAIL] Cannot test manager patch other — SCHED_ID empty"
fi

# 4d. Patch silently ignores assigned_to field — update should still succeed
if [ -n "$SCHED_ID" ]; then
  REASSIGN_PATCH=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"assigned_to\": $MGR_ID, \"notes\": \"reassign-attempt\"}")
  REASSIGN_PATCH_CODE=$(echo "$REASSIGN_PATCH" | tail -n 1)
  REASSIGN_TARGET=$(echo "$REASSIGN_PATCH" | head -n -1 | jq -r '.assigned_to // empty')
  check_status "Patch: assigned_to field ignored, still returns 200" "200" "$REASSIGN_PATCH_CODE"
  if [ "$REASSIGN_TARGET" = "$STAFF_ID" ]; then
    echo -e "[$PASS] assigned_to not changed (still staff id=$STAFF_ID)"
  else
    echo -e "[$FAIL] assigned_to was changed to $REASSIGN_TARGET (expected $STAFF_ID)"
  fi
fi

# 4e. Customer patch → 403
if [ -n "$SCHED_ID" ]; then
  CUST_PATCH=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $CUST_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"notes": "customer-patch"}')
  CUST_PATCH_CODE=$(echo "$CUST_PATCH" | tail -n 1)
  check_status "Customer: patch returns 403" "403" "$CUST_PATCH_CODE"
fi

# 4f. Unauthenticated patch → 401
if [ -n "$SCHED_ID" ]; then
  UNAUTH_PATCH=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Content-Type: application/json" \
    -d '{"notes": "unauth-patch"}')
  UNAUTH_PATCH_CODE=$(echo "$UNAUTH_PATCH" | tail -n 1)
  check_status "Unauthenticated: patch returns 401" "401" "$UNAUTH_PATCH_CODE"
fi

# ===========================================================================
# 5. POST /api/schedules/assign_slot/ — assign slot (upsert)
# ===========================================================================
echo ""
echo "--- 5. Assign slot ---"

# 5a. Admin assigns slot → creates new schedule (201)
ASSIGN_NEW_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-18\",
    \"day\": \"mon\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
ASSIGN_NEW_CODE=$(echo "$ASSIGN_NEW_RESP" | tail -n 1)
check_status "Assign slot: admin creates new schedule via assign_slot (201)" "201" "$ASSIGN_NEW_CODE"

# 5b. Admin assigns another slot on same schedule → updates in-place (200)
ASSIGN_UPDATE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-18\",
    \"day\": \"tue\",
    \"start\": \"09:00\",
    \"end\": \"17:00\"
  }")
ASSIGN_UPDATE_CODE=$(echo "$ASSIGN_UPDATE_RESP" | tail -n 1)
check_status "Assign slot: add day to existing schedule returns 200" "200" "$ASSIGN_UPDATE_CODE"
ENTRIES_AFTER=$(echo "$ASSIGN_UPDATE_RESP" | head -n -1 | jq -r '.entries | keys | join(",")')
echo "       Entries now: $ENTRIES_AFTER"

# 5c. Manager assigns slot for staff → creates new (201)
MGR_ASSIGN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $MGR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-25\",
    \"day\": \"wed\",
    \"start\": \"10:00\",
    \"end\": \"18:00\"
  }")
MGR_ASSIGN_CODE=$(echo "$MGR_ASSIGN_RESP" | tail -n 1)
check_status "Assign slot: manager creates slot for staff (201)" "201" "$MGR_ASSIGN_CODE"

# 5d. Manager tries to assign slot to another manager → 403
MGR_ASSIGN_MGR_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $MGR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $MGR2_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"mon\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
MGR_ASSIGN_MGR_CODE=$(echo "$MGR_ASSIGN_MGR_RESP" | tail -n 1)
check_status "Assign slot: manager blocked from assigning to another manager (403)" "403" "$MGR_ASSIGN_MGR_CODE"

# 5e. Missing required fields → 400
MISSING_FIELDS_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"assigned_to\": $STAFF_ID, \"week_start\": \"$WEEK\"}")
MISSING_FIELDS_CODE=$(echo "$MISSING_FIELDS_RESP" | tail -n 1)
check_status "Assign slot: missing day/start/end returns 400" "400" "$MISSING_FIELDS_CODE"

# 5f. Invalid day value → 400
BAD_DAY_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"monday\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
BAD_DAY_CODE=$(echo "$BAD_DAY_RESP" | tail -n 1)
check_status "Assign slot: invalid day value returns 400" "400" "$BAD_DAY_CODE"

# 5g. Invalid time format (not HH:MM) → 400
BAD_TIME_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"mon\",
    \"start\": \"8am\",
    \"end\": \"4pm\"
  }")
BAD_TIME_CODE=$(echo "$BAD_TIME_RESP" | tail -n 1)
check_status "Assign slot: invalid time format returns 400" "400" "$BAD_TIME_CODE"

# 5h. week_start not a Monday (2026-05-05 is Tuesday) → 400
BAD_WEEK_ASSIGN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-05\",
    \"day\": \"mon\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
BAD_WEEK_ASSIGN_CODE=$(echo "$BAD_WEEK_ASSIGN" | tail -n 1)
check_status "Assign slot: week_start not Monday returns 400" "400" "$BAD_WEEK_ASSIGN_CODE"

# 5i. Customer cannot assign slot → 403
CUST_ASSIGN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Authorization: Bearer $CUST_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"mon\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
CUST_ASSIGN_CODE=$(echo "$CUST_ASSIGN_RESP" | tail -n 1)
check_status "Customer: assign_slot returns 403" "403" "$CUST_ASSIGN_CODE"

# 5j. Unauthenticated → 401
UNAUTH_ASSIGN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/assign_slot/" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"mon\",
    \"start\": \"08:00\",
    \"end\": \"16:00\"
  }")
UNAUTH_ASSIGN_CODE=$(echo "$UNAUTH_ASSIGN" | tail -n 1)
check_status "Unauthenticated: assign_slot returns 401" "401" "$UNAUTH_ASSIGN_CODE"

# ===========================================================================
# 6. POST /api/schedules/remove_slot/ — remove slot
# ===========================================================================
echo ""
echo "--- 6. Remove slot ---"

# 6a. Admin removes an existing slot → 200
REMOVE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-18\",
    \"day\": \"tue\"
  }")
REMOVE_CODE=$(echo "$REMOVE_RESP" | tail -n 1)
check_status "Admin: remove existing slot returns 200" "200" "$REMOVE_CODE"
ENTRIES_AFTER_REMOVE=$(echo "$REMOVE_RESP" | head -n -1 | jq -r '.entries | keys | join(",")')
echo "       Entries after remove: $ENTRIES_AFTER_REMOVE"

# 6b. Remove last slot — schedule should be deactivated (active=false)
REMOVE_LAST_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-05-18\",
    \"day\": \"mon\"
  }")
REMOVE_LAST_CODE=$(echo "$REMOVE_LAST_RESP" | tail -n 1)
REMOVE_LAST_BODY=$(echo "$REMOVE_LAST_RESP" | head -n -1)
ACTIVE_AFTER=$(echo "$REMOVE_LAST_BODY" | jq '.active')
check_status "Remove last slot: schedule deactivated, still returns 200" "200" "$REMOVE_LAST_CODE"
if [ "$ACTIVE_AFTER" = "false" ]; then
  echo -e "[$PASS] Schedule correctly deactivated after last slot removed"
else
  echo -e "[$FAIL] Expected active=false, got active=$ACTIVE_AFTER"
fi

# 6c. Manager removes slot from own-created schedule → 200
# Use the schedule created by MGR_TOKEN for staff (WEEK2 / MGR_CREATED_SCHED_ID)
if [ -n "$MGR_CREATED_SCHED_ID" ]; then
  MGR_REMOVE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
    -H "Authorization: Bearer $MGR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"assigned_to\": $STAFF_ID,
      \"week_start\": \"$WEEK2\",
      \"day\": \"tue\"
    }")
  MGR_REMOVE_CODE=$(echo "$MGR_REMOVE_RESP" | tail -n 1)
  check_status "Manager: remove slot from own-created schedule returns 200" "200" "$MGR_REMOVE_CODE"
else
  echo -e "[$FAIL] Cannot test manager remove own slot — MGR_CREATED_SCHED_ID empty"
fi

# 6d. Remove non-existent day in schedule → 404
MISSING_DAY_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"sat\"
  }")
MISSING_DAY_CODE=$(echo "$MISSING_DAY_RESP" | tail -n 1)
check_status "Remove slot: day not in schedule entries returns 404" "404" "$MISSING_DAY_CODE"

# 6e. Missing required fields → 400
MISSING_REMOVE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"assigned_to\": $STAFF_ID}")
MISSING_REMOVE_CODE=$(echo "$MISSING_REMOVE_RESP" | tail -n 1)
check_status "Remove slot: missing week_start/day returns 400" "400" "$MISSING_REMOVE_CODE"

# 6f. Manager2 tries to remove slot from schedule created by Manager1 → 403
# Admin created SCHED_ID for staff on WEEK; so manager has no ownership
if [ -n "$SCHED_ID" ]; then
  MGR2_REMOVE_OTHER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
    -H "Authorization: Bearer $MGR2_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"assigned_to\": $STAFF_ID,
      \"week_start\": \"$WEEK\",
      \"day\": \"mon\"
    }")
  MGR2_REMOVE_CODE=$(echo "$MGR2_REMOVE_OTHER" | tail -n 1)
  check_status "Manager2: remove slot from schedule they didn't create returns 403" "403" "$MGR2_REMOVE_CODE"
else
  echo -e "[$FAIL] Cannot test manager2 remove other — SCHED_ID empty"
fi

# 6g. Customer cannot remove slot → 403
CUST_REMOVE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Authorization: Bearer $CUST_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"$WEEK\",
    \"day\": \"mon\"
  }")
CUST_REMOVE_CODE=$(echo "$CUST_REMOVE_RESP" | tail -n 1)
check_status "Customer: remove_slot returns 403" "403" "$CUST_REMOVE_CODE"

# 6h. Unauthenticated → 401
UNAUTH_REMOVE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/remove_slot/" \
  -H "Content-Type: application/json" \
  -d "{\"assigned_to\": $STAFF_ID, \"week_start\": \"$WEEK\", \"day\": \"mon\"}")
UNAUTH_REMOVE_CODE=$(echo "$UNAUTH_REMOVE" | tail -n 1)
check_status "Unauthenticated: remove_slot returns 401" "401" "$UNAUTH_REMOVE_CODE"

# ===========================================================================
# 7. DELETE /api/schedules/<pk>/ — destroy
# ===========================================================================
echo ""
echo "--- 7. Destroy schedule ---"

# 7a. Manager deletes own-created schedule → 204
# We need a fresh schedule to delete because ones above may be exhausted
FRESH_MGR_SCHED=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schedules/" \
  -H "Authorization: Bearer $MGR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to\": $STAFF_ID,
    \"week_start\": \"2026-06-01\",
    \"entries\": {\"mon\": \"08:00-16:00\"}
  }")
FRESH_MGR_ID=$(echo "$FRESH_MGR_SCHED" | head -n -1 | jq -r '.id // empty')
FRESH_MGR_CODE=$(echo "$FRESH_MGR_SCHED" | tail -n 1)
check_status "Setup: manager creates fresh schedule for delete tests" "201" "$FRESH_MGR_CODE"

if [ -n "$FRESH_MGR_ID" ]; then
  MGR_DELETE_RESP=$(curl -s -w "\n%{http_code}" -X DELETE \
    "$BASE_URL/schedules/$FRESH_MGR_ID/" \
    -H "Authorization: Bearer $MGR_TOKEN")
  MGR_DELETE_CODE=$(echo "$MGR_DELETE_RESP" | tail -n 1)
  check_status "Manager: delete own-created schedule returns 204" "204" "$MGR_DELETE_CODE"
else
  echo -e "[$FAIL] Cannot test manager delete own — FRESH_MGR_ID empty"
fi

# 7b. Manager tries to delete schedule they didn't create → 404 (not in their qs)
if [ -n "$SCHED_ID" ]; then
  MGR_DELETE_OTHER=$(curl -s -w "\n%{http_code}" -X DELETE \
    "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $MGR_TOKEN")
  MGR_DELETE_OTHER_CODE=$(echo "$MGR_DELETE_OTHER" | tail -n 1)
  check_status "Manager: delete schedule they didn't create returns 404" "404" "$MGR_DELETE_OTHER_CODE"
else
  echo -e "[$FAIL] Cannot test manager delete other — SCHED_ID empty"
fi

# 7c. Customer tries to delete → 403
if [ -n "$SCHED_ID" ]; then
  CUST_DELETE=$(curl -s -w "\n%{http_code}" -X DELETE \
    "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $CUST_TOKEN")
  CUST_DELETE_CODE=$(echo "$CUST_DELETE" | tail -n 1)
  check_status "Customer: delete returns 403" "403" "$CUST_DELETE_CODE"
fi

# 7d. Unauthenticated delete → 401
if [ -n "$SCHED_ID" ]; then
  UNAUTH_DELETE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/schedules/$SCHED_ID/")
  UNAUTH_DELETE_CODE=$(echo "$UNAUTH_DELETE" | tail -n 1)
  check_status "Unauthenticated: delete returns 401" "401" "$UNAUTH_DELETE_CODE"
fi

# 7e. Admin deletes any schedule → 204
if [ -n "$SCHED_ID" ]; then
  ADMIN_DELETE=$(curl -s -w "\n%{http_code}" -X DELETE \
    "$BASE_URL/schedules/$SCHED_ID/" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
  ADMIN_DELETE_CODE=$(echo "$ADMIN_DELETE" | tail -n 1)
  check_status "Admin: delete any schedule returns 204" "204" "$ADMIN_DELETE_CODE"
fi

# 7f. Admin deletes non-existent pk → 404
ADMIN_DELETE_GHOST=$(curl -s -w "\n%{http_code}" -X DELETE \
  "$BASE_URL/schedules/999999/" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
ADMIN_DELETE_GHOST_CODE=$(echo "$ADMIN_DELETE_GHOST" | tail -n 1)
check_status "Admin: delete non-existent pk returns 404" "404" "$ADMIN_DELETE_GHOST_CODE"

# ===========================================================================
# Summary
# ===========================================================================
echo ""
echo "============================================="
echo " Test run complete"
echo "============================================="
