import type { WorkSchedule, Weekday } from "../../types/user";

// ── constants ─────────────────────────────────────────────────────────────────

export const DAYS: { key: Weekday; label: string; short: string }[] = [
    { key: "mon", label: "Monday", short: "Mon" },
    { key: "tue", label: "Tuesday", short: "Tue" },
    { key: "wed", label: "Wednesday", short: "Wed" },
    { key: "thu", label: "Thursday", short: "Thu" },
    { key: "fri", label: "Friday", short: "Fri" },
    { key: "sat", label: "Saturday", short: "Sat" },
    { key: "sun", label: "Sunday", short: "Sun" },
];

export const START_HOUR = 7;
export const END_HOUR = 26; // 02:00 next day
export const LEAD_HOURS = 24; // Require assignment at least this many hours before slot start
export const HOUR_SLOTS = Array.from(
    { length: END_HOUR - START_HOUR },
    (_, i) => START_HOUR + i,
);

// ── shift period windows ──────────────────────────────────────────────────────

export interface ShiftWindow {
    key: string;
    label: string;
    startHour: number;
    endHour: number;
    /** CSS Module class name (camelCase) for the period band. */
    periodClass: string;
}

export const SHIFT_WINDOWS: ShiftWindow[] = [
    {
        key: "morning",
        label: "Morning",
        startHour: 7,
        endHour: 11,
        periodClass: "periodMorning",
    },
    {
        key: "lunch",
        label: "Lunch",
        startHour: 11,
        endHour: 15,
        periodClass: "periodLunch",
    },
    {
        key: "afternoon",
        label: "Afternoon",
        startHour: 15,
        endHour: 18,
        periodClass: "periodAfternoon",
    },
    {
        key: "evening",
        label: "Evening",
        startHour: 18,
        endHour: 22,
        periodClass: "periodEvening",
    },
    {
        key: "night",
        label: "Night",
        startHour: 22,
        endHour: 26,
        periodClass: "periodNight",
    },
];

export function getShiftWindow(hour: number): ShiftWindow | null {
    return (
        SHIFT_WINDOWS.find((w) => hour >= w.startHour && hour < w.endHour) ??
        null
    );
}

// ── helpers ───────────────────────────────────────────────────────────────────

export function getMondayOf(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    d.setDate(d.getDate() + diff);
    d.setHours(0, 0, 0, 0);
    return d;
}

export function toISODate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

export function formatWeekRange(monday: Date): string {
    const sunday = new Date(monday);
    sunday.setDate(sunday.getDate() + 6);
    const fmt = (d: Date) =>
        d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
    return `${fmt(monday)} – ${fmt(sunday)} ${sunday.getFullYear()}`;
}

export function todayDayIndex(weekMonday: Date): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = Math.round(
        (today.getTime() - weekMonday.getTime()) / 86_400_000,
    );
    return diff >= 0 && diff <= 6 ? diff : -1;
}

export function padHour(h: number): string {
    return (h % 24).toString().padStart(2, "0") + ":00";
}

/** Parse "HH:MM-HH:MM" → start/end hour numbers + formatted strings. */
export function parseShiftRange(
    entry: string | undefined,
): { start: number; end: number; startStr: string; endStr: string } | null {
    if (!entry) return null;
    const m = entry.match(/^(\d{2}):(\d{2})-(\d{2}):(\d{2})$/);
    if (!m) return null;
    return {
        start: parseInt(m[1]),
        end: parseInt(m[3]),
        startStr: `${m[1]}:${m[2]}`,
        endStr: `${m[3]}:${m[4]}`,
    };
}

export function shiftCoversHour(
    entry: string | undefined,
    hour: number,
): boolean {
    const r = parseShiftRange(entry);
    if (r === null) return false;
    // Cross-midnight shift (e.g. 22:00-02:00): covers [start,24) and [0,end)
    if (r.end <= r.start) return hour >= r.start || hour < r.end;
    return hour >= r.start && hour < r.end;
}

/** Build a per-user map of the active schedule for the given week. */
export function buildUserScheduleMap(
    schedules: WorkSchedule[],
    weekStart: string,
): Map<number, WorkSchedule> {
    const map = new Map<number, WorkSchedule>();
    for (const s of schedules) {
        if (s.week_start !== weekStart || !s.active) continue;
        const existing = map.get(s.assigned_to);
        if (!existing || s.updated_at > existing.updated_at)
            map.set(s.assigned_to, s);
    }
    return map;
}

export function columnDate(weekMonday: Date, dayIndex: number): string {
    const d = new Date(weekMonday);
    d.setDate(d.getDate() + dayIndex);
    return d.getDate().toString();
}

/** Check if a time slot is in the past relative to current time. */
export function isSlotPast(
    weekMonday: Date,
    dayIndex: number,
    slotHour: number,
): boolean {
    const now = new Date();
    const currentDate = new Date(now);
    currentDate.setHours(0, 0, 0, 0);

    const slotDate = new Date(weekMonday);
    slotDate.setDate(slotDate.getDate() + dayIndex);
    slotDate.setHours(0, 0, 0, 0);

    // If slot is on a past date, it's in the past
    if (slotDate < currentDate) return true;

    // If slot is on future date, it's not in the past
    if (slotDate > currentDate) return false;

    // Same date: compare hours
    return slotHour < now.getHours();
}

/** Check if a time slot is too soon (within LEAD_HOURS). */
export function isSlotTooSoon(
    weekMonday: Date,
    dayIndex: number,
    slotHour: number,
    leadHours: number = LEAD_HOURS,
): boolean {
    const slotDate = new Date(weekMonday);
    slotDate.setDate(slotDate.getDate() + dayIndex);
    slotDate.setHours(slotHour, 0, 0, 0);

    const cutoff = new Date();
    cutoff.setHours(cutoff.getHours() + leadHours);

    return slotDate < cutoff;
}
