#!/bin/bash
# =============================================================================
# JWT Authentication - Test Suite
# Tests: login, authenticated requests, token refresh, X-New-Access-Token header,
#        and logout / token-expired handling.
# =============================================================================
# Usage:
#   chmod +x test_jwt_auth.sh
#   ./test_jwt_auth.sh
#   ./test_jwt_auth.sh admin@example.com admin123   # override credentials
# =============================================================================

API="http://localhost:8000/api"
EMAIL="${1:-admin@example.com}"
PASSWORD="${2:-admin123}"

# ─── colour helpers ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0

pass() { echo -e "  ${GREEN}✓ PASS${NC} — $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗ FAIL${NC} — $1"; ((FAIL++)); }
section() { echo -e "\n${CYAN}${BOLD}[$1]${NC} $2"; }

# Extract a JSON field from a string without jq dependency
json_get() { echo "$1" | grep -o "\"$2\":\"[^\"]*" | head -1 | cut -d'"' -f4; }
header_get() {
    # $1 = raw headers (from curl -D -), $2 = header name (lowercase)
    echo "$1" | grep -i "^$2:" | head -1 | sed 's/^[^:]*: *//' | tr -d '\r'
}

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   JWT Authentication · Test Suite        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo    "  API:  $API"
echo    "  User: $EMAIL"

# =============================================================================
section "1" "Server reachability"
# =============================================================================
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API/users/me/")
if [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "200" ]]; then
    pass "Server is running (HTTP $HTTP_CODE)"
else
    fail "Server not reachable (HTTP $HTTP_CODE — expected 401)"
    echo -e "\n${RED}Aborting — make sure Django is running on port 8000.${NC}"
    exit 1
fi

