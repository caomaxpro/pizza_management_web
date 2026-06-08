import type { AxiosResponse } from "axios";
import API from "./api";
import type { User } from "../types/user";

export interface ListUsersParams {
    search?: string;
    role?: string;
    status?: string;
    ordering?: string;
    page?: number;
    page_size?: number;
}

export interface PaginatedUsers {
    count: number;
    next: string | null;
    previous: string | null;
    results: User[];
}

export interface CreateUserPayload {
    email: string;
    username: string;
    password: string;
    role: "admin" | "manager" | "staff" | "user";
    is_active?: boolean;
}

export interface UpdateUserPayload {
    email?: string;
    role?: "admin" | "manager" | "staff" | "user";
    is_active?: boolean;
}

export const usersAPI = {
    /** GET /users/ — list with server-side filtering, sorting, pagination */
    list: (params?: ListUsersParams): Promise<AxiosResponse<PaginatedUsers>> =>
        API.get("/users/", { params }),

    /** GET /users/:id/ */
    retrieve: (id: string | number): Promise<AxiosResponse<User>> =>
        API.get(`/users/${id}/`),

    /** POST /users/ — admin creates a new user */
    create: (payload: CreateUserPayload): Promise<AxiosResponse<User>> =>
        API.post("/users/", payload),

    /** PATCH /users/:id/ */
    update: (
        id: string | number,
        payload: UpdateUserPayload,
    ): Promise<AxiosResponse<User>> => API.patch(`/users/${id}/`, payload),

    /** DELETE /users/:id/ */
    delete: (id: string | number): Promise<AxiosResponse<void>> =>
        API.delete(`/users/${id}/`),

    /** PATCH /users/:id/assign-task/ — admin/manager only, target must be staff */
    assignTask: (
        id: string | number,
        payload: { can_stock_take?: boolean; can_receive_stock?: boolean },
    ): Promise<AxiosResponse<User>> =>
        API.patch(`/users/${id}/assign-task/`, payload),

    /** PATCH /users/:id/assign-role/ — admin/manager only */
    assignRole: (
        id: string | number,
        role: string,
    ): Promise<AxiosResponse<User>> =>
        API.patch(`/users/${id}/assign-role/`, { role }),
};
