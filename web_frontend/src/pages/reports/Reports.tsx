import { useState, type ReactNode } from "react";
import { ChartBar, ShoppingCart, CurrencyDollar } from "@phosphor-icons/react";
import styles from "./Reports.module.scss";
import { InventoryTab } from "./InventoryTab";
import { OrdersTab } from "./OrdersTab";
import { PaymentTab } from "./PaymentTab";

// ── Main ─────────────────────────────────────────────────────────────────────

type TabKey = "inventory" | "orders" | "payment";

const TABS: { key: TabKey; label: string; icon: ReactNode }[] = [
    { key: "inventory", label: "Inventory", icon: <ChartBar size={16} /> },
    { key: "orders", label: "Orders", icon: <ShoppingCart size={16} /> },
    { key: "payment", label: "Payment", icon: <CurrencyDollar size={16} /> },
];

export default function Reports() {
    const [activeTab, setActiveTab] = useState<TabKey>("inventory");

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>
                    <ChartBar size={24} weight="bold" /> Reports & Analytics
                </h1>
                <p className={styles.subtitle}>
                    Inventory usage, order trends, and payment statistics
                </p>
            </div>

            <nav className={styles.tabs}>
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        className={`${styles.tabBtn} ${activeTab === tab.key ? styles.activeTab : ""}`}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        <span
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 8,
                            }}
                        >
                            {tab.icon}
                            {tab.label}
                        </span>
                    </button>
                ))}
            </nav>

            <div className={styles.tabPanel}>
                {activeTab === "inventory" && <InventoryTab />}
                {activeTab === "orders" && <OrdersTab />}
                {activeTab === "payment" && <PaymentTab />}
            </div>
        </div>
    );
}
