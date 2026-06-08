#!/bin/bash
# =============================================================================
# User Management — Full cURL integration test
# Covers: CreateMixin, UpdateMixin (assign-role, change-password), DeleteMixin,
#         AuthMixin (login/logout), ReadMixin
#
# Usage:
#   chmod +x test_user_management.sh
#   ./test_user_management.sh
#
# Requires a running Django dev server:
#   python manage.py runserver
# =============================================================================

API="${API_BASE:-http://localhost:8000/api}"
PASS=0
FAIL=0

# ── Helpers ──────────────────────────────────────────────────────────────────

green()  { echo -e "\033[32m✔  $*\033[0m"; }
red()    { echo -e "\033[31m✘  $*\033[0m"; }
cyan()   { echo -e "\033[36m── $*\033[0m"; }
section(){ echo ""; echo -e "\033[1;34m══ $* ══\033[0m"; }

assert_status() {
    local label="$1" expected="$2" actual="$3" body="$4"
    if [ "$actual" = "$expected" ]; then
        green "$label (HTTP $actual)"
        (( PASS++ ))
    else
        red "$label  →  expected HTTP $expected, got HTTP $actual"
        echo "    body: $body" | head -c 300
        echo ""
        (( FAIL++ ))
    fi
}

json_field() {
    # Extract a top-level JSON string field value (simple grep-based, no jq needed)
    local field="$1" json="$2"
    echo "$json" | grep -o "\"${field}\":\"[^\"]*" | head -1 | cut -d'"' -f4
}

json_int_field() {
    local field="$1" json="$2"
    echo "$json" | grep -o "\"${field}\":[0-9]*" | head -1 | cut -d':' -f2
}

do_post() {
    local url="$1" data="$2" token="${3:-}"
    local auth_header=""
    [ -n "$token" ] && auth_header="-H \"Authorization: Bearer $token\""
    curl -s -w "\n__STATUS__%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        ${token:+-H "Authorization: Bearer $token"} \
        -d "$data"
}

do_patch() {
    local url="$1" data="$2" token="${3:-}"
    curl -s -w "\n__STATUS__%{http_code}" -X PATCH "$url" \
        -H "Content-Type: application/json" \
        ${token:+-H "Authorization: Bearer $token"} \
        -d "$data"
}

do_get() {
    local url="$1" token="${2:-}"
    curl -s -w "\n__STATUS__%{http_code}" -X GET "$url" \
        -H "Content-Type: application/json" \
        ${token:+-H "Authorization: Bearer $token"}
}

do_delete() {
    local url="$1" token="${2:-}"
    curl -s -w "\n__STATUS__%{http_code}" -X DELETE "$url" \
        ${token:+-H "Authorization: Bearer $token"}
}

# Split body and status from a curl response
resp_body()   { echo "$1" | sed 's/__STATUS__[0-9]*$//'; }
resp_status() { echo "$1" | grep -o '__STATUS__[0-9]*' | cut -d'_' -f3; }

# Login shortcut: returns access token or empty string
login() {
    local email="$1" password="$2"
    local resp
    resp=$(do_post "$API/users/login/" "{\"email\":\"$email\",\"password\":\"$password\"}")
    local body; body=$(resp_body "$resp")
    json_field "access" "$body"
}

# ── Seed data: unique suffix per run ─────────────────────────────────────────
TS=$(date +%s)
ADMIN_EMAIL="admin_${TS}@pizza.test"
ADMIN_PASS="AdminPass1!"
MGR_EMAIL="mgr_${TS}@pizza.test"
MGR_PASS="MgrPass1!"
STAFF_EMAIL="staff_${TS}@pizza.test"
STAFF_PASS="StaffPass1!"
CUST_EMAIL="cust_${TS}@pizza.test"
CUST_PASS="CustPass1!"

echo ""
echo "▶ API base: $API"
echo "▶ Test run: $TS"

