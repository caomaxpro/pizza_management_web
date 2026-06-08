/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import inventoryAPI from "../../services/inventory";
import type { InventoryItem } from "../../services/inventory";
import providerAPI from "../../services/provider";
import type { Provider } from "../../services/provider";
import styles from "./Inventory.module.scss";
import InventoryHeader from "./InventoryHeader";
import InventoryFilter, { type InventoryFilters } from "./InventoryFilter";
import InventoryList from "./InventoryList";
import InventoryForm from "./InventoryForm";
import BulkStockPanel from "./BulkStockPanel";
import { useInventoryWebSocket } from "../../hooks/useInventoryWebSocket";

export default function Inventory() {
    const navigate = useNavigate();
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [providers, setProviders] = useState<Provider[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [filters, setFilters] = useState<InventoryFilters>({});
    const [sortBy, setSortBy] = useState<string>("name");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
    const [formOpen, setFormOpen] = useState(false);
    const [editItem, setEditItem] = useState<InventoryItem | null>(null);
    const [isFormLoading, setIsFormLoading] = useState(false);
    const [bulkPanelReason, setBulkPanelReason] = useState<
        "receipt" | "stock_take" | null
    >(null);

    useEffect(() => {
        inventoryAPI.list().then((data) => {
            setItems(data);
            setLoading(false);
        });
        providerAPI.list().then(setProviders);
    }, []);

    const sortedItems = useMemo(() => {
        const sorted = [...items];
        sorted.sort((a, b) => {
            let aValue: unknown = a[sortBy as keyof InventoryItem];
            let bValue: unknown = b[sortBy as keyof InventoryItem];
            if (typeof aValue === "string" && typeof bValue === "string") {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
            if (aValue! < bValue!) return sortOrder === "asc" ? -1 : 1;
            if (aValue! > bValue!) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });
        return sorted;
    }, [items, sortBy, sortOrder]);

    const filteredItems = useMemo(() => {
        if (!filters || Object.keys(filters).length === 0) return sortedItems;
        return sortedItems.filter((item) => {
            if (
                filters.search &&
                !item.name.toLowerCase().includes(filters.search.toLowerCase())
            )
                return false;
            if (filters.unit && item.unit !== filters.unit) return false;
            if (filters.is_active !== undefined && filters.is_active !== "") {
                const active = filters.is_active === "true";
                if (item.is_active !== active) return false;
            }
            if (filters.needs_reorder && !item.needs_reorder) return false;
            return true;
        });
    }, [sortedItems, filters]);

    const totalCount = filteredItems.length;
    const totalPages = Math.ceil(totalCount / pageSize);
    const paginatedItems = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        return filteredItems.slice(startIdx, startIdx + pageSize);
    }, [filteredItems, currentPage, pageSize]);

    const handleSelectAll = useCallback(() => {
        if (selectedIds.size === paginatedItems.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedItems.map((i) => i.id)));
        }
    }, [selectedIds, paginatedItems]);

    const handleSelectOne = useCallback((id: number | string) => {
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
        if (!confirm("Delete this inventory item?")) return;
        await inventoryAPI.delete(id);
        setItems((prev) => prev.filter((i) => i.id !== id));
    }, []);

    const handleBulkDelete = useCallback(async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} items?`)) return;
        await inventoryAPI.deleteMany(Array.from(selectedIds));
        setItems((prev) => prev.filter((i) => !selectedIds.has(i.id)));
        setSelectedIds(new Set());
    }, [selectedIds]);

    const handleCreate = useCallback(() => {
        setEditItem(null);
        setFormOpen(true);
    }, []);

    const handleEdit = useCallback(
        (id: number) => {
            const item = items.find((i) => i.id === id) ?? null;
            setEditItem(item);
            setFormOpen(true);
        },
        [items],
    );

    const handleView = useCallback(
        (id: number) => {
            console.log("Navigating to inventory details:", id);
            navigate(`/inventory/${id}`);
        },
        [navigate],
    );

    const handleFormSubmit = useCallback(
        async (data: any) => {
            try {
                setIsFormLoading(true);
                const payload: any = {
                    name: data.name,
                    description: data.description || undefined,
                    unit: data.unit,
                    current_stock: data.current_stock
                        ? Number(data.current_stock)
                        : 0,
                    min_threshold: data.min_threshold
                        ? Number(data.min_threshold)
                        : 5,
                    max_threshold: data.max_threshold
                        ? Number(data.max_threshold)
                        : undefined,
                    is_active: data.is_active !== "false",
                };
                if (data.provider_id) {
                    payload.provider_id = Number(data.provider_id);
                }

                if (editItem) {
                    const updated = await inventoryAPI.update(
                        editItem.id,
                        payload,
                    );
                    setItems((prev) =>
                        prev.map((i) => (i.id === updated.id ? updated : i)),
                    );
                } else {
                    const created = await inventoryAPI.create(payload);
                    setItems((prev) => [created, ...prev]);
                }
                setFormOpen(false);
                setEditItem(null);
            } catch (error) {
                console.error("Failed to save inventory item:", error);
            } finally {
                setIsFormLoading(false);
            }
        },
        [editItem],
    );

    const handleFilter = useCallback((f: InventoryFilters) => {
        // Use functional updaters to skip re-renders when values haven't changed.
        // This prevents Filter's autoApply effect from cycling: register → values change
        // → autoApply fires → setFilters → re-render → fields remount → register again.
        setFilters((prev) => {
            const next = f || {};
            if (
                prev.search === next.search &&
                prev.unit === next.unit &&
                prev.is_active === next.is_active &&
                prev.needs_reorder === next.needs_reorder
            ) {
                return prev; // Same reference → React bails out, no re-render
            }
            return next;
        });
        setCurrentPage((prev) => (prev === 1 ? prev : 1));
    }, []);

    const handleBulkSuccess = useCallback((updatedItems: InventoryItem[]) => {
        setItems((prev) => {
            const map = new Map(updatedItems.map((i) => [i.id, i]));
            return prev.map((i) => map.get(i.id) ?? i);
        });
    }, []);

    const handleWSUpdate = useCallback(
        (item: InventoryItem) =>
            setItems((prev) => prev.map((i) => (i.id === item.id ? item : i))),
        [],
    );
    const handleWSDelete = useCallback(
        (id: number) => setItems((prev) => prev.filter((i) => i.id !== id)),
        [],
    );
    const handleWSCreate = useCallback(
        (item: InventoryItem) => setItems((prev) => [item, ...prev]),
        [],
    );
    useInventoryWebSocket(handleWSUpdate, handleWSDelete, handleWSCreate);

    const formInitialData = editItem
        ? {
              ...editItem,
              provider_id: editItem.provider?.id
                  ? String(editItem.provider.id)
                  : "",
              is_active: String(editItem.is_active),
          }
        : {};

    return (
        <div className={styles.container}>
            <InventoryHeader
                onCreate={handleCreate}
                total={totalCount}
                onBulkReceipt={() => setBulkPanelReason("receipt")}
                onBulkStockTake={() => setBulkPanelReason("stock_take")}
            />
            <InventoryFilter onFilter={handleFilter} />
            {bulkPanelReason ? (
                <BulkStockPanel
                    items={filteredItems}
                    initialReason={bulkPanelReason}
                    onClose={() => setBulkPanelReason(null)}
                    onSuccess={handleBulkSuccess}
                />
            ) : (
                <InventoryList
                    items={paginatedItems}
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
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onBulkDelete={handleBulkDelete}
                    totalPages={totalPages}
                    totalCount={totalCount}
                    onPageChange={handlePageChange}
                    onPageSizeChange={handlePageSizeChange}
                    pageSizeOptions={[10, 20, 50, 100]}
                />
            )}
            <InventoryForm
                open={formOpen}
                onClose={() => {
                    setFormOpen(false);
                    setEditItem(null);
                }}
                onSubmit={handleFormSubmit}
                initialData={formInitialData}
                isLoading={isFormLoading}
                providers={providers}
            />
        </div>
    );
}
