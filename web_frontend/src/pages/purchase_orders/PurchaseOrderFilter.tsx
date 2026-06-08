import React, { useState } from "react";
import styles from "./PurchaseOrderFilter.module.scss";

export interface PurchaseOrderFilters {
    status?: string;
    provider?: string;
    dateFrom?: string;
    dateTo?: string;
}

interface PurchaseOrderFilterProps {
    onFilter: (filters: PurchaseOrderFilters) => void;
}

export default function PurchaseOrderFilter({
    onFilter,
}: PurchaseOrderFilterProps) {
    const [status, setStatus] = useState<string>("");
    const [provider, setProvider] = useState<string>("");
    const [dateFrom, setDateFrom] = useState<string>("");
    const [dateTo, setDateTo] = useState<string>("");

    const apply = () => {
        onFilter({ status, provider, dateFrom, dateTo });
    };

    const clear = () => {
        setStatus("");
        setProvider("");
        setDateFrom("");
        setDateTo("");
        onFilter({});
    };

    return (
        <div className={styles.filterContainer}>
            <div className={styles.row}>
                <label className={styles.label}>Status</label>
                <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                >
                    <option value="">Any</option>
                    <option value="pending">Pending</option>
                    <option value="ordered">Ordered</option>
                    <option value="paid">Paid</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>

            <div className={styles.row}>
                <label className={styles.label}>Provider</label>
                <input
                    type="text"
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    placeholder="Provider name"
                />
            </div>

            <div className={styles.row}>
                <label className={styles.label}>Date From</label>
                <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                />
                <label className={styles.label}>To</label>
                <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                />
            </div>

            <div className={styles.actions}>
                <button
                    type="button"
                    className={styles.btnPrimary}
                    onClick={apply}
                >
                    Apply
                </button>
                <button
                    type="button"
                    className={styles.btnOutline}
                    onClick={clear}
                >
                    Clear
                </button>
            </div>
        </div>
    );
}
