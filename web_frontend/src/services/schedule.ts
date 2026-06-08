import type { AxiosResponse } from "axios";
import API from "./api";
import type { WorkSchedule, ShiftTaskPerm } from "../types/user";

export interface CreateSchedulePayload {
    assigned_to: number;
    week_start: string; // YYYY-MM-DD (must be a Monday)
    entries: Partial<Record<string, string>>;
    notes?: string;
    active?: boolean;
}

export interface UpdateSchedulePayload {
    week_start?: string;
    entries?: Partial<Record<string, string>>;
    notes?: string;
    active?: boolean;
}

/** Body for POST /api/schedules/assign_slot/ */
export interface AssignSlotPayload {
    assigned_to: number | number[]; // single or batch assignment
    week_start: string; // YYYY-MM-DD Monday
    day: string; // mon | tue | wed | thu | fri | sat | sun
    start: string; // HH:MM
    end: string; // HH:MM
    notes?: string;
    active?: boolean;
}

export interface AssignSlotResponse {
    schedules: WorkSchedule[];
    errors?: Record<string, string>; // userId → error message (partial failure)
    partial?: boolean;
}

/** Body for POST /api/schedules/remove_slot/ */
export interface RemoveSlotPayload {
    assigned_to: number;
    week_start: string;
    day: string;
    /** Shift start time (HH:MM) identifying which entry to remove. */
    start: string;
}

/** Body for POST /api/schedules/assign_shift_task/ */
export interface AssignShiftTaskPayload {
    user_id: number;
    week_start: string; // YYYY-MM-DD
    day: string; // mon | tue | ... | sun
    shift_start: string; // HH:MM — identifies which shift entry
    can_stock_take?: boolean;
    can_receive_stock?: boolean;
}

export const scheduleAPI = {
    /** List all schedules visible to the caller.
     *  Pass `week` (YYYY-MM-DD) to filter by week_start. */
    list: (week?: string): Promise<AxiosResponse<WorkSchedule[]>> =>
        API.get("/schedules/", { params: week ? { week } : undefined }),

    retrieve: (id: number): Promise<AxiosResponse<WorkSchedule>> =>
        API.get(`/schedules/${id}/`),

    create: (
        payload: CreateSchedulePayload,
    ): Promise<AxiosResponse<WorkSchedule>> => API.post("/schedules/", payload),

    update: (
        id: number,
        payload: UpdateSchedulePayload,
    ): Promise<AxiosResponse<WorkSchedule>> =>
        API.patch(`/schedules/${id}/`, payload),

    delete: (id: number): Promise<AxiosResponse<void>> =>
        API.delete(`/schedules/${id}/`),

    /** Assign (or overwrite) a shift for one or more staff members.
     *  Pass `assigned_to` as a number or number[] for batch assignment.
     *  Creates weekly schedules automatically if they don't exist yet. */
    assignSlot: (
        payload: AssignSlotPayload,
    ): Promise<AxiosResponse<AssignSlotResponse>> =>
        API.post("/schedules/assign_slot/", payload),

    /** Remove a single day's shift from a user's weekly schedule. */
    removeSlot: (
        payload: RemoveSlotPayload,
    ): Promise<AxiosResponse<WorkSchedule>> =>
        API.post("/schedules/remove_slot/", payload),

    /**
     * Assign task permissions scoped to a specific shift entry.
     * This does NOT modify the user's global can_stock_take / can_receive_stock.
     * The permission is tied to the given shift and is removed when that
     * WorkSchedule is deleted.
     */
    assignShiftTask: (
        payload: AssignShiftTaskPayload,
    ): Promise<AxiosResponse<ShiftTaskPerm>> =>
        API.post("/schedules/assign_shift_task/", payload),
};
