import axios, { type AxiosResponse, type AxiosError } from "axios";
import type { Item } from "../types/item";

const API = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api",
    timeout: 30000, // Increased from 10s to 30s for file uploads
    withCredentials: true, // Send cookies with every request
});

// Track if a refresh is already in progress to avoid multiple refresh attempts
let isRefreshing = false;
let failedQueue: {
    resolve: (value?: unknown) => void;
    reject: (reason?: unknown) => void;
}[] = [];

const processQueue = (error: unknown, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    isRefreshing = false;
    failedQueue = [];
};

// Debug: Log cookies before each request
API.interceptors.request.use((config) => {
    console.log("[API Request]", config.method?.toUpperCase(), config.url);

    // Get token from localStorage and add to Authorization header
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log("[API] Authorization header set from localStorage");
    } else {
        console.log("[API] No token in localStorage");
    }

    console.log("[Cookies]", document.cookie || "(no cookies)");
    return config;
});

// response interceptor: global error handling + automatic token refresh
API.interceptors.response.use(
    (res) => {
        console.log("[API Response]", res.status, res.config.url);
        console.log("[Response Data]", res.data);

        // Check if backend auto-refreshed access token during auth
        const newAccessToken = res.headers["x-new-access-token"];
        if (newAccessToken) {
            console.log(
                "[Auth Interceptor] Backend auto-refreshed access token",
            );
            localStorage.setItem("access_token", newAccessToken);
            console.log(
                "[Auth Interceptor] ✓ New access token saved to localStorage",
            );
        }

        return res;
    },
    (err: AxiosError) => {
        const status = err.response?.status;
        const message =
            (err.response?.data as Record<string, unknown>)?.message ||
            err.message;
        const url = err.config?.url;

        console.error("[API Error]", status, url);
        console.error("[Error Response]", err.response?.data);

        // Handle 401 Unauthorized - try to refresh token
        if (status === 401 && url !== "/auth/refresh/") {
            console.log(
                "[Auth Interceptor] 401 Unauthorized - attempting token refresh",
            );

            if (!isRefreshing) {
                isRefreshing = true;
                const refreshToken = localStorage.getItem("refresh_token");

                if (refreshToken) {
                    console.log(
                        "[Auth Interceptor] Refresh token found - calling refresh endpoint",
                    );

                    // Make refresh request without regular interceptors to avoid loops
                    // Send refresh token in request body (simplejwt format)
                    return axios
                        .post(
                            `${import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api"}/auth/refresh/`,
                            { refresh: refreshToken },
                            {
                                withCredentials: true,
                            },
                        )
                        .then((response) => {
                            const { access, refresh } = response.data;

                            // Update tokens
                            if (access) {
                                localStorage.setItem("access_token", access);
                                console.log(
                                    "[Auth Interceptor] \u2713 Access token updated",
                                );
                            }
                            if (refresh) {
                                localStorage.setItem("refresh_token", refresh);
                                console.log(
                                    "[Auth Interceptor] \u2713 Refresh token updated",
                                );
                            }

                            // Update the failed request with new token
                            if (err.config && access) {
                                err.config.headers.Authorization = `Bearer ${access}`;
                            }

                            processQueue(null, access);

                            // Retry original request
                            return API(err.config!);
                        })
                        .catch((refreshError) => {
                            console.error(
                                "[Auth Interceptor] Refresh token failed:",
                                refreshError,
                            );

                            // Refresh failed - clear tokens and redirect to login
                            localStorage.removeItem("access_token");
                            localStorage.removeItem("refresh_token");

                            // Dispatch logout event for auth store to catch
                            window.dispatchEvent(
                                new CustomEvent("auth:token-expired", {
                                    detail: "Session expired",
                                }),
                            );

                            processQueue(refreshError, null);
                            return Promise.reject(refreshError);
                        });
                } else {
                    // No refresh token - clear auth
                    console.log(
                        "[Auth Interceptor] No refresh token - clearing auth",
                    );
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");

                    window.dispatchEvent(
                        new CustomEvent("auth:token-expired", {
                            detail: "Session expired",
                        }),
                    );

                    processQueue(err, null);
                    return Promise.reject(err);
                }
            } else {
                // Refresh already in progress - queue this request
                console.log(
                    "[Auth Interceptor] Refresh in progress - queueing request",
                );
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        if (err.config && token) {
                            err.config.headers.Authorization = `Bearer ${token}`;
                        }
                        return API(err.config!);
                    })
                    .catch((error) => {
                        return Promise.reject(error);
                    });
            }
        }

        switch (status) {
            case 400:
                console.error("Bad Request:", message);
                break;

            case 403:
                console.error("Forbidden - access denied");
                // Optional: show "Access Denied" toast
                break;

            case 404:
                console.error("Not Found:", message);
                // Optional: show "Resource not found" toast
                break;

            case 409:
                console.error("Conflict:", message);
                // Optional: handle duplicate/conflict
                break;

            case 422:
                console.error("Validation Error:", message);
                // Optional: show validation errors to user
                break;

            case 429:
                console.error("Too Many Requests - rate limited");
                // Optional: show "Please try again later"
                break;

            case 500:
                console.error("Internal Server Error");
                // Optional: show "Something went wrong" toast
                break;

            case 502:
            case 503:
            case 504:
                console.error("Service Unavailable");
                // Optional: show "Server maintenance" toast
                break;

            default:
                console.error("Network Error:", message);
        }

        return Promise.reject(err);
    },
);