# =============================================================================
section "0. SEED — create admin account via Django shell (one-time)"
# =============================================================================
# The very first admin must be created out-of-band because the API itself
# requires an admin JWT to call create-staff.  We use manage.py shell.
cyan "Creating superuser $ADMIN_EMAIL via manage.py..."
python manage.py shell -c "
from user_management.models import User
if not User.objects.filter(email='$ADMIN_EMAIL').exists():
    u = User.objects.create_user(
        username='admin_$TS', email='$ADMIN_EMAIL', password='$ADMIN_PASS'
    )
    u.role = 'admin'
    u.is_staff = True
    u.save()
    print('admin created')
else:
    print('admin already exists')
" 2>/dev/null
echo ""

# =============================================================================
section "1. AUTH — Login / Logout"
# =============================================================================

# --- 1a: login with wrong password → 401
cyan "1a. Login with wrong password"
resp=$(do_post "$API/users/login/" '{"email":"nobody@x.com","password":"wrong"}')
assert_status "login wrong creds" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 1b: login missing fields → 400
cyan "1b. Login missing fields"
resp=$(do_post "$API/users/login/" '{}')
assert_status "login missing fields" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 1c: admin login → 200, get token
cyan "1c. Admin login"
resp=$(do_post "$API/users/login/" "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")
assert_status "admin login" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"
ADMIN_TOKEN=$(json_field "access" "$(resp_body "$resp")")

if [ -z "$ADMIN_TOKEN" ]; then
    red "FATAL: Could not obtain admin token — aborting remaining tests."
    echo ""
    echo "PASS: $PASS  FAIL: $FAIL"
    exit 1
fi

# =============================================================================
section "2. CREATE — Customer self-registration (public)"
# =============================================================================

# --- 2a: register customer, no auth
cyan "2a. Register customer (no auth)"
resp=$(do_post "$API/users/" "{\"username\":\"cust_${TS}\",\"email\":\"$CUST_EMAIL\",\"password\":\"$CUST_PASS\"}")
assert_status "register customer 201" "201" "$(resp_status "$resp")" "$(resp_body "$resp")"
CUST_BODY=$(resp_body "$resp")
CUST_ID=$(json_int_field "id" "$CUST_BODY")
CUST_ROLE=$(json_field "role" "$CUST_BODY")
if [ "$CUST_ROLE" = "customer" ]; then
    green "  role forced to 'customer'"
    (( PASS++ ))
else
    red "  role NOT forced — got '$CUST_ROLE'"
    (( FAIL++ ))
fi

# --- 2b: register customer with role=admin in body → still role=customer
cyan "2b. Register customer with role=admin body (should still be customer)"
resp=$(do_post "$API/users/" "{\"username\":\"hacker_${TS}\",\"email\":\"hacker_${TS}@x.com\",\"password\":\"$CUST_PASS\",\"role\":\"admin\"}")
assert_status "register hacker 201" "201" "$(resp_status "$resp")" "$(resp_body "$resp")"
HACK_ROLE=$(json_field "role" "$(resp_body "$resp")")
if [ "$HACK_ROLE" = "customer" ]; then
    green "  role escalation blocked"
    (( PASS++ ))
else
    red "  role escalation NOT blocked — got '$HACK_ROLE'"
    (( FAIL++ ))
fi

# --- 2c: duplicate email → 400
cyan "2c. Duplicate email → 400"
resp=$(do_post "$API/users/" "{\"username\":\"dup_${TS}\",\"email\":\"$CUST_EMAIL\",\"password\":\"$CUST_PASS\"}")
assert_status "duplicate email 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# =============================================================================
section "3. CREATE-STAFF — Admin/Manager only"
# =============================================================================

# --- 3a: no token → 401
cyan "3a. create-staff without token → 401"
resp=$(do_post "$API/users/create-staff/" '{"username":"x","email":"x@x.com","password":"pass1234!","role":"staff"}')
assert_status "create-staff no token 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 3b: role=customer rejected → 400
cyan "3b. create-staff role=customer → 400"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"c2_${TS}\",\"email\":\"c2_${TS}@x.com\",\"password\":\"pass1234!\",\"role\":\"customer\"}" \
    "$ADMIN_TOKEN")
assert_status "create-staff customer 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 3c: role=admin rejected → 403
cyan "3c. create-staff role=admin → 403"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"adm2_${TS}\",\"email\":\"adm2_${TS}@x.com\",\"password\":\"pass1234!\",\"role\":\"admin\"}" \
    "$ADMIN_TOKEN")
