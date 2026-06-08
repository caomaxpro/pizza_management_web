import { useRef, useEffect } from "react";
import type { Weekday } from "../../types/user";
import {
    DAYS,
    SHIFT_WINDOWS,
    padHour,
    columnDate,
    isSlotPast,
    isSlotTooSoon,
} from "./helpers";
import type { SlotInfo, AssignedStaff } from "./types";
import styles from "./UserTimetable.module.scss";

interface TimetableGridProps {
    todayIdx: number;
    onSlotClick: (slot: SlotInfo) => void;
    getWindowAssignments: (
        day: Weekday,
        startHour: number,
        endHour: number,
    ) => AssignedStaff[];
    weekMonday: Date;
}

export default function TimetableGrid({
    todayIdx,
    onSlotClick,
    getWindowAssignments,
    weekMonday,
}: TimetableGridProps) {
    const todayHeaderRef = useRef<HTMLDivElement>(null);
    const firstDayRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // If today is in this week, scroll to today; otherwise scroll to day 0 (Monday)
        const scrollTarget =
            todayIdx >= 0 ? todayHeaderRef.current : firstDayRef.current;
        if (scrollTarget) {
            scrollTarget.scrollIntoView({
                behavior: "smooth",
                inline: "center",
                block: "nearest",
            });
        }
    }, [todayIdx]);

    return (
        <div className={styles.gridScroll}>
            <div className={styles.grid}>
                {/* Corner cell */}
                <div className={`${styles.cell} ${styles.cornerCell}`} />

                {/* Day header cells */}
                {DAYS.map((day, i) => (
                    <div
                        key={day.key}
                        ref={
                            i === 0
                                ? firstDayRef
                                : i === todayIdx
                                  ? todayHeaderRef
                                  : null
                        }
                        className={`${styles.cell} ${styles.dayHeader} ${
                            i === todayIdx ? styles.todayHeader : ""
                        }`}
                    >
                        <span className={styles.dayShort}>{day.short}</span>
                        <span className={styles.dayDate}>
                            {columnDate(weekMonday, i)}
                        </span>
                    </div>
                ))}

                {/* One row per shift window */}
                {SHIFT_WINDOWS.map((win) => {
                    const periodClass = styles[win.periodClass] ?? "";
                    return [
                        // Window label
                        <div
                            key={`lbl-${win.key}`}
                            className={[
                                styles.cell,
                                styles.hourLabel,
                                periodClass,
                            ].join(" ")}
                        >
                            <span className={styles.windowLabel}>
                                {win.label}
                            </span>
                            <span></span>
                            <span className={styles.windowRange}>
                                {padHour(win.startHour)} -{" "}
                                {padHour(win.endHour)}
                            </span>
                        </div>,

                        // Day cells
                        ...DAYS.map((day, i) => {
                            const isToday = i === todayIdx;
                            const isPast = isSlotPast(
                                weekMonday,
                                i,
                                win.startHour,
                            );
                            const isTooSoon = isSlotTooSoon(
                                weekMonday,
                                i,
                                win.startHour,
                            );
                            const isDisabled = isPast || isTooSoon;
                            const windowStaff = getWindowAssignments(
                                day.key,
                                win.startHour,
                                win.endHour,
                            );

                            return (
                                <div
                                    key={`${day.key}-${win.key}`}
                                    className={[
                                        styles.cell,
                                        styles.slotCell,
                                        periodClass,
                                        isToday ? styles.todayCol : "",
                                        windowStaff.length > 0
                                            ? styles.occupied
                                            : "",
                                        isPast ? styles.pastSlot : "",
                                        isTooSoon ? styles.tooSoonSlot : "",
                                    ].join(" ")}
                                    role="button"
                                    tabIndex={isDisabled ? -1 : 0}
                                    onClick={() => {
                                        if (!isDisabled) {
                                            onSlotClick({
                                                day: day.key,
                                                dayIndex: i,
                                                hour: win.startHour,
                                                startHint: win.startHour,
                                                endHint: win.endHour,
                                            });
                                        }
                                    }}
                                    onKeyDown={(e) => {
                                        if (!isDisabled && e.key === "Enter") {
                                            onSlotClick({
                                                day: day.key,
                                                dayIndex: i,
                                                hour: win.startHour,
                                                startHint: win.startHour,
                                                endHint: win.endHour,
                                            });
                                        }
                                    }}
                                    aria-label={`${day.label} ${
                                        win.label
                                    } (${padHour(win.startHour)}–${padHour(
                                        win.endHour,
                                    )})${
                                        isPast
                                            ? " (past)"
                                            : isTooSoon
                                              ? " (too soon)"
                                              : ""
                                    }`}
                                >
                                    {windowStaff.map((a) => (
                                        <span
                                            key={a.schedule.id}
                                            className={styles.staffChip}
                                        >
                                            {a.schedule.assigned_to_username}
                                        </span>
                                    ))}
                                    {windowStaff.length === 0 &&
                                        !isDisabled && (
                                            <span className={styles.addHint}>
                                                +
                                            </span>
                                        )}
                                </div>
                            );
                        }),
                    ];
                })}
            </div>
        </div>
    );
}
