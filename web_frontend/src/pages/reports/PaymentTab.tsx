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
    Cell,
} from "recharts";
import { PeriodSelector } from "./PeriodSelector";
import {
    getStatusColor,
    getPaymentStatusColor,
    getPaymentMethodColor,
    fmt,
} from "./helpers";
import type { RevenueReport, PaymentReport } from "./types";

export function PaymentTab() {
    const [days, setDays] = useState("30");
    const [report, setReport] = useState<RevenueReport | null>(null);
    const [paymentReport, setPaymentReport] = useState<PaymentReport | null>(
        null,
    );
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [revRes, payRes] = await Promise.all([
                API.get(`/orders/report/revenue/?days=${days}`),
                API.get(`/payments/report/?days=${days}`),
            ]);
            setReport(revRes.data);
            setPaymentReport(payRes.data);
        } catch {
            setError("Failed to load payment data.");
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
            ) : report ? (
                <>
                    {/* Summary */}
                    <div className={styles.statsGrid}>
                        <div className={`${styles.statCard} ${styles.statOk}`}>
                            <span className={styles.statValue}>
                                {fmt(report.total_revenue)}
                            </span>
                            <span className={styles.statLabel}>
                                Total Revenue
                            </span>
                        </div>
                        <div className={`${styles.statCard} ${styles.statOk}`}>
                            <span className={styles.statValue}>
                                {fmt(report.net_revenue)}
                            </span>
                            <span className={styles.statLabel}>
                                Net Revenue
                            </span>
                        </div>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {report.total_orders}
                            </span>
                            <span className={styles.statLabel}>
                                Total Orders
                            </span>
                        </div>
                        <div className={styles.statCard}>
                            <span className={styles.statValue}>
                                {fmt(report.average_order_value)}
                            </span>
                            <span className={styles.statLabel}>
                                Avg Order Value
                            </span>
                        </div>
                        {paymentReport && (
                            <div className={styles.statCard}>
                                <span className={styles.statValue}>
                                    {paymentReport.total_payments}
                                </span>
                                <span className={styles.statLabel}>
                                    Total Payments
                                </span>
                            </div>
                        )}
                        {report.total_cancellation_fees > 0 && (
                            <div
                                className={`${styles.statCard} ${styles.statDanger}`}
                            >
                                <span className={styles.statValue}>
                                    {fmt(report.total_cancellation_fees)}
                                </span>
                                <span className={styles.statLabel}>
                                    Cancellation Fees
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Daily revenue chart with order count */}
                    {report.daily_revenue.length > 0 && (
                        <div className={styles.chartSection}>
                            <h3>Daily Revenue & Order Count</h3>
                            <div className={styles.chartBox}>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart
                                        data={report.daily_revenue}
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
                                            yAxisId="revenue"
                                            orientation="left"
                                            tickFormatter={(v) =>
                                                `${(v / 1000).toFixed(0)}k`
                                            }
                                        />
                                        <YAxis
                                            yAxisId="orders"
                                            orientation="right"
                                            allowDecimals={false}
                                            tick={{ fontSize: 11 }}
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
                                            yAxisId="revenue"
                                            type="monotone"
                                            dataKey="total"
                                            name="Revenue"
                                            stroke="#10b981"
                                            strokeWidth={2}
                                            dot={{ r: 3 }}
                                        />
                                        <Line
                                            yAxisId="orders"
                                            type="monotone"
                                            dataKey="order_count"
                                            name="Orders"
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

                    {/* Daily delivered orders & revenue */}
                    {report.daily_revenue.length > 0 && (
                        <div className={styles.chartSection}>
                            <h3>Daily Delivered Orders & Revenue</h3>
                            <div className={styles.chartBox}>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart
                                        data={report.daily_revenue}
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
                                                    name === "Orders"
                                                        ? [v, name]
                                                        : [fmt(v), name]) as any
                                            }
                                        />
                                        <Legend />
                                        <Line
                                            yAxisId="orders"
                                            type="monotone"
                                            dataKey="order_count"
                                            name="Orders"
                                            stroke="#10b981"
                                            strokeWidth={2}
                                            dot={{ r: 3 }}
                                        />
                                        <Line
                                            yAxisId="revenue"
                                            type="monotone"
                                            dataKey="total"
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

                    {/* Payment method breakdown */}
                    {paymentReport &&
                        paymentReport.payment_method_breakdown.length > 0 && (
                            <div className={styles.chartSection}>
                                <h3>Payment Method Breakdown</h3>
                                <div className={styles.chartBox}>
                                    <ResponsiveContainer
                                        width="100%"
                                        height={260}
                                    >
                                        <BarChart
                                            data={
                                                paymentReport.payment_method_breakdown
                                            }
                                            layout="vertical"
                                            margin={{
                                                top: 5,
                                                right: 80,
                                                left: 90,
                                                bottom: 5,
                                            }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis
                                                type="number"
                                                allowDecimals={false}
                                            />
                                            <YAxis
                                                type="category"
                                                dataKey="label"
                                                tick={{ fontSize: 12 }}
                                                width={85}
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
                                            <Bar
                                                dataKey="count"
                                                name="Transactions"
                                                radius={[0, 4, 4, 0]}
                                            >
                                                {paymentReport.payment_method_breakdown.map(
                                                    (entry, i) => (
                                                        <Cell
                                                            key={i}
                                                            fill={getPaymentMethodColor(
                                                                entry.method,
                                                            )}
                                                        />
                                                    ),
                                                )}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className={styles.tableWrap}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Method</th>
                                                <th>Transactions</th>
                                                <th>Total Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {paymentReport.payment_method_breakdown.map(
                                                (m) => (
                                                    <tr key={m.method}>
                                                        <td>
                                                            <span
                                                                className={
                                                                    styles.badge
                                                                }
                                                                style={{
                                                                    backgroundColor:
                                                                        getPaymentMethodColor(
                                                                            m.method,
                                                                        ),
                                                                }}
                                                            >
                                                                {m.label}
                                                            </span>
                                                        </td>
                                                        <td>{m.count}</td>
                                                        <td>{fmt(m.total)}</td>
                                                    </tr>
                                                ),
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                    {/* Revenue by status chart + table */}
                    {report.revenue_by_status.length > 0 && (
                        <div className={styles.chartSection}>
                            <h3>Revenue by Order Status</h3>
                            <div className={styles.chartBox}>
                                <ResponsiveContainer width="100%" height={280}>
                                    <BarChart
                                        data={report.revenue_by_status}
                                        margin={{
                                            top: 5,
                                            right: 30,
                                            left: 10,
                                            bottom: 5,
                                        }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="status" />
                                        <YAxis
                                            tickFormatter={(v) =>
                                                `${(v / 1000).toFixed(0)}k`
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
                                        <Bar
                                            dataKey="total"
                                            name="Revenue"
                                            radius={[4, 4, 0, 0]}
                                        >
                                            {report.revenue_by_status.map(
                                                (entry, i) => (
                                                    <Cell
                                                        key={i}
                                                        fill={getStatusColor(
                                                            entry.status,
                                                        )}
                                                    />
                                                ),
                                            )}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            <div className={styles.tableWrap}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Status</th>
                                            <th>Orders</th>
                                            <th>Total Revenue</th>
                                            <th>Avg Order</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {report.revenue_by_status.map((s) => (
                                            <tr key={s.status}>
                                                <td>
                                                    <span
                                                        className={styles.badge}
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
                                                <td>{fmt(s.total)}</td>
                                                <td>{fmt(s.average)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Payment status breakdown */}
                    {paymentReport &&
                        paymentReport.payment_status_breakdown.length > 0 && (
                            <div className={styles.tableSection}>
                                <h3>Payments by Status</h3>
                                <div className={styles.tableWrap}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Status</th>
                                                <th>Count</th>
                                                <th>Total Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {paymentReport.payment_status_breakdown.map(
                                                (s) => (
                                                    <tr key={s.status}>
                                                        <td>
                                                            <span
                                                                className={
                                                                    styles.badge
                                                                }
                                                                style={{
                                                                    backgroundColor:
                                                                        getPaymentStatusColor(
                                                                            s.status,
                                                                        ),
                                                                }}
                                                            >
                                                                {s.status}
                                                            </span>
                                                        </td>
                                                        <td>{s.count}</td>
                                                        <td>{fmt(s.total)}</td>
                                                    </tr>
                                                ),
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                    {/* Refund statistics */}
                    {paymentReport &&
                        paymentReport.refund_stats.total_refunds > 0 && (
                            <div className={styles.chartSection}>
                                <h3>Refund Statistics</h3>
                                <div className={styles.statsGrid}>
                                    <div className={styles.statCard}>
                                        <span className={styles.statValue}>
                                            {
                                                paymentReport.refund_stats
                                                    .total_refunds
                                            }
                                        </span>
                                        <span className={styles.statLabel}>
                                            Total Refunds
                                        </span>
                                    </div>
                                    <div
                                        className={`${styles.statCard} ${styles.statDanger}`}
                                    >
                                        <span className={styles.statValue}>
                                            {fmt(
                                                paymentReport.refund_stats
                                                    .total_amount,
                                            )}
                                        </span>
                                        <span className={styles.statLabel}>
                                            Total Refunded
                                        </span>
                                    </div>
                                    {paymentReport.refund_stats
                                        .requested_count > 0 && (
                                        <div
                                            className={`${styles.statCard} ${styles.statWarn}`}
                                        >
                                            <span className={styles.statValue}>
                                                {
                                                    paymentReport.refund_stats
                                                        .requested_count
                                                }
                                            </span>
                                            <span className={styles.statLabel}>
                                                Requested
                                            </span>
                                        </div>
                                    )}
                                    {paymentReport.refund_stats.pending_count >
                                        0 && (
                                        <div
                                            className={`${styles.statCard} ${styles.statWarn}`}
                                        >
                                            <span className={styles.statValue}>
                                                {
                                                    paymentReport.refund_stats
                                                        .pending_count
                                                }
                                            </span>
                                            <span className={styles.statLabel}>
                                                Pending Review
                                            </span>
                                        </div>
                                    )}
                                    {paymentReport.refund_stats
                                        .processing_count > 0 && (
                                        <div className={styles.statCard}>
                                            <span className={styles.statValue}>
                                                {
                                                    paymentReport.refund_stats
                                                        .processing_count
                                                }
                                            </span>
                                            <span className={styles.statLabel}>
                                                Processing
                                            </span>
                                        </div>
                                    )}
                                    <div
                                        className={`${styles.statCard} ${styles.statOk}`}
                                    >
                                        <span className={styles.statValue}>
                                            {
                                                paymentReport.refund_stats
                                                    .processed_count
                                            }
                                        </span>
                                        <span className={styles.statLabel}>
                                            Processed
                                        </span>
                                    </div>
                                    {paymentReport.refund_stats.rejected_count >
                                        0 && (
                                        <div
                                            className={`${styles.statCard} ${styles.statDanger}`}
                                        >
                                            <span className={styles.statValue}>
                                                {
                                                    paymentReport.refund_stats
                                                        .rejected_count
                                                }
                                            </span>
                                            <span className={styles.statLabel}>
                                                Rejected
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                    {/* Cancelled orders summary */}
                    {report.cancelled_orders.count > 0 && (
                        <div className={styles.chartSection}>
                            <h3>Cancelled Orders</h3>
                            <div className={styles.statsGrid}>
                                <div
                                    className={`${styles.statCard} ${styles.statDanger}`}
                                >
                                    <span className={styles.statValue}>
                                        {report.cancelled_orders.count}
                                    </span>
                                    <span className={styles.statLabel}>
                                        Cancelled
                                    </span>
                                </div>
                                <div
                                    className={`${styles.statCard} ${styles.statDanger}`}
                                >
                                    <span className={styles.statValue}>
                                        {fmt(
                                            report.cancelled_orders
                                                .total_order_value,
                                        )}
                                    </span>
                                    <span className={styles.statLabel}>
                                        Lost Revenue
                                    </span>
                                </div>
                                <div
                                    className={`${styles.statCard} ${styles.statWarn}`}
                                >
                                    <span className={styles.statValue}>
                                        {fmt(
                                            report.cancelled_orders
                                                .total_cancellation_fees,
                                        )}
                                    </span>
                                    <span className={styles.statLabel}>
                                        Fees Collected
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <div className={styles.empty}>No payment data available.</div>
            )}
        </div>
    );
}
