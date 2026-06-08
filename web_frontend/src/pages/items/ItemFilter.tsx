/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useCallback } from "react";
import { Input, Select, Button } from "../../components/ui";
import styles from "./ItemFilter.module.scss";

export interface ItemFilterOptions {
    search: string;
    status: "all" | "active" | "inactive";
    priceMin: string;
    priceMax: string;
}

export interface ItemFilterProps {
    filters: ItemFilterOptions;
    onFilterChange: (filters: ItemFilterOptions) => void;
    onApplyFilters: (filters: ItemFilterOptions) => void;
    availableCategories: string[];
}

const CATEGORY_OPTIONS = [
    { value: "", label: "All Categories" },
    { value: "pizza", label: "Pizza" },
    { value: "burger", label: "Burger" },
    { value: "salad", label: "Salad" },
    { value: "drink", label: "Drink" },
    { value: "dessert", label: "Dessert" },
];

const STATUS_OPTIONS = [
    { value: "all", label: "All Status" },
    { value: "active", label: "Active Only" },
    { value: "inactive", label: "Inactive Only" },
];

export default function ItemFilter({
    filters,
    onFilterChange,
    onApplyFilters,
    availableCategories,
}: ItemFilterProps) {
    const [localFilters, setLocalFilters] =
        useState<ItemFilterOptions>(filters);

    const handleSearchChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            setLocalFilters({ ...localFilters, search: e.target.value });
        },
        [localFilters],
    );

    const handleCategoryChange = useCallback(
        (value: string | string[], _event?: React.ChangeEvent<any>) => {
            setLocalFilters({
                ...localFilters,
                category: typeof value === "string" ? value : value[0] || "",
            });
        },
        [localFilters],
    );

    const handleStatusChange = useCallback(
        (value: string | string[], _event?: React.ChangeEvent<any>) => {
            setLocalFilters({
                ...localFilters,
                status: (typeof value === "string"
                    ? value
                    : value[0] || "all") as ItemFilterOptions["status"],
            });
        },
        [localFilters],
    );

    const handlePriceMinChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            setLocalFilters({ ...localFilters, priceMin: e.target.value });
        },
        [localFilters],
    );

    const handlePriceMaxChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            setLocalFilters({ ...localFilters, priceMax: e.target.value });
        },
        [localFilters],
    );

    const handleResetFilters = useCallback(() => {
        const resetFilters: ItemFilterOptions = {
            search: "",
            category: "",
            status: "all",
            priceMin: "",
            priceMax: "",
        };
        setLocalFilters(resetFilters);
        onFilterChange(resetFilters);
    }, [onFilterChange]);

    const handleApplyFiltersClick = useCallback(() => {
        onApplyFilters(localFilters);
    }, [localFilters, onApplyFilters]);

    const hasActiveFilters =
        localFilters.search ||
        localFilters.category ||
        localFilters.status !== "all" ||
        localFilters.priceMin ||
        localFilters.priceMax;

    return (
        <div className={styles.filterContainer}>
            <div className={styles.filterHeader}>
                <h3>🔍 Filters</h3>
                <div className={styles.filterActions}>
                    {hasActiveFilters && (
                        <>
                            <Button
                                variant="outline"
                                size="md"
                                onClick={handleResetFilters}
                            >
                                ↻ Reset Filters
                            </Button>
                            <Button
                                variant="primary"
                                size="md"
                                onClick={handleApplyFiltersClick}
                            >
                                ✅ Apply Filters
                            </Button>
                        </>
                    )}
                </div>
            </div>

            <div className={styles.filterGrid}>
                {/* Search */}
                <div className={styles.filterGroup}>
                    <Input
                        label="Search"
                        type="text"
                        placeholder="Search by name..."
                        value={localFilters.search}
                        onChange={handleSearchChange}
                    />
                </div>

                {/* Category */}
                <div className={styles.filterGroup}>
                    <Select
                        label="Category"
                        value={localFilters.category}
                        onChange={handleCategoryChange}
                        options={CATEGORY_OPTIONS}
                    />
                </div>

                {/* Status */}
                <div className={styles.filterGroup}>
                    <Select
                        label="Status"
                        value={localFilters.status}
                        onChange={handleStatusChange}
                        options={STATUS_OPTIONS}
                    />
                </div>

                {/* Price Range */}
                <div className={styles.filterGroup}>
                    <Input
                        label="Min Price ($)"
                        type="number"
                        placeholder="0"
                        value={localFilters.priceMin}
                        onChange={handlePriceMinChange}
                        min="0"
                        step="0.01"
                    />
                </div>

                <div className={styles.filterGroup}>
                    <Input
                        label="Max Price ($)"
                        type="number"
                        placeholder="999"
                        value={localFilters.priceMax}
                        onChange={handlePriceMaxChange}
                        min="0"
                        step="0.01"
                    />
                </div>
            </div>
        </div>
    );
}