export default API;

// simple API helpers
export type FilterParams = Record<
    string,
    string | number | boolean | Array<string | number>
>;

export const itemAPI = {
    // Caller can override the generic if needed: itemAPI.getAll<MyItem[]>()
    getAll: <T = Item[]>(): Promise<AxiosResponse<T>> => API.get<T>("/items"),

    // Get single item by id
    get: <T = Item>(id: string): Promise<AxiosResponse<T>> =>
        API.get<T>(`/items/${id}`),

    // Get many with query/filter params (pagination, filters, sort)
    getMany: <T = Item[]>(params?: FilterParams): Promise<AxiosResponse<T>> =>
        API.get<T>("/items", { params }),

    // Create one
    create: <T = Item>(data: T): Promise<AxiosResponse<T>> =>
        API.post<T>("/items", data),

    // Create many (bulk import) - endpoint should exist on backend (/items/bulk)
    createMany: <T = Item[]>(data: T[]): Promise<AxiosResponse<T[]>> =>
        API.post<T[]>("/items/bulk", data),

    // Update one (partial)
    update: <T = Partial<Item>>(
        id: string,
        data: T,
    ): Promise<AxiosResponse<T>> => API.put<T>(`/items/${id}`, data),

    // Update many by ids payload: [{ id, ...patch }]
    updateMany: <T = Partial<Item>>(
        payload: { id: string; data: T }[],
    ): Promise<AxiosResponse<void>> => API.put("/items/bulk", payload),

    // Update all matching filter with same patch (useful for discounts) - backend: PATCH /items
    updateAll: <T = Partial<Item>>(
        data: T,
        params?: FilterParams,
    ): Promise<AxiosResponse<void>> => API.patch("/items", data, { params }),

    // Remove one
    remove: (id: string): Promise<AxiosResponse<void>> =>
        API.delete<void>(`/items/${id}`),

    // Remove many by ids array
    removeMany: (ids: string[]): Promise<AxiosResponse<void>> =>
        API.delete("/items", { data: { ids } }),

    // Remove all matching filter (use with caution)
    removeAll: (params?: FilterParams): Promise<AxiosResponse<void>> =>
        API.delete("/items/all", { params }),

    // Export items (CSV/Excel) - returns blob
    export: (params?: FilterParams): Promise<AxiosResponse<Blob>> =>
        API.get("/items/export", { params, responseType: "blob" }),
};
