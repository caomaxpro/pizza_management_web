# 💻 Code Structure Reference

## Current Project Layout

```
web_frontend/
├── src/
│   ├── pages/
│   │   ├── ✅ Login.tsx (190 lines)
│   │   │   └── Login form with email/password validation
│   │   ├── ✅ Register.tsx (254 lines)
│   │   │   └── Registration form with phone field
│   │   ├── ✅ ChangePassword.tsx (229 lines)
│   │   │   └── Password change with old password verification
│   │   ├── ✅ Dashboard.tsx (211 lines)
│   │   │   └── User profile, quick actions, navigation cards
│   │   ├── 🟡 Items.tsx (19 lines)
│   │   │   └── Placeholder with loading message
│   │   ├── 🟡 Orders.tsx (19 lines)
│   │   │   └── Placeholder with loading message
│   │   ├── 🟡 Settings.tsx (19 lines)
│   │   │   └── Placeholder with loading message
│   │   ├── 🟡 Reports.tsx (19 lines)
│   │   │   └── Placeholder with loading message
│   │   └── ⚪ ItemDetail.tsx (0 lines)
│   │       └── Empty - need to implement
│   │
│   ├── components/
│   │   ├── ✅ ProtectedRoute.tsx (16 lines)
│   │   │   └── Route guard checking auth status
│   │   ├── layout/
│   │   │   ├── ⚪ Layout.tsx
│   │   │   ├── ⚪ Header.tsx
│   │   │   ├── ⚪ Sidebar.tsx
│   │   │   ├── ⚪ Avatar.tsx
│   │   │   └── ⚪ UserMenu.tsx
│   │   ├── ui/
│   │   │   ├── ⚪ Table.tsx
│   │   │   ├── ⚪ Modal.tsx
│   │   │   ├── ⚪ SearchBar.tsx
│   │   │   └── ⚪ Pagination.tsx
│   │   ├── items/
│   │   │   ├── ⚪ ItemCard.tsx
│   │   │   └── ⚪ ItemForm.tsx
│   │   └── dialogs/
│   │       └── ⚪ ConfirmDialog.tsx
│   │
│   ├── store/
│   │   ├── ✅ authStore.ts (149 lines)
│   │   │   ├── State: user, token, isLoading, error, isAuthenticated
│   │   │   ├── Actions: login, register, logout, changePassword, refreshToken
│   │   │   └── Persistence: localStorage
│   │   ├── ⚪ itemStore.ts
│   │   ├── ⚪ orderStore.ts
│   │   └── ⚪ uiStore.ts
│   │
│   ├── services/
│   │   ├── ✅ api.ts (141 lines)
│   │   │   ├── Axios instance
│   │   │   ├── Request interceptor (JWT header)
│   │   │   ├── Response interceptor (error handling)
│   │   │   └── Base URL: http://localhost:8000/api
│   │   ├── ✅ auth.ts (40 lines)
│   │   │   ├── POST /auth/login/
│   │   │   ├── POST /auth/register/
│   │   │   ├── POST /auth/logout/
│   │   │   ├── GET /auth/me/
│   │   │   ├── POST /auth/refresh/
│   │   │   └── POST /auth/change-password/
│   │   ├── ⚪ item.ts
│   │   │   ├── GET /items/ (list)
│   │   │   ├── GET /items/{id}/ (detail)
│   │   │   ├── POST /items/ (create)
│   │   │   ├── PUT /items/{id}/ (update)
│   │   │   └── DELETE /items/{id}/ (delete)
│   │   └── ⚪ upload.ts
│   │       ├── POST /upload/ (file upload)
│   │       └── (image handling)
│   │
│   ├── types/
│   │   ├── ✅ user.ts (36 lines)
│   │   │   ├── User interface
│   │   │   ├── LoginRequest interface
│   │   │   ├── RegisterRequest interface
│   │   │   ├── ChangePasswordRequest interface
│   │   │   └── AuthResponse interface
│   │   ├── 🟡 item.ts (34 lines)
│   │   │   ├── ItemType enum (11 values)
│   │   │   └── Item interface (partial)
│   │   ├── ⚪ order.ts
│   │   │   ├── Order interface
│   │   │   ├── OrderItem interface
│   │   │   └── OrderStatus enum
│   │   ├── ⚪ api.ts
│   │   │   ├── ApiError interface
│   │   │   ├── PaginationResponse interface
│   │   │   └── FilterParams interface
│   │   └── ⚪ index.ts
│   │       └── Export all types
│   │
│   ├── hooks/
│   │   ├── ⚪ useAuth.ts
│   │   │   └── Convenience hook for authStore
│   │   ├── ⚪ useFetch.ts
│   │   │   └── Generic data fetching hook
│   │   └── ⚪ useDebounce.ts
│   │       └── Debounce values for search
│   │
│   ├── utils/
│   │   ├── ⚪ validators.ts
│   │   │   ├── validateEmail()
│   │   │   ├── validatePassword()
│   │   │   ├── validatePhone()
│   │   │   └── etc.
│   │   └── ⚪ helpers.ts
│   │       ├── formatPrice()
│   │       ├── formatDate()
│   │       └── etc.
│   │
│   ├── assets/
│   │   ├── images/
│   │   └── svg/
│   │
│   ├── ✅ App.tsx (145 lines)
│   │   ├── BrowserRouter setup
│   │   ├── Public routes: /login, /register
│   │   ├── Protected routes: /dashboard, /items, /orders, etc.
│   │   └── Root redirect to /dashboard
│   │
│   ├── ✅ main.tsx (10 lines)
│   │   └── React app initialization
│   │
│   ├── index.css
│   └── App.css
│
├── 📦 package.json
├── 🔧 vite.config.ts
├── 🔧 tsconfig.json
├── 🔧 eslint.config.js
└── 📖 README.md
```

