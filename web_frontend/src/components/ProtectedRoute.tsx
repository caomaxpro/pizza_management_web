import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import MainLayout from "./layout/MainLayout";

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, user, isHydrating } = useAuthStore();

    console.log(
        "[ProtectedRoute] isAuthenticated:",
        isAuthenticated,
        "isHydrating:",
        isHydrating,
        "user:",
        user,
    );

    // Show loading spinner while hydrating
    if (isHydrating) {
        console.log("[ProtectedRoute] HYDRATING - showing loading spinner");
        return (
            <div
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "100vh",
                    backgroundColor: "#f5f5f5",
                }}
            >
                <div style={{ textAlign: "center" }}>
                    <div
                        style={{
                            width: "40px",
                            height: "40px",
                            border: "4px solid #e0e0e0",
                            borderTop: "4px solid #1976d2",
                            borderRadius: "50%",
                            animation: "spin 1s linear infinite",
                            margin: "0 auto 16px",
                        }}
                    />
                    <p style={{ color: "#666", fontSize: "14px" }}>
                        Loading...
                    </p>
                    <style>{`
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    `}</style>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        console.log(
            "[ProtectedRoute] NOT AUTHENTICATED - redirecting to /login",
        );
        return <Navigate to="/login" replace />;
    }

    console.log("[ProtectedRoute] AUTHENTICATED - rendering MainLayout");
    return <MainLayout>{children}</MainLayout>;
}
