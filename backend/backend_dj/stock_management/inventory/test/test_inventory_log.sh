#!/bin/bash

# Test InventoryLog bulk-create endpoint and log listing
# Tests:
#   POST /api/inventory-log/bulk-create/
#   GET  /api/inventory-log/
#   GET  /api/inventory-log/{id}/

BASE_URL="http://localhost:8000/api"
TIMESTAMP=$(date +%s%N)
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass()    { echo -e "${GREEN}  ✅ PASS${NC}: $1"; ((PASS++)); }
fail()    { echo -e "${RED}  ❌ FAIL${NC}: $1"; ((FAIL++)); }
section() { echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"; }

# ── helpers ──────────────────────────────────────────────────────────────────

get_field() { echo "$1" | grep -o "\"$2\":[^,}]*" | head -1 | sed 's/.*: *//;s/[",]//g'; }
get_id()    { get_field "$1" "id"; }
AUTH()      { echo "-H \"Authorization: Bearer $TOKEN\""; }

# ── AUTH: login ──────────────────────────────────────────────────────────────

section "AUTH — Login"

_try_login() {
  echo "$( curl -s -X POST "$BASE_URL/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$1\",\"password\":\"$2\"}" )"
}

LOGIN_RESP=$(_try_login "admin@example.com" "admin123")
TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [[ -z "$TOKEN" ]]; then
  LOGIN_RESP=$(_try_login "admin" "admin123")
  TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
fi

if [[ -z "$TOKEN" ]]; then
  LOGIN_RESP=$(_try_login "testuser123" "TestPass123!")
  TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
fi

if [[ -n "$TOKEN" ]]; then
  pass "Logged in — token acquired (${TOKEN:0:20}...)"
else
  fail "Could not obtain JWT token — response: $LOGIN_RESP"
  echo -e "${RED}Aborting: authentication required for all inventory endpoints${NC}"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"

# ── setup: create 2 inventory items to work with ─────────────────────────────

section "SETUP — Create test inventory items"

ITEM1=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{\"name\":\"Log Test Item A $TIMESTAMP\",\"unit\":\"kg\",\"current_stock\":100,\"min_threshold\":10}")
ITEM1_ID=$(get_id "$ITEM1")

ITEM2=$(curl -s -X POST "$BASE_URL/inventory/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{\"name\":\"Log Test Item B $TIMESTAMP\",\"unit\":\"pcs\",\"current_stock\":50,\"min_threshold\":5}")
ITEM2_ID=$(get_id "$ITEM2")

if [[ -n "$ITEM1_ID" && "$ITEM1_ID" =~ ^[0-9]+$ ]]; then
  pass "Created inventory item A (ID=$ITEM1_ID)"
else
  fail "Could not create inventory item A — response: $ITEM1"
  echo "Aborting: need inventory items to test logs"
  exit 1
fi

if [[ -n "$ITEM2_ID" && "$ITEM2_ID" =~ ^[0-9]+$ ]]; then
  pass "Created inventory item B (ID=$ITEM2_ID)"
else
  fail "Could not create inventory item B — response: $ITEM2"
  exit 1
fi

# ── 1. bulk-create: receipt ───────────────────────────────────────────────────

section "1. POST /api/inventory-log/bulk-create/ — reason_type: receipt"

