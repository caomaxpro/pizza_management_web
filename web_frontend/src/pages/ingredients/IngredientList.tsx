/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useMemo, useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, Pizza } from "@phosphor-icons/react";
import { ingredientAPI } from "../../services/ingredients";
import { useIngredientStore } from "../../store/ingredientStore";
import { Button, Filter } from "@components/ui";
import ExportMenu, { type ExportColumn } from "@components/ui/ExportMenu";
import SearchField from "@components/form/fields/SearchField";
import SelectField from "@components/form/fields/SelectField";
import TextField from "@components/form/fields/TextField";
import CustomListTable, {
    type CustomListColumn,
} from "@components/ui/CustomListTable";
import type { FilterOptions } from "./IngredientFilter";
import styles from "./IngredientList.module.scss";

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function IngredientList() {
    const navigate = useNavigate();
    const {
        ingredients: cacheIngredients,
        fetchAllIngredients,
        setIngredients: setCacheIngredients,
    } = useIngredientStore();
    const [selectedIds, setSelectedIds] = useState<Set<number | string>>(
        new Set(),
    );
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sortBy, setSortBy] = useState<string>("name");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
    const [filters, setFilters] = useState<FilterOptions>({
        search: "",
        type: "",
        subType: "",
        status: "all",
        priceMin: "",
        priceMax: "",
    });
    // Applied filters (changed when Apply Filters button clicked)
    const [appliedFilters, setAppliedFilters] =
        useState<FilterOptions>(filters);

    // Fetch all ingredients once on component mount
    useEffect(() => {
        fetchAllIngredients();
    }, [fetchAllIngredients]);

    // Refetch when cache is cleared (after edit/delete operations)
    useEffect(() => {
        if (cacheIngredients.length === 0) {
            fetchAllIngredients();
        }
    }, [cacheIngredients.length, fetchAllIngredients]);

    // Handle Apply Filters button
    const handleApplyFilters = useCallback((newFilters: FilterOptions) => {
        setFilters(newFilters);
        setAppliedFilters(newFilters);
        setCurrentPage(1); // Reset to page 1 when filters are applied
    }, []);

    const availableTypes = useMemo(
        () => [
            { value: "", label: "All Types" },
            { value: "dough", label: "dough" },
            { value: "sauce", label: "sauce" },
            { value: "cheese", label: "cheese" },
            { value: "topping", label: "topping" },
            { value: "extra", label: "extra" },
        ],
        [],
    );

    // Get available sub-types from cached ingredients (moved before filterFields)
    const availableSubTypes = useMemo(() => {
        const subTypes = new Set<string>();
        cacheIngredients.forEach((ing) => {
            if (ing.sub_type) {
                subTypes.add(ing.sub_type);
            }
        });
        return Array.from(subTypes).sort();
    }, [cacheIngredients]);

    const filterFields = useMemo(
        () => [
            <SearchField
                key="search"
                name="search"
                label="Search"
                value={filters.search}
                onChange={() => {}}
                onSearch={(value) =>
                    handleApplyFilters({ ...filters, search: value })
                }
                autoSearch={true}
                placeholder="Search by name or description..."
                style={{ width: "360px" }}
            />,
            <SelectField
                key="type"
                name="type"
                label="Type"
                value={filters.type}
                onChange={() => {}}
                options={availableTypes}
                style={{ width: "180px" }}
                selectWrapperBackgroundColor="white"
            />,
            <SelectField
                key="subType"
                name="subType"
                label="Sub-type"
                value={filters.subType}
                onChange={() => {}}
                options={[
                    { value: "", label: "All" },
                    ...availableSubTypes.map((s) => ({ value: s, label: s })),
                ]}
                style={{ width: "180px" }}
                selectWrapperBackgroundColor="white"
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
                style={{ width: "150px" }}
                selectWrapperBackgroundColor="white"
            />,
            <TextField
                key="priceMin"
                name="priceMin"
                label="Min Price"
                type="number"
                value={filters.priceMin}
                onChange={() => {}}
                placeholder="$0"
                style={{ width: "120px" }}
            />,
            <TextField
                key="priceMax"
                name="priceMax"
                label="Max Price"
                type="number"
                value={filters.priceMax}
                onChange={() => {}}
                placeholder="$999"
                style={{ width: "120px" }}
            />,
        ],
        [filters, availableSubTypes, availableTypes, handleApplyFilters],
    );

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

    // Client-side filtering and sorting
    const filteredIngredients = useMemo(() => {
        let result = [...cacheIngredients];

        // Apply filters
        result = result.filter((ing) => {
            // Search filter
            const searchLower = appliedFilters.search.toLowerCase();
            const matchesSearch =
                ing.name.toLowerCase().includes(searchLower) ||
                (ing.description &&
                    ing.description.toLowerCase().includes(searchLower));

            // Type filter
            const matchesType =
                !appliedFilters.type || ing.type === appliedFilters.type;

            // Sub-type filter
            const matchesSubType =
                !appliedFilters.subType ||
                ing.sub_type === appliedFilters.subType;

            // Status filter
            const matchesStatus =
                appliedFilters.status === "all" ||
                (appliedFilters.status === "active" && ing.is_active) ||
                (appliedFilters.status === "inactive" && !ing.is_active);

            // Price range filter
            const priceMin = appliedFilters.priceMin
                ? parseFloat(appliedFilters.priceMin)
                : 0;
            const priceMax = appliedFilters.priceMax
                ? parseFloat(appliedFilters.priceMax)
                : Infinity;
            const matchesPrice = ing.price >= priceMin && ing.price <= priceMax;

            return (
                matchesSearch &&
                matchesType &&
                matchesSubType &&
                matchesStatus &&
                matchesPrice
            );
        });

        // Apply sorting
        result.sort((a, b) => {
            let aValue: string | number = "";
            let bValue: string | number = "";

            switch (sortBy) {
                case "name":
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case "type":
                    aValue = a.type.toLowerCase();
                    bValue = b.type.toLowerCase();
                    break;
                case "price":
                    aValue = a.price;
                    bValue = b.price;
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });

        return result;
    }, [cacheIngredients, appliedFilters, sortBy, sortOrder]);

    // Pagination
    const totalCount = filteredIngredients.length;
    const totalPages = useMemo(
        () => Math.ceil(totalCount / pageSize),
        [totalCount, pageSize],
    );

    const paginatedIngredients = useMemo(() => {
        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = startIdx + pageSize;
        return filteredIngredients.slice(startIdx, endIdx);
    }, [filteredIngredients, currentPage, pageSize]);

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
                navigate("/ingredients/import-review", {
                    state: { importedData: json },
                });
            } catch (err) {
                alert("Invalid JSON file");
            }
        };
        reader.readAsText(file);
        e.target.value = "";
    };

    // Event handlers
    const handleDelete = useCallback(
        async (id: number) => {
            if (!confirm("Are you sure you want to delete this ingredient?"))
                return;
            try {
                await ingredientAPI.delete(id);
                setCacheIngredients((prev) =>
                    prev.filter((ing) => ing.id !== id),
                );
            } catch {
                alert("Failed to delete ingredient");
            }
        },
        [setCacheIngredients],
    );
    const actions = useCallback(
        (row: any) => (
            <div style={{ display: "flex", gap: 8 }}>
                <Button
                    size="sm"
                    variant="primary"
                    onClick={() => navigate(`/ingredients/${row.id}`)}
                >
                    View
                </Button>
                <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => navigate(`/ingredients/${row.id}/edit`)}
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
        [navigate, handleDelete],
    );

    const columns = useMemo<CustomListColumn[]>(
        () => [
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
            {
                key: "type",
                title: "Type",
                sortable: true,
                render: (row: any) => (
                    <span
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 2,
                        }}
                    >
                        <span className={styles.badgeType}>{row.type}</span>
                        {row.sub_type && (
                            <span
                                className={styles.badgeType}
                                style={{ opacity: 0.7 }}
                            >
                                {row.sub_type}
                            </span>
                        )}
                    </span>
                ),
            },
            {
                key: "price",
                title: "Price",
                sortable: true,
                align: "right",
                render: (row: any) => `$${Number(row.price).toFixed(2)}`,
            },
            {
                key: "is_active",
                title: "Status",
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
                width: 180,
            },
        ],
        [actions],
    );

    const handleSelectAll = useCallback(() => {
        if (selectedIds.size === paginatedIngredients.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedIngredients.map((ing) => ing.id!)));
        }
    }, [selectedIds.size, paginatedIngredients]);

    const handleSelectOne = useCallback((id: string | number) => {
        setSelectedIds((prev) => {
            const newSelected = new Set(prev);
            if (newSelected.has(id)) {
                newSelected.delete(id);
            } else {
                newSelected.add(id);
            }
            return newSelected;
        });
    }, []);

    const handleBulkDelete = useCallback(async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} ingredients?`)) return;
        try {
            const ids = Array.from(selectedIds).map((v) => Number(v));
            await ingredientAPI.bulkDelete(ids);
            setCacheIngredients((prev) =>
                prev.filter((ing) => !ids.includes(Number(ing.id!))),
            );
            setSelectedIds(new Set());
        } catch {
            alert("Failed to delete ingredients");
        }
    }, [selectedIds, setCacheIngredients]);

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
            { key: "type", label: "Type" },
            { key: "sub_type", label: "Sub-type" },
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
                    <h1>
                        <Pizza
                            size={32}
                            weight="fill"
                            style={{ marginRight: 8 }}
                        />
                        Ingredients
                    </h1>
                    <p
                        className={styles.subtitle}
                        style={{ marginLeft: "5px" }}
                    >
                        Manage pizza ingredients, toppings, sauces, and more
                    </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <Button
                        variant="primary"
                        size="md"
                        onClick={() => navigate("/ingredients/create")}
                    >
                        New Ingredient
                    </Button>
                    <Button
                        variant="outline"
                        size="md"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Import JSON
                    </Button>
                    <ExportMenu
                        data={filteredIngredients}
                        selectedIds={selectedIds}
                        filenamePrefix="ingredients"
                        columns={exportColumns}
                        buttonLabel="Export"
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
                initialValues={filters}
                onApply={(vals) => handleApplyFilters(vals as FilterOptions)}
                onReset={(vals) => setFilters(vals as FilterOptions)}
            />

            {/* Bulk Actions */}
            {selectedIds.size > 0 && (
                <div className={styles.bulkActions}>
                    <span>{selectedIds.size} selected</span>
                    <Button
                        variant="secondary"
                        size="md"
                        onClick={() =>
                            navigate("/ingredients/bulk-edit", {
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
                data={paginatedIngredients}
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
                pageSizeOptions={PAGE_SIZE_OPTIONS}
            />
        </div>
    );
}
