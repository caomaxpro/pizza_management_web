/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import styles from "./CustomListTable.module.scss";
import Pagination from "./Pagination";

export interface CustomListColumn {
    key: string;
    title: string;
    sortable?: boolean;
    width?: string | number;
    align?: "left" | "center" | "right";
    render?: (row: any) => React.ReactNode;
    /** CSS class applied to each <td> cell in this column */
    className?: string;
    /** Inline styles applied to each <td> cell in this column */
    cellStyle?: React.CSSProperties;
    /** CSS class applied to the <th> header cell of this column */
    headerClassName?: string;
}

export interface CustomListTableProps {
    columns: CustomListColumn[];
    data: any[];
    sortBy?: string;
    sortOrder?: "asc" | "desc";
    onSort?: (column: string) => void;
    selectedIds?: Set<number | string>;
    onSelectAll?: () => void;
    onSelectOne?: (id: number | string) => void;
    rowKey?: (row: any) => string | number;
    showCheckboxes?: boolean;
    // Pagination props
    currentPage?: number;
    totalPages?: number;
    totalCount?: number;
    pageSize?: number;
    onPageChange?: (page: number) => void;
    onPageSizeChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    pageSizeOptions?: number[];
}

export default function CustomListTable({
    columns,
    data,
    sortBy,
    sortOrder,
    onSort,
    selectedIds,
    onSelectAll,
    onSelectOne,
    rowKey = (row) => row.id,
    showCheckboxes = false,
    // Pagination props
    currentPage = 1,
    totalPages = 1,
    totalCount = 0,
    pageSize = 20,
    onPageChange,
    onPageSizeChange,
    pageSizeOptions = [10, 20, 50, 100],
}: CustomListTableProps) {
    const getSortIcon = (col: CustomListColumn) => {
        if (!col.sortable) return null;
        if (sortBy !== col.key)
            return <span className={styles.sortIcon}>⇅</span>;
        return (
            <span className={styles.sortIcon}>
                {sortOrder === "asc" ? "↑" : "↓"}
            </span>
        );
    };

    return (
        <div className={styles.container}>
            <div className={styles.tableWrapper}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            {showCheckboxes && (
                                <th className={styles.checkboxCol}>
                                    <input
                                        type="checkbox"
                                        checked={
                                            selectedIds &&
                                            data.length > 0 &&
                                            selectedIds.size === data.length
                                        }
                                        onChange={onSelectAll}
                                    />
                                </th>
                            )}
                            {columns.map((col) => (
                                <th
                                    key={col.key}
                                    style={{
                                        width: col.width,
                                        textAlign: col.align || "left",
                                    }}
                                    className={
                                        [
                                            col.sortable
                                                ? styles.sortableHeader
                                                : undefined,
                                            col.headerClassName,
                                        ]
                                            .filter(Boolean)
                                            .join(" ") || undefined
                                    }
                                    onClick={
                                        col.sortable && onSort
                                            ? (e) => {
                                                  e.preventDefault();
                                                  onSort(col.key);
                                              }
                                            : undefined
                                    }
                                >
                                    {col.title} {getSortIcon(col)}
                                </th>
                            ))}
                            {/* actions are implemented as a regular column in `columns` now */}
                        </tr>
                    </thead>
                    <tbody>
                        {data.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={
                                        columns.length +
                                        (showCheckboxes ? 1 : 0) +
                                        0
                                    }
                                    className={styles.empty}
                                >
                                    No data found.
                                </td>
                            </tr>
                        ) : (
                            data.map((row) => (
                                <tr key={rowKey(row)}>
                                    {showCheckboxes && (
                                        <td className={styles.checkboxCol}>
                                            <input
                                                type="checkbox"
                                                checked={selectedIds?.has(
                                                    rowKey(row),
                                                )}
                                                onChange={() =>
                                                    onSelectOne &&
                                                    onSelectOne(rowKey(row))
                                                }
                                            />
                                        </td>
                                    )}
                                    {columns.map((col) => (
                                        <td
                                            key={col.key}
                                            style={{
                                                textAlign: col.align || "left",
                                                ...col.cellStyle,
                                            }}
                                            className={col.className}
                                        >
                                            {col.render
                                                ? col.render(row)
                                                : row[col.key]}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
                {/* Pagination: always show when page-size control exists so user can limit items per page */}
            </div>

            {onPageSizeChange && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalCount={totalCount}
                    pageSize={pageSize}
                    onPageChange={onPageChange ?? (() => {})}
                    onPageSizeChange={onPageSizeChange}
                    pageSizeOptions={pageSizeOptions}
                />
            )}
        </div>
    );
}
