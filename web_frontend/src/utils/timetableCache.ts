/**
 * localStorage cache for timetable data.
 *
 * Schedules are cached per-week (key = ISO Monday date, e.g. "2026-05-04").
 * Staff list + current user are cached together with a longer TTL.
 */
import type { WorkSchedule, User } from "../types/user";

// ── TTLs ──────────────────────────────────────────────────────────────────────

/** How long a single week's schedule cache is considered fresh (5 minutes). */
const SCHEDULE_TTL_MS = 5 * 60 * 1000;

/** How long the staff list / current user cache is considered fresh (10 minutes). */
const STAFF_TTL_MS = 10 * 60 * 1000;

// ── Storage keys ──────────────────────────────────────────────────────────────

const scheduleKey = (weekKey: string) => `tz_sched_${weekKey}`;
const STAFF_KEY = "tz_staff_meta";

// ── Types ─────────────────────────────────────────────────────────────────────

interface WeekEntry {
    data: WorkSchedule[];
    fetchedAt: number;
}

interface StaffEntry {
    staffList: User[];
    currentUser: User;
    fetchedAt: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function read<T>(key: string): T | null {
    try {
        const raw = localStorage.getItem(key);
        return raw ? (JSON.parse(raw) as T) : null;
    } catch {
        return null;
    }
}

function write(key: string, value: unknown): void {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {
        // Quota exceeded or private-browsing – silently degrade.
    }
}

// ── Schedule cache ────────────────────────────────────────────────────────────

export function getCachedSchedules(weekKey: string): WorkSchedule[] | null {
    const entry = read<WeekEntry>(scheduleKey(weekKey));
    if (!entry) return null;
    if (Date.now() - entry.fetchedAt > SCHEDULE_TTL_MS) return null;
    return entry.data;
}

export function setCachedSchedules(
    weekKey: string,
    data: WorkSchedule[],
): void {
    write(scheduleKey(weekKey), { data, fetchedAt: Date.now() });
}

/** Immediately invalidate a week's cache (call after any write operation). */
export function invalidateScheduleCache(weekKey: string): void {
    try {
        localStorage.removeItem(scheduleKey(weekKey));
    } catch {
        // ignore
    }
}

// ── Staff / current-user cache ────────────────────────────────────────────────

export function getCachedStaffMeta(): {
    staffList: User[];
    currentUser: User;
} | null {
    const entry = read<StaffEntry>(STAFF_KEY);
    if (!entry) return null;
    if (Date.now() - entry.fetchedAt > STAFF_TTL_MS) return null;
    return { staffList: entry.staffList, currentUser: entry.currentUser };
}

export function setCachedStaffMeta(staffList: User[], currentUser: User): void {
    write(STAFF_KEY, { staffList, currentUser, fetchedAt: Date.now() });
}
