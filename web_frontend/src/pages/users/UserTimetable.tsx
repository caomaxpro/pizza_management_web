/* eslint-disable no-useless-catch */
import { useState, useEffect, useCallback, useRef, memo } from "react";
import { scheduleAPI } from "../../services/schedule";
import { usersAPI } from "../../services/users";
import type {
    AssignSlotPayload,
    RemoveSlotPayload,
    AssignShiftTaskPayload,
} from "../../services/schedule";
import type { ShiftTaskPerm } from "../../types/user";
import { authAPI } from "../../services/auth";
import type { WorkSchedule, Weekday, User } from "../../types/user";
import {
    getMondayOf,
    toISODate,
    todayDayIndex,
    buildUserScheduleMap,
    parseShiftRange,
    shiftCoversHour,
} from "./helpers";
import {
    getCachedSchedules,
    setCachedSchedules,
    invalidateScheduleCache,
    getCachedStaffMeta,
    setCachedStaffMeta,
} from "../../utils/timetableCache";
import type { SlotInfo, AssignedStaff } from "./types";
import SlotModal from "./SlotModal";
import TimetableNavigation from "./TimetableNavigation";
import TimetableGrid from "./TimetableGrid";
import styles from "./UserTimetable.module.scss";

// Memoize heavy components to prevent unnecessary re-renders
const MemoTimetableNavigation = memo(TimetableNavigation);
const MemoTimetableGrid = memo(TimetableGrid);
const MemoSlotModal = memo(SlotModal);

// ── main component ────────────────────────────────────────────────────────────

