# 🗺️ Implementation Roadmap - Web Frontend

## Phase 1: Layout & Navigation System (2-3 days)
**Goal:** Establish consistent layout across all pages

### Components to Build
```
Priority 1 - CRITICAL (Day 1)
├── src/components/layout/Layout.tsx
│   ├── Left sidebar navigation
│   ├── Top header bar
│   ├── Main content area
│   └── Mobile responsive
├── src/components/layout/Header.tsx
│   ├── Logo/branding
│   ├── User profile button
│   └── Logout action
└── src/components/layout/Sidebar.tsx
    ├── Navigation menu
    ├── Active route indicator
    ├── Icons for each page
    └── Collapse on mobile

Priority 2 - HIGH (Day 2)
├── src/components/layout/UserMenu.tsx
│   ├── Profile dropdown
│   ├── Settings link
│   ├── Change password link
│   └── Logout button
└── src/components/layout/Avatar.tsx
    ├── User photo/initial
    ├── Status indicator
    └── Tooltip
```

### Layout Structure
```
┌─────────────────────────────────┐
│        Header (Header.tsx)       │ <- Logo, User Menu
├─────────┬───────────────────────┤
│         │                       │
│ Sidebar │   Main Content        │ <- Layout.tsx wraps everything
│ (Sidebar│   from Pages          │
│  .tsx)  │                       │
│         │                       │
└─────────┴───────────────────────┘
```

---

## Phase 2: Base UI Component Library (2-3 days)
**Goal:** Build reusable UI components for consistency

### Components to Build
```
src/components/ui/
├── Table.tsx (HIGH PRIORITY)
│   ├── Column definitions
│   ├── Sorting & pagination
│   ├── Row selection
│   ├── Loading state
│   └── Empty state
│
├── Modal.tsx (HIGH PRIORITY)
│   ├── Header, body, footer
│   ├── Close button
│   ├── Size variants (sm, md, lg)
│   └── Scroll handling
│
├── SearchBar.tsx (MEDIUM)
│   ├── Debounced input
│   ├── Search icon
│   ├── Clear button
│   └── Placeholder text
│
└── Pagination.tsx (MEDIUM)
    ├── Page numbers
    ├── Previous/Next buttons
    ├── Go to page input
    └── Items per page select
```

### Dialog/Modal Components
```
src/components/dialogs/
└── ConfirmDialog.tsx
    ├── Title & description
    ├── Action buttons (Confirm/Cancel)
    ├── Icon indicator
    └── Danger/Warning variants
```

---

## Phase 3: Item Management System (2-3 days)
**Goal:** Full CRUD for menu items

### Files to Create
```
src/services/item.ts - API calls
├── getItems()
├── getItem(id)
├── createItem()
├── updateItem()
├── deleteItem()
├── uploadItemImage()
└── getItemsByCategory()

src/store/itemStore.ts - State management
├── items: Item[]
├── loading: boolean
├── error: string | null
├── selectedItem: Item | null
├── actions: {
│   ├── fetchItems()
│   ├── fetchItem(id)
│   ├── createItem()
│   ├── updateItem()
│   ├── deleteItem()
│   └── selectItem()
│ }

src/components/items/
├── ItemCard.tsx
│   ├── Item image
│   ├── Name & price
│   ├── Description
│   ├── Action buttons (Edit/Delete)
│   └── On click handler
│
└── ItemForm.tsx
    ├── Text fields (name, price, etc)
    ├── Image upload
    ├── Category select
    ├── Description textarea
    ├── Toggle buttons for type
    ├── Submit/Cancel buttons
    └── Validation messages

src/pages/Items.tsx - List view
├── Items grid/table
├── Search & filter
├── Create button
├── Edit/Delete actions
├── Pagination
└── Loading/error states

src/pages/ItemDetail.tsx - Detail view
├── Item image gallery
├── Item info section
├── Edit button
├── Delete confirmation
├── Back button
└── Related items
```

### Types to Complete
```
src/types/item.ts
├── Item interface (complete existing)
├── CreateItemRequest
├── UpdateItemRequest
├── ItemFilter
└── ItemResponse
```

---

## Phase 4: Order Management System (2-3 days)
**Goal:** Full order tracking and management

### Files to Create
```
src/types/order.ts
├── Order interface
├── OrderItem interface
├── OrderStatus enum
├── CreateOrderRequest
├── UpdateOrderRequest

src/services/item.ts (extend)
├── getOrders()
├── getOrder(id)
├── createOrder()
├── updateOrder()
├── cancelOrder()
├── getOrdersByStatus()

src/store/orderStore.ts - State management
├── orders: Order[]
├── selectedOrder: Order | null
├── filter: OrderFilter
├── actions: {...}

src/components/orders/
├── OrderCard.tsx
├── OrderForm.tsx
├── OrderStatus.tsx

src/pages/Orders.tsx
├── Orders list/table
├── Filters by status
├── Search by order number
├── Order details modal
└── Action buttons
```

---

## Phase 5: Advanced Features (Ongoing)
**Goal:** Polish and complete remaining features

