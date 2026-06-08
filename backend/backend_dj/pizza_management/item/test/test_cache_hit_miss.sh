#!/bin/bash
# Test cache behavior (HIT/MISS) for items list endpoint
# Usage: bash test_cache_hit_miss.sh [BASE_URL] [QUERY_STRING]

BASE_URL="${1:-http://localhost:8000}"
API_PATH="/api/pizza/items/"
QUERY_STRING="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGE_PY="${MANAGE_PY:-$SCRIPT_DIR/../../../manage.py}"

# Compute params hash same as the application
compute_hash() {
  local qs="$1"
  python3 - <<PY
import json,hashlib,sys
qs = sys.argv[1] if len(sys.argv)>1 else ''
if not qs:
    params = {}
else:
    # qs expected like "a=1&b=2"
    from urllib.parse import parse_qs
    raw = parse_qs(qs, keep_blank_values=True)
    # normalize to single values where appropriate
    params = {k: (v[0] if len(v)==1 else v) for k,v in raw.items()}
print(hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8])
PY
}

PARAMS_HASH=$(compute_hash "$QUERY_STRING")
CACHE_KEY="items_list:all:params_${PARAMS_HASH}"

echo "Base URL: $BASE_URL"
echo "Endpoint: $API_PATH"
echo "Query: $QUERY_STRING"
echo "Computed cache key: $CACHE_KEY"

# helper to run manage.py shell commands
manage_shell() {
  local cmd="$1"
  if [[ -f "$MANAGE_PY" ]]; then
    python3 "$MANAGE_PY" shell -c "$cmd"
  else
    echo "(manage.py not found at $MANAGE_PY)"
    return 2
  fi
}

# Ensure key is deleted
echo "\nDeleting cache key (if present)..."
manage_shell "from django.core.cache import cache; cache.delete('$CACHE_KEY'); print('deleted')" >/dev/null 2>&1 || true

# Confirm MISS
echo "Checking cache before request (expect MISS):"
manage_shell "from django.core.cache import cache; v=cache.get('$CACHE_KEY'); print('HIT' if v is not None else 'MISS')"

# Make first request
echo "\nMaking first request (should populate cache)..."
URL="$BASE_URL$API_PATH"
if [[ -n "$QUERY_STRING" ]]; then
  URL="$URL?$QUERY_STRING"
fi
HTTP1=$(curl -s -w "%{http_code}" -o /tmp/resp_cache_test -X GET "$URL")
BODY1=$(cat /tmp/resp_cache_test)
echo "HTTP $HTTP1"

# Check cache after first request (expect HIT)
echo "Checking cache after first request (expect HIT):"
manage_shell "from django.core.cache import cache; v=cache.get('$CACHE_KEY'); print('HIT' if v is not None else 'MISS')"

# Make second request
echo "\nMaking second request (should be served from cache)..."
HTTP2=$(curl -s -w "%{http_code}" -o /tmp/resp_cache_test2 -X GET "$URL")
BODY2=$(cat /tmp/resp_cache_test2)
echo "HTTP $HTTP2"

# Confirm cache still present
echo "Checking cache after second request (expect HIT):"
manage_shell "from django.core.cache import cache; v=cache.get('$CACHE_KEY'); print('HIT' if v is not None else 'MISS')"

# Cleanup temp files
rm -f /tmp/resp_cache_test /tmp/resp_cache_test2

echo "\nDone. If you see MISS before the first request and HIT afterwards, caching works."
