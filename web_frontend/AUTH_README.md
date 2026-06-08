# Web Frontend Auth Implementation Guide

## Overview
This web frontend implements a complete authentication system with:
- ✅ User Login
- ✅ User Registration
- ✅ Password Change
- ✅ JWT Token Management
- ✅ Protected Routes
- ✅ State Management with Zustand

## Architecture

### Components
```
src/
├── pages/
│   ├── Login.tsx              # Login page
│   ├── Register.tsx           # Registration page
│   ├── ChangePassword.tsx     # Password change page
│   ├── Dashboard.tsx          # Main dashboard
│   ├── Items.tsx              # Menu items (placeholder)
│   ├── Orders.tsx             # Orders (placeholder)
│   ├── Settings.tsx           # Settings (placeholder)
│   └── Reports.tsx            # Reports (placeholder)
├── components/
│   └── ProtectedRoute.tsx     # Route protection wrapper
├── store/
│   └── authStore.ts           # Zustand auth store
├── services/
│   ├── auth.ts                # Auth API endpoints
│   └── api.ts                 # Axios API client
├── types/
│   └── user.ts                # TypeScript interfaces
└── App.tsx                    # Router configuration
```

### Store State Management (Zustand)
- `user`: Current user object
- `token`: JWT access token
- `isLoading`: Loading state for API calls
- `error`: Error messages
- `isAuthenticated`: Boolean flag

### API Endpoints
Backend: `http://localhost:8000/api`

**Auth Endpoints:**
- `POST /auth/login/` - User login
- `POST /auth/register/` - User registration
- `POST /auth/logout/` - User logout
- `POST /auth/refresh/` - Refresh JWT token
- `GET /auth/me/` - Get current user
- `POST /auth/change-password/` - Change password

## Usage

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```

### Running Tests (Login Flow)
```bash
# Test data:
Email: testuser123
Password: TestPass123!

# Or register a new account
```

### Protected Routes
All routes except `/login` and `/register` are protected:
```typescript
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

### Using Auth Store
```typescript
import { useAuthStore } from "@/store/authStore";

function Component() {
  const { user, token, login, logout, isLoading } = useAuthStore();
  
  // Use state and actions
}
```

## Features

### Login Page
- Email and password validation
- Error messages and feedback
- Loading state during API call
- Link to registration page
- Stores JWT token in localStorage

### Registration Page
- Full form validation
- Password confirmation
- Optional phone number
- Email duplicate prevention (server-side)
- Automatic login after registration

### Change Password Page
- Current password verification
- New password confirmation
- Password strength validation
- Success/error feedback
- Redirect after successful change

### Dashboard
- User profile information
- Quick action buttons
- Navigation cards to main sections
- Staff-only report section
- Logout functionality

## Security Features

✅ JWT Token Storage (localStorage)
✅ Authorization Header for API calls
✅ Automatic token refresh on 401
✅ Route protection with ProtectedRoute
✅ Form validation (client & server)
✅ Error handling and user feedback
✅ Automatic logout on token expiry

## Error Handling

The app handles various error scenarios:
- Invalid credentials
- Network errors
- Server errors (4xx, 5xx)
- Validation errors
- Token expiration

## Environment Variables

Create a `.env.local` file:
```
VITE_API_BASE=http://localhost:8000/api
```

## Next Steps

1. **Implement protected route guards** for admin-only pages
2. **Add role-based access control (RBAC)**
3. **Implement password recovery flow**
4. **Add email verification** for registration
5. **Add two-factor authentication (2FA)**
6. **Implement refresh token rotation**

## Testing Checklist

- [ ] Login with correct credentials
- [ ] Login with incorrect credentials
- [ ] Register new account
- [ ] View dashboard after login
- [ ] Change password successfully
- [ ] Logout and verify redirect to login
- [ ] Access protected route without token (redirects to login)
- [ ] Token persists after page refresh
- [ ] Handle network errors gracefully

## API Response Format

**Login Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "1",
    "email": "user@example.com",
    "name": "John Doe",
    "phone_number": "+1234567890"
  }
}
```

## TypeScript Support

All types are defined in `src/types/user.ts`:
- `User`: User entity
- `LoginRequest`: Login payload
- `RegisterRequest`: Registration payload
- `ChangePasswordRequest`: Password change payload
- `AuthResponse`: Auth API response

## Styling

Uses Material-UI (MUI) for consistent styling:
- `Card` components for form containers
- `TextField` for inputs
- `Button` for actions
- `Alert` for messages
- `Container` for layout

Responsive design with `xs`, `md`, `lg` breakpoints.

---

**Last Updated:** April 18, 2026
