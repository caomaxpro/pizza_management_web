import React, { useMemo } from "react";
import CustomListTable, {
    type CustomListColumn,
} from "@components/ui/CustomListTable";
import { Button } from "@components/ui";
import styles from "./PurchaseOrderList.module.scss";
import type { PurchaseOrder } from "../../services/purchaseOrder";
// Filter UI is provided by the parent `PurchaseOrders` page; do not render it here.

interface PurchaseOrderListProps {
    orders: PurchaseOrder[];
    loading: boolean;
    selectedIds: Set<number>;
    pageSize: number;
    currentPage: number;
    totalCount?: number;
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
    onPageChange?: (page: number) => void;
    onPageSizeChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    pageSizeOptions?: number[];
}

export default function PurchaseOrderList(props: PurchaseOrderListProps) {
    const {
        orders,
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

    // Orders are provided by the parent; filtering UI is also rendered there.
    const filteredOrders = orders;

    const columns: CustomListColumn[] = useMemo(
        () => [
            {
                key: "order_number",
                title: "Order Number",
                sortable: true,
            },
            {
                key: "provider",
                title: "Provider",
                sortable: true,
                render: (row) => row.provider?.name || "-",
            },
            {
                key: "order_date",
                title: "Order Date",
                sortable: true,
                render: (row) => row.order_date?.slice(0, 10),
            },
            {
                key: "status",
                title: "Status",
                sortable: true,
                render: (row) => {
                    const cls =
                        {
                            pending: styles.badgePending,
                            paid: styles.badgePaid,
                            ordered: styles.badgeOrdered,
                            delivered: styles.badgeDelivered,
                            cancelled: styles.badgeCancelled,
                        }[row.status as string] ?? styles.badge;
                    return <span className={cls}>{row.status}</span>;
                },
            },
            {
                key: "total_cost",
                title: "Total",
                sortable: true,
                render: (row) =>
                    row.total_cost.toLocaleString(undefined, {
                        style: "currency",
                        currency: "USD",
                    }),
                align: "right",
            },
            {
                key: "actions",
                title: "Actions",
                render: (row) => (
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button
                            size="sm"
                            variant="outline"
                            className={styles.btnView}
                            onClick={() => onView?.(row.id)}
                        >
                            View
                        </Button>
                        <Button
                            size="sm"
                            variant="secondary"
                            className={styles.btnEdit}
                            onClick={() => onEdit?.(row.id)}
                        >
                            Edit
                        </Button>
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
                headerClassName: styles.actionsCol,
                className: styles.actionsCol,
                width: 180,
            },
        ],
        [onView, onEdit, onDelete],
    );

    return (
        <div className={styles.listContainer}>
            {loading ? (
                <div className={styles.loading}>Loading...</div>
            ) : (
                <>
                    {/* Filter UI is rendered by the parent `PurchaseOrders` page. */}
                    {selectedIds.size > 0 && (
                        <div className={styles.bulkActions}>
                            <span>{selectedIds.size} selected</span>
                            <Button
                                variant="outline"
                                size="md"
                                onClick={onBulkDelete}
                            >
                                Delete
                            </Button>
                        </div>
                    )}
                    <CustomListTable
                        columns={columns}
                        data={filteredOrders}
                        sortBy={sortBy}
                        sortOrder={sortOrder}
                        onSort={onSort}
                        selectedIds={selectedIds}
                        onSelectAll={onSelectAll}
                        onSelectOne={onSelectOne}
                        showCheckboxes
                        currentPage={currentPage}
                        totalPages={totalPages}
                        totalCount={filteredOrders.length}
                        pageSize={pageSize}
                        onPageChange={onPageChange}
                        onPageSizeChange={onPageSizeChange}
                        pageSizeOptions={pageSizeOptions}
                    />
                </>
            )}
        </div>
    );
}
