/* eslint-disable @typescript-eslint/no-explicit-any */
import { useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, PencilSimple } from "@phosphor-icons/react";
import { Button } from "../../components/ui";
import { useItemStore } from "../../store/itemStore";
import styles from "./ItemList.module.scss";

interface ItemListTableProps {
    paginatedItems: any[];
    selectedIds: Set<number>;
    sortBy: string;
    sortOrder: "asc" | "desc";
    totalCount: number;
    currentPage: number;
    pageSize: number;
    totalPages: number;
    onSelectAll: () => void;
    onSelectOne: (id: number) => void;
    onColumnSort: (column: string) => void;
    onDelete: (id: number) => void;
    onPageChange: (page: number) => void;
    onPageSizeChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function ItemListTable({
    paginatedItems,
    selectedIds,
    sortBy,
    sortOrder,
    totalCount,
    currentPage,
    pageSize,
    totalPages,
    onSelectAll,
    onSelectOne,
    onColumnSort,
    onDelete,
    onPageChange,
    onPageSizeChange,
}: ItemListTableProps) {
    const navigate = useNavigate();

    // Helper to render sort icon
    const getSortIcon = (column: string) => {
        if (sortBy !== column) return "⇅"; // Default icon
        return sortOrder === "asc" ? "↑" : "↓";
    };

    // Page info
    const startItem = totalCount > 0 ? (currentPage - 1) * pageSize + 1 : 0;
    const endItem = Math.min(currentPage * pageSize, totalCount);

    return (
        <>
            {/* Table or Empty */}
            {paginatedItems.length === 0 ? (
                <div className={styles.empty}>
                    No items found. Create one to get started!
                </div>
            ) : (
                <>
                    {/* Table */}
                    <div className={styles.tableWrapper}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th className={styles.checkboxCol}>
                                        <input
                                            type="checkbox"
                                            checked={
                                                selectedIds.size ===
                                                    paginatedItems.length &&
                                                paginatedItems.length > 0
                                            }
                                            onChange={onSelectAll}
                                        />
                                    </th>
                                    <th>Image</th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() => onColumnSort("name")}
                                        title="Click to sort by name"
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Name
                                            <span
                                                style={{
                                                    fontSize: "12px",
                                                    opacity:
                                                        sortBy === "name"
                                                            ? 1
                                                            : 0.5,
                                                }}
                                            >
                                                {getSortIcon("name")}
                                            </span>
                                        </span>
                                    </th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() => onColumnSort("category")}
                                        title="Click to sort by category"
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Category
                                            <span
                                                style={{
                                                    fontSize: "12px",
                                                    opacity:
                                                        sortBy === "category"
                                                            ? 1
                                                            : 0.5,
                                                }}
                                            >
                                                {getSortIcon("category")}
                                            </span>
                                        </span>
                                    </th>
                                    <th
                                        style={{
                                            cursor: "pointer",
                                            userSelect: "none",
                                        }}
                                        onClick={() => onColumnSort("price")}
                                        title="Click to sort by price"
                                    >
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            Price
                                            <span
                                                style={{
                                                    fontSize: "12px",
                                                    opacity:
                                                        sortBy === "price"
                                                            ? 1
                                                            : 0.5,
                                                }}
                                            >
                                                {getSortIcon("price")}
                                            </span>
                                        </span>
                                    </th>
                                    <th>Status</th>
                                    <th className={styles.actionsCol}>
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedItems.map((item) => (
                                    <tr key={item.id}>
                                        <td className={styles.checkboxCol}>
                                            <input
                                                type="checkbox"
                                                checked={selectedIds.has(
                                                    item.id!,
                                                )}
                                                onChange={() =>
                                                    onSelectOne(item.id!)
                                                }
                                            />
                                        </td>
                                        <td className={styles.imageCol}>
                                            {item.image_url ? (
                                                <img
                                                    src={item.image_url}
                                                    alt={item.name}
                                                    className={styles.thumbnail}
                                                />
                                            ) : (
                                                <div className={styles.noImage}>
                                                    No Image
                                                </div>
                                            )}
                                        </td>
                                        <td
                                            onClick={() => {
                                                useItemStore
                                                    .getState()
                                                    .setCurrentItem(item);
                                                navigate(`/items/${item.id}`);
                                            }}
                                            className={styles.clickableCell}
                                            style={{ cursor: "pointer" }}
                                        >
                                            <strong>{item.name}</strong>
                                        </td>
                                        <td>
                                            <span className={styles.badge}>
                                                {item.category}
                                            </span>
                                        </td>
                                        <td>${item.price.toLocaleString()}</td>
                                        <td>
                                            <span
                                                className={
                                                    item.is_active
                                                        ? styles.badgeActive
                                                        : styles.badgeInactive
                                                }
                                            >
                                                {item.is_active ? (
                                                    <>
                                                        <CheckCircle
                                                            size={16}
                                                            weight="fill"
                                                        />{" "}
                                                        Active
                                                    </>
                                                ) : (
                                                    <>
                                                        <XCircle
                                                            size={16}
                                                            weight="fill"
                                                        />{" "}
                                                        Inactive
                                                    </>
                                                )}
                                            </span>
                                        </td>
                                        <td>
                                            <div className={styles.actions}>
                                                <button
                                                    className={styles.viewBtn}
                                                    onClick={() =>
                                                        navigate(
                                                            `/items/${item.id}`,
                                                        )
                                                    }
                                                    title="View Details"
                                                >
                                                    👁️
                                                </button>
                                                <button
                                                    className={styles.editBtn}
                                                    onClick={() =>
                                                        navigate(
                                                            `/items/${item.id}/edit`,
                                                        )
                                                    }
                                                    title="Edit"
                                                >
                                                    <PencilSimple size={18} />
                                                </button>
                                                <button
                                                    className={styles.deleteBtn}
                                                    onClick={() =>
                                                        onDelete(item.id!)
                                                    }
                                                    title="Delete"
                                                >
                                                    🗑️
                                                </button>
                                            </div>
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
                                items
                            </span>
                            <select
                                value={pageSize}
                                onChange={onPageSizeChange}
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
                                onClick={() => onPageChange(currentPage - 1)}
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
                                                    onPageChange(page)
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
                                onClick={() => onPageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                            >
                                Next
                                <svg
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    style={{ marginLeft: 4 }}
                                >
                                    <polyline points="9 18 15 12 9 6"></polyline>
                                </svg>
                            </Button>
                        </div>
                    </div>
                </>
            )}
        </>
    );
}
