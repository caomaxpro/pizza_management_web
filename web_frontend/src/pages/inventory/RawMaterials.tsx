import { useState } from "react";
import styles from "./RawMaterials.module.scss";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    BarChart,
    Bar,
} from "recharts";

interface InventoryItem {
    id: number;
    name: string;
    currentStock: number;
    minThreshold: number;
    maxThreshold: number;
    unit: string;
    description: string;
}

interface InventoryLog {
    date: string;
    quantity: number;
    change: number;
}

// Sample inventory items
const INVENTORY_ITEMS: InventoryItem[] = [
    {
        id: 1,
        name: "Pork Meat",
        currentStock: 45,
        minThreshold: 20,
        maxThreshold: 100,
        unit: "kg",
        description: "Fresh pork meat for pizza toppings",
    },
    {
        id: 2,
        name: "Mozzarella Cheese",
        currentStock: 35,
        minThreshold: 25,
        maxThreshold: 80,
        unit: "kg",
        description: "High quality mozzarella cheese",
    },
    {
        id: 3,
        name: "Tomato Sauce",
        currentStock: 60,
        minThreshold: 30,
        maxThreshold: 150,
        unit: "l",
        description: "Italian tomato sauce base",
    },
    {
        id: 4,
        name: "Pizza Dough",
        currentStock: 15,
        minThreshold: 10,
        maxThreshold: 50,
        unit: "kg",
        description: "Pre-made pizza dough",
    },
];

// Sample history data for each item
const INVENTORY_HISTORY: Record<number, InventoryLog[]> = {
    1: [
        { date: "Jan 1", quantity: 30, change: 10 },
        { date: "Jan 2", quantity: 35, change: 5 },
        { date: "Jan 3", quantity: 40, change: 5 },
        { date: "Jan 4", quantity: 38, change: -2 },
        { date: "Jan 5", quantity: 42, change: 4 },
        { date: "Jan 6", quantity: 45, change: 3 },
        { date: "Jan 7", quantity: 45, change: 0 },
    ],
    2: [
        { date: "Jan 1", quantity: 20, change: 0 },
        { date: "Jan 2", quantity: 25, change: 5 },
        { date: "Jan 3", quantity: 28, change: 3 },
        { date: "Jan 4", quantity: 32, change: 4 },
        { date: "Jan 5", quantity: 34, change: 2 },
        { date: "Jan 6", quantity: 35, change: 1 },
        { date: "Jan 7", quantity: 35, change: 0 },
    ],
    3: [
        { date: "Jan 1", quantity: 40, change: 10 },
        { date: "Jan 2", quantity: 45, change: 5 },
        { date: "Jan 3", quantity: 50, change: 5 },
        { date: "Jan 4", quantity: 55, change: 5 },
        { date: "Jan 5", quantity: 58, change: 3 },
        { date: "Jan 6", quantity: 60, change: 2 },
        { date: "Jan 7", quantity: 60, change: 0 },
    ],
    4: [
        { date: "Jan 1", quantity: 5, change: 0 },
        { date: "Jan 2", quantity: 8, change: 3 },
        { date: "Jan 3", quantity: 12, change: 4 },
        { date: "Jan 4", quantity: 14, change: 2 },
        { date: "Jan 5", quantity: 15, change: 1 },
        { date: "Jan 6", quantity: 15, change: 0 },
        { date: "Jan 7", quantity: 15, change: 0 },
    ],
};

