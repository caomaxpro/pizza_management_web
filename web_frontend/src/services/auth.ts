import type { AxiosResponse } from "axios";
import API from "./api";
import type {
    User,
    RegisterRequest,
    ChangePasswordRequest,
    AuthResponse,
} from "../types/user";

export interface LoginPayload {
    email: string;
    password: string;
}

export interface RefreshResponse {
    access: string;
    refresh?: string;
}

export const authAPI = {
    login: (payload: LoginPayload): Promise<AxiosResponse<AuthResponse>> =>
        API.post("/auth/login/", payload),

    register: (
        payload: RegisterRequest,
    ): Promise<AxiosResponse<AuthResponse>> =>
        API.post("/auth/register/", payload),

    logout: (): Promise<AxiosResponse<void>> => API.post("/auth/logout/"),

    refresh: (): Promise<AxiosResponse<RefreshResponse>> => {
        const refreshToken = localStorage.getItem("refresh_token");
        return API.post("/auth/refresh/", { refresh: refreshToken });
    },

    getCurrentUser: (): Promise<AxiosResponse<User>> => API.get("/users/me/"),

    changePassword: (
        payload: ChangePasswordRequest,
    ): Promise<AxiosResponse<void>> =>
        API.post("/auth/change-password/", payload),

    /** List only admin/manager/staff users (not customers). */
    listAssignable: (): Promise<AxiosResponse<User[]>> =>
        API.get("/users/assignable/"),

    /** List all employees (admin, manager, staff) — excludes customers. */
    listEmployees: (): Promise<AxiosResponse<User[]>> =>
        API.get("/users/employees/"),
};