---

## Key Files Explained

### ✅ App.tsx (Router Configuration)
```typescript
// Key structure:
<BrowserRouter>
  <Routes>
    {/* Public routes */}
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    
    {/* Protected routes */}
    <Route element={<ProtectedRoute />}>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/items" element={<Items />} />
      <Route path="/orders" element={<Orders />} />
      <Route path="/change-password" element={<ChangePassword />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/reports" element={<Reports />} />
    </Route>
    
    {/* Home redirect */}
    <Route path="/" element={<Navigate to="/dashboard" />} />
  </Routes>
</BrowserRouter>
```

### ✅ authStore.ts (State Management Pattern)
```typescript
// Usage example:
const { login, logout, user, token, isLoading, error } = useAuthStore();

// Structure:
create((set) => ({
  // State
  user: null,
  token: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,
  
  // Actions
  login: async (email, password) => { /* ... */ },
  register: async (data) => { /* ... */ },
  logout: () => { /* ... */ },
  changePassword: async (data) => { /* ... */ },
  refreshToken: async () => { /* ... */ },
}))
```

### ✅ API Service Pattern (api.ts)
```typescript
// Axios instance with interceptors:
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
});

// Request interceptor adds JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor handles errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle logout
    }
    return Promise.reject(error);
  }
);
```

### ✅ Protected Route Pattern
```typescript
// Usage:
<Route element={<ProtectedRoute />}>
  <Route path="/dashboard" element={<Dashboard />} />
</Route>

// Implementation checks:
- Is user authenticated?
- Do they have valid token?
- If no → redirect to /login
- If yes → render component
```

---

## Type System Overview

### User Types (COMPLETE)
```typescript
interface User {
  id: number;
  email: string;
  username: string;
  phone_number: string;
  first_name: string;
  last_name: string;
  role: 'customer' | 'staff' | 'admin';
  created_at: string;
  updated_at: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  phone_number: string;
}

interface AuthResponse {
  user: User;
  token: string;
}
```

### Item Types (PARTIAL)
```typescript
enum ItemType {
  PIZZA = 'pizza',
  SIDE = 'side',
  DRINK = 'drink',
  DESSERT = 'dessert',
  // etc.
}

interface Item {
  id: number;
  name: string;
  description: string;
  price: number;
  image?: string;
  type: ItemType;
  // Missing: customization fields, categories, etc.
}
```

### Order Types (NOT YET)
```typescript
// Need to create:
enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PREPARING = 'preparing',
  READY = 'ready',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

interface OrderItem {
  id: number;
  item_id: number;
  quantity: number;
  customizations: Record<string, string>;
  price: number;
}

interface Order {
  id: number;
  user_id: number;
  items: OrderItem[];
  status: OrderStatus;
  total_price: number;
  delivery_address: string;
  created_at: string;
  // etc.
}
```

---

## Component Architecture

### Page Component (Current Pattern)
```typescript
export default function ItemsPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch items
    // Set loading/error states
  }, []);
  
  if (loading) return <CircularProgress />;
  
  return (
    <div>
      {/* Items grid/table */}
      {items.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
```

### Store Component (Zustand Pattern)
```typescript
interface ItemState {
  // State
  items: Item[];
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchItems: () => Promise<void>;
  addItem: (item: Item) => void;
  updateItem: (id: number, item: Item) => Promise<void>;
  deleteItem: (id: number) => Promise<void>;
}

export const useItemStore = create<ItemState>((set) => ({
  // ... implementation
}));
```

---

## API Endpoint Structure

### Implemented (Working)
```
POST   /auth/login/                    ✅
POST   /auth/register/                 ✅
POST   /auth/logout/                   ✅
GET    /auth/me/                       ✅
POST   /auth/refresh/                  ✅
POST   /auth/change-password/          ✅
```

