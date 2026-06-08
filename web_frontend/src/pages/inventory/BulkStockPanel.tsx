import { useState, useCallback, useMemo } from "react";
import type { InventoryItem } from "../../services/inventory";
import inventoryAPI from "../../services/inventory";
import MessageCard from "../../components/form/fields/MessageCard";
import styles from "./BulkStockPanel.module.scss";

interface BulkStockPanelProps {
    items: InventoryItem[];
    initialReason: "receipt" | "stock_take";
    onClose: () => void;
    onSuccess: (updatedItems: InventoryItem[]) => void;
}

const SOFT_WARN_ABSOLUTE = 10_000;
const SOFT_WARN_RELATIVE = 10;

export default function BulkStockPanel({
    items,
    initialReason,
    onClose,
    onSuccess,
}: BulkStockPanelProps) {
    const [reasonType, setReasonType] = useState<"receipt" | "stock_take">(
        initialReason,
    );
    const [qtys, setQtys] = useState<Record<number, string>>({});
    const [notes, setNotes] = useState<Record<number, string>>({});
    const [isLoading, setIsLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState("");
    const [errorMsg, setErrorMsg] = useState<string | string[] | null>(null);
    const [lastSubmitted, setLastSubmitted] = useState<number[] | null>(null);
    const [errorItemIds, setErrorItemIds] = useState<Set<number>>(new Set());

    const filledEntries = useMemo(
        () =>
            items
                .filter((item) => {
                    const v = qtys[item.id];
                    return (
                        v !== undefined &&
                        v !== "" &&
                        Number(v) !== item.current_stock
                    );
                })
                .map((item) => ({
                    inventory_id: item.id,
                    quantity_change: Number(qtys[item.id]) - item.current_stock,
                    reason_type: reasonType,
                    reason_detail: notes[item.id]?.trim() || undefined,
                })),
        [qtys, notes, reasonType, items],
    );

    const handleQty = useCallback((id: number, val: string) => {
        setQtys((prev) => ({ ...prev, [id]: val }));
        setSuccessMsg("");
        setErrorMsg(null);
        setErrorItemIds(new Set());
    }, []);

    const handleNote = useCallback((id: number, val: string) => {
        setNotes((prev) => ({ ...prev, [id]: val }));
    }, []);

    const handleClear = useCallback(() => {
        setQtys({});
        setNotes({});
        setSuccessMsg("");
        setErrorMsg(null);
        setErrorItemIds(new Set());
    }, []);

    const handleSubmit = useCallback(async () => {
        if (filledEntries.length === 0) return;

        // Validate receipt entries
        if (reasonType === "receipt") {
            const invalidReceipt = filledEntries.filter(
                (e) => e.quantity_change < 0,
            );
            if (invalidReceipt.length > 0) {
                const errorIds = new Set(
                    invalidReceipt.map((e) => e.inventory_id),
                );
                setErrorItemIds(errorIds);
                const lines = invalidReceipt
                    .map((e) => {
                        const item = items.find((i) => i.id === e.inventory_id);
                        return `• ${item?.name ?? `#${e.inventory_id}`}: cannot decrease stock in receipt mode`;
                    })
                    .join("\n");
                setErrorMsg(lines);
                return;
            }
        }

        const suspicious = filledEntries.filter((e) => {
            const item = items.find((i) => i.id === e.inventory_id);
            if (!item) return false;
            const abs = Math.abs(e.quantity_change);
            return (
                abs > SOFT_WARN_ABSOLUTE ||
                (item.current_stock > 0 &&
                    abs > SOFT_WARN_RELATIVE * item.current_stock)
            );
        });
        if (suspicious.length > 0) {
            const lines = suspicious
                .map((e) => {
                    const item = items.find((i) => i.id === e.inventory_id);
                    const sign = e.quantity_change > 0 ? "+" : "";
                    return `• ${item?.name ?? `#${e.inventory_id}`}: ${sign}${e.quantity_change}`;
                })
                .join("\n");
            const ok = window.confirm(
                `⚠ The following quantities seem unusually large:\n${lines}\n\nContinue anyway?`,
            );
            if (!ok) return;
        }

        try {
            setIsLoading(true);
            setErrorMsg(null);
            const result = await inventoryAPI.bulkCreateLogs(filledEntries);
            const logIds = Array.isArray(result) ? result.map((l) => l.id) : [];
            setLastSubmitted(logIds);

            const affectedIds = filledEntries.map((e) => e.inventory_id);
            const refreshed = await Promise.all(
                affectedIds.map((id) => inventoryAPI.get(id)),
            );
            onSuccess(refreshed);

            setQtys({});
            setNotes({});
            const inventoriesUpdated = new Set(affectedIds).size;
            setSuccessMsg(
                `Done — ${logIds.length} log(s) created, ${inventoriesUpdated} item(s) updated.`,
            );
        } catch (err: unknown) {
            const data = (
                err as {
                    response?: {
                        data?: { error?: string; errors?: { msg?: string }[] };
                    };
                }
            )?.response?.data;
            if (data?.errors) {
                setErrorMsg(data.errors.map((e) => e.msg ?? String(e)));
            } else {
                setErrorMsg(
                    data?.error ??
                        "Submit failed. Please check the values and try again.",
                );
            }
        } finally {
            setIsLoading(false);
        }
    }, [filledEntries, items, onSuccess, reasonType]);

    const handleRevert = useCallback(async () => {
        if (!lastSubmitted || lastSubmitted.length === 0) return;
        const ok = window.confirm(
            `Revert last operation? This will undo ${lastSubmitted.length} log entry(s) just created.`,
        );
        if (!ok) return;
        try {
            setIsLoading(true);
            setErrorMsg(null);
            const reverseLogs = await inventoryAPI.revertLogs(lastSubmitted);
            const inventoryIds = [
                ...new Set(reverseLogs.map((l) => l.inventory)),
            ];
            const refreshed = await Promise.all(
                inventoryIds.map((id) => inventoryAPI.get(id)),
            );
            onSuccess(refreshed);
            setLastSubmitted(null);
            setSuccessMsg(
                `Reverted — ${lastSubmitted.length} log entry(s) reversed.`,
            );
        } catch (err: unknown) {
            const data = (err as { response?: { data?: { error?: string } } })
                ?.response?.data;
            setErrorMsg(data?.error ?? "Revert failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
    }, [lastSubmitted, onSuccess]);

    const isReceipt = reasonType === "receipt";

    return (
        <>
            {/* Messages - Outside Panel */}
            {successMsg && (
                <div style={{ marginBottom: "0.5rem" }}>
                    <MessageCard
                        message={successMsg}
                        variant="success"
                        dismissible={false}
                    />
                </div>
            )}
            {errorMsg && (
                <div style={{ marginBottom: "0.5rem" }}>
                    <MessageCard
                        message={errorMsg}
                        variant="error"
                        dismissible
                        onDismiss={() => {
                            setErrorMsg(null);
                            setErrorItemIds(new Set());
                        }}
                    />
                </div>
            )}
            <div className={styles.panel}>
                {/* Header */}
                <div className={styles.panelHeader}>
                    <p className={styles.panelTitle}>
                        {isReceipt ? "Bulk Receipt" : "Bulk Stock Take"}
                    </p>

                    {/* Reason toggle */}
                    <div className={styles.toggleGroup}>
                        <button
                            className={
                                reasonType === "receipt"
                                    ? `${styles.toggleBtnActive} ${styles.receipt}`
                                    : styles.toggleBtn
                            }
                            onClick={() => setReasonType("receipt")}
                        >
                            Receipt
                        </button>
                        <button
                            className={
                                reasonType === "stock_take"
                                    ? `${styles.toggleBtnActive} ${styles.stock_take}`
                                    : styles.toggleBtn
                            }
                            onClick={() => setReasonType("stock_take")}
                        >
                            Stock Take
                        </button>
                    </div>

                    <button className={styles.closeBtn} onClick={onClose}>
                        ×
                    </button>
                </div>

                {/* Table */}
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Item</th>
                                <th>Unit</th>
                                <th style={{ textAlign: "right" }}>Stock</th>
                                <th style={{ textAlign: "right" }}>
                                    New Count
                                </th>
                                <th>Note</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => {
                                const qtyVal = qtys[item.id] ?? "";
                                const newValue = Number(qtyVal);
                                const isFilled =
                                    qtyVal !== "" &&
                                    newValue !== item.current_stock;
                                const willReorder =
                                    isFilled && newValue <= item.min_threshold;
                                const isError = errorItemIds.has(item.id);
                                return (
                                    <tr
                                        key={item.id}
                                        style={{
                                            backgroundColor: isError
                                                ? "#fee2e2"
                                                : undefined,
                                        }}
                                    >
                                        <td style={{ color: "#9ca3af" }}>
                                            {idx + 1}
                                        </td>
                                        <td>
                                            <span style={{ fontWeight: 500 }}>
                                                {item.name}
                                            </span>
                                        </td>
                                        <td className={styles.stockCell}>
                                            {item.unit}
                                        </td>
                                        <td style={{ textAlign: "right" }}>
                                            {isFilled ? (
                                                <>
                                                    <span
                                                        style={{
                                                            color: "#9ca3af",
                                                        }}
                                                    >
                                                        {item.current_stock}
                                                    </span>
                                                    <span
                                                        style={{
                                                            color: "#9ca3af",
                                                        }}
                                                    >
                                                        {" → "}
                                                    </span>
                                                    <span
                                                        style={{
                                                            fontWeight: 500,
                                                            color: willReorder
                                                                ? "#ef4444"
                                                                : "#10b981",
                                                        }}
                                                    >
                                                        {newValue}
                                                    </span>
                                                </>
                                            ) : (
                                                <span
                                                    style={{ color: "#374151" }}
                                                >
                                                    {item.current_stock}
                                                </span>
                                            )}
                                        </td>
                                        <td style={{ textAlign: "right" }}>
                                            <input
                                                type="number"
                                                step="any"
                                                min="0"
                                                className={
                                                    isFilled
                                                        ? `${styles.qtyInput} ${isReceipt ? styles.filled : styles.filledTake}`
                                                        : styles.qtyInput
                                                }
                                                placeholder={String(
                                                    item.current_stock,
                                                )}
                                                value={qtyVal}
                                                onChange={(e) =>
                                                    handleQty(
                                                        item.id,
                                                        e.target.value,
                                                    )
                                                }
                                            />
                                        </td>
                                        <td>
                                            <input
                                                type="text"
                                                className={styles.noteInput}
                                                placeholder="optional note"
                                                value={notes[item.id] ?? ""}
                                                onChange={(e) =>
                                                    handleNote(
                                                        item.id,
                                                        e.target.value,
                                                    )
                                                }
                                            />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* Footer */}
                <div className={styles.footer}>
                    <span className={styles.summary}>
                        {filledEntries.length > 0 ? (
                            <>
                                <span className={styles.summaryCount}>
                                    {filledEntries.length}
                                </span>{" "}
                                item
                                {filledEntries.length !== 1 ? "s" : ""} will be
                                updated
                            </>
                        ) : (
                            "Enter quantities to adjust stock"
                        )}
                    </span>

                    {successMsg &&
                        lastSubmitted &&
                        lastSubmitted.length > 0 && (
                            <button
                                className={styles.btnRevert}
                                onClick={handleRevert}
                                disabled={isLoading}
                            >
                                Revert
                            </button>
                        )}

                    <button
                        className={styles.btnClear}
                        onClick={handleClear}
                        disabled={isLoading || filledEntries.length === 0}
                    >
                        Clear
                    </button>

                    <button
                        className={`${styles.btnSubmit} ${styles[reasonType]}`}
                        onClick={handleSubmit}
                        disabled={isLoading || filledEntries.length === 0}
                    >
                        {isLoading
                            ? "Saving…"
                            : isReceipt
                              ? `Confirm Receipt (${filledEntries.length})`
                              : `Confirm Stock Take (${filledEntries.length})`}
                    </button>
                </div>
            </div>
        </>
    );
}