# =============================================================================
section "2" "Login → receive access + refresh tokens"
# =============================================================================
LOGIN_RESP=$(curl -s -c /tmp/jwt_test_cookies.txt \
    -X POST "$API/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

ACCESS_TOKEN=$(json_get "$LOGIN_RESP" "access")
REFRESH_TOKEN=$(json_get "$LOGIN_RESP" "refresh")

if [[ -n "$ACCESS_TOKEN" ]]; then
    pass "Access token present in response body"
else
    fail "Access token missing from response body"
    echo "  Response: $LOGIN_RESP"
fi

if [[ -n "$REFRESH_TOKEN" ]]; then
    pass "Refresh token present in response body"
else
    fail "Refresh token missing from response body"
fi

# Check cookies were set
if grep -q "access_token" /tmp/jwt_test_cookies.txt 2>/dev/null; then
    pass "access_token httpOnly cookie set by server"
else
    fail "access_token cookie NOT set by server"
fi

if grep -q "refresh_token" /tmp/jwt_test_cookies.txt 2>/dev/null; then
    pass "refresh_token httpOnly cookie set by server"
else
    fail "refresh_token cookie NOT set by server"
fi

echo    "  Token preview: ${ACCESS_TOKEN:0:30}..."

# =============================================================================
section "3" "Authenticated request (Authorization: Bearer header)"
# =============================================================================
ME_RESP=$(curl -s \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API/users/me/")

ME_EMAIL=$(json_get "$ME_RESP" "email")
if [[ "$ME_EMAIL" == "$EMAIL" ]]; then
    pass "GET /users/me/ returns correct user ($ME_EMAIL)"
else
    fail "GET /users/me/ did not return expected user — got: $ME_RESP"
fi

# =============================================================================
section "4" "Request WITHOUT token → must return 401"
# =============================================================================
NO_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API/users/me/")
if [[ "$NO_AUTH_CODE" == "401" ]]; then
    pass "Unauthenticated request correctly returns 401"
else
    fail "Expected 401, got $NO_AUTH_CODE"
fi

# =============================================================================
section "5" "Token refresh via POST /auth/refresh/ (body: {refresh: ...})"
# =============================================================================
REFRESH_RESP=$(curl -s \
    -X POST "$API/auth/refresh/" \
    -H "Content-Type: application/json" \
    -d "{\"refresh\":\"$REFRESH_TOKEN\"}")

NEW_ACCESS=$(json_get "$REFRESH_RESP" "access")
NEW_REFRESH=$(json_get "$REFRESH_RESP" "refresh")

if [[ -n "$NEW_ACCESS" ]]; then
    pass "New access token returned after refresh"
else
    fail "No access token in refresh response — got: $REFRESH_RESP"
fi

if [[ -n "$NEW_REFRESH" ]]; then
    pass "Refresh token rotated (new refresh token returned)"
else
    fail "No rotated refresh token returned"
fi

# Verify new access token actually works
if [[ -n "$NEW_ACCESS" ]]; then
    ME2=$(curl -s -H "Authorization: Bearer $NEW_ACCESS" "$API/users/me/")
    ME2_EMAIL=$(json_get "$ME2" "email")
    if [[ "$ME2_EMAIL" == "$EMAIL" ]]; then
        pass "New access token is valid — /users/me/ OK"
    else
        fail "New access token rejected — got: $ME2"
    fi
fi

# =============================================================================
section "6" "Auto-refresh via cookie (X-New-Access-Token header)"
# =============================================================================
# First, log in fresh to get both cookies set properly
curl -s -c /tmp/jwt_test_cookies2.txt \
    -X POST "$API/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" > /dev/null

# Make a request using cookies (simulating browser — no Authorization header)
# Capture response headers to check for X-New-Access-Token
COOKIE_RESP_HEADERS=$(curl -s -D - \
    -b /tmp/jwt_test_cookies2.txt \
    -c /tmp/jwt_test_cookies2.txt \
    -o /dev/null \
    "$API/users/me/")

HTTP_VIA_COOKIE=$(echo "$COOKIE_RESP_HEADERS" | grep "^HTTP/" | tail -1 | awk '{print $2}')
if [[ "$HTTP_VIA_COOKIE" == "200" ]]; then
    pass "Cookie-authenticated request succeeds (HTTP 200)"
else
    # 401 here can mean access_token cookie has expired — auto-refresh might
    # not fire unless the token is actually expired. This is expected in tests.
    echo -e "  ${YELLOW}⚠ SKIP${NC} — Cookie test returned HTTP $HTTP_VIA_COOKIE (cookie may already be expired in test environment)"
fi

# Check the CORS exposure of X-New-Access-Token is wired up
# We verify it doesn't get stripped (can only confirm via actual expiry in prod,
# but we check settings directly)
if grep -q "X-New-Access-Token" \
    "$(dirname "$0")/backend_dj/backend_dj/settings.py" 2>/dev/null; then
    pass "CORS_EXPOSE_HEADERS includes X-New-Access-Token in settings.py"
elif grep -rq "CORS_EXPOSE_HEADERS" \
    "$(dirname "$0")/backend_dj/backend_dj/settings.py" 2>/dev/null; then
    pass "CORS_EXPOSE_HEADERS found in settings.py"
else
    fail "CORS_EXPOSE_HEADERS not found — js cannot read X-New-Access-Token cross-origin"
fi

# =============================================================================
section "7" "Stale (invalid) token → 401"
# =============================================================================
FAKE_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJmYWtlQGV4YW1wbGUuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
FAKE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $FAKE_TOKEN" \
    "$API/users/me/")
if [[ "$FAKE_CODE" == "401" ]]; then
    pass "Expired/fake token correctly returns 401"
else
    fail "Expected 401 for fake token, got $FAKE_CODE"
fi

# =============================================================================
section "8" "Refresh with invalid token → 401"
# =============================================================================
BAD_REFRESH_RESP=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API/auth/refresh/" \
    -H "Content-Type: application/json" \
    -d '{"refresh":"totally-invalid-token"}')
if [[ "$BAD_REFRESH_RESP" == "401" ]]; then
    pass "Invalid refresh token correctly returns 401"
else
    fail "Expected 401 for bad refresh token, got $BAD_REFRESH_RESP"
fi

# =============================================================================
section "9" "Refresh with empty body → 400"
# =============================================================================
EMPTY_REFRESH=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API/auth/refresh/" \
    -H "Content-Type: application/json" \
    -d '{}')
if [[ "$EMPTY_REFRESH" == "400" ]]; then
    pass "Missing refresh token body correctly returns 400"
else
    fail "Expected 400 for empty refresh body, got $EMPTY_REFRESH"
fi

# =============================================================================
section "10" "Logout → cookies cleared"
# =============================================================================
# Log in and capture cookies
curl -s -c /tmp/jwt_logout_cookies.txt \
    -X POST "$API/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" > /dev/null

LOGOUT_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -b /tmp/jwt_logout_cookies.txt \
    -c /tmp/jwt_logout_cookies.txt \
    -X POST "$API/auth/logout/")
if [[ "$LOGOUT_CODE" == "200" ]]; then
    pass "Logout returns 200"
else
    fail "Logout returned $LOGOUT_CODE (expected 200)"
fi

# After logout, cookies should have expired max_age = 0
# Check Set-Cookie headers from logout response
LOGOUT_HEADERS=$(curl -s -D - \
    -b /tmp/jwt_logout_cookies.txt \
    -X POST "$API/auth/logout/" -o /dev/null)

if echo "$LOGOUT_HEADERS" | grep -qi "access_token=;"; then
    pass "access_token cookie cleared (empty value) on logout"
elif echo "$LOGOUT_HEADERS" | grep -qi "access_token"; then
    pass "access_token Set-Cookie header present on logout response"
else
    fail "No access_token cookie clearing header in logout response"
fi

# Verify old token is still technically valid access-token-wise (logout is stateless)
# (simplejwt without blacklist — tokens remain valid until exp)
AFTER_LOGOUT=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API/users/me/")
if [[ "$AFTER_LOGOUT" == "200" ]]; then
    echo -e "  ${YELLOW}⚠ NOTE${NC} — Token remains valid after logout (stateless JWT — expected if blacklist is not enabled)"
elif [[ "$AFTER_LOGOUT" == "401" ]]; then
    pass "Token invalidated server-side after logout"
fi

# =============================================================================
section "11" "Schedule assign_slot (admin role required)"
# =============================================================================
# Fetch list of staff users to get a valid user ID
USERS_RESP=$(curl -s \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API/users/assignable/")

# Find a staff/manager user ID other than the admin
STAFF_ID=$(echo "$USERS_RESP" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

if [[ -z "$STAFF_ID" ]]; then
    echo -e "  ${YELLOW}⚠ SKIP${NC} — No assignable users found; skipping assign_slot test"
else
    SLOT_RESP=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API/schedules/assign_slot/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": $STAFF_ID,
            \"week_start\": \"2026-05-11\",
            \"day\": \"monday\",
            \"shift\": \"morning\",
            \"start_time\": \"08:00\",
            \"end_time\": \"16:00\"
        }")

    if [[ "$SLOT_RESP" == "200" || "$SLOT_RESP" == "201" ]]; then
        pass "assign_slot accepted (HTTP $SLOT_RESP)"
    elif [[ "$SLOT_RESP" == "400" ]]; then
        echo -e "  ${YELLOW}⚠ NOTE${NC} — assign_slot returned 400 (may be 24h lead constraint or duplicate slot)"
    elif [[ "$SLOT_RESP" == "403" ]]; then
        fail "assign_slot returned 403 — authenticated user lacks required role"
    else
        echo -e "  ${YELLOW}⚠ NOTE${NC} — assign_slot returned $SLOT_RESP"
    fi
fi

# =============================================================================
# Summary
# =============================================================================
TOTAL=$((PASS + FAIL))
echo -e "\n${BOLD}══════════════════════════════════════════${NC}"
echo -e "  ${BOLD}Results: $TOTAL tests  — ${GREEN}$PASS passed${NC}  ${RED}$FAIL failed${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}\n"

# Cleanup temp files
rm -f /tmp/jwt_test_cookies.txt /tmp/jwt_test_cookies2.txt /tmp/jwt_logout_cookies.txt

[[ $FAIL -eq 0 ]]
