import React, { useState, useEffect } from "react";
import { X, Warning } from "@phosphor-icons/react";
import CustomForm2 from "../../components/form/CustomForm2";
import TextareaField from "../../components/form/fields/TextareaField";
import SelectField from "../../components/form/fields/SelectField";
import type { WorkSchedule, Weekday, User } from "../../types/user";
import { DAYS, END_HOUR, padHour, isSlotTooSoon, LEAD_HOURS } from "./helpers";
import type { SlotInfo, AssignedStaff } from "./types";
import styles from "./UserTimetable.module.scss";
import MessageCard from "@components/form/fields/MessageCard";
import { TaskPermissionForm, AssignedStaffRow } from "./SlotModal.components";

export interface SlotModalProps {
    slot: SlotInfo;
    assigned: AssignedStaff[];
    staffList: User[];
    weekStart: string;
    weekMonday: Date;
    currentUserRole?: string;
    onSave: (
        userIds: number[],
        day: Weekday,
        startStr: string,
        endStr: string,
        notes: string,
    ) => Promise<void>;
    onRemove: (
        schedule: WorkSchedule,
        day: Weekday,
        startStr: string,
    ) => Promise<void>;
    onClose: () => void;
    saving: boolean;
    onAssignTask?: (
        userId: number,
        tasks: { can_stock_take: boolean; can_receive_stock: boolean },
    ) => Promise<void>;
    /**
     * Assign task permissions scoped to a single shift entry.
     * Does NOT modify the user's global can_stock_take / can_receive_stock.
     */
    onAssignShiftTask?: (
        userId: number,
        weekStart: string,
        day: Weekday,
        shiftStart: string,
        tasks: { can_stock_take: boolean; can_receive_stock: boolean },
    ) => Promise<void>;
    /** Optional class applied to the overlay element */
    overlayClassName?: string;
    /** Optional inline style applied to the overlay element */
    overlayStyle?: React.CSSProperties;
    /** Optional class applied to the inner modal element */
    modalClassName?: string;
    /** Optional inline style applied to the inner modal element */
    modalStyle?: React.CSSProperties;
}

// ── SlotModal ─────────────────────────────────────────────────────────────────

