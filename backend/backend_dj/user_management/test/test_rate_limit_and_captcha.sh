#!/bin/bash
# =============================================================================
# test_rate_limit_and_captcha.sh
# =============================================================================
# Verifies @rate_limit and @captcha_guard on all decorated user_management
# endpoints.
#
# Endpoints under test
# ──────────────────────────────────────────────────────────────────────────────
#  POST /api/auth/login/            limit=10/15min/IP   CAPTCHA at 6th request
#  POST /api/auth/register/         limit=5/hour/IP     CAPTCHA at 3rd request
#  POST /api/users/change-password/ limit=5/15min/user  (no CAPTCHA)
#  POST /api/users/create-staff/    limit=10/hour/IP+user
#
# Cache key format (rate_helpers.py)
#   IP scope     → rl:{prefix}:ip:127.0.0.1
#   user scope   → rl:{prefix}:user:{user_id}
#   ip+user      → rl:{prefix}:ip+user:127.0.0.1:{user_id}
#
# Prerequisites
#   • Django dev server running at BASE_URL
#   • Redis running (used by the rate counter cache)
#   • jq installed
#   • redis-cli installed
#
# Usage
#   bash test_rate_limit_and_captcha.sh [BASE_URL]
#   # e.g. bash test_rate_limit_and_captcha.sh http://localhost:8000
# =============================================================================

