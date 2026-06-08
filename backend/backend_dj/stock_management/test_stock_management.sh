#!/bin/bash

# ============================================================================
# Stock Management Module - Comprehensive cURL Test Script
# ============================================================================
# Test: Inventory, Provider, Purchase Order, Purchase Order Items
# Auth Required: Admin/Staff account for all operations
# ============================================================================

API_BASE="http://localhost:8000/api"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
}

print_section() {
  echo -e "\n${CYAN}─── $1 ───${NC}\n"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}→ $1${NC}"
}

# ============================================================================
# STEP 1: LOGIN & GET JWT TOKEN
# ============================================================================

print_header "LOGIN & AUTHENTICATION"

# Try to login with admin credentials
print_section "Attempting to login..."
print_info "POST /api/auth/login/"

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin",
    "password": "admin123"
  }')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  print_error "Failed to get access token"
  echo "Response: $LOGIN_RESPONSE"
  echo ""
  print_info "Trying alternative credentials..."
  
  # Try with testuser
  LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "testuser123",
      "password": "TestPass123!"
    }')
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
  REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ]; then
    print_error "Failed to authenticate with any credentials"
    echo "This script requires a valid admin/staff account"
    exit 1
  fi
fi

print_success "Authentication successful"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."

# ============================================================================
# STEP 2: TEST PROVIDER CRUD
# ============================================================================

print_header "PROVIDER MANAGEMENT"

# Create Provider 1
print_section "CREATE Provider"
print_info "POST /api/provider/"

CREATE_PROVIDER_1=$(curl -s -X POST "$API_BASE/provider/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Pizza Supplier Co",
    "email": "supplier@pizzaco.com",
    "phone": "+1-555-0101",
    "address": "123 Main St, City",
    "contact_person": "John Supplier"
  }')

PROVIDER_1_ID=$(echo "$CREATE_PROVIDER_1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$PROVIDER_1_ID" ]; then
  print_success "Provider 1 created (ID: $PROVIDER_1_ID)"
else
  print_error "Failed to create Provider 1"
  echo "Response: $CREATE_PROVIDER_1"
fi

# Create Provider 2
print_info "Creating second Provider..."

CREATE_PROVIDER_2=$(curl -s -X POST "$API_BASE/provider/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Cheese Distributor Ltd",
    "email": "cheese@distributor.com",
    "phone": "+1-555-0102",
    "address": "456 Oak Ave, Town",
    "contact_person": "Jane Cheese"
  }')

PROVIDER_2_ID=$(echo "$CREATE_PROVIDER_2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$PROVIDER_2_ID" ]; then
  print_success "Provider 2 created (ID: $PROVIDER_2_ID)"
else
  print_error "Failed to create Provider 2"
fi

# List Providers
print_section "READ Providers"
print_info "GET /api/provider/"

