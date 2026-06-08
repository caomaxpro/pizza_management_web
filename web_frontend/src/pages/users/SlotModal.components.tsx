import React from "react";
import CheckField from "../../components/form/fields/CheckField";
import type { AssignedStaff } from "./types";
import styles from "./UserTimetable.module.scss";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

interface TaskPermissionRowProps {
    scope: "permanent" | "shift";
    userId: number;
    can_stock_take: boolean;
    can_receive_stock: boolean;
    permanentStockTake?: boolean; // for disabling shift row
    permanentReceiveStock?: boolean; // for disabling shift row
    onToggleStock: (userId: number, checked: boolean) => void;
    onToggleReceipt: (userId: number, checked: boolean) => void;
    isLoading: boolean;
}

export const TaskPermissionRow: React.FC<TaskPermissionRowProps> = ({
    scope,
    userId,
    can_stock_take,
    can_receive_stock,
    permanentStockTake,
    permanentReceiveStock,
    onToggleStock,
    onToggleReceipt,
    isLoading,
}) => (
    <div className={styles.taskPermScopeRow}>
        <span className={styles.taskPermScopeLabel}>
            {scope === "permanent" ? "Permanent" : "This shift"}
        </span>
        <CheckField
            className={styles.taskPermCheck}
            label="Stock"
            value={can_stock_take}
            onChange={(checked) => onToggleStock(userId, checked)}
            disabled={
                isLoading ||
                (scope === "shift" && (permanentStockTake ?? false))
            }
        />
        <CheckField
            className={styles.taskPermCheck}
            label="Receipt"
            value={can_receive_stock}
            onChange={(checked) => onToggleReceipt(userId, checked)}
            disabled={
                isLoading ||
                (scope === "shift" && (permanentReceiveStock ?? false))
            }
        />
    </div>
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

interface AssignedStaffRowProps {
    assigned: AssignedStaff;
    staffRole: "admin" | "manager" | "staff";
    onRemove: () => Promise<void>;
    onTogglePermanentStock: (userId: number, checked: boolean) => void;
    onTogglePermanentReceipt: (userId: number, checked: boolean) => void;
    onToggleShiftStock: (userId: number, checked: boolean) => void;
    onToggleShiftReceipt: (userId: number, checked: boolean) => void;
    permanentStock: boolean;
    permanentReceipt: boolean;
    shiftStock: boolean;
    shiftReceipt: boolean;
    showPermanent: boolean;
    showShift: boolean;
    isSaving: boolean;
    isRemoving: boolean;
    onRemoveStart: () => void;
    onRemoveEnd: () => void;
}

export const AssignedStaffRow: React.FC<AssignedStaffRowProps> = ({
    assigned,
    staffRole,
    onRemove,
    onTogglePermanentStock,
    onTogglePermanentReceipt,
    onToggleShiftStock,
    onToggleShiftReceipt,
    permanentStock,
    permanentReceipt,
    shiftStock,
    shiftReceipt,
    showPermanent,
    showShift,
    isSaving,
    isRemoving,
    onRemoveStart,
    onRemoveEnd,
}) => {
    const handleRemoveClick = async () => {
        onRemoveStart();
        try {
            await onRemove();
        } finally {
            onRemoveEnd();
        }
    };

    return (
        <div className={styles.assignedRow}>
            <div className={styles.assignedInfo}>
                <span className={styles.assignedName}>
                    {assigned.schedule.assigned_to_username}
                </span>
                <span className={styles.assignedTime}>
                    {assigned.startStr} – {assigned.endStr}
                </span>

                {/* Task permission section */}
                {staffRole === "staff" && (showPermanent || showShift) && (
                    <div className={styles.taskPermSection}>
                        {showPermanent && (
                            <TaskPermissionRow
                                scope="permanent"
                                userId={assigned.schedule.assigned_to}
                                can_stock_take={permanentStock}
                                can_receive_stock={permanentReceipt}
                                onToggleStock={onTogglePermanentStock}
                                onToggleReceipt={onTogglePermanentReceipt}
                                isLoading={isSaving}
                            />
                        )}

                        {showShift && (
                            <TaskPermissionRow
                                scope="shift"
                                userId={assigned.schedule.assigned_to}
                                can_stock_take={shiftStock}
                                can_receive_stock={shiftReceipt}
                                permanentStockTake={permanentStock}
                                permanentReceiveStock={permanentReceipt}
                                onToggleStock={onToggleShiftStock}
                                onToggleReceipt={onToggleShiftReceipt}
                                isLoading={isSaving}
                            />
                        )}
                    </div>
                )}
            </div>

            <div className={styles.assignedActions}>
                <button
                    className={styles.removeBtn}
                    onClick={handleRemoveClick}
                    disabled={isSaving || isRemoving}
                >
                    {isRemoving ? "Removing..." : "Remove"}
                </button>
            </div>
        </div>
    );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

interface TaskPermissionFormProps {
    hasSelectedStaff: boolean;
    onAssignTask?: boolean | (() => void);
    onAssignShiftTask?: boolean | (() => void);
    taskScope: "permanent" | "shift";
    onScopeChange: (scope: "permanent" | "shift") => void;
    newStaffTaskPerms: {
        can_stock_take: boolean;
        can_receive_stock: boolean;
    };
    onUpdateStock: (checked: boolean) => void;
    onUpdateReceipt: (checked: boolean) => void;
    isLoading: boolean;
}

export const TaskPermissionForm: React.FC<TaskPermissionFormProps> = ({
    hasSelectedStaff,
    onAssignTask,
    onAssignShiftTask,
    taskScope,
    onScopeChange,
    newStaffTaskPerms,
    onUpdateStock,
    onUpdateReceipt,
    isLoading,
}) => {
    if (!hasSelectedStaff || (!onAssignTask && !onAssignShiftTask)) {
        return null;
    }

    const hasBothScopes = !!onAssignTask && !!onAssignShiftTask;

    return (
        <div className={styles.taskPermsInForm}>
            <p className={styles.taskPermsLabel}>Task permissions</p>

            {/* Scope toggle — only shown when both callbacks are available */}
            {hasBothScopes && (
                <div className={styles.taskScopeToggle}>
                    <button
                        type="button"
                        className={
                            taskScope === "permanent"
                                ? styles.taskScopeBtnActive
                                : styles.taskScopeBtn
                        }
                        onClick={() => onScopeChange("permanent")}
                    >
                        Permanent
                    </button>
                    <button
                        type="button"
                        className={
                            taskScope === "shift"
                                ? styles.taskScopeBtnActive
                                : styles.taskScopeBtn
                        }
                        onClick={() => onScopeChange("shift")}
                    >
                        This shift only
                    </button>
                </div>
            )}

            <CheckField
                className={styles.taskPermCheck}
                label="Stock Take"
                value={newStaffTaskPerms.can_stock_take}
                onChange={onUpdateStock}
                disabled={isLoading}
            />
            <CheckField
                className={styles.taskPermCheck}
                label="Receive Stock"
                value={newStaffTaskPerms.can_receive_stock}
                onChange={onUpdateReceipt}
                disabled={isLoading}
            />
        </div>
    );
};
