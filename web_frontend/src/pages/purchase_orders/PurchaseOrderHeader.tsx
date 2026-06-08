import React from "react";
import styles from "./PurchaseOrderHeader.module.scss";
import { Button } from "../../components/ui";

interface PurchaseOrderHeaderProps {
    onCreate: () => void;
    total: number;
}

export default function PurchaseOrderHeader({
    onCreate,
    total,
}: PurchaseOrderHeaderProps) {
    return (
        <div className={styles.headerContainer}>
            <div>
                <h1>Purchase Orders</h1>
                <p className={styles.subtitle}>
                    Manage purchase orders and suppliers ({total} total)
                </p>
            </div>
            <Button variant="primary" size="md" onClick={onCreate}>
                + Create Purchase Order
            </Button>
        </div>
    );
}
