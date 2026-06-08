/* eslint-disable @typescript-eslint/no-unused-vars */
import { useMemo, useCallback, useState } from "react";
import { CheckCircle, XCircle } from "@phosphor-icons/react";
import { Button } from "../../components/ui";
import styles from "./Orders.module.scss";

interface OrderFilterOptions {
    search: string;
    status: string;
    dateFrom: string;
    dateTo: string;
    priceMin: string;
    priceMax: string;
}

interface Order {
    id: number;
    order_number: string;
    customer_name: string;
    customer_email: string;
    total_amount: number;
    status: "pending" | "processing" | "completed" | "cancelled";
    created_at: string;
    items_count: number;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function Orders() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sortBy, setSortBy] = useState<string>("created_at");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
    const [appliedFilters, setAppliedFilters] = useState<OrderFilterOptions>({
        search: "",
        status: "",
        dateFrom: "",
        dateTo: "",
        priceMin: "",
        priceMax: "",
    });

    // Handle Apply Filters button
    const handleApplyFilters = useCallback((newFilters: OrderFilterOptions) => {
        setAppliedFilters(newFilters);
        setCurrentPage(1);
    }, []);

    // Client-side filtering and sorting
    const filteredAndSortedOrders = useMemo(() => {
        let result = [...orders];

        // Apply filters
        result = result.filter((order) => {
            const searchLower = appliedFilters.search.toLowerCase();
            const matchesSearch =
                order.order_number.toLowerCase().includes(searchLower) ||
                order.customer_name.toLowerCase().includes(searchLower) ||
                order.customer_email.toLowerCase().includes(searchLower);

            const matchesStatus =
                !appliedFilters.status ||
                order.status === appliedFilters.status;

            const priceMin = appliedFilters.priceMin
                ? parseFloat(appliedFilters.priceMin)
                : 0;
            const priceMax = appliedFilters.priceMax
                ? parseFloat(appliedFilters.priceMax)
                : Infinity;
            const matchesPrice =
                order.total_amount >= priceMin &&
                order.total_amount <= priceMax;

            return matchesSearch && matchesStatus && matchesPrice;
        });

        // Apply sorting
        result.sort((a, b) => {
            let aValue: string | number = "";
            let bValue: string | number = "";

            switch (sortBy) {
                case "order_number":
                    aValue = a.order_number.toLowerCase();
                    bValue = b.order_number.toLowerCase();
                    break;
                case "customer_name":
                    aValue = a.customer_name.toLowerCase();
                    bValue = b.customer_name.toLowerCase();
                    break;
                case "total_amount":
                    aValue = a.total_amount;
                    bValue = b.total_amount;
                    break;
                case "created_at":
                    aValue = new Date(a.created_at).getTime();
                    bValue = new Date(b.created_at).getTime();
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });

        return result;
    }, [orders, appliedFilters, sortBy, sortOrder]);

    // Pagination
    const totalCount = filteredAndSortedOrders.length;
    const totalPages = useMemo(
        () => Math.ceil(totalCount / pageSize),
        [totalCount, pageSize],
    );

    const paginatedOrders = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = startIdx + pageSize;
        return filteredAndSortedOrders.slice(startIdx, endIdx);
    }, [filteredAndSortedOrders, currentPage, pageSize]);

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
                    <h1>🛒 Orders</h1>
                    <p className={styles.subtitle}>
                        View all customer orders ({totalCount} total)
                    </p>
                </div>
            </div>

            {/* Table or Empty */}
            {paginatedOrders.length === 0 ? (
                <div className={styles.empty}>
                    No orders found. Create one to get started!
                </div>
            ) : (
                <>
                    {/* Table */}
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
                                            handleColumnSort("order_number")
                                        }
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Order #
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("order_number")}
                                            </span>
                                        </span>
                                    </th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() =>
                                            handleColumnSort("customer_name")
                                        }
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Customer
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("customer_name")}
                                            </span>
                                        </span>
                                    </th>
                                    <th>Email</th>
                                    <th>Items</th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() =>
                                            handleColumnSort("total_amount")
                                        }
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Total
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("total_amount")}
                                            </span>
                                        </span>
                                    </th>
                                    <th>Status</th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() =>
                                            handleColumnSort("created_at")
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
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("created_at")}
                                            </span>
                                        </span>
                                    </th>
                                    <th className={styles.actionsCol}>
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedOrders.map((order) => (
                                    <tr key={order.id}>
                                        <td>
                                            <strong>
                                                {order.order_number}
                                            </strong>
                                        </td>
                                        <td>{order.customer_name}</td>
                                        <td>{order.customer_email}</td>
                                        <td>{order.items_count}</td>
                                        <td>
                                            ${order.total_amount.toFixed(2)}
                                        </td>
                                        <td>
                                            <span
                                                style={{
                                                    padding: "4px 8px",
                                                    borderRadius: "4px",
                                                    fontSize: "12px",
                                                    fontWeight: "bold",
                                                    backgroundColor:
                                                        order.status ===
                                                        "completed"
                                                            ? "#d4edda"
                                                            : order.status ===
                                                                "pending"
                                                              ? "#fff3cd"
                                                              : order.status ===
                                                                  "cancelled"
                                                                ? "#f8d7da"
                                                                : "#cce5ff",
                                                    color:
                                                        order.status ===
                                                        "completed"
                                                            ? "#155724"
                                                            : order.status ===
                                                                "pending"
                                                              ? "#856404"
                                                              : order.status ===
                                                                  "cancelled"
                                                                ? "#721c24"
                                                                : "#004085",
                                                }}
                                            >
                                                {order.status}
                                            </span>
                                        </td>
                                        <td>
                                            {new Date(
                                                order.created_at,
                                            ).toLocaleDateString()}
                                        </td>
                                        <td>
                                            <span
                                                style={{
                                                    color: "#888",
                                                    fontSize: "12px",
                                                }}
                                            >
                                                {order.status ===
                                                "completed" ? (
                                                    <>
                                                        <CheckCircle
                                                            size={16}
                                                            weight="fill"
                                                        />{" "}
                                                        Completed
                                                    </>
                                                ) : order.status ===
                                                  "pending" ? (
                                                    "⏳ Pending"
                                                ) : order.status ===
                                                  "cancelled" ? (
                                                    <>
                                                        <XCircle
                                                            size={16}
                                                            weight="fill"
                                                        />{" "}
                                                        Cancelled
                                                    </>
                                                ) : (
                                                    "🔄 Processing"
                                                )}
                                            </span>
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
                                Showing {startItem} - {endItem} of {totalCount}{" "}
                                orders
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
                                    { length: Math.min(5, totalPages) },
                                    (_, i) => {
                                        const page =
                                            Math.max(1, currentPage - 2) + i;
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
    );
}