export default function UserTimetable() {
    const [weekMonday, setWeekMonday] = useState<Date>(() =>
        getMondayOf(new Date()),
    );
    const [schedules, setSchedules] = useState<WorkSchedule[]>([]);
    const [staffList, setStaffList] = useState<User[]>([]);
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [openSlot, setOpenSlot] = useState<SlotInfo | null>(null);
    const [saving, setSaving] = useState(false);
    // Track in-flight background refreshes so we don't double-fetch
    const refreshingWeeks = useRef<Set<string>>(new Set());
    // True after the first successful data load — prevents grid unmount during navigation
    const hasEverLoaded = useRef(false);

    const weekStart = toISODate(weekMonday);
    const todayIdx = todayDayIndex(weekMonday);
    const userScheduleMap = buildUserScheduleMap(schedules, weekStart);

    // Pre-fetch adjacent weeks to avoid lag on navigation
    const preFetchWeek = useCallback(async (date: Date) => {
        const key = toISODate(date);
        if (getCachedSchedules(key) || refreshingWeeks.current.has(key)) return;
        refreshingWeeks.current.add(key);
        try {
            const res = await scheduleAPI.list(key);
            setCachedSchedules(key, res.data);
        } catch {
            // silently fail pre-fetch
        } finally {
            refreshingWeeks.current.delete(key);
        }
    }, []);

    const fetchData = useCallback(async () => {
        const key = toISODate(weekMonday);

        // ── 1. Serve from cache immediately (no loading spinner) ──────────────
        const cachedSchedules = getCachedSchedules(key);
        const cachedMeta = getCachedStaffMeta();
        if (cachedSchedules) {
            setSchedules(cachedSchedules);
            hasEverLoaded.current = true;
            if (cachedMeta) {
                setStaffList(cachedMeta.staffList);
                setCurrentUser(cachedMeta.currentUser);
                return;
            }
        }

        // ── 2. Fetch whatever is missing / stale ──────────────────────────────
        // Show spinner only if the week has no cached data at all
        if (!cachedSchedules) setLoading(true);
        setError(null);

        // Guard against duplicate in-flight requests for the same week
        if (refreshingWeeks.current.has(key)) return;
        refreshingWeeks.current.add(key);

        try {
            const fetchSchedules = !cachedSchedules
                ? scheduleAPI.list(key)
                : null;
            const fetchStaff = !cachedMeta ? authAPI.listAssignable() : null;
            const fetchUser = !cachedMeta ? authAPI.getCurrentUser() : null;

            const [schRes, staffRes, userRes] = await Promise.all([
                fetchSchedules,
                fetchStaff,
                fetchUser,
            ]);

            if (schRes) {
                setCachedSchedules(key, schRes.data);
                setSchedules(schRes.data);
                hasEverLoaded.current = true;
            }
            if (staffRes && userRes) {
                setCachedStaffMeta(staffRes.data, userRes.data);
                setStaffList(staffRes.data);
                setCurrentUser(userRes.data);
            }
        } catch {
            setError("Failed to load timetable data. Please try again.");
        } finally {
            setLoading(false);
            refreshingWeeks.current.delete(key);
        }
    }, [weekMonday]);

    useEffect(() => {
        void fetchData();
    }, [fetchData]);

    // Memoize slot assignments to avoid recomputing on every render
    const getSlotAssignments = useCallback(
        (day: Weekday, hour: number): AssignedStaff[] => {
            const roleRank: Record<string, number> = {
                admin: 0,
                manager: 1,
                staff: 2,
            };
            return [...userScheduleMap.values()]
                .flatMap((s) => {
                    const dayEntry = s.entries[day];
                    // Normalize to array (support both legacy string and new list format)
                    const shifts = Array.isArray(dayEntry)
                        ? dayEntry
                        : dayEntry
                          ? [dayEntry]
                          : [];
                    return shifts
                        .filter((entry) => shiftCoversHour(entry, hour))
                        .map((entry) => {
                            const range = parseShiftRange(entry)!;
                            const shiftTaskPerm = s.shift_task_perms?.find(
                                (p) =>
                                    p.day === day &&
                                    p.shift_start === range.startStr,
                            );
                            return {
                                schedule: s,
                                startStr: range.startStr,
                                endStr: range.endStr,
                                shiftTaskPerm,
                            };
                        });
                })
                .sort((a, b) => {
                    const ra = roleRank[a.schedule.assigned_to_role] ?? 2;
                    const rb = roleRank[b.schedule.assigned_to_role] ?? 2;
                    if (ra !== rb) return ra - rb;
                    return a.startStr.localeCompare(b.startStr);
                });
        },
        [userScheduleMap],
    );

    // Memoize window assignments to avoid recalculating for each slot
    const getWindowAssignments = useCallback(
        (day: Weekday, startHour: number, endHour: number): AssignedStaff[] => {
            // Key by scheduleId+startStr so the same person can appear in multiple windows
            const seen = new Set<string>();
            const result: AssignedStaff[] = [];
            for (let h = startHour; h < endHour; h++) {
                for (const a of getSlotAssignments(day, h)) {
                    const key = `${a.schedule.id}-${a.startStr}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        result.push(a);
                    }
                }
            }
            return result;
        },
        [getSlotAssignments],
    );

    async function handleSave(
        userIds: number[],
        day: Weekday,
        startStr: string,
        endStr: string,
        notes: string,
    ) {
        setSaving(true);
        try {
            const payload: AssignSlotPayload = {
                assigned_to: userIds.length === 1 ? userIds[0] : userIds,
                week_start: weekStart,
                day,
                start: startStr,
                end: endStr,
                ...(notes ? { notes } : {}),
            };
            const res = await scheduleAPI.assignSlot(payload);
            setSchedules((prev) => {
                let updated = [...prev];
                for (const s of res.data.schedules) {
                    const idx = updated.findIndex((x) => x.id === s.id);
                    updated =
                        idx >= 0
                            ? updated.map((x) => (x.id === s.id ? s : x))
                            : [...updated, s];
                }
                // Bust the cache so the next navigation (or reload) is fresh
                invalidateScheduleCache(weekStart);
                setCachedSchedules(weekStart, updated);
                return updated;
            });
            // Surface partial errors to the caller so SlotModal can show them
            if (res.data.partial && res.data.errors) {
                const msgs = Object.values(res.data.errors).join(" ");
                throw new Error(msgs);
            }
            setOpenSlot(null);
        } catch (err) {
            // Re-throw error so SlotModal can display it
            throw err;
        } finally {
            setSaving(false);
        }
    }

    async function handleAssignShiftTask(
        userId: number,
        weekStartStr: string,
        day: Weekday,
        shiftStart: string,
        tasks: { can_stock_take: boolean; can_receive_stock: boolean },
    ) {
        const payload: AssignShiftTaskPayload = {
            user_id: userId,
            week_start: weekStartStr,
            day,
            shift_start: shiftStart,
            can_stock_take: tasks.can_stock_take,
            can_receive_stock: tasks.can_receive_stock,
        };
        const res = await scheduleAPI.assignShiftTask(payload);
        const updatedPerm: ShiftTaskPerm = res.data;
        // Patch the matching WorkSchedule's shift_task_perms in state
        setSchedules((prev) =>
            prev.map((s) => {
                if (s.assigned_to !== userId || s.week_start !== weekStartStr)
                    return s;
                const existing = s.shift_task_perms ?? [];
                const idx = existing.findIndex(
                    (p) => p.day === day && p.shift_start === shiftStart,
                );
                const updated: ShiftTaskPerm[] =
                    idx >= 0
                        ? existing.map((p, i) => (i === idx ? updatedPerm : p))
                        : [...existing, updatedPerm];
                return { ...s, shift_task_perms: updated };
            }),
        );
        // Invalidate cache so the updated perms are persisted on next reload
        invalidateScheduleCache(weekStartStr);
    }

    async function handleRemove(
        schedule: WorkSchedule,
        day: Weekday,
        startStr: string,
    ) {
        setSaving(true);
        try {
            const payload: RemoveSlotPayload = {
                assigned_to: schedule.assigned_to,
                week_start: weekStart,
                day,
                start: startStr,
            };
            const res = await scheduleAPI.removeSlot(payload);
            setSchedules((prev) => {
                const updated = prev
                    .map((s) => (s.id === res.data.id ? res.data : s))
                    .filter((s) => Object.keys(s.entries).length > 0);
                invalidateScheduleCache(weekStart);
                setCachedSchedules(weekStart, updated);
                return updated;
            });
        } catch {
            // keep modal open
        } finally {
            setSaving(false);
        }
    }

    const goToPrevWeek = useCallback(() => {
        const currentScrollY = window.scrollY;
        setWeekMonday((d) => {
            const p = new Date(d);
            p.setDate(p.getDate() - 7);
            // Pre-fetch the week before for smooth navigation
            const preFetchDate = new Date(p);
            preFetchDate.setDate(preFetchDate.getDate() - 7);
            preFetchWeek(preFetchDate);
            return p;
        });
        // Restore scroll position after render
        requestAnimationFrame(() => {
            window.scrollTo(0, currentScrollY);
        });
    }, [preFetchWeek]);

    const goToNextWeek = useCallback(() => {
        const currentScrollY = window.scrollY;
        setWeekMonday((d) => {
            const n = new Date(d);
            n.setDate(n.getDate() + 7);
            // Pre-fetch the week after for smooth navigation
            const preFetchDate = new Date(n);
            preFetchDate.setDate(preFetchDate.getDate() + 7);
            preFetchWeek(preFetchDate);
            return n;
        });
        // Restore scroll position after render
        requestAnimationFrame(() => {
            window.scrollTo(0, currentScrollY);
        });
    }, [preFetchWeek]);

    const handleCloseModal = useCallback(() => {
        setOpenSlot(null);
    }, []);

    const handleAssignTaskCallback = useCallback(
        async (
            userId: number,
            tasks: { can_stock_take: boolean; can_receive_stock: boolean },
        ) => {
            const res = await usersAPI.assignTask(userId, tasks);
            const updated = res.data;
            setStaffList((prev) =>
                prev.map((u) => (parseInt(u.id) === userId ? updated : u)),
            );
        },
        [],
    );

    const goToToday = useCallback(
        () => setWeekMonday(getMondayOf(new Date())),
        [],
    );

    return (
        <div className={styles.wrapper}>
            {/* ── navigation ── */}
            <MemoTimetableNavigation
                weekMonday={weekMonday}
                onPrevWeek={goToPrevWeek}
                onNextWeek={goToNextWeek}
                onToday={goToToday}
            />

            {/* ── state messages ── */}
            {/* Spinner only on initial load — navigation uses opacity fade instead */}
            {!hasEverLoaded.current && loading && (
                <div className={styles.stateMsg}>
                    <span className={styles.spinner} /> Loading…
                </div>
            )}
            {!loading && error && (
                <div className={styles.errorMsg}>{error}</div>
            )}

            {/* ── timetable grid ── */}
            {/* Keep grid mounted after first load to avoid flicker on week navigation */}
            {hasEverLoaded.current && !error && (
                <div
                    style={{
                        opacity: loading ? 0.5 : 1,
                        transition: "opacity 150ms ease",
                        pointerEvents: loading ? "none" : undefined,
                    }}
                >
                    <MemoTimetableGrid
                        todayIdx={todayIdx}
                        onSlotClick={setOpenSlot}
                        getWindowAssignments={getWindowAssignments}
                        weekMonday={weekMonday}
                    />
                </div>
            )}

            {/* ── slot modal ── */}
            {openSlot && (
                <MemoSlotModal
                    slot={openSlot}
                    weekStart={weekStart}
                    weekMonday={weekMonday}
                    assigned={getWindowAssignments(
                        openSlot.day,
                        openSlot.startHint ?? openSlot.hour,
                        openSlot.endHint ?? openSlot.hour + 1,
                    )}
                    staffList={staffList}
                    currentUserRole={currentUser?.role}
                    onSave={handleSave}
                    onRemove={handleRemove}
                    onClose={handleCloseModal}
                    saving={saving}
                    modalStyle={{ height: "700px", width: "600px" }}
                    onAssignTask={handleAssignTaskCallback}
                    onAssignShiftTask={handleAssignShiftTask}
                />
            )}
        </div>
    );
}
