export interface User {
    id: string;
    email: string;
    username?: string;
    name?: string;
    phone_number?: string;
    role?: "admin" | "manager" | "staff" | "user";
    is_staff?: boolean;
    is_superuser?: boolean;
    is_active?: boolean;
    date_joined?: string;
    created_at?: string;
    updated_at?: string;
    can_stock_take?: boolean;
    can_receive_stock?: boolean;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
    phone_number?: string;
}

export interface ChangePasswordRequest {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
}

export interface AuthResponse {
    access: string;
    refresh: string;
    user?: User;
}

export type Weekday = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export interface ShiftTaskPerm {
    id: number;
    day: string; // mon / tue / ... / sun
    shift_start: string; // HH:MM
    can_stock_take: boolean;
    can_receive_stock: boolean;
}

export interface WorkSchedule {
    id: number;
    created_by: number | null;
    created_by_username: string | null;
    assigned_to: number;
    assigned_to_username: string;
    assigned_to_role: "admin" | "manager" | "staff";
    assigned_to_email: string | null;
    /** ISO date string for the Monday of the week, e.g. "2026-05-04" */
    week_start: string;
    /** Map of weekday abbreviation → shift(s). Value is a list of "HH:MM-HH:MM" strings.
     *  Legacy single-string format is also handled for backward compatibility. */
    entries: Partial<Record<Weekday, string | string[]>>;
    notes: string | null;
    active: boolean;
    created_at: string;
    updated_at: string;
    /** Shift-scoped task permissions for this schedule's entries. */
    shift_task_perms?: ShiftTaskPerm[];
}
