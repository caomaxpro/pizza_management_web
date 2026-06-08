/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useRef } from "react";
import { CheckCircle } from "@phosphor-icons/react";
import styles from "./Reports.module.scss";
import inventoryAPI from "../../services/inventory";
import SelectField from "../../components/form/fields/SelectField";
import ToggleField, {
    type ToggleOption,
} from "../../components/form/fields/ToggleField";
import type { InventoryItem, InventoryLog } from "../../services/inventory";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line,
    Legend,
    LabelList,
} from "recharts";
import { getStockColor } from "./helpers";

export function InventoryTab() {
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
    const [logs, setLogs] = useState<InventoryLog[]>([]);
    const [logsLoading, setLogsLoading] = useState(false);
    const [timePeriod, setTimePeriod] = useState<"day" | "week" | "month">(
        "day",
    );
    const changesChartRef = useRef<HTMLDivElement>(null);
    const cumulativeChartRef = useRef<HTMLDivElement>(null);
    const stockChartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        inventoryAPI
            .list()
            .then((itemList) => {
                setItems(itemList);
                if (itemList.length > 0) {
                    setSelectedItemId(itemList[0].id);
                }
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    // Fetch logs for selected item
    useEffect(() => {
        if (!selectedItemId) return;
        let mounted = true;
        const currentRequestId = selectedItemId; // Track which item's logs we're fetching

        setLogs([]);
        setLogsLoading(true);

        const fetchLogs = async () => {
            try {
                const data = await inventoryAPI.getLogs(selectedItemId);

                // Only update if:
                // 1. Component still mounted
                // 2. This is the latest request (prevent race condition if user switched items fast)
                if (!mounted || currentRequestId !== selectedItemId) {
                    return;
                }

                // Sort by created_at ascending
                const sorted = [...data].sort(
                    (a, b) =>
                        new Date(a.created_at).getTime() -
                        new Date(b.created_at).getTime(),
                );
                setLogs(sorted);
            } catch (e) {
                console.error("Failed to fetch logs:", e);
                // Only clear if still mounted and same request
                if (mounted && currentRequestId === selectedItemId) {
                    setLogs([]);
                }
            } finally {
                // Only update loading state if still mounted and this was the latest request
                if (mounted && currentRequestId === selectedItemId) {
                    setLogsLoading(false);
                }
            }
        };

        fetchLogs();

        return () => {
            mounted = false;
        };
    }, [selectedItemId]);

    if (loading) return <div className={styles.loading}>Loading…</div>;

    const sorted = [...items].sort(
        (a, b) => (a.stock_percentage ?? 0) - (b.stock_percentage ?? 0),
    );
    const needsReorder = items.filter((i) => i.needs_reorder);
    const outOfStock = items.filter((i) => i.current_stock === 0);

    const chartData = sorted.slice(0, 20).map((i) => ({
        name: i.name.length > 20 ? i.name.slice(0, 20) + "…" : i.name,
        pct: Math.round(i.stock_percentage ?? 0),
        fill: getStockColor(Math.round(i.stock_percentage ?? 0)),
    }));

    // Transform logs for time-period changes chart
    const getTimeKey = (date: Date): string => {
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");

        if (timePeriod === "day") {
            const year = date.getFullYear();
            return `${year}-${month}-${day}`;
        } else if (timePeriod === "week") {
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay());
            const wYear = weekStart.getFullYear();
            const wMonth = String(weekStart.getMonth() + 1).padStart(2, "0");
            const wDay = String(weekStart.getDate()).padStart(2, "0");
            return `${wYear}-${wMonth}-${wDay}`;
        } else {
            // month
            const year = date.getFullYear();
            return `${year}-${month}`;
        }
    };

    const periodChangesMap = new Map<string, number>();
    logs.forEach((log) => {
        const key = getTimeKey(new Date(log.created_at));
        periodChangesMap.set(
            key,
            (periodChangesMap.get(key) ?? 0) + log.quantity_change,
        );
    });

    const periodChangesData = Array.from(periodChangesMap.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([key, change]) => {
            let displayLabel = key;
            if (timePeriod === "week") {
                const [, month, day] = key.split("-");
                displayLabel = `Week of ${month}-${day}`;
            } else if (timePeriod === "month") {
                const [year, month] = key.split("-");
                const monthNames = [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ];
                displayLabel = `${monthNames[parseInt(month) - 1]} ${year}`;
            } else {
                displayLabel = key.slice(-5);
            }

            return {
                label: displayLabel,
                change: Math.round(change * 100) / 100,
            };
        });

    // Calculate cumulative stock over time
    const cumulativeData = [...logs]
        .sort(
            (a, b) =>
                new Date(a.created_at).getTime() -
                new Date(b.created_at).getTime(),
        )
        .reduce(
            (acc, log) => {
                const newStock = (acc.lastStock ?? 0) + log.quantity_change;
                const date = new Date(log.created_at).toLocaleDateString(
                    "en-CA",
                    {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                    },
                );
                acc.lastStock = newStock;
                // Only add new entry if date changed or stock value changed
                if (
                    acc.data.length === 0 ||
                    date !== acc.data[acc.data.length - 1].date
                ) {
                    acc.data.push({
                        date,
                        stock: Math.round(newStock * 100) / 100,
                    });
                } else {
                    // Update the last entry for the same date
                    acc.data[acc.data.length - 1].stock =
                        Math.round(newStock * 100) / 100;
                }
                return acc;
            },
            {
                data: [] as Array<{ date: string; stock: number }>,
                lastStock: 0,
            },
        ).data;

    const selectedItem = items.find((i) => i.id === selectedItemId);

    // Custom Tooltip with dynamic positioning
    const CustomTooltip = ({
        active,
        payload,
        coordinate,
        unit,
        borderColor,
        containerRef,
        labelKey,
    }: any) => {
        if (!active || !payload || !coordinate || !containerRef?.current)
            return null;

        const rect = containerRef.current.getBoundingClientRect();
        const tooltipWidth = 180;
        const tooltipHeight = labelKey ? 52 : 36;
        const gap = 8;

        // For LineCharts (no labelKey), add offsets to align with mouse cursor
        // For BarChart (Stock Levels), use clean positioning above the bar
        const xOffset = labelKey ? 0 : 25;
        const yOffset = labelKey ? 0 : 10;

        const x = rect.left + coordinate.x - tooltipWidth / 2 + xOffset;
        const y = rect.top + coordinate.y - tooltipHeight - gap + yOffset;

        return (
            <div
                style={{
                    position: "fixed",
                    left: `${x}px`,
                    top: `${y}px`,
                    width: `${tooltipWidth}px`,
                    backgroundColor: "#1a1a2e",
                    border: `1px solid ${borderColor}`,
                    borderRadius: "8px",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
                    padding: "6px 10px",
                    zIndex: 1001,
                    color: "#fff",
                    fontSize: "12px",
                    pointerEvents: "none",
                }}
            >
                {labelKey && payload[0]?.payload?.[labelKey] && (
                    <div
                        style={{
                            fontSize: "11px",
                            opacity: 0.7,
                            marginBottom: "2px",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                        }}
                    >
                        {payload[0].payload[labelKey]}
                    </div>
                )}
                <div>
                    {payload[0]?.value} {unit}
                </div>
            </div>
        );
    };

    return (
        <div className={styles.tabContent}>
            {/* Summary cards */}
            <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <span className={styles.statValue}>{items.length}</span>
                    <span className={styles.statLabel}>Total Items</span>
                </div>
                <div className={`${styles.statCard} ${styles.statWarn}`}>
                    <span className={styles.statValue}>
                        {needsReorder.length}
                    </span>
                    <span className={styles.statLabel}>Need Reorder</span>
                </div>
                <div className={`${styles.statCard} ${styles.statDanger}`}>
                    <span className={styles.statValue}>
                        {outOfStock.length}
                    </span>
                    <span className={styles.statLabel}>Out of Stock</span>
                </div>
                <div className={`${styles.statCard} ${styles.statOk}`}>
                    <span className={styles.statValue}>
                        {items.filter((i) => !i.needs_reorder).length}
                    </span>
                    <span className={styles.statLabel}>Stock OK</span>
                </div>
            </div>

            {/* Stock level chart */}
            <div className={styles.chartSection}>
                <h3>Stock Levels (% of max capacity)</h3>
                <div className={styles.chartBox}>
                    <div ref={stockChartRef} style={{ width: "100%" }}>
                        <ResponsiveContainer
                            width="100%"
                            height={Math.max(280, chartData.length * 36)}
                        >
                            <BarChart
                                data={chartData}
                                layout="vertical"
                                margin={{
                                    top: 5,
                                    right: 60,
                                    left: 5,
                                    bottom: 5,
                                }}
                            >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    type="number"
                                    domain={[0, 100]}
                                    unit="%"
                                />
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    width={165}
                                    tick={{ fontSize: 12 }}
                                />
                                <Tooltip
                                    content={(props) => (
                                        <CustomTooltip
                                            {...props}
                                            unit="%"
                                            borderColor="#888"
                                            containerRef={stockChartRef}
                                            labelKey="name"
                                        />
                                    )}
                                />
                                <Bar
                                    dataKey="pct"
                                    name="Stock %"
                                    radius={[0, 6, 6, 0]}
                                    fill="#8884d8"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Purchase priority table */}
            <div className={styles.tableSection}>
                <h3>Purchase Priority (sorted by lowest stock first)</h3>
                <div className={styles.tableWrap}>
                    <table>
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Unit</th>
                                <th>Current</th>
                                <th>Min</th>
                                <th>Max</th>
                                <th>Stock %</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((item) => {
                                const pct = Math.round(
                                    item.stock_percentage ?? 0,
                                );
                                return (
                                    <tr
                                        key={item.id}
                                        className={
                                            item.needs_reorder
                                                ? styles.rowWarn
                                                : ""
                                        }
                                    >
                                        <td className={styles.itemName}>
                                            {item.name}
                                        </td>
                                        <td>{item.unit}</td>
                                        <td>{item.current_stock}</td>
                                        <td>{item.min_threshold}</td>
                                        <td>{item.max_threshold ?? "—"}</td>
                                        <td>
                                            <div
                                                className={styles.progressWrap}
                                            >
                                                <div
                                                    className={
                                                        styles.progressBar
                                                    }
                                                    style={{
                                                        width: `${Math.min(pct, 100)}%`,
                                                        backgroundColor:
                                                            getStockColor(pct),
                                                    }}
                                                />
                                                <span>{pct}%</span>
                                            </div>
                                        </td>
                                        <td>
                                            <span
                                                className={styles.badge}
                                                style={{
                                                    backgroundColor:
                                                        getStockColor(pct),
                                                }}
                                            >
                                                {pct < 30 ? (
                                                    "⚠ Low"
                                                ) : pct < 60 ? (
                                                    "⚡ Medium"
                                                ) : (
                                                    <>
                                                        <CheckCircle
                                                            size={16}
                                                            weight="fill"
                                                        />{" "}
                                                        Good
                                                    </>
                                                )}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Inventory Logs Section */}
            {selectedItem && (
                <div className={styles.chartSection}>
                    <h3>Stock Change Timeline</h3>
                    <SelectField
                        label="Select Item"
                        value={String(selectedItemId ?? "")}
                        onChange={(value) => setSelectedItemId(Number(value))}
                        options={items.map((item) => ({
                            value: String(item.id),
                            label: `${item.name} (${item.unit})`,
                        }))}
                        placeholder="Select an item"
                    />

                    {/* Time Period Selector */}
                    <ToggleField
                        value={timePeriod}
                        onChange={(value) =>
                            setTimePeriod(value as "day" | "week" | "month")
                        }
                        options={
                            [
                                { value: "day", label: "Daily" },
                                { value: "week", label: "Weekly" },
                                { value: "month", label: "Monthly" },
                            ] as ToggleOption[]
                        }
                        size="md"
                        style={{ marginBottom: "16px" }}
                    />

                    {/* Changes Chart */}
                    <div>
                        <h4 style={{ marginBottom: "12px" }}>
                            {timePeriod === "day"
                                ? "Daily"
                                : timePeriod === "week"
                                  ? "Weekly"
                                  : "Monthly"}{" "}
                            Quantity Changes
                        </h4>
                        <div className={styles.chartWrapper}>
                            <div
                                className={`${styles.chartLoadingOverlay} ${
                                    !logsLoading ? styles.hidden : ""
                                }`}
                            >
                                <div className={styles.loading}>
                                    <div className={styles.spinner} />
                                    <span>Loading chart…</span>
                                </div>
                            </div>
                            <div
                                ref={changesChartRef}
                                className={`${styles.chartContent} ${
                                    logsLoading ? styles.loading : ""
                                }`}
                            >
                                <ResponsiveContainer width="100%" height={280}>
                                    <LineChart data={periodChangesData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="label" />
                                        <YAxis />
                                        <Tooltip
                                            content={(props) => (
                                                <CustomTooltip
                                                    {...props}
                                                    unit={
                                                        selectedItem?.unit || ""
                                                    }
                                                    borderColor="#8b5cf6"
                                                    containerRef={
                                                        changesChartRef
                                                    }
                                                />
                                            )}
                                            cursor={{
                                                fill: "rgba(139, 92, 246, 0.1)",
                                            }}
                                        />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="change"
                                            stroke="#8b5cf6"
                                            strokeWidth={2}
                                            dot={{ fill: "#8b5cf6", r: 4 }}
                                            activeDot={{ r: 6 }}
                                            isAnimationActive={false}
                                            name="Quantity Change"
                                        >
                                            <LabelList
                                                dataKey="change"
                                                position="top"
                                                formatter={(v: any) => `${v}`}
                                                fill="#8b5cf6"
                                                fontSize={11}
                                                offset={8}
                                            />
                                        </Line>
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Cumulative Stock Chart */}
                    <div>
                        <h4 style={{ marginBottom: "12px" }}>
                            Cumulative Stock Level
                        </h4>
                        <div className={styles.chartWrapper}>
                            <div
                                className={`${styles.chartLoadingOverlay} ${
                                    !logsLoading ? styles.hidden : ""
                                }`}
                            >
                                <div className={styles.loading}>
                                    <div className={styles.spinner} />
                                    <span>Loading chart…</span>
                                </div>
                            </div>
                            <div
                                ref={cumulativeChartRef}
                                className={`${styles.chartContent} ${
                                    logsLoading ? styles.loading : ""
                                }`}
                            >
                                <ResponsiveContainer width="100%" height={280}>
                                    <LineChart data={cumulativeData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <Tooltip
                                            content={(props) => (
                                                <CustomTooltip
                                                    {...props}
                                                    unit={
                                                        selectedItem?.unit || ""
                                                    }
                                                    borderColor="#16c784"
                                                    containerRef={
                                                        cumulativeChartRef
                                                    }
                                                />
                                            )}
                                            cursor={{
                                                fill: "rgba(22, 199, 132, 0.1)",
                                            }}
                                        />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="stock"
                                            stroke="#16c784"
                                            strokeWidth={2}
                                            dot={{ fill: "#16c784", r: 4 }}
                                            activeDot={{ r: 6 }}
                                            isAnimationActive={false}
                                        >
                                            <LabelList
                                                dataKey="stock"
                                                position="top"
                                                formatter={(v: any) => `${v}`}
                                                fill="#16c784"
                                                fontSize={11}
                                                offset={8}
                                            />
                                        </Line>
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Empty state */}
                    {!logsLoading && logs.length === 0 && (
                        <div className={styles.chartBox}>
                            No stock changes recorded
                        </div>
                    )}

                    {/* Logs Table */}
                    {!logsLoading && logs.length > 0 && (
                        <div className={styles.tableWrap}>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Date & Time</th>
                                        <th>Type</th>
                                        <th>Quantity Change</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log) => (
                                        <tr key={log.id}>
                                            <td>
                                                {new Date(
                                                    log.created_at,
                                                ).toLocaleString("vi-VN")}
                                            </td>
                                            <td>
                                                <span
                                                    className={styles.badge}
                                                    style={{
                                                        backgroundColor:
                                                            log.reason_type ===
                                                            "receipt"
                                                                ? "#16c784"
                                                                : "#ffa500",
                                                    }}
                                                >
                                                    {log.reason_type_display ||
                                                        log.reason_type}
                                                </span>
                                            </td>
                                            <td
                                                style={{
                                                    color:
                                                        log.quantity_change > 0
                                                            ? "#16c784"
                                                            : "#ff6b6b",
                                                    fontWeight: 500,
                                                }}
                                            >
                                                {log.quantity_change > 0
                                                    ? "+"
                                                    : ""}
                                                {log.quantity_change}{" "}
                                                {selectedItem.unit}
                                            </td>
                                            <td>{log.reason_detail || "—"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