### Features to Implement
```
1. Reports & Analytics
   ├── Sales dashboard
   ├── Revenue charts
   ├── Top items
   ├── Customer stats
   └── Date range filters

2. Settings & Profile
   ├── User profile edit
   ├── Email preferences
   ├── Notification settings
   └── Account security

3. File Upload Service
   src/services/upload.ts
   ├── Image upload to backend
   ├── Progress tracking
   ├── Error handling
   └── File size validation

4. Utility Functions
   src/utils/validators.ts
   ├── Email validator
   ├── Phone validator
   ├── Price formatter
   ├── Date formatter
   └── URL validators
   
   src/utils/helpers.ts
   ├── formatPrice()
   ├── formatDate()
   ├── groupBy()
   ├── debounce()
   └── throttle()

5. Custom Hooks
   src/hooks/useAuth.ts
   ├── Current user state
   
   src/hooks/useFetch.ts
   ├── Generic data fetching
   ├── Loading, error, data states
   ├── Refetch function
   
   src/hooks/useDebounce.ts
   ├── Debounced value
   ├── Clear function
```

---

## Development Order (Recommended)

### Week 1
```
Day 1-2: Phase 1 (Layout)
├── Layout.tsx
├── Header.tsx
├── Sidebar.tsx
└── Integrate with existing pages

Day 3-4: Phase 2 (UI Components)
├── Table.tsx
├── Modal.tsx
├── SearchBar.tsx
└── Pagination.tsx

Day 5: Phase 3 Start (Item Service)
├── item.ts service
├── itemStore.ts
└── Types
```

### Week 2
```
Day 1-2: Phase 3 Continue (Item Components)
├── ItemCard.tsx
├── ItemForm.tsx
├── Items page implementation
└── ItemDetail page

Day 3-4: Phase 4 (Order System)
├── Order types
├── Order service
├── Order store
└── Orders page

Day 5: Polish & Testing
├── Bug fixes
├── UI refinements
└── Integration testing
```

---

## Git Commit Strategy

```bash
# Phase 1
git commit -m "feat: add layout system (Header, Sidebar, Layout)"

# Phase 2
git commit -m "feat: add base UI components (Table, Modal, SearchBar)"

# Phase 3
git commit -m "feat: add item management (service, store, components)"

# Phase 4
git commit -m "feat: add order management (service, store, pages)"

# Phase 5
git commit -m "feat: add advanced features (reports, settings, utils)"
```

---

## Testing Checklist (After Each Phase)

### Phase 1: Layout
- [ ] Responsive on mobile/tablet/desktop
- [ ] Navigation works on all pages
- [ ] User menu functional
- [ ] Logout works
- [ ] Active route highlighted

### Phase 2: UI Components
- [ ] Table renders data correctly
- [ ] Pagination works
- [ ] Modal opens/closes
- [ ] SearchBar filters correctly
- [ ] No console errors

### Phase 3: Items
- [ ] Fetch items from backend
- [ ] Display items in grid/table
- [ ] Create item form submits
- [ ] Edit item updates backend
- [ ] Delete shows confirmation
- [ ] Search filters items
- [ ] Image upload works

### Phase 4: Orders
- [ ] Fetch orders from backend
- [ ] Filter by status
- [ ] Create order
- [ ] Update order status
- [ ] Cancel order
- [ ] Order details display

### Phase 5: Polish
- [ ] No broken links
- [ ] All pages render
- [ ] Forms validate
- [ ] Error messages display
- [ ] Loading states show
- [ ] Mobile responsive

---

## Environmental Setup

### Environment Variables
```bash
# .env.local
VITE_API_BASE=http://localhost:8000/api
VITE_APP_TITLE=Pizza Ordering App
```

### Backend Requirements
```bash
# Make sure backend is running
cd backend/backend_dj
python manage.py runserver 8000
```

---

## Common Issues & Solutions

### Issue: Pages not showing with Layout
**Solution:** Wrap all pages with Layout component in App.tsx routes

### Issue: State not persisting
**Solution:** Zustand stores auto-persist; check localStorage

### Issue: API 401 errors
**Solution:** Check token in localStorage, ensure it's not expired

### Issue: Images not loading
**Solution:** Verify image URLs match backend paths, check CORS

---

## Performance Optimization Tips

1. **Lazy load routes** - Use React.lazy() for pages
2. **Virtualize large tables** - Use react-window for Item/Order lists
3. **Debounce search** - useDebounce hook for search inputs
4. **Image optimization** - Compress images, use WebP format
5. **Memoize components** - React.memo for list items
6. **Code splitting** - Automatic with Vite

---

## Dependencies Potentially Needed

```json
{
  "react-query": "^3.x",           // Server state management (optional)
  "react-hook-form": "^7.x",        // Better form handling (optional)
  "zod": "^3.x",                    // Schema validation (optional)
  "date-fns": "^2.x",               // Date utilities (optional)
  "react-window": "^1.x",           // Virtual scrolling (optional)
  "lucide-react": "^0.x"            // Icon library (alternative to Material Icons)
}
```

---

## Success Metrics

After full implementation:
- ✅ 100% auth features working
- ✅ Item CRUD fully functional  
- ✅ Order management complete
- ✅ Mobile responsive design
- ✅ Consistent UI across app
- ✅ All pages accessible
- ✅ No console errors
- ✅ TypeScript strict mode passing
- ✅ ESLint clean

---

**Next Step:** Start with Phase 1 - Layout System

*Document Version: 1.0 | Last Updated: April 18, 2026*
