import type { User } from "../../types/user";
import { PencilSimple } from "@phosphor-icons/react";
import Modal from "../../components/layout/Modal";
import { Button } from "../../components/ui";
import styles from "./UserDetailsModal.module.scss";

interface Props {
    isOpen: boolean;
    user: User | null;
    onClose: () => void;
    onEdit?: (user: User) => void;
}

export default function UserDetailsModal({
    isOpen,
    user,
    onClose,
    onEdit,
}: Props) {
    if (!user) return null;

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return "—";
        return new Date(dateStr).toLocaleDateString("vi-VN", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const getRoleBadgeColor = (role?: string) => {
        switch (role) {
            case "admin":
                return styles.roleBadgeAdmin;
            case "manager":
                return styles.roleBadgeManager;
            case "staff":
                return styles.roleBadgeStaff;
            case "user":
                return styles.roleBadgeUser;
            default:
                return styles.roleBadgeUser;
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="User Details">
            <div className={styles.container}>
                {/* Basic Info */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>Basic Information</h3>
                    <div className={styles.grid}>
                        <div className={styles.field}>
                            <label className={styles.label}>Username</label>
                            <div className={styles.value}>
                                {user.username || "—"}
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Email</label>
                            <div className={styles.value}>{user.email}</div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Name</label>
                            <div className={styles.value}>
                                {user.name || "—"}
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Phone Number</label>
                            <div className={styles.value}>
                                {user.phone_number || "—"}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Role & Permissions */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>Role & Permissions</h3>
                    <div className={styles.grid}>
                        <div className={styles.field}>
                            <label className={styles.label}>Role</label>
                            <div className={styles.value}>
                                <span
                                    className={`${styles.roleBadge} ${getRoleBadgeColor(user.role)}`}
                                >
                                    {user.role?.toUpperCase() || "USER"}
                                </span>
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Status</label>
                            <div className={styles.value}>
                                <span
                                    className={`${styles.statusBadge} ${user.is_active ? styles.statusActive : styles.statusInactive}`}
                                >
                                    {user.is_active ? "Active" : "Inactive"}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Task Permissions */}
                    <div className={styles.taskPerms}>
                        <label className={styles.label}>Task Permissions</label>
                        <div className={styles.permsList}>
                            <div className={styles.permItem}>
                                <input
                                    type="checkbox"
                                    checked={user.can_stock_take ?? false}
                                    disabled
                                    id="stock-take"
                                />
                                <label htmlFor="stock-take">
                                    Can Stock Take
                                </label>
                            </div>
                            <div className={styles.permItem}>
                                <input
                                    type="checkbox"
                                    checked={user.can_receive_stock ?? false}
                                    disabled
                                    id="receive-stock"
                                />
                                <label htmlFor="receive-stock">
                                    Can Receive Stock
                                </label>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Account Status */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>Account Status</h3>
                    <div className={styles.grid}>
                        <div className={styles.field}>
                            <label className={styles.label}>
                                Is Staff Member
                            </label>
                            <div className={styles.value}>
                                {user.is_staff ? "Yes" : "No"}
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Is Superuser</label>
                            <div className={styles.value}>
                                {user.is_superuser ? "Yes" : "No"}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Timestamps */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>Timestamps</h3>
                    <div className={styles.grid}>
                        <div className={styles.field}>
                            <label className={styles.label}>Date Joined</label>
                            <div className={styles.value}>
                                {formatDate(user.date_joined)}
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Created At</label>
                            <div className={styles.value}>
                                {formatDate(user.created_at)}
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Updated At</label>
                            <div className={styles.value}>
                                {formatDate(user.updated_at)}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Actions */}
                <div className={styles.actions}>
                    {onEdit && (
                        <Button
                            onClick={() => onEdit(user)}
                            variant="primary"
                            size="md"
                        >
                            <PencilSimple size={18} /> Edit User
                        </Button>
                    )}
                    <Button onClick={onClose} variant="secondary" size="md">
                        Close
                    </Button>
                </div>
            </div>
        </Modal>
    );
}
