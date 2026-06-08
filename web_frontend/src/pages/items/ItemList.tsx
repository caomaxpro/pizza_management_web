/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useMemo, useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Filter } from "../../components/ui";
import ExportMenu, { type ExportColumn } from "../../components/ui/ExportMenu";
import SearchField from "../../components/form/fields/SearchField";
import SelectField from "../../components/form/fields/SelectField";
import TextField from "../../components/form/fields/TextField";
import itemAPI from "../../services/item";
import { useItemStore } from "../../store/itemStore";
import type { Item } from "../../services/item";
import type { ItemFilterOptions } from "./ItemFilter";
import CustomListTable, {
    type CustomListColumn,
} from "../../components/ui/CustomListTable";
import ItemFormModal from "./ItemFormModal";
import styles from "./ItemList.module.scss";
import { CheckCircle, XCircle } from "@phosphor-icons/react";
import * as icons from "@assets/icons";

export default function ItemList() {
    const navigate = useNavigate();
    const {
        items: cacheItems,
        fetchAllItems,
        setItems: setCacheItems,
    } = useItemStore();
    const [selectedIds, setSelectedIds] = useState<Set<number | string>>(
        new Set(),
    );
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sortBy, setSortBy] = useState<string>("name");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
    const [filters, setFilters] = useState<ItemFilterOptions>({
        search: "",
        status: "all",
        priceMin: "",
        priceMax: "",
    });
    // Applied filters (changed when Apply Filters button clicked)
    const [appliedFilters, setAppliedFilters] =
        useState<ItemFilterOptions>(filters);

    // Modal state
    const [isFormModalOpen, setIsFormModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<Item | null>(null);

    // Fetch all items once on component mount
    useEffect(() => {
        fetchAllItems();
    }, [fetchAllItems]);

    // Handle Apply Filters button
    const handleApplyFilters = useCallback((newFilters: ItemFilterOptions) => {
        setAppliedFilters(newFilters);
        setCurrentPage(1); // Reset to page 1 when filters are applied
    }, []);

    // Client-side filtering and sorting
    const filteredAndSortedItems = useMemo(() => {
        let result = [...cacheItems];

        // Apply filters
        result = result.filter((item) => {
            const searchLower = appliedFilters.search.toLowerCase();
            const matchesSearch =
                item.name.toLowerCase().includes(searchLower) ||
                (item.description &&
                    item.description.toLowerCase().includes(searchLower));

            const matchesStatus =
                appliedFilters.status === "all" ||
                (appliedFilters.status === "active" && item.is_active) ||
                (appliedFilters.status === "inactive" && !item.is_active);

            const priceMin = appliedFilters.priceMin
                ? parseFloat(appliedFilters.priceMin)
                : 0;
            const priceMax = appliedFilters.priceMax
                ? parseFloat(appliedFilters.priceMax)
                : Infinity;
            const matchesPrice =
                item.price >= priceMin && item.price <= priceMax;

            return matchesSearch && matchesStatus && matchesPrice;
        });

        // Apply sorting
        result.sort((a, b) => {
            let aValue: string | number | boolean = "";
            let bValue: string | number | boolean = "";

            switch (sortBy) {
                case "name":
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case "price":
                    aValue = a.price;
                    bValue = b.price;
                    break;
                case "is_active":
                    aValue = a.is_active ? 1 : 0;
                    bValue = b.is_active ? 1 : 0;
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });

        return result;
    }, [cacheItems, appliedFilters, sortBy, sortOrder]);

    // Pagination
    const totalCount = filteredAndSortedItems.length;
    const totalPages = useMemo(
        () => Math.ceil(totalCount / pageSize),
        [totalCount, pageSize],
    );

    const paginatedItems = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = startIdx + pageSize;
        return filteredAndSortedItems.slice(startIdx, endIdx);
    }, [filteredAndSortedItems, currentPage, pageSize]);

    // Build filter fields array
    const filterFields = useMemo(
        () => [
            <SearchField
                key="search"
                name="search"
                label="Search"
                icon={icons.icons8Search}
                value={filters.search}
                onChange={() => {}}
                onSearch={(value) =>
                    handleApplyFilters({ ...filters, search: value })
                }
                autoSearch={true}
                placeholder="Search by name or description..."
                style={{ width: "400px" }}
            />,
            <SelectField
                key="status"
                name="status"
                label="Status"
                value={filters.status}
                onChange={() => {}}
                options={[
                    { value: "all", label: "All Status" },
                    { value: "active", label: "Active" },
                    { value: "inactive", label: "Inactive" },
                ]}
                style={{ width: "200px" }}
            />,
            <TextField
                key="priceMin"
                name="priceMin"
                label="Min Price"
                type="number"
                value={filters.priceMin}
                onChange={() => {}}
                placeholder="$0"
                style={{ width: "200px" }}
            />,
            <TextField
                key="priceMax"
                name="priceMax"
                label="Max Price"
                type="number"
                value={filters.priceMax}
                onChange={() => {}}
                placeholder="$999"
                style={{ width: "200px" }}
            />,
        ],
        [filters, handleApplyFilters],
    );

    const handleDelete = useCallback(
        async (id: number) => {
            if (!confirm("Are you sure you want to delete this item?")) return;
            try {
                await itemAPI.delete(id);
                setCacheItems((prev) => prev.filter((item) => item.id !== id));
            } catch {
                alert("Failed to delete item");
            }
        },
        [setCacheItems],
    );

    const actions = useCallback(
        (row: any) => (
            <div style={{ display: "flex", gap: 8 }}>
                <Button
                    size="sm"
                    variant="primary"
                    onClick={() => navigate(`/items/${row.id}`)}
                >
                    View
                </Button>
                <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                        setEditingItem(row);
                        setIsFormModalOpen(true);
                    }}
                >
                    Edit
                </Button>
                <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(row.id)}
                >
                    Delete
                </Button>
            </div>
        ),
        [handleDelete, navigate],
    );

    const columns = useMemo<CustomListColumn[]>(() => {
        return [
            {
                key: "image_url",
                title: "Image",
                render: (row: any) =>
                    row.image_url ? (
                        <img
                            src={row.image_url}
                            alt={row.name}
                            style={{
                                width: 40,
                                height: 40,
                                objectFit: "cover",
                                borderRadius: 4,
                            }}
                        />
                    ) : (
                        <span style={{ color: "#ccc" }}>No image</span>
                    ),
            },
            {
                key: "name",
                title: "Name",
                sortable: true,
                render: (row: any) => (
                    <div style={{ display: "flex", flexDirection: "column" }}>
                        <strong>{row.name}</strong>
                        {row.description && (
                            <span style={{ color: "#666", fontSize: 12 }}>
                                {row.description}
                            </span>
                        )}
                    </div>
                ),
            },
            { key: "price", title: "Price", sortable: true, align: "right" },
            {
                key: "is_active",
                title: "Status",
                sortable: true,
                render: (row: any) =>
                    row.is_active ? (
                        <span
                            className={styles.badgeActive}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                                width: "fit-content",
                            }}
                        >
                            <CheckCircle size={16} weight="fill" />
                            Active
                        </span>
                    ) : (
                        <span
                            className={styles.badgeInactive}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                                width: "fit-content",
                            }}
                        >
                            <XCircle size={16} weight="fill" />
                            Inactive
                        </span>
                    ),
            },
            {
                key: "actions",
                title: "Actions",
                render: (row: any) => actions(row),
                headerClassName: styles.actionsCol,
                className: styles.actionsCol,
                width: 160,
            },
        ];
    }, [actions]);

    // File input ref for importing JSON
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    // Handler for importing JSON
    const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const json = JSON.parse(event.target?.result as string);
                navigate("/items/import-review", {
                    state: { importedData: json },
                });
            } catch (err) {
                alert("Invalid JSON file");
            }
        };
        reader.readAsText(file);
        e.target.value = "";
    };

    // Handle column sort
    const handleColumnSort = useCallback(
        (column: string) => {
            if (sortBy === column) {
                // Toggle sort order if same column
                setSortOrder(sortOrder === "asc" ? "desc" : "asc");
            } else {
                // Switch to new column with ascending order
                setSortBy(column);
                setSortOrder("asc");
            }
            setCurrentPage(1); // Reset to page 1 when sorting changes
        },
        [sortBy, sortOrder],
    );

    // Event handlers
    const handleSelectAll = useCallback(() => {
        if (selectedIds.size === paginatedItems.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedItems.map((item) => item.id!)));
        }
    }, [selectedIds.size, paginatedItems]);

    const handleSelectOne = useCallback((id: string | number) => {
        const key = typeof id === "number" ? id : Number(id);
        setSelectedIds((prev) => {
            const newSelected = new Set(prev);
            if (newSelected.has(key) || newSelected.has(String(key))) {
                newSelected.delete(key);
                newSelected.delete(String(key));
            } else {
                newSelected.add(key);
            }
            return newSelected;
        });
    }, []);

    const handleBulkDelete = useCallback(async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} items?`)) return;
        try {
            const ids = Array.from(selectedIds).map((v) => Number(v));
            await itemAPI.bulkDelete(ids);
            setCacheItems((prev) =>
                prev.filter((item) => !ids.includes(Number(item.id!))),
            );
            setSelectedIds(new Set());
        } catch {
            alert("Failed to delete items");
        }
    }, [selectedIds, setCacheItems]);

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

    // Export columns configuration
    const exportColumns: ExportColumn[] = useMemo(
        () => [
            { key: "id", label: "ID" },
            { key: "name", label: "Name" },
            { key: "description", label: "Description" },
            {
                key: "price",
                label: "Price",
                render: (v) => `$${Number(v).toFixed(2)}`,
            },
            {
                key: "is_active",
                label: "Status",
                render: (v) => (v ? "Active" : "Inactive"),
            },
            { key: "image_url", label: "Image URL" },
        ],
        [],
    );

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h1>Menu Items</h1>
                    <p className={styles.subtitle}>
                        Manage menu items, offerings, and products ({totalCount}{" "}
                        total)
                    </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <Button
                        variant="primary"
                        size="md"
                        onClick={() => {
                            setEditingItem(null);
                            setIsFormModalOpen(true);
                        }}
                    >
                        New Item
                    </Button>
                    <Button
                        variant="primary"
                        size="md"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Import JSON
                    </Button>
                    <ExportMenu
                        data={filteredAndSortedItems}
                        selectedIds={selectedIds}
                        filenamePrefix="items"
                        columns={exportColumns}
                    />
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="application/json"
                        style={{ display: "none" }}
                        onChange={handleImportJson}
                    />
                </div>
            </div>

            {/* Filters */}
            <Filter
                fields={filterFields}
                initialValues={appliedFilters}
                onApply={(values) =>
                    handleApplyFilters(values as ItemFilterOptions)
                }
                onReset={() => {
                    const emptyFilters: ItemFilterOptions = {
                        search: "",
                        status: "all",
                        priceMin: "",
                        priceMax: "",
                    };
                    setFilters(emptyFilters);
                    setAppliedFilters(emptyFilters);
                }}
                applyLabel="Apply Filters"
                resetLabel="Clear Filters"
            />

            {/* Bulk Actions */}
            {selectedIds.size > 0 && (
                <div className={styles.bulkActions}>
                    <span>{selectedIds.size} selected</span>
                    <Button
                        variant="secondary"
                        size="md"
                        onClick={() =>
                            navigate("/items/bulk-edit", {
                                state: {
                                    selectedIds: Array.from(selectedIds),
                                },
                            })
                        }
                    >
                        Bulk Edit
                    </Button>
                    <Button
                        variant="outline"
                        size="md"
                        onClick={handleBulkDelete}
                    >
                        Delete
                    </Button>
                </div>
            )}

            {/* Table or Empty */}
            <CustomListTable
                columns={columns}
                data={paginatedItems}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSort={handleColumnSort}
                selectedIds={selectedIds}
                onSelectAll={handleSelectAll}
                onSelectOne={handleSelectOne}
                showCheckboxes
                currentPage={currentPage}
                totalPages={totalPages}
                pageSize={pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
            />

            {/* Item Form Modal */}
            <ItemFormModal
                isOpen={isFormModalOpen}
                onClose={() => {
                    setIsFormModalOpen(false);
                    setEditingItem(null);
                }}
                editingItem={editingItem}
                onSuccess={() => {
                    // Modal will close automatically
                }}
            />
        </div>
    );
}