### To Implement (Item Management)
```
GET    /items/                         ❌ (list)
GET    /items/{id}/                    ❌ (detail)
POST   /items/                         ❌ (create)
PUT    /items/{id}/                    ❌ (update)
DELETE /items/{id}/                    ❌ (delete)
GET    /items/?search=query            ❌ (search)
GET    /items/?category=type           ❌ (filter)
```

### To Implement (Order Management)
```
GET    /orders/                        ❌ (list)
GET    /orders/{id}/                   ❌ (detail)
POST   /orders/                        ❌ (create)
PUT    /orders/{id}/                   ❌ (update)
DELETE /orders/{id}/                   ❌ (cancel)
GET    /orders/?status=pending         ❌ (filter by status)
```

---

## Current Code Statistics

| Metric | Count |
|--------|-------|
| Total TypeScript Files | 41 |
| Implemented Files | 11 |
| Empty Files | 24 |
| Total Lines of Code | 1,376 |
| Auth System LOC | ~850 |
| Placeholder LOC | ~96 |
| Average LOC per file | ~34 |

### Top 10 Largest Files
1. Register.tsx - 254 lines
2. ChangePassword.tsx - 229 lines
3. Dashboard.tsx - 211 lines
4. Login.tsx - 190 lines
5. authStore.ts - 149 lines
6. App.tsx - 145 lines
7. api.ts - 141 lines
8. auth.ts - 40 lines
9. user.ts - 36 lines
10. item.ts - 34 lines

---

## Dependency Map Example

### Login Flow Dependencies
```
Login.tsx
├── imports: useAuthStore
├── imports: useNavigate (React Router)
├── imports: useFormik (form handling)
├── calls: authStore.login()
│   └── calls: authAPI.login()
│       └── calls: api.post() → axios
│           └── includes: Authorization header
└── navigates to: /dashboard
```

### Dashboard Flow Dependencies
```
Dashboard.tsx
├── uses: ProtectedRoute (render guard)
├── imports: useAuthStore
├── reads: authStore.user
├── displays: user profile info
└── links to: Items, Orders, Reports, Settings
```

---

## Configuration Files

### Environment Variables (Needed)
```bash
# .env.local
VITE_API_BASE=http://localhost:8000/api
VITE_APP_TITLE=Pizza Ordering App
```

### TypeScript Configuration
- tsconfig.json - Root config
- tsconfig.app.json - App-specific
- tsconfig.node.json - Build tool config

### ESLint Configuration
- eslint.config.js - Linting rules

### Build Configuration
- vite.config.ts - Vite build settings

---

## Testing Approach

### Current Testable Features
```
✅ Login with valid credentials
✅ Login with invalid credentials
✅ Register new account
✅ Logout
✅ Navigate to dashboard
✅ Access protected routes
✅ Redirect to login if no token
```

### To Test (When Implemented)
```
❌ List items from API
❌ Create item
❌ Edit item
❌ Delete item
❌ Search items
❌ Create order
❌ Update order status
❌ View reports
```

---

## Next Implementation Files

### Week 1 Priority
1. `src/components/layout/Layout.tsx` - Main layout wrapper
2. `src/components/layout/Header.tsx` - Top navigation
3. `src/components/layout/Sidebar.tsx` - Side menu
4. `src/components/ui/Table.tsx` - Data table
5. `src/services/item.ts` - Item API calls
6. `src/store/itemStore.ts` - Item state

### Week 2 Priority
1. `src/components/items/ItemCard.tsx` - Item display
2. `src/components/items/ItemForm.tsx` - Item form
3. `src/pages/Items.tsx` - Items page (replace placeholder)
4. `src/types/order.ts` - Order types
5. `src/store/orderStore.ts` - Order state
6. `src/pages/Orders.tsx` - Orders page

---

## Quick Reference Commands

### Development
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Type check
npx tsc --noEmit

# Lint check
npm run lint

# Format code
npx prettier --write .
```

### Testing Auth
```bash
# Test login
Email: testuser123
Password: TestPass123!

# Test registration
- Create new email
- Set password
- Verify phone
```

---

## Summary

**What Works Now:**
- ✅ Authentication (login, register, logout)
- ✅ Protected routes
- ✅ User dashboard
- ✅ API client setup
- ✅ State management pattern

**What's Missing:**
- 🔴 Layout system (5 files)
- 🔴 UI components (4 files)
- 🟡 Services for items/orders (2 files)
- 🟡 Stores for items/orders (2 files)
- 🟡 Full pages implementation (5 files)
- 🟡 Utilities & helpers (4 files)

**Total Work Remaining:** ~2,500 lines of code (2-3 weeks)

---

*Reference Document - Last Updated: April 18, 2026*
