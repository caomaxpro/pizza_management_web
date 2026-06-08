/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from "zustand";
import { authAPI, type LoginPayload } from "../services/auth";
import type {
    User,
    RegisterRequest,
    ChangePasswordRequest,
} from "../types/user";
import type { AxiosError } from "axios";
import { isTokenExpired } from "../utils/jwt";
import { clearAllCache } from "../utils/clearAllCache";

interface ApiErrorResponse {
    detail?: string;
    email?: string[];
    message?: string;
    [key: string]: unknown;
}

function getErrorMessage(error: unknown, defaultMessage: string): string {
    if (error instanceof Error) {
        return error.message;
    }
    if (typeof error === "object" && error !== null) {
        const axiosError = error as AxiosError<ApiErrorResponse>;
        const data = axiosError.response?.data;
        if (data?.detail) return data.detail;
        if (data?.email && Array.isArray(data.email)) return data.email[0];
        if (data?.email && typeof data.email === "string") return data.email;
    }
    return defaultMessage;
}

interface AuthState {
    user: User | null;
    isLoading: boolean;
    error: string | null;
    isAuthenticated: boolean;
    isHydrating: boolean;
    isRefreshing: boolean; // Track if refresh is in progress

    // Actions
    login: (payload: LoginPayload) => Promise<void>;
    register: (payload: RegisterRequest) => Promise<void>;
    logout: () => void;
    refreshToken: () => Promise<void>; // Manual refresh action
    changePassword: (payload: ChangePasswordRequest) => Promise<void>;
    getCurrentUser: () => Promise<void>;
    clearError: () => void;
    hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    isHydrating: true,
    isRefreshing: false,