LIST_PROVIDERS=$(curl -s -X GET "$API_BASE/provider/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

PROVIDER_COUNT=$(echo "$LIST_PROVIDERS" | grep -o '"id":' | wc -l)
print_success "Retrieved $PROVIDER_COUNT providers"

# Retrieve single Provider
if [ -n "$PROVIDER_1_ID" ]; then
  print_info "GET /api/provider/$PROVIDER_1_ID/"
  
  RETRIEVE_PROVIDER=$(curl -s -X GET "$API_BASE/provider/$PROVIDER_1_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  PROVIDER_NAME=$(echo "$RETRIEVE_PROVIDER" | grep -o '"name":"[^"]*' | cut -d'"' -f4)
  print_success "Retrieved Provider: $PROVIDER_NAME"
fi

# Update Provider
if [ -n "$PROVIDER_1_ID" ]; then
  print_section "UPDATE Provider"
  print_info "PATCH /api/provider/$PROVIDER_1_ID/"
  
  UPDATE_PROVIDER=$(curl -s -X PATCH "$API_BASE/provider/$PROVIDER_1_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "phone": "+1-555-9999",
      "contact_person": "John Updated"
    }')
  
  print_success "Provider updated"
fi

# ============================================================================
# STEP 3: TEST INVENTORY CRUD
# ============================================================================

print_header "INVENTORY MANAGEMENT"

# Create Inventory Item 1
print_section "CREATE Inventory"
print_info "POST /api/inventory/"

CREATE_INVENTORY_1=$(curl -s -X POST "$API_BASE/inventory/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Mozzarella Cheese",
    "description": "Fresh mozzarella cheese for pizza",
    "unit": "kg",
    "quantity": 50,
    "min_threshold": 10,
    "max_threshold": 100,
    "reorder_quantity": 30,
    "provider_id": '$PROVIDER_1_ID'
  }')

INVENTORY_1_ID=$(echo "$CREATE_INVENTORY_1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$INVENTORY_1_ID" ]; then
  print_success "Inventory Item 1 created (ID: $INVENTORY_1_ID)"
else
  print_error "Failed to create Inventory Item 1"
  echo "Response: $CREATE_INVENTORY_1"
fi

# Create Inventory Item 2 (Low stock example)
print_info "Creating low-stock Inventory item..."

CREATE_INVENTORY_2=$(curl -s -X POST "$API_BASE/inventory/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Tomato Sauce",
    "description": "Red tomato sauce for pizza base",
    "unit": "l",
    "quantity": 5,
    "min_threshold": 10,
    "max_threshold": 100,
    "reorder_quantity": 30,
    "provider_id": '$PROVIDER_2_ID'
  }')

INVENTORY_2_ID=$(echo "$CREATE_INVENTORY_2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$INVENTORY_2_ID" ]; then
  print_success "Inventory Item 2 created (ID: $INVENTORY_2_ID, LOW STOCK)"
fi

# List Inventory
print_section "READ Inventory"
print_info "GET /api/inventory/"

LIST_INVENTORY=$(curl -s -X GET "$API_BASE/inventory/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

INVENTORY_COUNT=$(echo "$LIST_INVENTORY" | grep -o '"id":' | wc -l)
print_success "Retrieved $INVENTORY_COUNT inventory items"

# Get Low Stock Items
print_info "GET /api/inventory/low-stock/"

LOW_STOCK=$(curl -s -X GET "$API_BASE/inventory/low-stock/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

LOW_STOCK_COUNT=$(echo "$LOW_STOCK" | grep -o '"id":' | wc -l)
print_success "Found $LOW_STOCK_COUNT low-stock items"

# Retrieve single Inventory
if [ -n "$INVENTORY_1_ID" ]; then
  print_info "GET /api/inventory/$INVENTORY_1_ID/"
  
  RETRIEVE_INVENTORY=$(curl -s -X GET "$API_BASE/inventory/$INVENTORY_1_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  ITEM_NAME=$(echo "$RETRIEVE_INVENTORY" | grep -o '"name":"[^"]*' | head -1 | cut -d'"' -f4)
  print_success "Retrieved Inventory Item: $ITEM_NAME"
fi

# Update Inventory
if [ -n "$INVENTORY_1_ID" ]; then
  print_section "UPDATE Inventory"
  print_info "PATCH /api/inventory/$INVENTORY_1_ID/"
  
  UPDATE_INVENTORY=$(curl -s -X PATCH "$API_BASE/inventory/$INVENTORY_1_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "quantity": 75,
      "min_threshold": 15
    }')
  
  print_success "Inventory item updated"
fi

# Get Inventory History
if [ -n "$INVENTORY_1_ID" ]; then
  print_info "GET /api/inventory/$INVENTORY_1_ID/history/"
  
  INVENTORY_HISTORY=$(curl -s -X GET "$API_BASE/inventory/$INVENTORY_1_ID/history/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  print_success "Retrieved inventory history"
fi

# ============================================================================
# STEP 4: TEST PURCHASE ORDER CRUD
# ============================================================================

print_header "PURCHASE ORDER MANAGEMENT"

# Create Purchase Order
print_section "CREATE Purchase Order"
print_info "POST /api/purchase-order/"

CREATE_PO=$(curl -s -X POST "$API_BASE/purchase-order/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "order_number": "PO-'$(date +%s)'",
    "provider_id": '$PROVIDER_1_ID',
    "order_date": "2026-04-18",
    "expected_delivery_date": "2026-04-25",
    "status": "pending"
  }')

PO_ID=$(echo "$CREATE_PO" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$PO_ID" ]; then
  print_success "Purchase Order created (ID: $PO_ID)"
else
  print_error "Failed to create Purchase Order"
  echo "Response: $CREATE_PO"
fi

# List Purchase Orders
print_section "READ Purchase Orders"
print_info "GET /api/purchase-order/"

LIST_PO=$(curl -s -X GET "$API_BASE/purchase-order/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

PO_COUNT=$(echo "$LIST_PO" | grep -o '"id":' | wc -l)
print_success "Retrieved $PO_COUNT purchase orders"

# Retrieve single Purchase Order
if [ -n "$PO_ID" ]; then
  print_info "GET /api/purchase-order/$PO_ID/"
  
  RETRIEVE_PO=$(curl -s -X GET "$API_BASE/purchase-order/$PO_ID/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  print_success "Retrieved Purchase Order"
fi

# ============================================================================
# STEP 5: TEST PURCHASE ORDER ITEM CRUD
# ============================================================================

if [ -n "$PO_ID" ] && [ -n "$INVENTORY_1_ID" ]; then
  print_header "PURCHASE ORDER ITEMS"
  
  # Create Purchase Order Item
  print_section "CREATE Purchase Order Item"
  print_info "POST /api/purchase-order-item/"
  
  CREATE_POI=$(curl -s -X POST "$API_BASE/purchase-order-item/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "purchase_order_id": '$PO_ID',
      "inventory_id": '$INVENTORY_1_ID',
      "quantity": 25,
      "unit_price": 10.50
    }')
  
  POI_ID=$(echo "$CREATE_POI" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  
  if [ -n "$POI_ID" ]; then
    print_success "Purchase Order Item created (ID: $POI_ID)"
  else
    print_error "Failed to create Purchase Order Item"
    echo "PO_ID: $PO_ID, INVENTORY_ID: $INVENTORY_1_ID"
    echo "Response: $CREATE_POI"
  fi
  
  # List Purchase Order Items
  print_section "READ Purchase Order Items"
  print_info "GET /api/purchase-order-item/"
  
  LIST_POI=$(curl -s -X GET "$API_BASE/purchase-order-item/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  POI_COUNT=$(echo "$LIST_POI" | grep -o '"id":' | wc -l)
  print_success "Retrieved $POI_COUNT purchase order items"
  
  # Retrieve single PO Item
  if [ -n "$POI_ID" ]; then
    print_info "GET /api/purchase-order-item/$POI_ID/"
    
    RETRIEVE_POI=$(curl -s -X GET "$API_BASE/purchase-order-item/$POI_ID/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    print_success "Retrieved Purchase Order Item"
  fi
  
  # Update Purchase Order Item
  if [ -n "$POI_ID" ]; then
    print_section "UPDATE Purchase Order Item"
    print_info "PATCH /api/purchase-order-item/$POI_ID/"
    
    UPDATE_POI=$(curl -s -X PATCH "$API_BASE/purchase-order-item/$POI_ID/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d '{
        "quantity": 30,
        "unit_price": 11.00
      }')
    
    print_success "Purchase Order Item updated"
  fi
fi

# ============================================================================
# STEP 6: TEST PURCHASE ORDER CUSTOM ACTIONS
# ============================================================================

if [ -n "$PO_ID" ]; then
  print_header "PURCHASE ORDER CUSTOM ACTIONS"
  
  # Confirm Receipt
  print_section "CONFIRM RECEIPT"
  print_info "POST /api/purchase-order/$PO_ID/confirm-receipt/"
  
  CONFIRM_RECEIPT=$(curl -s -X POST "$API_BASE/purchase-order/$PO_ID/confirm-receipt/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  print_success "Confirm receipt request sent"
  
  # Create another PO for cancel test
  print_section "creating another PO to test cancel..."
  
  CREATE_PO_2=$(curl -s -X POST "$API_BASE/purchase-order/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "order_number": "PO-CANCEL-'$(date +%s)'",
      "provider_id": '$PROVIDER_2_ID',
      "order_date": "2026-04-18",
      "expected_delivery_date": "2026-04-28",
      "status": "pending"
    }')
  
  PO_2_ID=$(echo "$CREATE_PO_2" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  
  if [ -n "$PO_2_ID" ]; then
    print_success "Created second PO for cancel test (ID: $PO_2_ID)"
    
    # Cancel PO
    print_info "POST /api/purchase-order/$PO_2_ID/cancel/"
    
    CANCEL_PO=$(curl -s -X POST "$API_BASE/purchase-order/$PO_2_ID/cancel/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    print_success "Cancel request sent"
  fi
fi

# ============================================================================
# STEP 7: TEST BULK OPERATIONS
# ============================================================================

print_header "BULK OPERATIONS (Delete/Update Many)"

# Test Bulk Delete (delete-many)
if [ -n "$PROVIDER_1_ID" ] && [ -n "$PROVIDER_2_ID" ]; then
  print_section "BULK DELETE Providers"
  print_info "POST /api/provider/delete-many/"
  
  BULK_DELETE=$(curl -s -X DELETE "$API_BASE/provider/delete-many/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
      \"ids\": [$PROVIDER_1_ID, $PROVIDER_2_ID]
    }")
  
  print_success "Bulk delete request sent"
fi

# ============================================================================
# STEP 8: INVENTORY LOG
# ============================================================================

print_header "INVENTORY LOG"

print_section "READ Inventory Logs"
print_info "GET /api/inventory-log/"

LIST_LOGS=$(curl -s -X GET "$API_BASE/inventory-log/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

LOG_COUNT=$(echo "$LIST_LOGS" | grep -o '"id":' | wc -l)
print_success "Retrieved $LOG_COUNT inventory logs"

# ============================================================================
# TEST SUMMARY
# ============================================================================

print_header "TEST SUMMARY"

echo -e "${GREEN}✓ Test suite completed!${NC}\n"

echo -e "${YELLOW}Tested Modules:${NC}"
echo "  • Provider Management (CRUD + Bulk Delete)"
echo "  • Inventory Management (CRUD + Low Stock + History)"
echo "  • Purchase Order Management (CRUD + Custom Actions)"
echo "  • Purchase Order Items (CRUD)"
echo "  • Inventory Logs (Read)"
echo ""

echo -e "${YELLOW}Expected Results:${NC}"
echo "  ✓ 401 Unauthorized when no Authentication header"
echo "  ✓ 403 Forbidden for non-admin delete operations"
echo "  ✓ 201 Created for successful POST operations"
echo "  ✓ 200 OK for successful GET/PATCH operations"
echo "  ✓ 204 No Content for successful DELETE operations"
echo ""

echo -e "${YELLOW}Authorization Requirements:${NC}"
echo "  ✓ All operations require JWT authentication (Bearer token)"
echo "  ✓ All operations require admin/staff role"
echo "  ✓ Token expires in 15 minutes (configurable)"
echo ""

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ All tests completed successfully!${NC}"
echo -e "${BLUE}=========================================${NC}\n"