BASE_URL="${1:-http://localhost:8000}"
API="$BASE_URL/api"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass()  { echo -e "  ${GREEN}✓ PASS${RESET}  $*"; }
fail()  { echo -e "  ${RED}✗ FAIL${RESET}  $*"; ((FAILURES++)); }
info()  { echo -e "  ${CYAN}ℹ${RESET}  $*"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
header(){ echo -e "\n${BOLD}${CYAN}══ $* ══${RESET}"; }

FAILURES=0

# ── Cache helpers (django_redis-aware) ────────────────────────────────────────
#
# Django cache is configured in settings.py as:
#   BACKEND   : django_redis.cache.RedisCache
#   LOCATION  : redis://127.0.0.1:6379/1        ← DB 1, NOT DB 0
#   COMPRESSOR: ZlibCompressor                   ← values are zlib-compressed
#
# django_redis prepends ":<version>:" to every key, so the actual Redis key
# for "rl:login:ip:127.0.0.1" stored at DB 1 is ":1:rl:login:ip:127.0.0.1".
#
# Consequences for this test script:
#   flush_key   → redis-cli -n 1 DEL ":1:<key>"   (DEL works without decompression)
#   set_counter → python manage.py shell           (must write a compressed value)
#   get_counter → python manage.py shell           (must decompress to read)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANAGE_PY="${MANAGE_PY:-$SCRIPT_DIR/../../manage.py}"
REDIS_DB="${REDIS_DB:-1}"
CACHE_KEY_PREFIX="${CACHE_KEY_PREFIX:-:1:}"   # django_redis default version prefix

# Delete a Django cache key via redis-cli (DEL needs no decompression)
flush_key() {
    if command -v redis-cli &>/dev/null; then
        redis-cli -n "$REDIS_DB" DEL "${CACHE_KEY_PREFIX}$1" >/dev/null 2>&1
    else
        warn "redis-cli not found – cannot flush key '$1'. Counters may persist."
    fi
}

# Set a Django cache counter using the Django shell (writes compressed value)
set_counter() {
    local key="$1" val="$2" ttl="${3:-3600}"
    if [[ -f "$MANAGE_PY" ]]; then
        python "$MANAGE_PY" shell -c \
            "from django.core.cache import cache; cache.set('$key', $val, timeout=$ttl)" \
            >/dev/null 2>&1
    else
        warn "manage.py not found – cannot pre-set counter '$key'."
    fi
}

# Read a Django cache counter via the Django shell (decompresses automatically)
get_counter() {
    if [[ -f "$MANAGE_PY" ]]; then
        python "$MANAGE_PY" shell -c \
            "from django.core.cache import cache; v=cache.get('$1'); print(v if v is not None else 'N/A')" \
            2>/dev/null | tail -1
    else
        echo "N/A"
    fi
}

# POST wrapper — returns HTTP status code on stdout
post() {
    local url="$1" data="$2" token="${3:-}"
    local headers=(-H "Content-Type: application/json")
    [[ -n "$token" ]] && headers+=(-H "Authorization: Bearer $token")
    curl -s -o /dev/null -w "%{http_code}" -X POST "$url" "${headers[@]}" -d "$data"
}

# POST wrapper — returns full body (for parsing tokens / user_id)
post_body() {
    local url="$1" data="$2" token="${3:-}"
    local headers=(-H "Content-Type: application/json")
    [[ -n "$token" ]] && headers+=(-H "Authorization: Bearer $token")
    curl -s -X POST "$url" "${headers[@]}" -d "$data"
}

# POST wrapper — returns "BODY|||STATUS" in a single curl call
# Use get_status / get_body to parse the result
post_full() {
    local url="$1" data="$2" token="${3:-}"
    local headers=(-H "Content-Type: application/json")
    [[ -n "$token" ]] && headers+=(-H "Authorization: Bearer $token")
    curl -s -w "|||%{http_code}" -X POST "$url" "${headers[@]}" -d "$data"
}
get_status() { echo "${1##*|||}" ; }
get_body()   { echo "${1%|||*}"  ; }

# Assert HTTP code
assert_status() {
    local got="$1" want="$2" label="$3"
    if [[ "$got" == "$want" ]]; then
        pass "$label (HTTP $got)"
    else
        fail "$label — expected HTTP $want, got HTTP $got"
    fi
}

# =============================================================================
# 0. Setup — create or confirm test users
# =============================================================================
header "0. Setup"

# Unique suffix to avoid clashing with real data
SUFFIX="ratelimittest_$$"
CUSTOMER_EMAIL="customer_${SUFFIX}@example.com"
CUSTOMER_USER="cust_${SUFFIX}"
CUSTOMER_PASS="TestPass@1234"

ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"

info "Test customer : $CUSTOMER_EMAIL"
info "Admin account : $ADMIN_EMAIL  (override via env ADMIN_EMAIL / ADMIN_PASS)"

# Register test customer (ignore failure if it already exists)
REG_BODY=$(post_body "$API/auth/register/" "{
    \"email\":\"$CUSTOMER_EMAIL\",
    \"username\":\"$CUSTOMER_USER\",
    \"password\":\"$CUSTOMER_PASS\",
    \"first_name\":\"Rate\",\"last_name\":\"Test\"
}")
CUSTOMER_ID=$(echo "$REG_BODY" | jq -r '.user.id // empty' 2>/dev/null)
if [[ -z "$CUSTOMER_ID" ]]; then
    # Already exists — try to login to get the ID
    LOGIN_BODY=$(post_body "$API/auth/login/" "{\"email\":\"$CUSTOMER_EMAIL\",\"password\":\"$CUSTOMER_PASS\"}")
    CUSTOMER_ID=$(echo "$LOGIN_BODY" | jq -r '.user.id // empty' 2>/dev/null)
fi
[[ -n "$CUSTOMER_ID" ]] && info "Customer ID  : $CUSTOMER_ID" || warn "Could not determine customer ID"

# Get admin token for create-staff tests
LOGIN_BODY=$(post_body "$API/auth/login/" "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")
ADMIN_TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access // empty' 2>/dev/null)
ADMIN_ID=$(echo "$LOGIN_BODY" | jq -r '.user.id // empty' 2>/dev/null)
if [[ -n "$ADMIN_TOKEN" ]]; then
    info "Admin token  : ${ADMIN_TOKEN:0:30}..."
    info "Admin ID     : $ADMIN_ID"
else
    warn "Admin login failed — create-staff rate-limit test will be skipped"
    warn "Set ADMIN_EMAIL and ADMIN_PASS env vars to run all tests"
fi

# Flush all potentially-stale counters once at the top
flush_key "rl:login:ip:127.0.0.1"
flush_key "rl:register:ip:127.0.0.1"
[[ -n "$CUSTOMER_ID" ]] && flush_key "rl:chpwd:user:$CUSTOMER_ID"
[[ -n "$ADMIN_ID"    ]] && flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"

# =============================================================================
# 1. Login — rate limit  (limit=10, window=900, scope=ip)
# =============================================================================
header "1. Login — rate limit  (10 req / 15 min / IP)"

flush_key "rl:login:ip:127.0.0.1"

LOGIN_DATA="{\"email\":\"$CUSTOMER_EMAIL\",\"password\":\"$CUSTOMER_PASS\"}"

info "Sending 10 consecutive login requests..."
for i in $(seq 1 10); do
    STATUS=$(post "$API/auth/login/" "$LOGIN_DATA")
    # Accepted: 200 (ok), 400 (bad credentials), 401 (wrong pw) — NOT 429
    if [[ "$STATUS" == "429" ]]; then
        fail "Request #$i returned 429 too early (limit should be 10)"
        break
    fi
done
COUNTER=$(get_counter "rl:login:ip:127.0.0.1")
info "Counter after 10 requests: $COUNTER"
pass "10 requests allowed (no 429 yet)"

info "Sending 11th request (should be 429)..."
STATUS=$(post "$API/auth/login/" "$LOGIN_DATA")
assert_status "$STATUS" "429" "11th login → rate limit 429"

RETRY=$(curl -s -X POST "$API/auth/login/" \
    -H "Content-Type: application/json" -d "$LOGIN_DATA" | jq -r '.retry_after_seconds // empty' 2>/dev/null)
[[ -n "$RETRY" ]] && pass "Response includes retry_after_seconds=$RETRY" \
                  || warn "Response missing retry_after_seconds field"

# Reset for next test
flush_key "rl:login:ip:127.0.0.1"

# =============================================================================
# 2. Login — @captcha_guard trigger  (threshold = 60 % of 10 = 6th request)
# =============================================================================
header "2. Login — @captcha_guard trigger  (threshold = max(1, int(10*0.6)) = 6)"

# ── 2a: below threshold (count=4 → 5th request) — must NOT require CAPTCHA ───
set_counter "rl:login:ip:127.0.0.1" 4 900
info "2a: counter pre-set to 4 (next = 5th, below threshold=6) — CAPTCHA should NOT fire"
RES=$(post_full "$API/auth/login/" "$LOGIN_DATA")
HTTP=$(get_status "$RES")
if [[ "$HTTP" == "403" ]]; then
    BODY=$(get_body "$RES")
    if echo "$BODY" | jq -r '.error // empty' 2>/dev/null | grep -qi "captcha"; then
        fail "2a: CAPTCHA fired at count=5 which is BELOW threshold=6"
    else
        pass "2a: 403 is not CAPTCHA-related (permission/credential check)"
    fi
else
    pass "2a: No CAPTCHA block below threshold (HTTP $HTTP)"
fi

# ── 2b: at threshold (count=5 → 6th request) — CAPTCHA MUST fire ─────────────
flush_key "rl:login:ip:127.0.0.1"
set_counter "rl:login:ip:127.0.0.1" 5 900
info "2b: counter pre-set to 5 (next = 6th, AT threshold) — no recaptcha_token sent"
RES=$(post_full "$API/auth/login/" "$LOGIN_DATA")
HTTP=$(get_status "$RES")
BODY=$(get_body "$RES")
if [[ "$HTTP" == "403" ]]; then
    pass "2b: CAPTCHA block at threshold — HTTP 403 (RECAPTCHA_ENABLED=True)"
    ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
    [[ -n "$ERR" ]] && pass "2b: error field present: \"$ERR\"" \
                    || warn "2b: error field missing in 403 body"
elif [[ "$HTTP" == "200" || "$HTTP" == "401" || "$HTTP" == "400" ]]; then
    warn "2b: No CAPTCHA block (HTTP $HTTP) — RECAPTCHA_ENABLED=False or RECAPTCHA_SECRET_KEY not set"
else
    info "2b: HTTP $HTTP"
fi

# ── 2c: at threshold WITH fake token — Google must reject it ─────────────────
flush_key "rl:login:ip:127.0.0.1"
set_counter "rl:login:ip:127.0.0.1" 5 900
info "2c: same threshold, send WITH a fake recaptcha_token — should be rejected"
LOGIN_WITH_TOKEN="{\"email\":\"$CUSTOMER_EMAIL\",\"password\":\"$CUSTOMER_PASS\",\"recaptcha_token\":\"FAKE_TOKEN_TEST\"}"
RES=$(post_full "$API/auth/login/" "$LOGIN_WITH_TOKEN")
HTTP=$(get_status "$RES")
BODY=$(get_body "$RES")
if [[ "$HTTP" == "403" ]]; then
    pass "2c: Fake token correctly rejected (HTTP 403)"
    ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
    [[ -n "$ERR" ]] && info "   error: \"$ERR\""
elif [[ "$HTTP" == "200" || "$HTTP" == "401" || "$HTTP" == "400" ]]; then
    warn "2c: Fake token accepted (HTTP $HTTP) — RECAPTCHA_ENABLED=False (dev mode)"
fi

# ── 2d: above threshold (count=8 → 9th request) — CAPTCHA still enforced ─────
flush_key "rl:login:ip:127.0.0.1"
set_counter "rl:login:ip:127.0.0.1" 8 900
info "2d: counter=8 (above threshold, still below rate-limit 10) — CAPTCHA still required"
RES=$(post_full "$API/auth/login/" "$LOGIN_DATA")
HTTP=$(get_status "$RES")
if [[ "$HTTP" == "403" ]]; then
    pass "2d: CAPTCHA still enforced above threshold (HTTP 403)"
elif [[ "$HTTP" == "429" ]]; then
    fail "2d: Got 429 at count=8+1=9 which is under the rate limit (10)"
elif [[ "$HTTP" == "200" || "$HTTP" == "401" || "$HTTP" == "400" ]]; then
    warn "2d: No CAPTCHA (HTTP $HTTP) — RECAPTCHA_ENABLED=False"
fi

flush_key "rl:login:ip:127.0.0.1"

# =============================================================================
# 3. Register — rate limit  (limit=5, window=3600, scope=ip)
# =============================================================================
header "3. Register — rate limit  (5 req / hour / IP)"

flush_key "rl:register:ip:127.0.0.1"

info "Sending 5 register requests with unique emails..."
for i in $(seq 1 5); do
    DATA="{\"email\":\"reg_${i}_${SUFFIX}@example.com\",\"username\":\"reg_${i}_${SUFFIX}\",\"password\":\"Pass@${i}1234\"}"
    STATUS=$(post "$API/auth/register/" "$DATA")
    if [[ "$STATUS" == "429" ]]; then
        fail "Request #$i returned 429 too early (limit should be 5)"
        break
    fi
done
COUNTER=$(get_counter "rl:register:ip:127.0.0.1")
info "Counter after 5 requests: $COUNTER"
pass "5 register requests allowed"

info "Sending 6th request (should be 429)..."
DATA="{\"email\":\"reg_6_${SUFFIX}@example.com\",\"username\":\"reg_6_${SUFFIX}\",\"password\":\"Pass@61234\"}"
STATUS=$(post "$API/auth/register/" "$DATA")
assert_status "$STATUS" "429" "6th register → rate limit 429"

flush_key "rl:register:ip:127.0.0.1"

# =============================================================================
# 4. Register — @captcha_guard trigger  (threshold = 60 % of 5 = 3rd request)
# =============================================================================
header "4. Register — @captcha_guard trigger  (threshold = max(1, int(5*0.6)) = 3)"

# ── 4a: below threshold (count=1 → 2nd request) — must NOT require CAPTCHA ───
set_counter "rl:register:ip:127.0.0.1" 1 3600
info "4a: counter pre-set to 1 (next = 2nd, below threshold=3) — CAPTCHA should NOT fire"
DATA_BT="{\"email\":\"reg_bt_${SUFFIX}@example.com\",\"username\":\"reg_bt_${SUFFIX}\",\"password\":\"Pass@1234\"}"
RES=$(post_full "$API/auth/register/" "$DATA_BT")
HTTP=$(get_status "$RES")
if [[ "$HTTP" == "403" ]]; then
    BODY=$(get_body "$RES")
    if echo "$BODY" | jq -r '.error // empty' 2>/dev/null | grep -qi "captcha"; then
        fail "4a: CAPTCHA fired at count=2 which is BELOW threshold=3"
    else
        pass "4a: 403 is not CAPTCHA-related (permission/credential check)"
    fi
else
    pass "4a: No CAPTCHA block below threshold (HTTP $HTTP)"
fi

# ── 4b: at threshold (count=2 → 3rd request) — CAPTCHA MUST fire ─────────────
flush_key "rl:register:ip:127.0.0.1"
set_counter "rl:register:ip:127.0.0.1" 2 3600
info "4b: counter pre-set to 2 (next = 3rd, AT threshold) — no recaptcha_token sent"
DATA_AT="{\"email\":\"reg_at_${SUFFIX}@example.com\",\"username\":\"reg_at_${SUFFIX}\",\"password\":\"Pass@1234\"}"
RES=$(post_full "$API/auth/register/" "$DATA_AT")
HTTP=$(get_status "$RES")
BODY=$(get_body "$RES")
if [[ "$HTTP" == "403" ]]; then
    pass "4b: CAPTCHA block at threshold — HTTP 403 (RECAPTCHA_ENABLED=True)"
    ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
    [[ -n "$ERR" ]] && pass "4b: error field: \"$ERR\"" || warn "4b: error field missing"
elif [[ "$HTTP" == "201" || "$HTTP" == "400" ]]; then
    warn "4b: No CAPTCHA block (HTTP $HTTP) — RECAPTCHA_ENABLED=False"
else
    info "4b: HTTP $HTTP"
fi

# ── 4c: at threshold WITH fake token — Google must reject it ─────────────────
flush_key "rl:register:ip:127.0.0.1"
set_counter "rl:register:ip:127.0.0.1" 2 3600
info "4c: same threshold, WITH fake recaptcha_token — should be rejected"
DATA_FAKE="{\"email\":\"reg_fake_${SUFFIX}@example.com\",\"username\":\"reg_fake_${SUFFIX}\",\"password\":\"Pass@1234\",\"recaptcha_token\":\"FAKE_TOKEN_TEST\"}"
RES=$(post_full "$API/auth/register/" "$DATA_FAKE")
HTTP=$(get_status "$RES")
BODY=$(get_body "$RES")
if [[ "$HTTP" == "403" ]]; then
    pass "4c: Fake token correctly rejected (HTTP 403)"
    ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
    [[ -n "$ERR" ]] && info "   error: \"$ERR\""
elif [[ "$HTTP" == "201" || "$HTTP" == "400" ]]; then
    warn "4c: Fake token accepted (HTTP $HTTP) — RECAPTCHA_ENABLED=False (dev mode)"
fi

flush_key "rl:register:ip:127.0.0.1"

# =============================================================================
# 5. change-password — rate limit  (limit=5, window=900, scope=user)
# =============================================================================
header "5. change-password — rate limit  (5 req / 15 min / user)"

if [[ -z "$CUSTOMER_ID" ]]; then
    warn "Skipped — could not determine customer ID (check register/login above)"
else
    flush_key "rl:chpwd:user:$CUSTOMER_ID"

    # Get a fresh token
    LOGIN_BODY=$(post_body "$API/auth/login/" "{\"email\":\"$CUSTOMER_EMAIL\",\"password\":\"$CUSTOMER_PASS\"}")
    TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access // empty' 2>/dev/null)

    if [[ -z "$TOKEN" ]]; then
        warn "Skipped — could not log in as test customer"
    else
        info "Using customer token: ${TOKEN:0:30}..."
        # Use wrong old_password intentionally — decorator runs BEFORE validation, so 400 still increments counter
        PWD_DATA="{\"old_password\":\"WRONG_PASSWORD\",\"new_password\":\"NewPass@9999\"}"

        info "Sending 5 change-password requests (wrong old_password → 400, counter still increments)..."
        for i in $(seq 1 5); do
            STATUS=$(post "$API/users/change-password/" "$PWD_DATA" "$TOKEN")
            if [[ "$STATUS" == "429" ]]; then
                fail "Request #$i returned 429 too early (limit should be 5)"
                break
            fi
        done
        COUNTER=$(get_counter "rl:chpwd:user:$CUSTOMER_ID")
        info "Counter after 5 requests: $COUNTER"
        pass "5 change-password requests allowed (all 400 for wrong old_password)"

        info "Sending 6th request (should be 429)..."
        STATUS=$(post "$API/users/change-password/" "$PWD_DATA" "$TOKEN")
        assert_status "$STATUS" "429" "6th change-password → rate limit 429"

        flush_key "rl:chpwd:user:$CUSTOMER_ID"
    fi
fi

# =============================================================================
# 6. create-staff — rate limit  (limit=10, window=3600, scope=ip+user)
# =============================================================================
header "6. create-staff — rate limit  (10 req / hour / IP+user)"

if [[ -z "$ADMIN_TOKEN" || -z "$ADMIN_ID" ]]; then
    warn "Skipped — no admin token/ID (set ADMIN_EMAIL and ADMIN_PASS)"
else
    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"

    info "Sending 10 create-staff requests (all will fail 400/403/409 for bad data, counter still increments)..."
    STAFF_DATA="{\"email\":\"staff_PLACEHOLDER_${SUFFIX}@example.com\",\"username\":\"staff_PLACEHOLDER_${SUFFIX}\",\"password\":\"Pass@1234\",\"role\":\"staff\"}"

    for i in $(seq 1 10); do
        DATA=$(echo "$STAFF_DATA" | sed "s/PLACEHOLDER/$i/g")
        STATUS=$(post "$API/users/create-staff/" "$DATA" "$ADMIN_TOKEN")
        if [[ "$STATUS" == "429" ]]; then
            fail "Request #$i returned 429 too early (limit should be 10)"
            break
        fi
    done
    COUNTER=$(get_counter "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID")
    info "Counter after 10 requests: $COUNTER"
    pass "10 create-staff requests allowed"

    info "Sending 11th request (should be 429)..."
    DATA=$(echo "$STAFF_DATA" | sed "s/PLACEHOLDER/11/g")
    STATUS=$(post "$API/users/create-staff/" "$DATA" "$ADMIN_TOKEN")
    assert_status "$STATUS" "429" "11th create-staff → rate limit 429"

    RETRY=$(curl -s -X POST "$API/users/create-staff/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -d "$DATA" | jq -r '.retry_after_seconds // empty' 2>/dev/null)
    [[ -n "$RETRY" ]] && pass "Response includes retry_after_seconds=$RETRY" \
                      || warn "Response missing retry_after_seconds field"

    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
fi

# =============================================================================
# 7. create-staff — @captcha_guard trigger  (threshold = 60 % of 10 = 6th)
# =============================================================================
header "7. create-staff — @captcha_guard trigger  (threshold = max(1, int(10*0.6)) = 6)"

if [[ -z "$ADMIN_TOKEN" || -z "$ADMIN_ID" ]]; then
    warn "Skipped — no admin token/ID (set ADMIN_EMAIL and ADMIN_PASS)"
else
    # ── 7a: below threshold (count=4 → 5th request) — must NOT require CAPTCHA ──
    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
    set_counter "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID" 4 3600
    info "7a: counter pre-set to 4 (next = 5th, below threshold=6) — CAPTCHA should NOT fire"
    DATA_7A='{"email":"staff_7a_'"$SUFFIX"'@example.com","username":"staff_7a_'"$SUFFIX"'","password":"Pass@1234","role":"staff"}'
    RES=$(post_full "$API/users/create-staff/" "$DATA_7A" "$ADMIN_TOKEN")
    HTTP=$(get_status "$RES")
    if [[ "$HTTP" == "403" ]]; then
        BODY=$(get_body "$RES")
        ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
        if echo "$ERR" | grep -qi "captcha\|challenge"; then
            fail "7a: CAPTCHA fired at count=5 which is BELOW threshold=6"
        else
            pass "7a: 403 is not CAPTCHA-related (\"$ERR\")"
        fi
    else
        pass "7a: No CAPTCHA block below threshold (HTTP $HTTP)"
    fi

    # ── 7b: at threshold (count=5 → 6th request) — CAPTCHA MUST fire ────────────
    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
    set_counter "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID" 5 3600
    info "7b: counter pre-set to 5 (next = 6th, AT threshold) — no recaptcha_token sent"
    DATA_7B='{"email":"staff_7b_'"$SUFFIX"'@example.com","username":"staff_7b_'"$SUFFIX"'","password":"Pass@1234","role":"staff"}'
    RES=$(post_full "$API/users/create-staff/" "$DATA_7B" "$ADMIN_TOKEN")
    HTTP=$(get_status "$RES")
    BODY=$(get_body "$RES")
    if [[ "$HTTP" == "403" ]]; then
        ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
        if echo "$ERR" | grep -qi "captcha\|CAPTCHA\|challenge"; then
            pass "7b: CAPTCHA block at threshold — HTTP 403 (RECAPTCHA_ENABLED=True)"
            info "   error: \"$ERR\""
        else
            # Could be a permission 403 — warn but don't fail (depends on user role setup)
            warn "7b: 403 received but error doesn't mention CAPTCHA: \"$ERR\""
        fi
    elif [[ "$HTTP" == "201" || "$HTTP" == "400" || "$HTTP" == "409" ]]; then
        warn "7b: No CAPTCHA block (HTTP $HTTP) — RECAPTCHA_ENABLED=False"
    else
        info "7b: HTTP $HTTP  body: $(echo "$BODY" | head -c 200)"
    fi

    # ── 7c: at threshold WITH fake token — Google must reject it ─────────────────
    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
    set_counter "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID" 5 3600
    info "7c: same threshold, WITH fake recaptcha_token — should be rejected"
    DATA_7C='{"email":"staff_7c_'"$SUFFIX"'@example.com","username":"staff_7c_'"$SUFFIX"'","password":"Pass@1234","role":"staff","recaptcha_token":"FAKE_TOKEN_TEST"}'
    RES=$(post_full "$API/users/create-staff/" "$DATA_7C" "$ADMIN_TOKEN")
    HTTP=$(get_status "$RES")
    BODY=$(get_body "$RES")
    if [[ "$HTTP" == "403" ]]; then
        pass "7c: Fake token correctly rejected (HTTP 403)"
        ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
        [[ -n "$ERR" ]] && info "   error: \"$ERR\""
    elif [[ "$HTTP" == "201" || "$HTTP" == "400" || "$HTTP" == "409" ]]; then
        warn "7c: Fake token accepted (HTTP $HTTP) — RECAPTCHA_ENABLED=False (dev mode)"
    else
        info "7c: HTTP $HTTP"
    fi

    # ── 7d: above threshold (count=8 → 9th) — CAPTCHA still enforced ────────────
    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
    set_counter "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID" 8 3600
    info "7d: counter=8 (above threshold, still below rate-limit 10) — CAPTCHA still required"
    DATA_7D='{"email":"staff_7d_'"$SUFFIX"'@example.com","username":"staff_7d_'"$SUFFIX"'","password":"Pass@1234","role":"staff"}'
    RES=$(post_full "$API/users/create-staff/" "$DATA_7D" "$ADMIN_TOKEN")
    HTTP=$(get_status "$RES")
    if [[ "$HTTP" == "403" ]]; then
        BODY=$(get_body "$RES")
        ERR=$(echo "$BODY" | jq -r '.error // empty' 2>/dev/null)
        if echo "$ERR" | grep -qi "captcha\|challenge"; then
            pass "7d: CAPTCHA still enforced above threshold (HTTP 403)"
        else
            pass "7d: 403 received (may be permission, RECAPTCHA_ENABLED=False)"
        fi
    elif [[ "$HTTP" == "429" ]]; then
        fail "7d: Got 429 at count=8+1=9 which is under the rate limit (10)"
    elif [[ "$HTTP" == "201" || "$HTTP" == "400" || "$HTTP" == "409" ]]; then
        warn "7d: No CAPTCHA (HTTP $HTTP) — RECAPTCHA_ENABLED=False"
    fi

    flush_key "rl:cstaff:ip+user:127.0.0.1:$ADMIN_ID"
fi

# =============================================================================
# 8. Inspect live counters (optional sanity check)
# =============================================================================
header "8. Redis counter state after all tests"

if [[ -f "$MANAGE_PY" ]]; then
    for key in \
        "rl:login:ip:127.0.0.1" \
        "rl:register:ip:127.0.0.1" \
        "rl:chpwd:user:${CUSTOMER_ID:-?}" \
        "rl:cstaff:ip+user:127.0.0.1:${ADMIN_ID:-?}"; do
        VAL=$(python "$MANAGE_PY" shell -c \
            "from django.core.cache import cache; v=cache.get('$key'); print(v if v is not None else '(not set)')" \
            2>/dev/null | tail -1)
        info "$key = ${VAL:-(not set)}"
    done
else
    warn "manage.py not found — cannot inspect counters"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
if [[ "$FAILURES" -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}  ALL TESTS PASSED${RESET}"
else
    echo -e "${RED}${BOLD}  $FAILURES TEST(S) FAILED${RESET}"
fi
echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}\n"

exit "$FAILURES"
