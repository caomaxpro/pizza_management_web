import { useCallback, useState } from "react";
import { Input, Button } from "../../components/ui";
import SelectField from "../../components/form/fields/SelectField";
import styles from "./IngredientFilter.module.scss";

export interface FilterOptions {
    search: string;
    type: string;
    subType: string;
    status: "all" | "active" | "inactive";
    priceMin: string;
    priceMax: string;
}

export interface IngredientFilterProps {
    filters: FilterOptions;
    onFilterChange: (filters: FilterOptions) => void;
    onApplyFilters: (filters: FilterOptions) => void;
    availableTypes: string[];
    availableSubTypes: string[];
}

const INGREDIENT_TYPES = [
    { value: "", label: "All Types" },
    { value: "dough", label: "Dough" },
    { value: "sauce", label: "Sauce" },
    { value: "cheese", label: "Cheese" },
    { value: "topping", label: "Topping" },
    { value: "extra", label: "Extra" },
];

const STATUS_OPTIONS = [
    { value: "all", label: "All Status" },
    { value: "active", label: "Active Only" },
    { value: "inactive", label: "Inactive Only" },
];

export default function IngredientFilter({
    filters,
    onFilterChange,
    onApplyFilters,
    availableSubTypes,
}: IngredientFilterProps) {
    // Local state for filter inputs (only updated on Apply)
    const [localFilters, setLocalFilters] = useState<FilterOptions>(filters);
    const handleSearchChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            setLocalFilters({ ...localFilters, search: e.target.value });
        },
        [localFilters],
    );

    const handleTypeChange = useCallback(
        (value: string | string[]) => {
            setLocalFilters({
                ...localFilters,
                type: typeof value === "string" ? value : value[0] || "",
                subType: "", // Reset sub-type when changing type
            });
        },
        [localFilters],
    );

    const handleSubTypeChange = useCallback(
        (value: string | string[]) => {
            setLocalFilters({
                ...localFilters,
                subType: typeof value === "string" ? value : value[0] || "",
            });
        },
        [localFilters],
    );

    const handleStatusChange = useCallback(
        (value: string | string[]) => {
            setLocalFilters({
                ...localFilters,
                status: (typeof value === "string"
                    ? value
                    : value[0] || "") as FilterOptions["status"],
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
        const resetFilters: FilterOptions = {
            search: "",
            type: "",
            subType: "",
            status: "all",
            priceMin: "",
            priceMax: "",
        };
        setLocalFilters(resetFilters);
        onFilterChange(resetFilters); // Also reset parent state
    }, [onFilterChange]);

    const handleApplyFiltersClick = useCallback(() => {
        onApplyFilters(localFilters);
    }, [localFilters, onApplyFilters]);

    const hasActiveFilters =
        localFilters.search ||
        localFilters.type ||
        localFilters.subType ||
        localFilters.status !== "all" ||
        localFilters.priceMin ||
        localFilters.priceMax;

    return (
        <div className={styles.filterContainer}>
            <div className={styles.filterHeader}>
                <h3>Filters</h3>
                <div className={styles.filterActions}>
                    {hasActiveFilters && (
                        <>
                            <Button
                                variant="outline"
                                size="md"
                                onClick={handleResetFilters}
                            >
                                Reset Filters
                            </Button>
                            <Button
                                variant="primary"
                                size="md"
                                onClick={handleApplyFiltersClick}
                            >
                                Apply Filters
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

                {/* Type */}
                <div className={styles.filterGroup}>
                    <SelectField
                        label="Type"
                        value={localFilters.type}
                        onChange={handleTypeChange}
                        options={INGREDIENT_TYPES}
                        selectWrapperBackgroundColor="red"
                    />
                </div>

                {/* Sub-Type */}
                {availableSubTypes.length > 0 && (
                    <div className={styles.filterGroup}>
                        <SelectField
                            label="Sub-Type"
                            value={localFilters.subType}
                            onChange={handleSubTypeChange}
                            options={[
                                { value: "", label: "All Sub-Types" },
                                ...availableSubTypes.map((subType) => ({
                                    value: subType,
                                    label: subType,
                                })),
                            ]}
                            selectWrapperBackgroundColor="red"
                        />
                    </div>
                )}

                {/* Status */}
                <div className={styles.filterGroup}>
                    <SelectField
                        label="Status"
                        value={localFilters.status}
                        onChange={handleStatusChange}
                        options={STATUS_OPTIONS}
                        selectWrapperBackgroundColor="white"
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

            {hasActiveFilters && (
                <div className={styles.activeFilters}>
                    {localFilters.search && (
                        <span className={styles.filterTag}>
                            Search: {localFilters.search}
                        </span>
                    )}
                    {localFilters.type && (
                        <span className={styles.filterTag}>
                            Type: {localFilters.type}
                        </span>
                    )}
                    {localFilters.subType && (
                        <span className={styles.filterTag}>
                            Sub-Type: {localFilters.subType}
                        </span>
                    )}
                    {localFilters.status !== "all" && (
                        <span className={styles.filterTag}>
                            Status: {localFilters.status}
                        </span>
                    )}
                    {localFilters.priceMin && (
                        <span className={styles.filterTag}>
                            Min: ${localFilters.priceMin}
                        </span>
                    )}
                    {localFilters.priceMax && (
                        <span className={styles.filterTag}>
                            Max: ${localFilters.priceMax}
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}
