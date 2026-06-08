/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback } from "react";
import styles from "./Reports.module.scss";
import API from "../../services/api";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
} from "recharts";
import { PeriodSelector } from "./PeriodSelector";
import { getStatusColor, fmt } from "./helpers";
import type { OrdersReport, ItemsReport } from "./types";

export function OrdersTab() {
    const [days, setDays] = useState("30");
    const [ordersReport, setOrdersReport] = useState<OrdersReport | null>(null);
    const [itemsReport, setItemsReport] = useState<ItemsReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [oRes, iRes] = await Promise.all([
                API.get(`/orders/report/orders/?days=${days}`),
                API.get(`/orders/report/items/?days=${days}&limit=10`),
            ]);
            setOrdersReport(oRes.data);
            setItemsReport(iRes.data);
        } catch {
            setError("Failed to load order data.");
        } finally {
            setLoading(false);
        }
    }, [days]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return (
        <div className={styles.tabContent}>
            <PeriodSelector value={days} onChange={setDays} />

            {loading ? (
                <div className={styles.loading}>Loading…</div>
            ) : error ? (
                <div className={styles.error}>{error}</div>
            ) : (
                <>
                    {/* Summary */}
                    <div className={styles.statsGrid}>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {ordersReport?.total_orders ?? 0}
                            </span>
                            <span className={styles.statLabel}>
                                Total Orders
                            </span>
                        </div>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {fmt(ordersReport?.average_order_value ?? 0)}
                            </span>
                            <span className={styles.statLabel}>
                                Avg Order Value
                            </span>
                        </div>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {itemsReport?.total_items_ordered ?? 0}
                            </span>
                            <span className={styles.statLabel}>
                                Items Ordered
                            </span>
                        </div>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {itemsReport?.total_unique_items_ordered ?? 0}
                            </span>
                            <span className={styles.statLabel}>
                                Unique Items
                            </span>
                        </div>
                    </div>

                    {/* Daily delivered orders & revenue */}
                    {ordersReport &&
                        ordersReport.orders_last_30_days.length > 0 && (
                            <div className={styles.chartSection}>
                                <h3>Daily Delivered Orders & Revenue</h3>
                                <div className={styles.chartBox}>
                                    <ResponsiveContainer
                                        width="100%"
                                        height={300}
                                    >
                                        <LineChart
                                            data={ordersReport.orders_last_30_days.map(
                                                (d) => ({
                                                    ...d,
                                                    revenue:
                                                        d.count *
                                                        (ordersReport?.average_order_value ??
                                                            0),
                                                }),
                                            )}
                                            margin={{
                                                top: 10,
                                                right: 40,
                                                left: 10,
                                                bottom: 5,
                                            }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 11 }}
                                            />
                                            <YAxis
                                                yAxisId="orders"
                                                orientation="left"
                                                allowDecimals={false}
                                            />
                                            <YAxis
                                                yAxisId="revenue"
                                                orientation="right"
                                                tickFormatter={(v) =>
                                                    `$${(v / 1000).toFixed(0)}k`
                                                }
                                            />
                                            <Tooltip
                                                formatter={
                                                    ((v: any, name: any) =>
                                                        name === "Revenue"
                                                            ? [fmt(v), name]
                                                            : [v, name]) as any
                                                }
                                            />
                                            <Legend />
                                            <Line
                                                yAxisId="orders"
                                                type="monotone"
                                                dataKey="count"
                                                name="Delivered Orders"
                                                stroke="#10b981"
                                                strokeWidth={2}
                                                dot={{ r: 3 }}
                                            />
                                            <Line
                                                yAxisId="revenue"
                                                type="monotone"
                                                dataKey="revenue"
                                                name="Revenue"
                                                stroke="#8b5cf6"
                                                strokeWidth={2}
                                                strokeDasharray="4 2"
                                                dot={{ r: 2 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                    {/* Top items chart */}
                    {itemsReport && itemsReport.top_items.length > 0 && (
                        <div className={styles.chartSection}>
                            <h3>Top Ordered Items</h3>
                            <div className={styles.chartBox}>
                                <ResponsiveContainer width="100%" height={340}>
                                    <BarChart
                                        data={itemsReport.top_items}
                                        margin={{
                                            top: 10,
                                            right: 30,
                                            left: 0,
                                            bottom: 60,
                                        }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="item_name"
                                            tick={{ fontSize: 11 }}
                                            angle={-35}
                                            textAnchor="end"
                                        />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar
                                            dataKey="total_quantity"
                                            name="Qty Ordered"
                                            fill="#8b5cf6"
                                            radius={[4, 4, 0, 0]}
                                        />
                                        <Bar
                                            dataKey="times_ordered"
                                            name="Times Ordered"
                                            fill="#06b6d4"
                                            radius={[4, 4, 0, 0]}
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            <div className={styles.tableWrap}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Item</th>
                                            <th>Total Qty</th>
                                            <th>Times Ordered</th>
                                            <th>Total Revenue</th>
                                            <th>Avg Price</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {itemsReport.top_items.map(
                                            (item, i) => (
                                                <tr key={i}>
                                                    <td className={styles.rank}>
                                                        #{i + 1}
                                                    </td>
                                                    <td
                                                        className={
                                                            styles.itemName
                                                        }
                                                    >
                                                        {item.item_name}
                                                    </td>
                                                    <td>
                                                        {item.total_quantity}
                                                    </td>
                                                    <td>
                                                        {item.times_ordered}
                                                    </td>
                                                    <td>
                                                        {fmt(
                                                            item.total_revenue,
                                                        )}
                                                    </td>
                                                    <td>
                                                        {fmt(
                                                            item.avg_unit_price,
                                                        )}
                                                    </td>
                                                </tr>
                                            ),
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Orders trend */}
                    {ordersReport &&
                        ordersReport.orders_last_30_days.length > 0 && (
                            <div className={styles.chartSection}>
                                <h3>Orders Trend (Last 30 Days)</h3>
                                <div className={styles.chartBox}>
                                    <ResponsiveContainer
                                        width="100%"
                                        height={280}
                                    >
                                        <LineChart
                                            data={
                                                ordersReport.orders_last_30_days
                                            }
                                            margin={{
                                                top: 5,
                                                right: 30,
                                                left: 0,
                                                bottom: 5,
                                            }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 11 }}
                                            />
                                            <YAxis />
                                            <Tooltip />
                                            <Line
                                                type="monotone"
                                                dataKey="count"
                                                name="Orders"
                                                stroke="#8b5cf6"
                                                strokeWidth={2}
                                                dot={{ r: 3 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                    {/* Status breakdown */}
                    {ordersReport &&
                        ordersReport.status_breakdown.length > 0 && (
                            <div className={styles.tableSection}>
                                <h3>Orders by Status</h3>
                                <div className={styles.tableWrap}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Status</th>
                                                <th>Count</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {ordersReport.status_breakdown.map(
                                                (s) => (
                                                    <tr key={s.status}>
                                                        <td>
                                                            <span
                                                                className={
                                                                    styles.badge
                                                                }
                                                                style={{
                                                                    backgroundColor:
                                                                        getStatusColor(
                                                                            s.status,
                                                                        ),
                                                                }}
                                                            >
                                                                {s.status}
                                                            </span>
                                                        </td>
                                                        <td>{s.count}</td>
                                                    </tr>
                                                ),
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                </>
            )}
        </div>
    );
}
