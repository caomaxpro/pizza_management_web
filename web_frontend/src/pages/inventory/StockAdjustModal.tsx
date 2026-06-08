import { useState } from "react";
import { Button } from "@components/ui";
import styles from "./StockAdjustModal.module.scss";
import type { InventoryItem } from "../../services/inventory";

interface StockAdjustModalProps {
    open: boolean;
    item: InventoryItem | null;
    reasonType: "receipt" | "stock_take";
    onClose: () => void;
    onSubmit: (quantityChange: number, note: string) => Promise<void>;
    isLoading?: boolean;
}

export default function StockAdjustModal({
    open,
    item,
    reasonType,
    onClose,
    onSubmit,
    isLoading = false,
}: StockAdjustModalProps) {
    const [quantity, setQuantity] = useState("");
    const [note, setNote] = useState("");
    const [error, setError] = useState("");

    if (!open || !item) return null;

    const isReceipt = reasonType === "receipt";

    const handleSubmit = async () => {
        const qty = parseFloat(quantity);
        if (isNaN(qty) || qty === 0) {
            setError("Quantity must be a non-zero number.");
            return;
        }
        if (isReceipt && qty <= 0) {
            setError("Receipt quantity must be positive.");
            return;
        }
        setError("");
        await onSubmit(qty, note.trim());
        setQuantity("");
        setNote("");
    };

    const handleClose = () => {
        setQuantity("");
        setNote("");
        setError("");
        onClose();
    };

    return (
        <div className={styles.overlay} onClick={handleClose}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2 className={styles.title}>
                        {isReceipt ? "Receipt" : "Stock Take"}
                    </h2>
                    <button className={styles.closeBtn} onClick={handleClose}>
                        ×
                    </button>
                </div>

                <span
                    className={
                        isReceipt ? styles.badgeReceipt : styles.badgeStockTake
                    }
                >
                    {isReceipt ? "receipt" : "stock_take"}
                </span>

                <div>
                    <div className={styles.itemName}>{item.name}</div>
                    <div className={styles.unit}>
                        Current stock: {item.current_stock} {item.unit}
                    </div>
                </div>

                <div className={styles.fieldGroup}>
                    <label className={styles.label}>
                        {isReceipt ? "Quantity to add" : "Quantity adjustment"}
                    </label>
                    <input
                        className={styles.input}
                        type="number"
                        step="any"
                        placeholder={isReceipt ? "e.g. 50" : "e.g. +10 or -5"}
                        value={quantity}
                        onChange={(e) => {
                            setQuantity(e.target.value);
                            setError("");
                        }}
                        autoFocus
                    />
                    <span className={styles.hint}>
                        {isReceipt
                            ? "Positive number — stock received into inventory."
                            : "Positive or negative — corrects actual stock level."}
                    </span>
                    {error && <span className={styles.error}>{error}</span>}
                </div>

                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Note (optional)</label>
                    <textarea
                        className={styles.textarea}
                        placeholder="e.g. Morning delivery, batch #42"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        rows={2}
                    />
                </div>

                <div className={styles.actions}>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleClose}
                        disabled={isLoading}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={handleSubmit}
                        disabled={isLoading}
                    >
                        {isLoading
                            ? "Saving…"
                            : isReceipt
                              ? "Confirm Receipt"
                              : "Confirm Stock Take"}
                    </Button>
                </div>
            </div>
        </div>
    );
}
