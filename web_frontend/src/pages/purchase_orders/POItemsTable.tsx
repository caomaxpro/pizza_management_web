import React from "react";
import { Button } from "@components/ui";
import styles from "./POItemsTable.module.scss";

interface InventoryOption {
    value: string;
    label: string;
}

interface POItemRow {
    inventory: string;
    quantity: string;
    actual_unit_price: string;
}

export interface POItemPayload {
    inventory: number;
    quantity: number;
    actual_unit_price?: number;
}

interface POItemsTableProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (items: POItemPayload[]) => void;
    isLoading?: boolean;
    inventoryOptions: InventoryOption[];
}

const INITIAL_ROWS = 10;
const ADD_ROWS_COUNT = 5;

const emptyRow = (): POItemRow => ({
    inventory: "",
    quantity: "",
    actual_unit_price: "",
});

export default function POItemsTable({
    open,
    onClose,
    onSubmit,
    isLoading = false,
    inventoryOptions,
}: POItemsTableProps) {
    const [rows, setRows] = React.useState<POItemRow[]>(() =>
        Array.from({ length: INITIAL_ROWS }, emptyRow),
    );

    if (!open) return null;

    const filledRows = rows.filter((r) => r.inventory && r.quantity);

    const updateRow = (
        index: number,
        field: keyof POItemRow,
        value: string,
    ) => {
        setRows((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], [field]: value };
            return next;
        });
    };

    const removeRow = (index: number) => {
        setRows((prev) => prev.filter((_, i) => i !== index));
    };

    const handleSave = () => {
        const items: POItemPayload[] = filledRows.map((r) => ({
            inventory: Number(r.inventory),
            quantity: Number(r.quantity),
            ...(r.actual_unit_price
                ? { actual_unit_price: Number(r.actual_unit_price) }
                : {}),
        }));
        onSubmit(items);
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.panel}>
                <div className={styles.header}>
                    <h3>Add Items</h3>
                    <span className={styles.hint}>
                        {filledRows.length} row
                        {filledRows.length !== 1 ? "s" : ""} ready to save
                    </span>
                </div>

                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Inventory Item</th>
                                <th>Qty</th>
                                <th>Unit Price (optional)</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((row, i) => (
                                <tr
                                    key={i}
                                    className={
                                        row.inventory ? styles.filled : ""
                                    }
                                >
                                    <td className={styles.rowNum}>{i + 1}</td>
                                    <td>
                                        <select
                                            className={styles.selectInput}
                                            value={row.inventory}
                                            onChange={(e) =>
                                                updateRow(
                                                    i,
                                                    "inventory",
                                                    e.target.value,
                                                )
                                            }
                                        >
                                            <option value="">— select —</option>
                                            {inventoryOptions.map((opt) => (
                                                <option
                                                    key={opt.value}
                                                    value={opt.value}
                                                >
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </td>
                                    <td>
                                        <input
                                            className={styles.numInput}
                                            type="number"
                                            min={0}
                                            value={row.quantity}
                                            onChange={(e) =>
                                                updateRow(
                                                    i,
                                                    "quantity",
                                                    e.target.value,
                                                )
                                            }
                                            placeholder="0"
                                        />
                                    </td>
                                    <td>
                                        <input
                                            className={styles.numInput}
                                            type="number"
                                            min={0}
                                            step="0.01"
                                            value={row.actual_unit_price}
                                            onChange={(e) =>
                                                updateRow(
                                                    i,
                                                    "actual_unit_price",
                                                    e.target.value,
                                                )
                                            }
                                            placeholder="—"
                                        />
                                    </td>
                                    <td>
                                        <button
                                            className={styles.removeBtn}
                                            onClick={() => removeRow(i)}
                                            tabIndex={-1}
                                            type="button"
                                        >
                                            ✕
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className={styles.footer}>
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                            setRows((prev) => [
                                ...prev,
                                ...Array.from(
                                    { length: ADD_ROWS_COUNT },
                                    emptyRow,
                                ),
                            ])
                        }
                    >
                        + {ADD_ROWS_COUNT} rows
                    </Button>
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={onClose}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="button"
                            variant="primary"
                            onClick={handleSave}
                            disabled={isLoading || filledRows.length === 0}
                        >
                            {isLoading
                                ? "Saving..."
                                : `Save ${filledRows.length || ""} item${filledRows.length !== 1 ? "s" : ""}`}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