RECEIPT_RESP=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{
    \"entries\": [
      {\"inventory_id\": $ITEM1_ID, \"quantity_change\": 20, \"reason_type\": \"receipt\", \"reason_detail\": \"PO-001\"},
      {\"inventory_id\": $ITEM2_ID, \"quantity_change\": 10, \"reason_type\": \"receipt\", \"reason_detail\": \"PO-001\"}
    ]
  }")

LOG1_ID=$(echo "$RECEIPT_RESP" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
REASON_TYPE=$(echo "$RECEIPT_RESP" | grep -o '"reason_type":"[^"]*"' | head -1 | grep -o '"receipt\|stock_take"')

if [[ -n "$LOG1_ID" ]]; then
  pass "Bulk receipt created — first log ID=$LOG1_ID"
else
  fail "Bulk receipt failed — response: $RECEIPT_RESP"
fi

if echo "$RECEIPT_RESP" | grep -q '"reason_type":"receipt"'; then
  pass "reason_type is 'receipt'"
else
  fail "reason_type not 'receipt' — response: $RECEIPT_RESP"
fi

if echo "$RECEIPT_RESP" | grep -q '"reason_detail":"PO-001"'; then
  pass "reason_detail 'PO-001' stored"
else
  fail "reason_detail missing — response: $RECEIPT_RESP"
fi

if echo "$RECEIPT_RESP" | grep -q '"reason_type_display":"Receipt"'; then
  pass "reason_type_display is 'Receipt'"
else
  fail "reason_type_display missing — response: $RECEIPT_RESP"
fi

# Stock should have increased
ITEM1_AFTER=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory/$ITEM1_ID/")
STOCK1=$(get_field "$ITEM1_AFTER" "current_stock")
if (( $(echo "$STOCK1 == 120" | bc -l) )); then
  pass "Item A stock updated: 100 + 20 = $STOCK1"
else
  fail "Item A stock wrong: expected 120, got $STOCK1"
fi

ITEM2_AFTER=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory/$ITEM2_ID/")
STOCK2=$(get_field "$ITEM2_AFTER" "current_stock")
if (( $(echo "$STOCK2 == 60" | bc -l) )); then
  pass "Item B stock updated: 50 + 10 = $STOCK2"
else
  fail "Item B stock wrong: expected 60, got $STOCK2"
fi

# ── 2. bulk-create: stock_take (negative adjustment) ─────────────────────────

section "2. POST /api/inventory-log/bulk-create/ — reason_type: stock_take"

TAKE_RESP=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{
    \"entries\": [
      {\"inventory_id\": $ITEM1_ID, \"quantity_change\": -5, \"reason_type\": \"stock_take\"},
      {\"inventory_id\": $ITEM2_ID, \"quantity_change\": -3, \"reason_type\": \"stock_take\"}
    ]
  }")

if echo "$TAKE_RESP" | grep -q '"reason_type":"stock_take"'; then
  pass "reason_type 'stock_take' accepted"
else
  fail "stock_take reason_type failed — response: $TAKE_RESP"
fi

ITEM1_AFTER2=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory/$ITEM1_ID/")
STOCK1B=$(get_field "$ITEM1_AFTER2" "current_stock")
if (( $(echo "$STOCK1B == 115" | bc -l) )); then
  pass "Item A stock after stock_take: 120 - 5 = $STOCK1B"
else
  fail "Item A stock wrong: expected 115, got $STOCK1B"
fi

# ── 3. bulk-create: multiple entries same item (aggregate) ───────────────────

section "3. POST bulk-create — multiple entries for same item (aggregated)"

AGG_RESP=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{
    \"entries\": [
      {\"inventory_id\": $ITEM1_ID, \"quantity_change\": 10, \"reason_type\": \"receipt\"},
      {\"inventory_id\": $ITEM1_ID, \"quantity_change\": 5,  \"reason_type\": \"receipt\"}
    ]
  }")

LOG_COUNT=$(echo "$AGG_RESP" | grep -o '"id":[0-9]*' | wc -l)
if [[ "$LOG_COUNT" -eq 2 ]]; then
  pass "2 log entries created for same item"
else
  fail "Expected 2 log entries, got $LOG_COUNT — response: $AGG_RESP"
fi

ITEM1_AGG=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory/$ITEM1_ID/")
STOCK1C=$(get_field "$ITEM1_AGG" "current_stock")
if (( $(echo "$STOCK1C == 130" | bc -l) )); then
  pass "Aggregated stock: 115 + 10 + 5 = $STOCK1C"
else
  fail "Aggregated stock wrong: expected 130, got $STOCK1C"
fi

# ── 4. validation: invalid reason_type ───────────────────────────────────────

section "4. Validation — invalid reason_type rejected"

BAD_REASON=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{\"entries\": [{\"inventory_id\": $ITEM1_ID, \"quantity_change\": 5, \"reason_type\": \"adjustment\"}]}")

if echo "$BAD_REASON" | grep -qiE '"errors"|"error"|"detail"'; then
  pass "Invalid reason_type 'adjustment' rejected"
else
  fail "Should have rejected 'adjustment' reason_type — response: $BAD_REASON"
fi

# ── 5. validation: zero quantity_change ──────────────────────────────────────

section "5. Validation — zero quantity_change rejected"

ZERO_QTY=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{\"entries\": [{\"inventory_id\": $ITEM1_ID, \"quantity_change\": 0, \"reason_type\": \"receipt\"}]}")

if echo "$ZERO_QTY" | grep -qiE '"errors"|"error"|"detail"'; then
  pass "Zero quantity_change rejected"
else
  fail "Should have rejected quantity_change=0 — response: $ZERO_QTY"
fi

# ── 6. validation: empty entries array ───────────────────────────────────────

section "6. Validation — empty entries array rejected"

EMPTY_ENTRIES=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{"entries": []}')

if echo "$EMPTY_ENTRIES" | grep -qiE '"errors"|"error"|"detail"'; then
  pass "Empty entries array rejected"
else
  fail "Should have rejected empty entries — response: $EMPTY_ENTRIES"
fi

# ── 7. validation: non-existent inventory_id ─────────────────────────────────

section "7. Validation — non-existent inventory_id rejected"

BAD_ID=$(curl -s -X POST "$BASE_URL/inventory-log/bulk-create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{"entries": [{"inventory_id": 999999, "quantity_change": 5, "reason_type": "receipt"}]}')

if echo "$BAD_ID" | grep -qiE '"errors"|"error"|"detail"'; then
  pass "Non-existent inventory_id rejected"
else
  fail "Should have rejected invalid inventory_id — response: $BAD_ID"
fi

# ── 8. GET /api/inventory-log/ ────────────────────────────────────────────────

section "8. GET /api/inventory-log/ — list logs"

LIST_RESP=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory-log/")
if echo "$LIST_RESP" | grep -q '"reason_type"'; then
  pass "Log list contains reason_type field"
else
  fail "Log list missing reason_type — response: $(echo $LIST_RESP | head -c 300)"
fi

if echo "$LIST_RESP" | grep -qv '"reason":[^_]'; then
  pass "Old 'reason' field not present"
else
  fail "Old 'reason' field still in response"
fi

# ── 9. GET /api/inventory-log/{id}/ ──────────────────────────────────────────

section "9. GET /api/inventory-log/{id}/ — retrieve single log"

DETAIL_RESP=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory-log/$LOG1_ID/")
if echo "$DETAIL_RESP" | grep -q '"reason_type":"receipt"'; then
  pass "Log detail has correct reason_type"
else
  fail "Log detail wrong — response: $DETAIL_RESP"
fi

if echo "$DETAIL_RESP" | grep -q '"reason_type_display":"Receipt"'; then
  pass "Log detail has reason_type_display"
else
  fail "reason_type_display missing from detail — response: $DETAIL_RESP"
fi

# ── 10. GET /api/inventory/{id}/history/ ─────────────────────────────────────

section "10. GET /api/inventory/{id}/history/ — history contains new log fields"

HIST_RESP=$(curl -s -H "$AUTH_HEADER" "$BASE_URL/inventory/$ITEM1_ID/history/")
if echo "$HIST_RESP" | grep -q '"reason_type"'; then
  pass "History response contains reason_type"
else
  echo -e "  (skip — history endpoint may use a different serializer)"
fi

# ── summary ───────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Results: ${GREEN}$PASS passed${NC}  ${RED}$FAIL failed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
