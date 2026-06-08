import { Routes, Route, Navigate } from "react-router-dom";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/dashboard/Dashboard";
import Orders from "./pages/orders/Orders";
import OrderLog from "./pages/order_log/OrderLog";
import PaymentLog from "./pages/payment_log/PaymentLog";
import Inventory from "./pages/inventory/Inventory";
import InventoryDetails from "./pages/inventory/InventoryDetails";
import PurchaseOrders from "./pages/purchase_orders/PurchaseOrders";
import PurchaseOrderDetails from "./pages/purchase_orders/PurchaseOrderDetails";
import Providers from "./pages/providers/Providers";
import Settings from "./pages/settings/Settings";
import Users from "./pages/users/Users";
import Auth from "./pages/auth/Auth";
import IngredientList from "./pages/ingredients/IngredientList";
import IngredientCreate from "./pages/ingredients/IngredientCreate";
import IngredientImportReview from "./pages/ingredients/IngredientImportReview";
import IngredientDetail from "./pages/ingredients/IngredientDetail";
import IngredientEdit from "./pages/ingredients/IngredientEdit";
import IngredientBulkEdit from "./pages/ingredients/IngredientBulkEdit";
import ItemList from "./pages/items/ItemList";
import ItemDetail from "./pages/items/ItemDetail";
import ItemBulkEdit from "./pages/items/ItemBulkEdit";
import ItemImportReview from "./pages/items/ItemImportReview";

// Components
import ProtectedRoute from "./components/ProtectedRoute";
import Reports from "./pages/reports/Reports";

export default function AppRoutes() {
    return (
        <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected routes */}
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <Dashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/items"
                element={
                    <ProtectedRoute>
                        <ItemList />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/items/:id"
                element={
                    <ProtectedRoute>
                        <ItemDetail />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/items/bulk-edit"
                element={
                    <ProtectedRoute>
                        <ItemBulkEdit />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/items/import-review"
                element={
                    <ProtectedRoute>
                        <ItemImportReview />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/orders"
                element={
                    <ProtectedRoute>
                        <Orders />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/settings"
                element={
                    <ProtectedRoute>
                        <Settings />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients"
                element={
                    <ProtectedRoute>
                        <IngredientList />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients/create"
                element={
                    <ProtectedRoute>
                        <IngredientCreate />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients/import-review"
                element={
                    <ProtectedRoute>
                        <IngredientImportReview />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients/:id"
                element={
                    <ProtectedRoute>
                        <IngredientDetail />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients/:id/edit"
                element={
                    <ProtectedRoute>
                        <IngredientEdit />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/ingredients/bulk-edit"
                element={
                    <ProtectedRoute>
                        <IngredientBulkEdit />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports"
                element={
                    <ProtectedRoute>
                        <Reports />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/order_log"
                element={
                    <ProtectedRoute>
                        <OrderLog />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/payment_log"
                element={
                    <ProtectedRoute>
                        <PaymentLog />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/inventory"
                element={
                    <ProtectedRoute>
                        <Inventory />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/inventory/:id"
                element={
                    <ProtectedRoute>
                        <InventoryDetails />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/purchase_orders"
                element={
                    <ProtectedRoute>
                        <PurchaseOrders />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/purchase_orders/:id"
                element={
                    <ProtectedRoute>
                        <PurchaseOrderDetails />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/providers"
                element={
                    <ProtectedRoute>
                        <Providers />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/users"
                element={
                    <ProtectedRoute>
                        <Users />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/auth"
                element={
                    <ProtectedRoute>
                        <Auth />
                    </ProtectedRoute>
                }
            />

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}
