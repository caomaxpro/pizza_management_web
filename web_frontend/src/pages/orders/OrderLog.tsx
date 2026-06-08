import { useMemo, useCallback, useState } from "react";
import { Button } from "../../components/ui";
import styles from "./Orders.module.scss";

interface OrderLogEntry {
    id: number;
    order_id: number;
    order_number: string;
    action: string;
    description: string;
    performed_by: string;
    created_at: string;
    timestamp: string;
}

interface LogFilterOptions {
    search: string;
    action: string;
    dateFrom: string;
    dateTo: string;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function OrderLog() {
    const [logs] = useState<OrderLogEntry[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sortBy, setSortBy] = useState<string>("created_at");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

    // Client-side filtering and sorting
    const filteredAndSortedLogs = useMemo(() => {
        const appliedFilters: LogFilterOptions = {
            search: "",
            action: "",
            dateFrom: "",
            dateTo: "",
        };
        let result = [...logs];

        // Apply filters
        result = result.filter((log) => {
            const searchLower = appliedFilters.search.toLowerCase();
            const matchesSearch =
                log.order_number.toLowerCase().includes(searchLower) ||
                log.order_id.toString().includes(searchLower) ||
                log.performed_by.toLowerCase().includes(searchLower) ||
                log.description.toLowerCase().includes(searchLower);

            const matchesAction =
                !appliedFilters.action || log.action === appliedFilters.action;

            return matchesSearch && matchesAction;
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
                case "action":
                    aValue = a.action.toLowerCase();
                    bValue = b.action.toLowerCase();
                    break;
                case "performed_by":
                    aValue = a.performed_by.toLowerCase();
                    bValue = b.performed_by.toLowerCase();
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
    }, [logs, sortBy, sortOrder]);

    // Pagination
    const totalCount = filteredAndSortedLogs.length;
    const totalPages = useMemo(
        () => Math.ceil(totalCount / pageSize),
        [totalCount, pageSize],
    );

    const paginatedLogs = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = startIdx + pageSize;
        return filteredAndSortedLogs.slice(startIdx, endIdx);
    }, [filteredAndSortedLogs, currentPage, pageSize]);

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

    const getActionColor = (action: string) => {
        const colors: Record<string, { bg: string; text: string }> = {
            created: { bg: "#d1ecf1", text: "#0c5460" },
            updated: { bg: "#cfe2ff", text: "#084298" },
            status_changed: { bg: "#fff3cd", text: "#856404" },
            payment_processed: { bg: "#d4edda", text: "#155724" },
            shipped: { bg: "#e2e3e5", text: "#383d41" },
            delivered: { bg: "#d4edda", text: "#155724" },
            cancelled: { bg: "#f8d7da", text: "#721c24" },
            refunded: { bg: "#f8d7da", text: "#721c24" },
        };
        return colors[action] || { bg: "#e2e3e5", text: "#383d41" };
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h1>📋 Order Log</h1>
                    <p className={styles.subtitle}>
                        View all order activity and changes ({totalCount} total)
                    </p>
                </div>
            </div>

            {/* Table or Empty */}
            {paginatedLogs.length === 0 ? (
                <div className={styles.empty}>
                    No logs found. Order activity will appear here!
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
                                            handleColumnSort("action")
                                        }
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Action
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("action")}
                                            </span>
                                        </span>
                                    </th>
                                    <th>Description</th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() =>
                                            handleColumnSort("performed_by")
                                        }
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Performed By
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("performed_by")}
                                            </span>
                                        </span>
                                    </th>
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
                                            Timestamp
                                            <span style={{ fontSize: "12px" }}>
                                                {getSortIcon("created_at")}
                                            </span>
                                        </span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedLogs.map((log) => {
                                    const colors = getActionColor(log.action);
                                    return (
                                        <tr key={log.id}>
                                            <td>
                                                <strong>
                                                    {log.order_number}
                                                </strong>
                                            </td>
                                            <td>
                                                <span
                                                    style={{
                                                        padding: "4px 8px",
                                                        borderRadius: "4px",
                                                        fontSize: "12px",
                                                        fontWeight: "bold",
                                                        backgroundColor:
                                                            colors.bg,
                                                        color: colors.text,
                                                    }}
                                                >
                                                    {log.action.replace(
                                                        /_/g,
                                                        " ",
                                                    )}
                                                </span>
                                            </td>
                                            <td>{log.description}</td>
                                            <td>{log.performed_by}</td>
                                            <td>
                                                <span
                                                    style={{
                                                        color: "#888",
                                                        fontSize: "12px",
                                                    }}
                                                >
                                                    {new Date(
                                                        log.created_at,
                                                    ).toLocaleString()}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className={styles.paginationContainer}>
                        <div className={styles.paginationInfo}>
                            <span>
                                Showing {startItem} - {endItem} of {totalCount}{" "}
                                logs
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
