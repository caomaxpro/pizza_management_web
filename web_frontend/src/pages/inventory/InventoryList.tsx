import React, { useMemo } from "react";
import CustomListTable, {
    type CustomListColumn,
} from "@components/ui/CustomListTable";
import { Button } from "@components/ui";
import styles from "./InventoryList.module.scss";
import type { InventoryItem } from "../../services/inventory";

interface InventoryListProps {
    items: InventoryItem[];
    loading: boolean;
    selectedIds: Set<number>;
    pageSize: number;
    currentPage: number;
    sortBy: string;
    sortOrder: "asc" | "desc";
    onSelectAll: () => void;
    onSelectOne: (id: number | string) => void;
    onSort: (column: string) => void;
    onView?: (id: number) => void;
    onEdit?: (id: number) => void;
    onDelete: (id: number) => void;
    onBulkDelete: () => void;
    totalPages?: number;
    totalCount?: number;
    onPageChange?: (page: number) => void;
    onPageSizeChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    pageSizeOptions?: number[];
}

export default function InventoryList(props: InventoryListProps) {
    const {
        items,
        loading,
        selectedIds,
        pageSize,
        currentPage,
        sortBy,
        sortOrder,
        onSelectAll,
        onSelectOne,
        onSort,
        onView,
        onEdit,
        onDelete,
        onBulkDelete,
        totalPages = 1,
        onPageChange,
        onPageSizeChange,
        pageSizeOptions = [10, 20, 50, 100],
    } = props;

    const columns: CustomListColumn[] = useMemo(() => {
        return [
            {
                key: "name",
                title: "Name",
                sortable: true,
                render: (row) => <span>{row.name}</span>,
                cellStyle: { width: "150px" },
            },
            {
                key: "unit",
                title: "Unit",
                sortable: true,
                // cellStyle: { width: "50px" },
            },
            {
                key: "current_stock",
                title: "Stock",
                sortable: true,
                // align: "right" as const,
                render: (row) => `${row.current_stock} ${row.unit}`,
                // cellStyle: { width: "50px" },
            },
            {
                key: "min_threshold",
                title: "Min",
                sortable: true,
                // align: "right" as const,
                render: (row) => `${row.min_threshold} ${row.unit}`,
                // cellStyle: { width: "50px" },
            },
            {
                key: "needs_reorder",
                title: "Status",
                render: (row) =>
                    row.needs_reorder ? (
                        <span className={styles.badgeLow}>⚠ Low</span>
                    ) : (
                        <span className={styles.badgeOk}>✓ OK</span>
                    ),
                // cellStyle: { width: "50px" },
            },
            // {
            //     key: "provider",
            //     title: "Provider",
            //     render: (row) => row.provider?.name || "-",
            // },
            {
                key: "is_active",
                title: "Active",
                render: (row) =>
                    row.is_active ? (
                        <span className={styles.badgeActive}>Active</span>
                    ) : (
                        <span className={styles.badgeInactive}>Inactive</span>
                    ),
            },
            {
                key: "actions",
                title: "Actions",
                render: (row) => (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {onView && (
                            <Button
                                size="sm"
                                variant="outline"
                                className={styles.btnView}
                                onClick={() => onView(row.id)}
                            >
                                View
                            </Button>
                        )}
                        {onEdit && (
                            <Button
                                size="sm"
                                variant="primary"
                                className={styles.btnEdit}
                                onClick={() => onEdit(row.id)}
                            >
                                Edit
                            </Button>
                        )}
                        <Button
                            size="sm"
                            variant="outline"
                            className={styles.btnDelete}
                            onClick={() => onDelete(row.id)}
                        >
                            Delete
                        </Button>
                    </div>
                ),
                width: 250,
            },
        ];
    }, [onView, onEdit, onDelete]);

    return (
        <div className={styles.listContainer}>
            {loading && <div className={styles.loading}>Loading...</div>}

            {selectedIds.size > 0 && (
                <div className={styles.bulkActions}>
                    <span>{selectedIds.size} selected</span>
                    <Button size="sm" variant="outline" onClick={onBulkDelete}>
                        Delete Selected
                    </Button>
                </div>
            )}

            <CustomListTable
                columns={columns}
                data={items}
                showCheckboxes={true}
                selectedIds={selectedIds}
                onSelectAll={onSelectAll}
                onSelectOne={onSelectOne}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
                pageSize={pageSize}
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={onPageChange}
                onPageSizeChange={onPageSizeChange}
                pageSizeOptions={pageSizeOptions}
            />
        </div>
    );
}