export default function RawMaterials() {
    const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(
        INVENTORY_ITEMS[0],
    );

    const getStockStatus = (item: InventoryItem) => {
        if (item.currentStock < item.minThreshold) return "⚠️ LOW";
        if (item.currentStock > item.maxThreshold) return "⛔ FULL";
        return "✅ OK";
    };

    const getStatusColor = (item: InventoryItem) => {
        if (item.currentStock < item.minThreshold) return "#ff6b6b";
        if (item.currentStock > item.maxThreshold) return "#ffa500";
        return "#51cf66";
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>🛢️ Raw Materials & Inventory</h1>
                <p className={styles.subtitle}>
                    Manage raw materials and track stock levels
                </p>
            </div>

            <div className={styles.content}>
                {/* Current Stock Overview */}
                <div className={styles.overviewSection}>
                    <h2>📦 Current Stock Overview</h2>
                    <div className={styles.stockGrid}>
                        {INVENTORY_ITEMS.map((item) => (
                            <div
                                key={item.id}
                                className={`${styles.stockCard} ${
                                    selectedItem?.id === item.id
                                        ? styles.selected
                                        : ""
                                }`}
                                onClick={() => setSelectedItem(item)}
                            >
                                <div className={styles.cardHeader}>
                                    <h3>{item.name}</h3>
                                    <span
                                        className={styles.status}
                                        style={{
                                            backgroundColor:
                                                getStatusColor(item),
                                        }}
                                    >
                                        {getStockStatus(item)}
                                    </span>
                                </div>
                                <div className={styles.cardContent}>
                                    <div className={styles.quantity}>
                                        <span className={styles.value}>
                                            {item.currentStock}
                                        </span>
                                        <span className={styles.unit}>
                                            {item.unit}
                                        </span>
                                    </div>
                                    <div className={styles.thresholds}>
                                        <small>
                                            Min: {item.minThreshold} {item.unit}
                                        </small>
                                        <small>
                                            Max: {item.maxThreshold} {item.unit}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Detailed Chart Section */}
                {selectedItem && (
                    <div className={styles.chartSection}>
                        <div className={styles.chartHeader}>
                            <h2>📈 Stock History: {selectedItem.name}</h2>
                            <p className={styles.description}>
                                {selectedItem.description}
                            </p>
                        </div>

                        <div className={styles.chartsContainer}>
                            {/* Line Chart - Stock Quantity Over Time */}
                            <div className={styles.chartBox}>
                                <h3>Stock Quantity Trend</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart
                                        data={
                                            INVENTORY_HISTORY[
                                                selectedItem.id
                                            ] || []
                                        }
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="quantity"
                                            stroke="#8884d8"
                                            strokeWidth={2}
                                            dot={{
                                                fill: "#8884d8",
                                                r: 4,
                                            }}
                                            name={`Stock (${selectedItem.unit})`}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Bar Chart - Daily Changes */}
                            <div className={styles.chartBox}>
                                <h3>Daily Stock Changes</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart
                                        data={
                                            INVENTORY_HISTORY[
                                                selectedItem.id
                                            ] || []
                                        }
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar
                                            dataKey="change"
                                            fill="#82ca9d"
                                            name={`Change (${selectedItem.unit})`}
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Item Details */}
                        <div className={styles.detailsSection}>
                            <div className={styles.detailsGrid}>
                                <div className={styles.detailBox}>
                                    <span className={styles.label}>
                                        Current Stock:
                                    </span>
                                    <span className={styles.value}>
                                        {selectedItem.currentStock}{" "}
                                        {selectedItem.unit}
                                    </span>
                                </div>
                                <div className={styles.detailBox}>
                                    <span className={styles.label}>
                                        Min Threshold:
                                    </span>
                                    <span className={styles.value}>
                                        {selectedItem.minThreshold}{" "}
                                        {selectedItem.unit}
                                    </span>
                                </div>
                                <div className={styles.detailBox}>
                                    <span className={styles.label}>
                                        Max Capacity:
                                    </span>
                                    <span className={styles.value}>
                                        {selectedItem.maxThreshold}{" "}
                                        {selectedItem.unit}
                                    </span>
                                </div>
                                <div className={styles.detailBox}>
                                    <span className={styles.label}>
                                        Stock %:
                                    </span>
                                    <span className={styles.value}>
                                        {Math.round(
                                            (selectedItem.currentStock /
                                                selectedItem.maxThreshold) *
                                                100,
                                        )}
                                        %
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
