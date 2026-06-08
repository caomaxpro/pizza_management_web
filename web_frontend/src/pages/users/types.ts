import type { WorkSchedule, Weekday, ShiftTaskPerm } from "../../types/user";

export interface SlotInfo {
    day: Weekday;
    dayIndex: number;
    hour: number;
    /** Window start hour pre-filled in the modal (e.g. 11 for Lunch 11-15). */
    startHint?: number;
    /** Window end hour pre-filled in the modal (e.g. 15 for Lunch 11-15). */
    endHint?: number;
}

export interface AssignedStaff {
    schedule: WorkSchedule;
    startStr: string;
    endStr: string;
    /** Shift-scoped task perm for this specific slot entry, if one exists. */
    shiftTaskPerm?: ShiftTaskPerm;
}
