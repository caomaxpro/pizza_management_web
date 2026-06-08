import { useMemo, useCallback, useState } from "react";
import { Button } from "../../components/ui";
import {
    BarChart,
    Bar,
    LineChart,
    Line,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import styles from "./Orders.module.scss";

interface OrderStats {
    period: string;
    total_orders: number;
    completed_orders: number;
    pending_orders: number;
    cancelled_orders: number;
    total_revenue: number;
    average_order_value: number;
    completion_rate: number;
}

interface StatusBreakdown {
    status: string;
    count: number;
    percentage: number;
}

interface RevenueMetrics {
    date: string;
    revenue: number;
    orders_count: number;
    average_value: number;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

const CHART_COLORS = ["#007bff", "#ffc107", "#28a745", "#dc3545", "#6f42c1"];

export default function OrderReports() {
    // Dummy data for chart demo
    const dummyRevenueMetrics: RevenueMetrics[] = [
        {
            date: "2024-04-01",
            revenue: 1200,
            orders_count: 30,
            average_value: 40,
        },
        {
            date: "2024-04-02",
            revenue: 900,
            orders_count: 22,
            average_value: 41,
        },
        {
            date: "2024-04-03",
            revenue: 1500,
            orders_count: 35,
            average_value: 43,
        },
        {
            date: "2024-04-04",
            revenue: 800,
            orders_count: 18,
            average_value: 44,
        },
        {
            date: "2024-04-05",
            revenue: 1700,
            orders_count: 38,
            average_value: 45,
        },
        {
            date: "2024-04-06",
            revenue: 1100,
            orders_count: 25,
            average_value: 44,
        },
        {
            date: "2024-04-07",
            revenue: 1400,
            orders_count: 32,
            average_value: 43,
        },
    ];

    const dummyStatusBreakdown: StatusBreakdown[] = [
        { status: "Completed", count: 85, percentage: 42.5 },
        { status: "Pending", count: 60, percentage: 30 },
        { status: "Processing", count: 40, percentage: 20 },
        { status: "Cancelled", count: 15, percentage: 7.5 },
    ];

    const [stats] = useState<OrderStats | null>(null);
    const [statusBreakdown] = useState<StatusBreakdown[]>(dummyStatusBreakdown);
    // Use dummy data for chart and table
    const [revenueMetrics] = useState<RevenueMetrics[]>(dummyRevenueMetrics);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sortBy, setSortBy] = useState<string>("date");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

    // Sorted metrics
    const sortedMetrics = useMemo(() => {
        const result = [...revenueMetrics];

        result.sort((a, b) => {
            let aValue: string | number = "";
            let bValue: string | number = "";

            switch (sortBy) {
                case "date":
                    aValue = new Date(a.date).getTime();
                    bValue = new Date(b.date).getTime();
                    break;
                case "revenue":
                    aValue = a.revenue;
                    bValue = b.revenue;
                    break;
                case "orders_count":
                    aValue = a.orders_count;
                    bValue = b.orders_count;
                    break;
                case "average_value":
                    aValue = a.average_value;
                    bValue = b.average_value;
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });

        return result;
    }, [revenueMetrics, sortBy, sortOrder]);

    // Pagination
    const totalCount = sortedMetrics.length;
    const totalPages = useMemo(
        () => Math.ceil(totalCount / pageSize),
        [totalCount, pageSize],
    );

    const paginatedMetrics = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = startIdx + pageSize;
        return sortedMetrics.slice(startIdx, endIdx);
    }, [sortedMetrics, currentPage, pageSize]);

    // Handle column sort
    const handleColumnSort = useCallback(
        (column: string) => {
            if (sortBy === column) {
                setSortOrder(sortOrder === "asc" ? "desc" : "asc");
            } else {
                setSortBy(column);
                setSortOrder("asc");
            }
            setCurrentPage(1);
        },
        [sortBy, sortOrder],
    );

    const getSortIcon = (column: string) => {
        if (sortBy !== column) return "⇅";
        return sortOrder === "asc" ? "↑" : "↓";
    };

    const handlePageChange = useCallback(
        (page: number) => {
            if (page >= 1 && page <= totalPages) setCurrentPage(page);
        },
        [totalPages],
    );

    const handlePageSizeChange = useCallback(
        (e: React.ChangeEvent<HTMLSelectElement>) => {
            setPageSize(Number(e.target.value));
            setCurrentPage(1);
        },
        [],
    );

    const startItem = totalCount > 0 ? (currentPage - 1) * pageSize + 1 : 0;
    const endItem = Math.min(currentPage * pageSize, totalCount);

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h1>📊 Order Reports</h1>
                    <p className={styles.subtitle}>
                        Analytics and insights about order performance
                    </p>
                </div>
            </div>

            {/* Summary Cards */}
            {stats && (
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "16px",
                        marginBottom: "24px",
                    }}
                >
                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #28a745",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Total Orders
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#333",
                            }}
                        >
                            {stats.total_orders}
                        </div>
                    </div>

                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #17a2b8",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Completed
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#28a745",
                            }}
                        >
                            {stats.completed_orders}
                        </div>
                    </div>

                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #ffc107",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Pending
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#ffc107",
                            }}
                        >
                            {stats.pending_orders}
                        </div>
                    </div>

                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #dc3545",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Cancelled
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#dc3545",
                            }}
                        >
                            {stats.cancelled_orders}
                        </div>
                    </div>

                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #007bff",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Total Revenue
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#007bff",
                            }}
                        >
                            ${stats.total_revenue.toFixed(2)}
                        </div>
                    </div>

                    <div
                        style={{
                            background: "#f8f9fa",
                            padding: "16px",
                            borderRadius: "8px",
                            borderLeft: "4px solid #6f42c1",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#666",
                                marginBottom: "4px",
                            }}
                        >
                            Avg Order Value
                        </div>
                        <div
                            style={{
                                fontSize: "24px",
                                fontWeight: "bold",
                                color: "#6f42c1",
                            }}
                        >
                            ${stats.average_order_value.toFixed(2)}
                        </div>
                    </div>
                </div>
            )}

            {/* Revenue Chart */}
            <div style={{ marginBottom: 32 }}>
                <h3 style={{ marginBottom: 16 }}>Revenue Chart (Demo)</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                        data={revenueMetrics}
                        margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(date) =>
                                new Date(date).toLocaleDateString()
                            }
                        />
                        <YAxis />
                        <Tooltip
                            labelFormatter={(date) =>
                                new Date(date as string).toLocaleDateString()
                            }
                        />
                        <Legend />
                        <Bar dataKey="revenue" fill="#007bff" name="Revenue" />
                        <Bar
                            dataKey="orders_count"
                            fill="#ffc107"
                            name="Orders"
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Revenue Trend LineChart */}
            <div style={{ marginBottom: 32 }}>
                <h3 style={{ marginBottom: 16 }}>Revenue Trend (Daily)</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                        data={revenueMetrics}
                        margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(date) =>
                                new Date(date).toLocaleDateString()
                            }
                        />
                        <YAxis />
                        <Tooltip
                            labelFormatter={(date) =>
                                new Date(date as string).toLocaleDateString()
                            }
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="revenue"
                            stroke="#007bff"
                            strokeWidth={2}
                            name="Revenue"
                            dot={{ fill: "#007bff", r: 4 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="average_value"
                            stroke="#28a745"
                            strokeWidth={2}
                            name="Avg Value"
                            dot={{ fill: "#28a745", r: 4 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Status Breakdown PieChart */}
            <div style={{ marginBottom: 32 }}>
                <h3 style={{ marginBottom: 16 }}>Order Status Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={statusBreakdown}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, value }) => {
                                const total = statusBreakdown.reduce(
                                    (sum, item) => sum + item.count,
                                    0,
                                );
                                const percentage = (
                                    (value / total) *
                                    100
                                ).toFixed(1);
                                return `${name} ${percentage}%`;
                            }}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="count"
                        >
                            {statusBreakdown.map((_entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={
                                        CHART_COLORS[
                                            index % CHART_COLORS.length
                                        ]
                                    }
                                />
                            ))}
                        </Pie>
                        <Tooltip />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Status Breakdown */}
            {statusBreakdown.length > 0 && (
                <div
                    style={{
                        background: "#f8f9fa",
                        padding: "16px",
                        borderRadius: "8px",
                        marginBottom: "24px",
                    }}
                >
                    <h3 style={{ marginTop: 0, marginBottom: "16px" }}>
                        Status Breakdown
                    </h3>
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "repeat(auto-fit, minmax(150px, 1fr))",
                            gap: "12px",
                        }}
                    >
                        {statusBreakdown.map((item) => (
                            <div
                                key={item.status}
                                style={{
                                    padding: "12px",
                                    background: "white",
                                    borderRadius: "6px",
                                    textAlign: "center",
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: "14px",
                                        fontWeight: "bold",
                                        marginBottom: "4px",
                                    }}
                                >
                                    {item.status}
                                </div>
                                <div
                                    style={{
                                        fontSize: "18px",
                                        color: "#007bff",
                                    }}
                                >
                                    {item.count}
                                </div>
                                <div
                                    style={{
                                        fontSize: "12px",
                                        color: "#888",
                                        marginTop: "4px",
                                    }}
                                >
                                    {item.percentage.toFixed(1)}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Revenue Metrics Table */}
            <div style={{ marginBottom: "24px" }}>
                <h3 style={{ marginBottom: "16px" }}>Daily Revenue Metrics</h3>

                {paginatedMetrics.length === 0 ? (
                    <div className={styles.empty}>
                        No revenue data available for this period.
                    </div>
                ) : (
                    <>
                        <div className={styles.tableWrapper}>
                            <table className={styles.table}>
                                <thead>
                                    <tr>
                                        <th
                                            style={{
                                                cursor: "pointer",
                                                userSelect: "none",
                                            }}
                                            onClick={() =>
                                                handleColumnSort("date")
                                            }
                                        >
                                            <span
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: "6px",
                                                }}
                                            >
                                                Date
                                                <span
                                                    style={{ fontSize: "12px" }}
                                                >
                                                    {getSortIcon("date")}
                                                </span>
                                            </span>
                                        </th>
                                        <th
                                            style={{
                                                cursor: "pointer",
                                                userSelect: "none",
                                            }}
                                            onClick={() =>
                                                handleColumnSort("revenue")
                                            }
                                        >
                                            <span
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: "6px",
                                                }}
                                            >
                                                Revenue
                                                <span
                                                    style={{ fontSize: "12px" }}
                                                >
                                                    {getSortIcon("revenue")}
                                                </span>
                                            </span>
                                        </th>
                                        <th
                                            style={{
                                                cursor: "pointer",
                                                userSelect: "none",
                                            }}
                                            onClick={() =>
                                                handleColumnSort("orders_count")
                                            }
                                        >
                                            <span
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: "6px",
                                                }}
                                            >
                                                Orders
                                                <span
                                                    style={{ fontSize: "12px" }}
                                                >
                                                    {getSortIcon(
                                                        "orders_count",
                                                    )}
                                                </span>
                                            </span>
                                        </th>
                                        <th
                                            style={{
                                                cursor: "pointer",
                                                userSelect: "none",
                                            }}
                                            onClick={() =>
                                                handleColumnSort(
                                                    "average_value",
                                                )
                                            }
                                        >
                                            <span
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: "6px",
                                                }}
                                            >
                                                Avg Value
                                                <span
                                                    style={{ fontSize: "12px" }}
                                                >
                                                    {getSortIcon(
                                                        "average_value",
                                                    )}
                                                </span>
                                            </span>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {paginatedMetrics.map((metric) => (
                                        <tr key={metric.date}>
                                            <td>
                                                {new Date(
                                                    metric.date,
                                                ).toLocaleDateString()}
                                            </td>
                                            <td>
                                                <strong>
                                                    ${metric.revenue.toFixed(2)}
                                                </strong>
                                            </td>
                                            <td>{metric.orders_count}</td>
                                            <td>
                                                $
                                                {metric.average_value.toFixed(
                                                    2,
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        <div className={styles.paginationContainer}>
                            <div className={styles.paginationInfo}>
                                <span>
                                    Showing {startItem} - {endItem} of{" "}
                                    {totalCount} days
                                </span>
                                <select
                                    value={pageSize}
                                    onChange={handlePageSizeChange}
                                    className={styles.pageSizeSelect}
                                >
                                    {PAGE_SIZE_OPTIONS.map((size) => (
                                        <option key={size} value={size}>
                                            {size} per page
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className={styles.paginationControls}>
                                <Button
                                    variant="outline"
                                    size="md"
                                    onClick={() =>
                                        handlePageChange(currentPage - 1)
                                    }
                                    disabled={currentPage === 1}
                                >
                                    ← Previous
                                </Button>

                                <div className={styles.pageNumbers}>
                                    {Array.from(
                                        {
                                            length: Math.min(5, totalPages),
                                        },
                                        (_, i) => {
                                            const page =
                                                Math.max(1, currentPage - 2) +
                                                i;
                                            return page <= totalPages ? (
                                                <button
                                                    key={page}
                                                    onClick={() =>
                                                        handlePageChange(page)
                                                    }
                                                    className={`${styles.pageNumber} ${page === currentPage ? styles.active : ""}`}
                                                >
                                                    {page}
                                                </button>
                                            ) : null;
                                        },
                                    )}
                                </div>

                                <Button
                                    variant="outline"
                                    size="md"
                                    onClick={() =>
                                        handlePageChange(currentPage + 1)
                                    }
                                    disabled={currentPage === totalPages}
                                >
                                    Next →
                                </Button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
