#!/bin/bash

###############################################################################
# Bulk Create Users Script (Optimized)
# Creates 20 staff accounts (mix of managers and staff) + 5 customers
# Saves all credentials to a file for future testing
###############################################################################

# Removed: set -e (allows script to continue even if commands fail)

BASE_URL="http://localhost:8000/api"
OUTPUT_FILE="test_credentials.txt"
LOG_FILE="bulk_create.log"
DELAY=2  # Delay between requests to avoid rate limits

# Clear output file
> "$OUTPUT_FILE"
> "$LOG_FILE"

echo "=== Bulk User Creation Script ===" | tee -a "$LOG_FILE"
echo "Base URL: $BASE_URL" | tee -a "$LOG_FILE"
echo "Output: $OUTPUT_FILE" | tee -a "$LOG_FILE"
echo "Delay between requests: ${DELAY}s" | tee -a "$LOG_FILE"
echo ""

# ============================================================================
# Step 1: Login as admin (admin should already exist from shell)
# ============================================================================

echo "Step 1: Getting admin token..." | tee -a "$LOG_FILE"

ADMIN_EMAIL="admin@pizza.local"
ADMIN_PASSWORD="AdminPass123!@#"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }")

ADMIN_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access // empty')

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ Failed to get admin token. Response: $LOGIN_RESPONSE" | tee -a "$LOG_FILE"
  exit 1
fi

echo "✅ Admin token obtained" | tee -a "$LOG_FILE"
echo "" >> "$OUTPUT_FILE"
echo "=== ADMIN ACCOUNT ===" >> "$OUTPUT_FILE"
echo "Email: $ADMIN_EMAIL" >> "$OUTPUT_FILE"
echo "Username: admin_pizza" >> "$OUTPUT_FILE"
echo "Password: $ADMIN_PASSWORD" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# ============================================================================
# Step 2: Create 20 Staff Accounts (mix of managers and staff)
# ============================================================================

echo "Step 2: Creating 20 staff accounts (managers & staff)..." | tee -a "$LOG_FILE"
echo "" >> "$OUTPUT_FILE"
echo "=== STAFF ACCOUNTS (20 total: 5 managers + 15 staff) ===" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

STAFF_COUNT=0
SUCCESS_COUNT=0

