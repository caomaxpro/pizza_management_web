/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useMemo, useState, useCallback } from "react";
import purchaseOrderAPI from "../../services/purchaseOrder";
import { useNavigate } from "react-router-dom";
import type { PurchaseOrder } from "../../services/purchaseOrder";
import styles from "./PurchaseOrders.module.scss";
import PurchaseOrderHeader from "./PurchaseOrderHeader";
import PurchaseOrderFilter, {
    type PurchaseOrderFilters,
} from "./PurchaseOrderFilter";

import PurchaseOrderList from "./PurchaseOrderList";
import PurchaseOrderForm from "./PurchaseOrderForm";

export default function PurchaseOrders() {
    const [orders, setOrders] = useState<PurchaseOrder[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [filters, setFilters] = useState<PurchaseOrderFilters>({});
    const [sortBy, setSortBy] = useState<string>("order_date");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
    const [formOpen, setFormOpen] = useState(false);

    useEffect(() => {
        purchaseOrderAPI.list().then((data) => {
            setOrders(data);
            setLoading(false);
        });
    }, []);

    const sortedOrders = useMemo(() => {
        const sorted = [...orders];
        sorted.sort((a, b) => {
            let aValue: unknown = a[sortBy as keyof PurchaseOrder];
            let bValue: unknown = b[sortBy as keyof PurchaseOrder];
            if (typeof aValue === "string" && typeof bValue === "string") {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
            if (aValue! < bValue!) return sortOrder === "asc" ? -1 : 1;
            if (aValue! > bValue!) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });
        return sorted;
    }, [orders, sortBy, sortOrder]);

    const filteredSortedOrders = useMemo(() => {
        if (!filters || Object.keys(filters).length === 0) return sortedOrders;
        return sortedOrders.filter((o) => {
            if (filters.status && String(o.status) !== String(filters.status))
                return false;
            if (
                filters.provider &&
                !(o.provider?.name || "")
                    .toLowerCase()
                    .includes(filters.provider.toLowerCase())
            )
                return false;
            const orderDate = o.order_date ? o.order_date.slice(0, 10) : "";
            if (filters.dateFrom && orderDate < filters.dateFrom) return false;
            if (filters.dateTo && orderDate > filters.dateTo) return false;
            return true;
        });
    }, [sortedOrders, filters]);

    const totalCount = filteredSortedOrders.length;
    const totalPages = Math.ceil(totalCount / pageSize);
    const paginatedOrders = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        return filteredSortedOrders.slice(startIdx, startIdx + pageSize);
    }, [filteredSortedOrders, currentPage, pageSize]);

    const handleSelectAll = useCallback(() => {
        if (selectedIds.size === paginatedOrders.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedOrders.map((o) => o.id)));
        }
    }, [selectedIds, paginatedOrders]);

    const handleSelectOne = useCallback((id: number | string) => {
        // If id is string, try to convert to number (since your ids are numbers)
        const numId = typeof id === "string" ? Number(id) : id;
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(numId)) next.delete(numId);
            else next.add(numId);
            return next;
        });
    }, []);

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

    const handleDelete = useCallback(async (id: number) => {
        if (!confirm("Delete this purchase order?")) return;
        await purchaseOrderAPI.delete(id);
        setOrders((prev) => prev.filter((o) => o.id !== id));
    }, []);

    const handleBulkDelete = useCallback(async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} orders?`)) return;
        await purchaseOrderAPI.bulkDelete(Array.from(selectedIds));
        setOrders((prev) => prev.filter((o) => !selectedIds.has(o.id)));
        setSelectedIds(new Set());
    }, [selectedIds]);

    // Handler for create PO button
    const handleCreatePO = useCallback(() => {
        setFormOpen(true);
    }, []);

    const navigate = useNavigate();

    const handleView = useCallback(
        (id: number) => {
            navigate(`/purchase_orders/${id}`);
        },
        [navigate],
    );

    const handleFormClose = useCallback(() => {
        setFormOpen(false);
    }, []);

    const handleFormSubmit = useCallback((data: any) => {
        // TODO: Call API to create PO, then refresh list
        setFormOpen(false);
        // Optionally: setLoading(true); purchaseOrderAPI.list()...
    }, []);

    // Handler for filter
    const handleFilter = useCallback((f: PurchaseOrderFilters) => {
        setFilters(f || {});
        setCurrentPage(1);
    }, []);

    return (
        <div className={styles.container}>
            <PurchaseOrderHeader
                onCreate={handleCreatePO}
                total={orders.length}
            />
            <PurchaseOrderFilter onFilter={handleFilter} />
            <PurchaseOrderList
                orders={paginatedOrders}
                loading={loading}
                selectedIds={selectedIds}
                pageSize={pageSize}
                currentPage={currentPage}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSelectAll={handleSelectAll}
                onSelectOne={handleSelectOne}
                onSort={handleColumnSort}
                onView={handleView}
                onDelete={handleDelete}
                onBulkDelete={handleBulkDelete}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                pageSizeOptions={[10, 20, 50, 100]}
            />
            <PurchaseOrderForm
                open={formOpen}
                onClose={handleFormClose}
                onSubmit={handleFormSubmit}
            />
        </div>
    );
}
