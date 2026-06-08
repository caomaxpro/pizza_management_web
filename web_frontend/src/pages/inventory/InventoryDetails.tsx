import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import inventoryAPI from "../../services/inventory";
import type { InventoryItem, InventoryLog } from "../../services/inventory";
import { useInventoryWebSocket } from "../../hooks/useInventoryWebSocket";
import { Button } from "@components/ui";
import styles from "./InventoryDetails.module.scss";
import StockAdjustModal from "./StockAdjustModal";

export default function InventoryDetails() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [item, setItem] = useState<InventoryItem | null>(null);
    const [logs, setLogs] = useState<InventoryLog[]>([]);
    const [adjustReason, setAdjustReason] = useState<
        "receipt" | "stock_take" | null
    >(null);
    const [isAdjusting, setIsAdjusting] = useState(false);

    useEffect(() => {
        if (!id) return;
        let mounted = true;
        const numId = Number(id);
        inventoryAPI
            .get(numId)
            .then((data) => mounted && setItem(data))
            .catch(() => mounted && navigate("/inventory"));
        inventoryAPI
            .getLogs(numId)
            .then((data) => mounted && setLogs(data))
            .catch(() => {});
        return () => {
            mounted = false;
        };
    }, [id, navigate]);

    // WebSocket support for real-time updates
    const handleWSUpdate = useCallback(
        (updatedItem: InventoryItem) => {
            if (updatedItem.id === Number(id)) {
                setItem(updatedItem);
            }
        },
        [id],
    );
    const handleWSDelete = useCallback(
        (deletedId: number) => {
            if (deletedId === Number(id)) {
                navigate("/inventory");
            }
        },
        [id, navigate],
    );
    useInventoryWebSocket(
        handleWSUpdate,
        handleWSDelete,
        () => {}, // onCreate not needed for details page
    );

    const handleAdjustSubmit = useCallback(
        async (quantityChange: number, note: string) => {
            if (!id || !item || !adjustReason) return;
            try {
                setIsAdjusting(true);
                const numId = Number(id);
                await inventoryAPI.bulkCreateLogs([
                    {
                        inventory_id: numId,
                        quantity_change: quantityChange,
                        reason_type: adjustReason,
                        reason_detail: note || undefined,
                    },
                ]);
                const [updated, updatedLogs] = await Promise.all([
                    inventoryAPI.get(numId),
                    inventoryAPI.getLogs(numId),
                ]);
                setItem(updated);
                setLogs(updatedLogs);
                setAdjustReason(null);
            } catch (error) {
                console.error("Stock adjustment failed:", error);
            } finally {
                setIsAdjusting(false);
            }
        },
        [id, item, adjustReason],
    );

    if (!item) {
        return <div style={{ padding: 32 }}>Loading...</div>;
    }

    const stockPct = item.max_threshold
        ? Math.round((item.current_stock / item.max_threshold) * 100)
        : null;

    return (
        <>
            <div className={styles.container}>
                {/* Header */}
                <div className={styles.header}>
                    <div>
                        <h2 className={styles.title}>{item.name}</h2>
                        <p className={styles.subtitle}>
                            {item.description || "No description"}
                        </p>
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button
                            variant="outline"
                            onClick={() => setAdjustReason("receipt")}
                        >
                            Receipt
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => setAdjustReason("stock_take")}
                        >
                            Stock Take
                        </Button>
                        <Button variant="outline" onClick={() => navigate(-1)}>
                            Back
                        </Button>
                    </div>
                </div>

                {/* Details list - vertical display without card borders */}
                <div className={styles.detailsList}>
                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Current Stock</div>
                        <div className={styles.detailValue}>
                            {item.current_stock} {item.unit}
                        </div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Min Threshold</div>
                        <div className={styles.detailValue}>
                            {item.min_threshold} {item.unit}
                        </div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Max Capacity</div>
                        <div className={styles.detailValue}>
                            {item.max_threshold
                                ? `${item.max_threshold} ${item.unit}`
                                : "—"}
                        </div>
                    </div>

                    {stockPct !== null && (
                        <div className={styles.detailRow}>
                            <div className={styles.detailKey}>Stock %</div>
                            <div className={styles.detailValue}>
                                {stockPct}%
                            </div>
                        </div>
                    )}

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Unit</div>
                        <div className={styles.detailValue}>{item.unit}</div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Provider</div>
                        <div className={styles.detailValue}>
                            {item.provider?.name || "—"}
                        </div>
                    </div>

                    {item.provider && (
                        <div className={styles.detailRow}>
                            <div className={styles.detailKey}>
                                Provider Category
                            </div>
                            <div className={styles.detailValue}>
                                {item.provider.category_display ||
                                    item.provider.category}
                            </div>
                        </div>
                    )}

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Status</div>
                        <div
                            className={
                                item.is_active
                                    ? styles.badgeActive
                                    : styles.badgeInactive
                            }
                        >
                            {item.is_active ? "Active" : "Inactive"}
                        </div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Reorder Needed</div>
                        <div
                            className={
                                item.needs_reorder
                                    ? styles.badgeLow
                                    : styles.badgeOk
                            }
                        >
                            {item.needs_reorder ? "⚠ Yes" : "✓ No"}
                        </div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Created At</div>
                        <div className={styles.detailValue}>
                            {new Date(item.created_at).toLocaleDateString()}
                        </div>
                    </div>

                    <div className={styles.detailRow}>
                        <div className={styles.detailKey}>Updated At</div>
                        <div className={styles.detailValue}>
                            {new Date(item.updated_at).toLocaleDateString()}
                        </div>
                    </div>
                </div>

                {/* Inventory Logs */}
                <div className={styles.logsSection}>
                    <h3>Stock History ({logs.length} changes)</h3>
                    {logs.length === 0 ? (
                        <p className={styles.empty}>
                            No stock changes recorded.
                        </p>
                    ) : (
                        <table className={styles.logsTable}>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Change</th>
                                    <th>Type</th>
                                    <th>Note</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map((log) => (
                                    <tr key={log.id}>
                                        <td>
                                            {new Date(
                                                log.created_at,
                                            ).toLocaleDateString()}
                                        </td>
                                        <td>
                                            {new Date(
                                                log.created_at,
                                            ).toLocaleTimeString()}
                                        </td>
                                        <td
                                            className={
                                                log.quantity_change >= 0
                                                    ? styles.positive
                                                    : styles.negative
                                            }
                                        >
                                            {log.quantity_change >= 0
                                                ? "+"
                                                : ""}
                                            {log.quantity_change} {item.unit}
                                        </td>
                                        <td>
                                            {log.reason_type_display ??
                                                log.reason_type}
                                        </td>
                                        <td>{log.reason_detail ?? "—"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
            <StockAdjustModal
                open={adjustReason !== null}
                item={item}
                reasonType={adjustReason ?? "receipt"}
                onClose={() => setAdjustReason(null)}
                onSubmit={handleAdjustSubmit}
                isLoading={isAdjusting}
            />
        </>
    );
}