assert_status "create-staff admin 403" "403" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 3d: admin creates a manager → 201
cyan "3d. Admin creates manager account → 201"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"mgr_${TS}\",\"email\":\"$MGR_EMAIL\",\"password\":\"$MGR_PASS\",\"role\":\"manager\"}" \
    "$ADMIN_TOKEN")
assert_status "create manager 201" "201" "$(resp_status "$resp")" "$(resp_body "$resp")"
MGR_ID=$(json_int_field "id" "$(resp_body "$resp")")

# --- 3e: admin creates a staff → 201
cyan "3e. Admin creates staff account → 201"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"staff_${TS}\",\"email\":\"$STAFF_EMAIL\",\"password\":\"$STAFF_PASS\",\"role\":\"staff\"}" \
    "$ADMIN_TOKEN")
assert_status "create staff 201" "201" "$(resp_status "$resp")" "$(resp_body "$resp")"
STAFF_ID=$(json_int_field "id" "$(resp_body "$resp")")

# --- 3f: get manager token
MGR_TOKEN=$(login "$MGR_EMAIL" "$MGR_PASS")
cyan "3f. Manager login"
[ -n "$MGR_TOKEN" ] && { green "manager token obtained"; (( PASS++ )); } || { red "manager login failed"; (( FAIL++ )); }

# --- 3g: manager cannot create another manager → 403
cyan "3g. Manager cannot create manager → 403"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"mgr2_${TS}\",\"email\":\"mgr2_${TS}@x.com\",\"password\":\"$MGR_PASS\",\"role\":\"manager\"}" \
    "$MGR_TOKEN")
assert_status "manager creates manager 403" "403" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 3h: manager can create a staff account → 201
cyan "3h. Manager creates staff account → 201"
resp=$(do_post "$API/users/create-staff/" \
    "{\"username\":\"staff2_${TS}\",\"email\":\"staff2_${TS}@x.com\",\"password\":\"$STAFF_PASS\",\"role\":\"staff\"}" \
    "$MGR_TOKEN")
assert_status "manager creates staff 201" "201" "$(resp_status "$resp")" "$(resp_body "$resp")"

# =============================================================================
section "4. READ — List / Detail"
# =============================================================================

# --- 4a: list without auth → 401/403
cyan "4a. List users without auth → 401"
resp=$(do_get "$API/users/")
assert_status "list no auth 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 4b: customer sees only themselves
cyan "4b. Customer sees only own profile"
CUST_TOKEN=$(login "$CUST_EMAIL" "$CUST_PASS")
resp=$(do_get "$API/users/" "$CUST_TOKEN")
LIST_BODY=$(resp_body "$resp")
# count items: number of "id": occurrences in results
COUNT=$(echo "$LIST_BODY" | grep -o '"id":' | wc -l)
if [ "$COUNT" -eq 1 ]; then
    green "  customer sees 1 record (own)"
    (( PASS++ ))
else
    red "  customer sees $COUNT records (expected 1)"
    (( FAIL++ ))
fi

# --- 4c: admin can see all
cyan "4c. Admin list returns multiple users"
resp=$(do_get "$API/users/" "$ADMIN_TOKEN")
COUNT=$(resp_body "$resp" | grep -o '"id":' | wc -l)
if [ "$COUNT" -gt 1 ]; then
    green "  admin sees $COUNT users (>1)"
    (( PASS++ ))
else
    red "  admin sees $COUNT users (expected >1)"
    (( FAIL++ ))
fi

# --- 4d: admin fetches own detail
cyan "4d. Detail view for existing user"
ADMIN_ID=$(json_int_field "id" "$(resp_body "$(do_get "$API/users/" "$ADMIN_TOKEN")")")
resp=$(do_get "$API/users/${ADMIN_ID}/" "$ADMIN_TOKEN")
assert_status "admin detail 200" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"

# =============================================================================
section "5. UPDATE — assign-role"
# =============================================================================

if [ -z "$CUST_ID" ]; then
    red "5. Skipping assign-role tests (no CUST_ID)"