# Create 5 managers
for i in {1..5}; do
  STAFF_USERNAME="manager_$i"
  STAFF_EMAIL="manager${i}@pizza.local"
  STAFF_PASSWORD="Manager${i}Pass123!@#"
  
  echo "[$((STAFF_COUNT + 1))/20] Creating manager: $STAFF_EMAIL..." | tee -a "$LOG_FILE"
  
  STAFF_RESPONSE=$(curl -s -X POST "$BASE_URL/users/create-staff/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d "{
      \"email\": \"$STAFF_EMAIL\",
      \"username\": \"$STAFF_USERNAME\",
      \"password\": \"$STAFF_PASSWORD\",
      \"first_name\": \"Manager\",
      \"last_name\": \"$i\",
      \"phone_number\": \"+84912345${i}90\",
      \"role\": \"manager\"
    }")
  
  ERROR=$(echo "$STAFF_RESPONSE" | jq -r '.error // empty')
  if [ ! -z "$ERROR" ]; then
    echo "  ⚠️  Error: $ERROR" | tee -a "$LOG_FILE"
  else
    echo "  ✅ Manager created" | tee -a "$LOG_FILE"
    echo "$STAFF_EMAIL | $STAFF_USERNAME | $STAFF_PASSWORD" >> "$OUTPUT_FILE"
    ((SUCCESS_COUNT++))
  fi
  
  ((STAFF_COUNT++))
  sleep "$DELAY"
done

# Create 15 staff
for i in {1..15}; do
  STAFF_USERNAME="staff_$i"
  STAFF_EMAIL="staff${i}@pizza.local"
  STAFF_PASSWORD="Staff${i}Pass123!@#"
  
  echo "[$((STAFF_COUNT + 1))/20] Creating staff: $STAFF_EMAIL..." | tee -a "$LOG_FILE"
  
  STAFF_RESPONSE=$(curl -s -X POST "$BASE_URL/users/create-staff/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d "{
      \"email\": \"$STAFF_EMAIL\",
      \"username\": \"$STAFF_USERNAME\",
      \"password\": \"$STAFF_PASSWORD\",
      \"first_name\": \"Staff\",
      \"last_name\": \"$i\",
      \"phone_number\": \"+84912345${i}00\",
      \"role\": \"staff\"
    }")
  
  ERROR=$(echo "$STAFF_RESPONSE" | jq -r '.error // empty')
  if [ ! -z "$ERROR" ]; then
    echo "  ⚠️  Error: $ERROR" | tee -a "$LOG_FILE"
  else
    echo "  ✅ Staff created" | tee -a "$LOG_FILE"
    echo "$STAFF_EMAIL | $STAFF_USERNAME | $STAFF_PASSWORD" >> "$OUTPUT_FILE"
    ((SUCCESS_COUNT++))
  fi
  
  ((STAFF_COUNT++))
  sleep "$DELAY"
done

echo "✅ Created $SUCCESS_COUNT/$STAFF_COUNT staff accounts" | tee -a "$LOG_FILE"
echo ""

# ============================================================================
# Step 3: Create 5 Customer Accounts
# ============================================================================

echo "Step 3: Creating 5 customer accounts..." | tee -a "$LOG_FILE"
echo "" >> "$OUTPUT_FILE"
echo "=== CUSTOMER ACCOUNTS (5 total) ===" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

CUSTOMER_COUNT=0
CUST_SUCCESS=0

for i in {1..5}; do
  CUST_USERNAME="customer_$i"
  CUST_EMAIL="customer${i}@pizza.local"
  CUST_PASSWORD="Customer${i}Pass123!@#"
  
  echo "[$i/5] Creating customer: $CUST_EMAIL..." | tee -a "$LOG_FILE"
  
  CUST_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register/" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"$CUST_EMAIL\",
      \"username\": \"$CUST_USERNAME\",
      \"password\": \"$CUST_PASSWORD\",
      \"first_name\": \"Customer\",
      \"last_name\": \"$i\",
      \"phone_number\": \"+84912345${i}50\"
    }")
  
  ERROR=$(echo "$CUST_RESPONSE" | jq -r '.error // empty')
  if [ ! -z "$ERROR" ]; then
    echo "  ⚠️  Error: $ERROR" | tee -a "$LOG_FILE"
  else
    echo "  ✅ Customer created" | tee -a "$LOG_FILE"
    echo "$CUST_EMAIL | $CUST_USERNAME | $CUST_PASSWORD" >> "$OUTPUT_FILE"
    ((CUST_SUCCESS++))
  fi
  
  ((CUSTOMER_COUNT++))
  sleep "$DELAY"
done

echo "✅ Created $CUST_SUCCESS/$CUSTOMER_COUNT customer accounts" | tee -a "$LOG_FILE"
echo ""

# ============================================================================
# Summary
# ============================================================================

TOTAL=$((1 + SUCCESS_COUNT + CUST_SUCCESS))
echo "=== SUMMARY ===" | tee -a "$LOG_FILE"
echo "✅ Total accounts created: $TOTAL" | tee -a "$LOG_FILE"
echo "  - 1 Admin" | tee -a "$LOG_FILE"
echo "  - 5 Managers ($(( SUCCESS_COUNT > 5 ? 5 : SUCCESS_COUNT ))/$((SUCCESS_COUNT >= 5 ? 5 : 0)) of staff total)" | tee -a "$LOG_FILE"
echo "  - 15 Staff ($(( SUCCESS_COUNT > 5 ? SUCCESS_COUNT - 5 : 0 ))/$((SUCCESS_COUNT > 5 ? 15 : 0)))" | tee -a "$LOG_FILE"
echo "  - 5 Customers ($CUST_SUCCESS/5)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📁 Credentials saved to: $OUTPUT_FILE" | tee -a "$LOG_FILE"
echo "📝 Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""

echo "=== TEST CREDENTIALS ===" | tee -a "$LOG_FILE"
cat "$OUTPUT_FILE"