    login: async (payload: LoginPayload) => {
        set({ isLoading: true, error: null });
        console.log("[Auth] LOGIN START - email:", payload.email);
        try {
            const response = await authAPI.login(payload);
            const { user, access, refresh } = response.data;
            console.log("[Auth] LOGIN SUCCESS - user:", user);

            // Store both access and refresh tokens
            if (access) {
                localStorage.setItem("access_token", access);
                console.log("[Auth] ✓ Access token saved to localStorage");
            } else {
                console.error("[Auth] ✗ No access token in response!");
            }

            if (refresh) {
                localStorage.setItem("refresh_token", refresh);
                console.log("[Auth] ✓ Refresh token saved to localStorage");
            } else {
                console.error("[Auth] ✗ No refresh token in response!");
            }

            set({
                user: user || null,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: unknown) {
            const message = getErrorMessage(error, "Login failed");
            set({
                error: message,
                isLoading: false,
            });
            throw error;
        }
    },

    register: async (payload: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
            const response = await authAPI.register(payload);
            const { user, access, refresh } = response.data;

            // Store both access and refresh tokens
            if (access) {
                localStorage.setItem("access_token", access);
            }
            if (refresh) {
                localStorage.setItem("refresh_token", refresh);
            }

            set({
                user: user || null,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: unknown) {
            const message = getErrorMessage(error, "Registration failed");
            set({
                error: message,
                isLoading: false,
            });
            throw error;
        }
    },

    logout: async () => {
        console.log("[Auth] LOGOUT START");
        try {
            // Only call logout API if we have tokens to send
            const hasTokens =
                localStorage.getItem("access_token") ||
                localStorage.getItem("refresh_token");
            if (hasTokens) {
                await authAPI.logout();
                console.log("[Auth] LOGOUT API SUCCESS");
            } else {
                console.log("[Auth] No tokens - skipping logout API call");
            }
        } catch (error) {
            console.error("[Auth] Logout api call failed:", error);
            // Not critical - continue clearing state
        } finally {
            // Clear all cache, storage, cookies, and Zustand stores
            clearAllCache();

            // Clear auth state
            set({
                user: null,
                isAuthenticated: false,
                error: null,
                isRefreshing: false,
            });
            console.log("[Auth] LOGOUT COMPLETE - all state cleared");
        }
    },

    refreshToken: async () => {
        // Prevent multiple simultaneous refresh requests
        const state = get();
        if (state.isRefreshing) {
            console.log("[Auth] Refresh already in progress, skipping");
            return;
        }

        set({ isRefreshing: true });
        console.log("[Auth] REFRESH TOKEN START");
        try {
            const response = await authAPI.refresh();
            const { access, refresh } = response.data;

            // Update both tokens
            if (access) {
                localStorage.setItem("access_token", access);
                console.log("[Auth] ✓ Access token refreshed");
            }
            if (refresh) {
                localStorage.setItem("refresh_token", refresh);
                console.log("[Auth] ✓ Refresh token refreshed");
            }

            set({ isRefreshing: false });
            console.log("[Auth] REFRESH TOKEN SUCCESS");
        } catch (error: unknown) {
            console.error("[Auth] REFRESH TOKEN FAILED - forcing logout");
            // Refresh failed - clear all cache and state
            clearAllCache();
            set({
                user: null,
                isAuthenticated: false,
                isRefreshing: false,
                error: "Session expired. Please login again.",
            });
            throw error;
        }
    },

    changePassword: async (payload: ChangePasswordRequest) => {
        set({ isLoading: true, error: null });
        try {
            await authAPI.changePassword(payload);
            set({ isLoading: false });
        } catch (error: unknown) {
            const message = getErrorMessage(error, "Password change failed");
            set({
                error: message,
                isLoading: false,
            });
            throw error;
        }
    },

    getCurrentUser: async () => {
        console.log("[Auth] GET_CURRENT_USER START");
        console.log(
            "[Auth] Cookies before request:",
            document.cookie || "(no cookies)",
        );
        try {
            const response = await authAPI.getCurrentUser();
            console.log(
                "[Auth] GET_CURRENT_USER SUCCESS - user:",
                response.data,
            );
            set({ user: response.data, isAuthenticated: true });
        } catch (error: unknown) {
            const axiosError = error as any;
            console.error(
                "[Auth] GET_CURRENT_USER FAILED - status:",
                axiosError.response?.status,
            );
            console.error("[Auth] Error data:", axiosError.response?.data);
            if (axiosError.response?.status === 401) {
                // Session expired or token invalid
                console.log("[Auth] 401 - clearing auth state");
                set({ isAuthenticated: false, user: null });
            } else {
                console.error(
                    "[Auth] Failed to fetch current user - other error",
                );
            }
        }
    },

    clearError: () => set({ error: null }),

    // Hydrate from localStorage on app start
    hydrate: () => {
        console.log("\n\n=== [Auth] HYDRATE STARTED ===");

        // Check if we have tokens in localStorage
        const accessToken = localStorage.getItem("access_token");
        const refreshToken = localStorage.getItem("refresh_token");
        console.log(
            "[Auth] Access token in localStorage:",
            accessToken ? "YES" : "NO",
        );
        console.log(
            "[Auth] Refresh token in localStorage:",
            refreshToken ? "YES" : "NO",
        );

        // If refresh token is expired, clear both tokens
        if (refreshToken && isTokenExpired(refreshToken)) {
            console.warn("[Auth] Refresh token expired - clearing auth");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            set({ isAuthenticated: false, isHydrating: false });
            console.log("[Auth] HYDRATE COMPLETE - Refresh token expired");
            return;
        }

        if (accessToken) {
            // Optimistic: if token exists, mark as authenticated immediately
            console.log(
                "[Auth] Token found → Optimistic authentication (trust localStorage)",
            );
            set({ isAuthenticated: true, isHydrating: false });
            console.log(
                "[Auth] HYDRATE COMPLETE - Marked as authenticated (optimistic)",
            );

            // Validate silently in background
            const state = get();
            state
                .getCurrentUser()
                .then(() => {
                    console.log(
                        "[Auth] Background validation: Token is valid ✓",
                    );
                })
                .catch(() => {
                    console.warn(
                        "[Auth] Background validation: Token expired or invalid ✗",
                    );
                    set({ isAuthenticated: false, user: null });
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                });
        } else {
            // No token - not authenticated
            console.log("[Auth] No token found → Not authenticated");
            set({ isAuthenticated: false, isHydrating: false });
            console.log("[Auth] HYDRATE COMPLETE - Not authenticated");
        }
    },
}));