else
    # --- 5a: no token → 401
    cyan "5a. assign-role without token → 401"
    resp=$(do_patch "$API/users/${CUST_ID}/assign-role/" '{"role":"staff"}')
    assert_status "assign-role no token 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

    # --- 5b: invalid role → 400
    cyan "5b. assign-role invalid role → 400"
    resp=$(do_patch "$API/users/${CUST_ID}/assign-role/" '{"role":"supervillain"}' "$ADMIN_TOKEN")
    assert_status "assign-role invalid 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

    # --- 5c: manager cannot assign admin → 403
    cyan "5c. Manager cannot assign admin role → 403"
    resp=$(do_patch "$API/users/${CUST_ID}/assign-role/" '{"role":"admin"}' "$MGR_TOKEN")
    assert_status "manager assign admin 403" "403" "$(resp_status "$resp")" "$(resp_body "$resp")"

    # --- 5d: admin promotes customer → staff → 200
    cyan "5d. Admin promotes customer to staff → 200"
    resp=$(do_patch "$API/users/${CUST_ID}/assign-role/" '{"role":"staff"}' "$ADMIN_TOKEN")
    assert_status "admin promote to staff 200" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"
    NEW_ROLE=$(json_field "role" "$(resp_body "$resp")")
    if [ "$NEW_ROLE" = "staff" ]; then
        green "  role updated to 'staff' in response"
        (( PASS++ ))
    else
        red "  role in response is '$NEW_ROLE' (expected 'staff')"
        (( FAIL++ ))
    fi

    # --- 5e: role-change log entry exists (verify via re-read has consistent role)
    cyan "5e. Role update persisted"
    resp=$(do_get "$API/users/${CUST_ID}/" "$ADMIN_TOKEN")
    PERSISTED_ROLE=$(json_field "role" "$(resp_body "$resp")")
    if [ "$PERSISTED_ROLE" = "staff" ]; then
        green "  persisted role = 'staff'"
        (( PASS++ ))
    else
        red "  persisted role = '$PERSISTED_ROLE' (expected 'staff')"
        (( FAIL++ ))
    fi
fi

# =============================================================================
section "6. UPDATE — change-password"
# =============================================================================

STAFF_TOKEN=$(login "$STAFF_EMAIL" "$STAFF_PASS")
cyan "(obtained staff token)"

# --- 6a: no token → 401
cyan "6a. change-password without token → 401"
resp=$(do_post "$API/users/change-password/" '{"old_password":"x","new_password":"y"}')
assert_status "change-pw no token 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6b: missing fields → 400
cyan "6b. change-password missing fields → 400"
resp=$(do_post "$API/users/change-password/" '{}' "$STAFF_TOKEN")
assert_status "change-pw empty 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6c: new password too short → 400
cyan "6c. change-password new password too short → 400"
resp=$(do_post "$API/users/change-password/" \
    "{\"old_password\":\"$STAFF_PASS\",\"new_password\":\"abc\"}" \
    "$STAFF_TOKEN")
assert_status "change-pw short 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6d: wrong old password → 400
cyan "6d. change-password wrong old password → 400"
resp=$(do_post "$API/users/change-password/" \
    '{"old_password":"Wrong111!","new_password":"NewPass99!"}' \
    "$STAFF_TOKEN")
assert_status "change-pw wrong old 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6e: correct → 200
cyan "6e. change-password success → 200"
NEW_STAFF_PASS="NewStaff99!"
resp=$(do_post "$API/users/change-password/" \
    "{\"old_password\":\"$STAFF_PASS\",\"new_password\":\"$NEW_STAFF_PASS\"}" \
    "$STAFF_TOKEN")
assert_status "change-pw success 200" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6f: old token still valid but old password no longer works
cyan "6f. Old password no longer works → 400"
resp=$(do_post "$API/users/change-password/" \
    "{\"old_password\":\"$STAFF_PASS\",\"new_password\":\"AnotherOne9!\"}" \
    "$STAFF_TOKEN")
assert_status "old pw rejected 400" "400" "$(resp_status "$resp")" "$(resp_body "$resp")"