export default function SlotModal({
    slot,
    assigned,
    staffList,
    weekStart,
    weekMonday,
    currentUserRole,
    onSave,
    onRemove,
    onClose,
    // saving, // prop removed: using local formSaving state instead
    onAssignTask,
    onAssignShiftTask,
    overlayClassName,
    overlayStyle,
    modalClassName,
    modalStyle,
}: SlotModalProps) {
    const [formSaving, setFormSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formKey, setFormKey] = useState(0);
    const [selectedStaffIds, setSelectedStaffIds] = useState<string[]>([]);
    const [isRemoving, setIsRemoving] = useState(false);
    /** Task perms for newly-assigned staff (form section). */
    const [newStaffTaskPerms, setNewStaffTaskPerms] = useState({
        can_stock_take: false,
        can_receive_stock: false,
    });
    /** "permanent" = update User flags; "shift" = create ShiftTaskPermission. */
    const [taskScope, setTaskScope] = useState<"permanent" | "shift">(
        onAssignShiftTask ? "shift" : "permanent",
    );
    /** Permanent task-perm state for already-assigned staff. */
    const [localTaskPerms, setLocalTaskPerms] = useState<
        Record<number, { can_stock_take: boolean; can_receive_stock: boolean }>
    >({});
    /** Shift-scoped task-perm state for already-assigned staff. */
    const [localShiftPerms, setLocalShiftPerms] = useState<
        Record<
            number,
            { id?: number; can_stock_take: boolean; can_receive_stock: boolean }
        >
    >({});

    // Reset form when slot changes
    useEffect(() => {
        setError(null);
        setSelectedStaffIds([]);
        setNewStaffTaskPerms({
            can_stock_take: false,
            can_receive_stock: false,
        });
        setTaskScope(onAssignShiftTask ? "shift" : "permanent");
    }, [slot.hour, slot.day, onAssignShiftTask]);

    // Sync permanent task perms from staffList whenever assigned list changes.
    useEffect(() => {
        const perms: Record<
            number,
            { can_stock_take: boolean; can_receive_stock: boolean }
        > = {};
        assigned.forEach((a) => {
            const user = staffList.find(
                (u) => parseInt(u.id) === a.schedule.assigned_to,
            );
            if (user) {
                perms[a.schedule.assigned_to] = {
                    can_stock_take: user.can_stock_take ?? false,
                    can_receive_stock: user.can_receive_stock ?? false,
                };
            }
        });
        setLocalTaskPerms(perms);
    }, [assigned, staffList]);

    // Sync shift-scoped task perms from the assigned list's shiftTaskPerm data.
    useEffect(() => {
        const perms: Record<
            number,
            { id?: number; can_stock_take: boolean; can_receive_stock: boolean }
        > = {};
        assigned.forEach((a) => {
            perms[a.schedule.assigned_to] = {
                id: a.shiftTaskPerm?.id,
                can_stock_take: a.shiftTaskPerm?.can_stock_take ?? false,
                can_receive_stock: a.shiftTaskPerm?.can_receive_stock ?? false,
            };
        });
        setLocalShiftPerms(perms);
    }, [assigned]);

    // Detect which assigned staff have unsaved permanent task perm changes
    const dirtyPermanentPerms = assigned.filter((a) => {
        if (a.schedule.assigned_to_role !== "staff") return false;
        const user = staffList.find(
            (u) => parseInt(u.id) === a.schedule.assigned_to,
        );
        const local = localTaskPerms[a.schedule.assigned_to];
        if (!user || !local) return false;
        return (
            (user.can_stock_take ?? false) !== local.can_stock_take ||
            (user.can_receive_stock ?? false) !== local.can_receive_stock
        );
    });

    // Detect which assigned staff have unsaved shift-scoped task perm changes
    const dirtyShiftPerms = assigned.filter((a) => {
        if (a.schedule.assigned_to_role !== "staff") return false;
        const original = a.shiftTaskPerm;
        const local = localShiftPerms[a.schedule.assigned_to];
        if (!local) return false;
        return (
            (original?.can_stock_take ?? false) !== local.can_stock_take ||
            (original?.can_receive_stock ?? false) !== local.can_receive_stock
        );
    });

    const hasDirtyPerms =
        dirtyPermanentPerms.length > 0 || dirtyShiftPerms.length > 0;

    const assignedIds = new Set(assigned.map((a) => a.schedule.assigned_to));
    const dayLabel = DAYS.find((d) => d.key === slot.day)?.label ?? slot.day;
    const isTooSoon = isSlotTooSoon(
        weekMonday,
        slot.dayIndex,
        slot.startHint ?? slot.hour,
    );

    // Determine which roles can be assigned based on current user's role
    const getAssignableRoles = (): string[] => {
        if (currentUserRole === "admin") {
            return ["manager", "staff"];
        } else if (currentUserRole === "manager") {
            return ["staff"];
        }
        return [];
    };

    const assignableRoles = getAssignableRoles();

    // Exclude managers from options if one is already assigned or one is already selected
    const hasAssignedManager = assigned.some(
        (a) => a.schedule.assigned_to_role === "manager",
    );
    const hasSelectedManager = selectedStaffIds.some((id) => {
        const u = staffList.find((u) => parseInt(u.id) === parseInt(id));
        return u?.role === "manager";
    });

    const hasSelectedStaff = selectedStaffIds.some((id) => {
        const u = staffList.find((u) => parseInt(u.id) === parseInt(id));
        return u?.role === "staff";
    });

    const availableStaff = staffList.filter((u) => {
        if (assignedIds.has(parseInt(u.id))) return false;
        if (!assignableRoles.includes(u.role || "")) return false;
        if (u.is_active === false) return false;
        return true;
    });

    // Reason to show instead of Select when no staff are available
    const noStaffReason: string | null = (() => {
        if (staffList.length === 0) return "Loading staff data…";
        if (assignableRoles.length === 0)
            return "You do not have permission to assign staff.";
        if (availableStaff.length === 0)
            return "All available staff are already assigned to this time slot.";
        return null;
    })();

    const initialValues = React.useMemo(
        () => ({ assigned_to: [] as string[], notes: "" }),
        [],
    );

    const fields = [
        noStaffReason ? (
            <div key="no-staff" className={styles.noStaffMsg}>
                {noStaffReason}
            </div>
        ) : (
            <SelectField
                key="assigned_to"
                name="assigned_to"
                label="Staff member"
                value={selectedStaffIds}
                onChange={(value: string | string[]) => {
                    const normalized = Array.isArray(value)
                        ? value
                        : value
                          ? [value]
                          : [];
                    setSelectedStaffIds(normalized);
                }}
                options={availableStaff.map((u) => {
                    const isManager = u.role === "manager";
                    const isDisabled =
                        isManager && (hasAssignedManager || hasSelectedManager);
                    return {
                        label: `${u.email}${u.name ? ` (${u.name})` : ""}`,
                        value: String(u.id),
                        disabled: isDisabled,
                    };
                })}
                placeholder="— select staff —"
                multi={true}
            />
        ),
        <TaskPermissionForm
            key="task-perms"
            hasSelectedStaff={hasSelectedStaff}
            onAssignTask={!!onAssignTask}
            onAssignShiftTask={!!onAssignShiftTask}
            taskScope={taskScope}
            onScopeChange={setTaskScope}
            newStaffTaskPerms={newStaffTaskPerms}
            onUpdateStock={(checked) =>
                setNewStaffTaskPerms((p) => ({
                    ...p,
                    can_stock_take: checked,
                }))
            }
            onUpdateReceipt={(checked) =>
                setNewStaffTaskPerms((p) => ({
                    ...p,
                    can_receive_stock: checked,
                }))
            }
            isLoading={formSaving}
        />,
        <TextareaField
            key="notes"
            name="notes"
            label="Notes"
            value=""
            onChange={() => {}}
            placeholder="Optional task or note…"
            rows={10}
        />,
    ].filter((f): f is React.ReactElement => Boolean(f));

    async function handleFormSubmit(values: Record<string, unknown>) {
        const rawIds = values.assigned_to;
        const idList: string[] = Array.isArray(rawIds)
            ? rawIds
            : rawIds
              ? [rawIds as string]
              : [];

        // Case 1: no staff selected — save pending task perm changes for existing staff
        if (idList.length === 0) {
            if (!hasDirtyPerms) return;
            setFormSaving(true);
            setError(null);
            try {
                // Save permanent perm changes
                if (dirtyPermanentPerms.length > 0 && onAssignTask) {
                    await Promise.all(
                        dirtyPermanentPerms.map((a) =>
                            onAssignTask(
                                a.schedule.assigned_to,
                                localTaskPerms[a.schedule.assigned_to],
                            ),
                        ),
                    );
                }
                // Save shift-scoped perm changes
                if (dirtyShiftPerms.length > 0 && onAssignShiftTask) {
                    await Promise.all(
                        dirtyShiftPerms.map((a) =>
                            onAssignShiftTask(
                                a.schedule.assigned_to,
                                weekStart,
                                slot.day,
                                a.startStr,
                                localShiftPerms[a.schedule.assigned_to],
                            ),
                        ),
                    );
                }
            } catch (err) {
                const errorMessage =
                    err instanceof Error
                        ? err.message
                        : "Failed to save task permissions.";
                setError(errorMessage);
            } finally {
                setFormSaving(false);
            }
            return;
        }

        // Case 2: staff selected — assign to shift (+ task perms for staff roles)
        const userIds = idList.map((id) => parseInt(id));

        setFormSaving(true);
        setError(null);
        try {
            await onSave(
                userIds,
                slot.day,
                padHour(slot.startHint ?? slot.hour),
                padHour(Math.min(slot.endHint ?? slot.hour + 1, END_HOUR)),
                (values.notes as string) ?? "",
            );
            setSelectedStaffIds([]);
            setNewStaffTaskPerms({
                can_stock_take: false,
                can_receive_stock: false,
            });
            setFormKey((k) => k + 1);
            setError(null);

            const staffUserIds = userIds.filter((id) => {
                const u = staffList.find((u) => parseInt(u.id) === id);
                return u?.role === "staff";
            });

            if (taskScope === "permanent" && onAssignTask) {
                if (staffUserIds.length > 0) {
                    await Promise.all(
                        staffUserIds.map((id) =>
                            onAssignTask(id, newStaffTaskPerms),
                        ),
                    );
                }
            } else if (taskScope === "shift" && onAssignShiftTask) {
                const shiftStartStr = padHour(slot.startHint ?? slot.hour);
                if (staffUserIds.length > 0) {
                    await Promise.all(
                        staffUserIds.map((id) =>
                            onAssignShiftTask(
                                id,
                                weekStart,
                                slot.day,
                                shiftStartStr,
                                newStaffTaskPerms,
                            ),
                        ),
                    );
                }
            }
        } catch (err) {
            const errorMessage =
                err instanceof Error
                    ? err.message
                    : typeof err === "object" && err !== null && "detail" in err
                      ? (err as { detail: string }).detail
                      : "Failed to assign staff. Please try again.";
            setError(errorMessage);
        } finally {
            setFormSaving(false);
        }
    }

    function handleToggleTask(
        userId: number,
        field: "can_stock_take" | "can_receive_stock",
        checked: boolean,
    ) {
        const current = localTaskPerms[userId] ?? {
            can_stock_take: false,
            can_receive_stock: false,
        };
        const updated = { ...current, [field]: checked };
        setLocalTaskPerms((p) => ({ ...p, [userId]: updated }));
    }

    function handleToggleShiftTask(
        userId: number,
        field: "can_stock_take" | "can_receive_stock",
        checked: boolean,
    ) {
        const current = localShiftPerms[userId] ?? {
            can_stock_take: false,
            can_receive_stock: false,
        };
        setLocalShiftPerms((p) => ({
            ...p,
            [userId]: { ...current, [field]: checked },
        }));
    }

    return (
        <div
            className={[styles.modalOverlay, overlayClassName]
                .filter(Boolean)
                .join(" ")}
            style={overlayStyle}
            onClick={onClose}
        >
            <div
                className={[styles.modal, modalClassName]
                    .filter(Boolean)
                    .join(" ")}
                style={modalStyle}
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
            >
                {/* header */}
                <div className={styles.modalHeader}>
                    <h3>
                        {dayLabel} &middot;{" "}
                        {padHour(slot.startHint ?? slot.hour)}–
                        {padHour(slot.endHint ?? slot.hour + 1)}
                    </h3>
                    <button
                        className={styles.closeBtn}
                        onClick={onClose}
                        aria-label="Close"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* body */}
                <div className={styles.modalBody}>
                    {/* Error card */}
                    {error && (
                        <MessageCard
                            message={error}
                            variant="error"
                            dismissible={true}
                            onDismiss={() => setError(null)}
                        />
                    )}

                    {/* Currently assigned staff */}
                    {assigned.length > 0 && (
                        <div className={styles.assignedSection}>
                            <p className={styles.sectionLabel}>
                                Assigned staff
                            </p>
                            {assigned.map((a) => (
                                <AssignedStaffRow
                                    key={a.schedule.id}
                                    assigned={a}
                                    staffRole={
                                        a.schedule.assigned_to_role as
                                            | "admin"
                                            | "manager"
                                            | "staff"
                                    }
                                    onRemove={async () => {
                                        setIsRemoving(true);
                                        try {
                                            await onRemove(
                                                a.schedule,
                                                slot.day,
                                                a.startStr,
                                            );
                                        } catch (err) {
                                            const errorMessage =
                                                err instanceof Error
                                                    ? err.message
                                                    : "Failed to remove staff";
                                            setError(errorMessage);
                                        } finally {
                                            setIsRemoving(false);
                                        }
                                    }}
                                    onTogglePermanentStock={(uid, checked) =>
                                        handleToggleTask(
                                            uid,
                                            "can_stock_take",
                                            checked,
                                        )
                                    }
                                    onTogglePermanentReceipt={(uid, checked) =>
                                        handleToggleTask(
                                            uid,
                                            "can_receive_stock",
                                            checked,
                                        )
                                    }
                                    onToggleShiftStock={(uid, checked) =>
                                        handleToggleShiftTask(
                                            uid,
                                            "can_stock_take",
                                            checked,
                                        )
                                    }
                                    onToggleShiftReceipt={(uid, checked) =>
                                        handleToggleShiftTask(
                                            uid,
                                            "can_receive_stock",
                                            checked,
                                        )
                                    }
                                    permanentStock={
                                        localTaskPerms[a.schedule.assigned_to]
                                            ?.can_stock_take ?? false
                                    }
                                    permanentReceipt={
                                        localTaskPerms[a.schedule.assigned_to]
                                            ?.can_receive_stock ?? false
                                    }
                                    shiftStock={
                                        localShiftPerms[a.schedule.assigned_to]
                                            ?.can_stock_take ?? false
                                    }
                                    shiftReceipt={
                                        localShiftPerms[a.schedule.assigned_to]
                                            ?.can_receive_stock ?? false
                                    }
                                    showPermanent={!!onAssignTask}
                                    showShift={!!onAssignShiftTask}
                                    isSaving={formSaving}
                                    isRemoving={isRemoving}
                                    onRemoveStart={() => setIsRemoving(true)}
                                    onRemoveEnd={() => setIsRemoving(false)}
                                />
                            ))}
                        </div>
                    )}

                    {/* Form using CustomForm2 */}
                    <div className={styles.formSection}>
                        <p className={styles.sectionLabel}>Assign staff</p>
                        {isTooSoon && (
                            <div className={styles.warningBox}>
                                <Warning size={18} weight="fill" /> Assignments
                                must be made at least {LEAD_HOURS} hours before
                                start time. Please choose a different time slot.
                            </div>
                        )}
                        <CustomForm2
                            key={formKey}
                            fields={fields}
                            initialValues={initialValues}
                            onSubmit={handleFormSubmit}
                            isLoading={formSaving}
                            submitLabel={
                                selectedStaffIds.length > 0
                                    ? "Assign"
                                    : hasDirtyPerms
                                      ? "Save changes"
                                      : "Assign"
                            }
                            fieldGap={12}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
