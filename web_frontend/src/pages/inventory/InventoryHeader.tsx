import React from "react";
import styles from "./InventoryHeader.module.scss";
import { Button } from "../../components/ui";

interface InventoryHeaderProps {
    onCreate: () => void;
    total: number;
    onBulkReceipt?: () => void;
    onBulkStockTake?: () => void;
}

export default function InventoryHeader({
    onCreate,
    total,
    onBulkReceipt,
    onBulkStockTake,
}: InventoryHeaderProps) {
    return (
        <div className={styles.headerContainer}>
            <div>
                <h1>Inventory</h1>
                <p className={styles.subtitle}>
                    Manage raw material stock levels ({total} total)
                </p>
            </div>
            <div
                style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    flexWrap: "wrap",
                }}
            >
                {onBulkReceipt && (
                    <Button variant="outline" size="md" onClick={onBulkReceipt}>
                        Bulk Receipt
                    </Button>
                )}
                {onBulkStockTake && (
                    <Button
                        variant="outline"
                        size="md"
                        onClick={onBulkStockTake}
                    >
                        Bulk Stock Take
                    </Button>
                )}
                <Button variant="primary" size="md" onClick={onCreate}>
                    + Add Inventory Item
                </Button>
            </div>
        </div>
    );
}