# --- 6g: login with new password works
cyan "6g. Login with new password → 200"
NEW_STAFF_TOKEN=$(login "$STAFF_EMAIL" "$NEW_STAFF_PASS")
[ -n "$NEW_STAFF_TOKEN" ] && { green "new password login ok"; (( PASS++ )); } || { red "new password login failed"; (( FAIL++ )); }

# =============================================================================
section "7. UPDATE — partial_update (PATCH profile)"
# =============================================================================

if [ -n "$STAFF_ID" ] && [ -n "$NEW_STAFF_TOKEN" ]; then
    cyan "7a. Staff patches own first_name → 200"
    resp=$(do_patch "$API/users/${STAFF_ID}/" \
        '{"first_name":"PatchedName"}' \
        "$NEW_STAFF_TOKEN")
    assert_status "patch first_name 200" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"

    cyan "7b. Staff cannot patch another user → 404/403"
    OTHER_ID=$CUST_ID
    resp=$(do_patch "$API/users/${OTHER_ID}/" \
        '{"first_name":"evil"}' \
        "$NEW_STAFF_TOKEN")
    ST=$(resp_status "$resp")
    if [[ "$ST" == "404" || "$ST" == "403" ]]; then
        green "patch other user blocked ($ST)"
        (( PASS++ ))
    else
        red "patch other user returned $ST (expected 403 or 404)"
        (( FAIL++ ))
    fi
fi

# =============================================================================
section "8. TASKS — list_tasks"
# =============================================================================

if [ -n "$STAFF_ID" ] && [ -n "$NEW_STAFF_TOKEN" ]; then
    cyan "8a. Authenticated staff fetches task list → 200"
    resp=$(do_get "$API/users/${STAFF_ID}/tasks/" "$NEW_STAFF_TOKEN")
    assert_status "list tasks 200" "200" "$(resp_status "$resp")" "$(resp_body "$resp")"

    cyan "8b. No token → 401"
    resp=$(do_get "$API/users/${STAFF_ID}/tasks/")
    assert_status "list tasks no token 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"
fi

# =============================================================================
section "9. DELETE — admin-only"
# =============================================================================

# --- 9a: no token → 401
if [ -n "$CUST_ID" ]; then
    cyan "9a. Delete without token → 401"
    resp=$(do_delete "$API/users/${CUST_ID}/")
    assert_status "delete no token 401" "401" "$(resp_status "$resp")" "$(resp_body "$resp")"

    # --- 9b: customer tries to delete → 403
    CUST_TOKEN2=$(login "$CUST_EMAIL" "$CUST_PASS")  # may fail if pw changed; that's ok
    if [ -n "$CUST_TOKEN2" ]; then
        cyan "9b. Customer tries to delete → 403"
        resp=$(do_delete "$API/users/${STAFF_ID}/" "$CUST_TOKEN2")
        assert_status "customer delete 403" "403" "$(resp_status "$resp")" "$(resp_body "$resp")"
    fi

    # --- 9c: admin deletes customer → 204
    cyan "9c. Admin deletes customer → 204"
    resp=$(do_delete "$API/users/${CUST_ID}/" "$ADMIN_TOKEN")
    assert_status "admin delete 204" "204" "$(resp_status "$resp")" "$(resp_body "$resp")"

    # --- 9d: deleted user is gone → 404
    cyan "9d. Deleted user no longer found → 404"
    resp=$(do_get "$API/users/${CUST_ID}/" "$ADMIN_TOKEN")
    assert_status "deleted user 404" "404" "$(resp_status "$resp")" "$(resp_body "$resp")"
fi

# =============================================================================
section "10. AUTH — Logout"
# =============================================================================

cyan "10a. Logout with token → 200/204"
resp=$(do_post "$API/users/logout/" '{}' "$ADMIN_TOKEN")
ST=$(resp_status "$resp")
if [[ "$ST" == "200" || "$ST" == "204" || "$ST" == "205" ]]; then
    green "logout ok ($ST)"
    (( PASS++ ))
else
    red "logout returned $ST"
    (( FAIL++ ))
fi

# =============================================================================
echo ""
echo "════════════════════════════════"
echo "  RESULTS:  ✔ $PASS passed   ✘ $FAIL failed"
echo "════════════════════════════════"
echo ""
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
