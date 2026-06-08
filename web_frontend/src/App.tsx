import { useEffect } from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { useItemWebSocket } from "./services/itemWebSocket";
import { useIngredientWebSocket } from "./services/ingredientWebSocket";
import AppRoutes from "./AppRoutes";
import "./App.css";

function App() {
    const { hydrate, logout } = useAuthStore();

    // Initialize WebSocket for real-time item updates
    useItemWebSocket();
    // Initialize WebSocket for real-time ingredient updates
    useIngredientWebSocket();

    useEffect(() => {
        console.log("[App] useEffect - calling hydrate()");
        hydrate();
    }, [hydrate]);

    // Listen for token expiration events from API interceptor
    useEffect(() => {
        const handleTokenExpired = () => {
            console.log("[App] Token expired event received - logging out");
            logout();
        };

        window.addEventListener(
            "auth:token-expired",
            handleTokenExpired as EventListener,
        );

        return () => {
            window.removeEventListener(
                "auth:token-expired",
                handleTokenExpired as EventListener,
            );
        };
    }, [logout]);

    return (
        <Router>
            <AppRoutes />
        </Router>
    );
}

export default App;
