import { useState, useEffect } from "react";
import Modal from "../../components/layout/Modal";
import { Button } from "../../components/ui";
import styles from "./Users.module.scss";
import { usersAPI } from "../../services/users";
import type { User } from "../../types/user";

interface Props {
    isOpen: boolean;
    user: User | null;
    onClose: () => void;
    onSuccess: (updated: User) => void;
}

export default function AssignTaskModal({
    isOpen,
    user,
    onClose,
    onSuccess,
}: Props) {
    const [canStockTake, setCanStockTake] = useState(
        () => user?.can_stock_take ?? false,
    );
    const [canReceiveStock, setCanReceiveStock] = useState(
        () => user?.can_receive_stock ?? false,
    );
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Sync checkboxes whenever the modal opens for a (different) user
    useEffect(() => {
        if (isOpen && user) {
            setCanStockTake(user.can_stock_take ?? false);
            setCanReceiveStock(user.can_receive_stock ?? false);
            setError(null);
        }
    }, [isOpen, user]);

    const handleClose = () => {
        setError(null);
        onClose();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setIsLoading(true);
        setError(null);
        try {
            const res = await usersAPI.assignTask(user.id, {
                can_stock_take: canStockTake,
                can_receive_stock: canReceiveStock,
            });
            onSuccess(res.data);
            handleClose();
        } catch (err: unknown) {
            const msg =
                (
                    err as {
                        response?: {
                            data?: { error?: string; detail?: string };
                        };
                    }
                )?.response?.data?.error ??
                (err as { response?: { data?: { detail?: string } } })?.response
                    ?.data?.detail ??
                "Failed to update task permissions.";
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            title={`Assign Tasks — ${user?.username ?? user?.email ?? ""}`}
            onClose={handleClose}
        >
            {user?.role !== "staff" && (
                <div
                    className={styles.error}
                    style={{ margin: "0 0 16px", padding: "12px 16px" }}
                >
                    Task permissions can only be assigned to staff users. This
                    user has role "{user?.role}".
                </div>
            )}

            <form onSubmit={handleSubmit}>
                {error && (
                    <div className={styles.error} style={{ marginBottom: 16 }}>
                        {error}
                    </div>
                )}

                <div className={styles.taskCheckboxList}>
                    <label className={styles.taskCheckbox}>
                        <input
                            type="checkbox"
                            checked={canStockTake}
                            disabled={user?.role !== "staff"}
                            onChange={(e) => setCanStockTake(e.target.checked)}
                        />
                        <span>
                            <strong>Stock Take</strong>
                            <small>
                                Allow this staff member to perform stock takes
                            </small>
                        </span>
                    </label>

                    <label className={styles.taskCheckbox}>
                        <input
                            type="checkbox"
                            checked={canReceiveStock}
                            disabled={user?.role !== "staff"}
                            onChange={(e) =>
                                setCanReceiveStock(e.target.checked)
                            }
                        />
                        <span>
                            <strong>Receive Stock</strong>
                            <small>
                                Allow this staff member to receive incoming
                                stock
                            </small>
                        </span>
                    </label>
                </div>

                <div className={styles.modalFooter}>
                    <Button
                        type="button"
                        variant="outline"
                        onClick={handleClose}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        disabled={isLoading || user?.role !== "staff"}
                    >
                        {isLoading ? "Saving…" : "Save"}
                    </Button>
                </div>
            </form>
        </Modal>
    );
}
