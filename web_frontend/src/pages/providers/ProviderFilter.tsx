import { SearchBar } from "../../components/ui/SearchBar";
import styles from "./Providers.module.scss";

const CATEGORY_COLORS: Record<string, string> = {
    fresh: "#10b981",
    canned: "#f59e0b",
    bottled: "#3b82f6",
    dairy: "#8b5cf6",
    equipment: "#6366f1",
    other: "#6b7280",
};

const CATEGORY_LABELS: Record<string, string> = {
    fresh: "Fresh Ingredients",
    canned: "Canned/Packaged",
    bottled: "Beverages/Oils",
    dairy: "Dairy Products",
    equipment: "Equipment/Supplies",
    other: "Other",
};

interface ProviderFilterProps {
    searchTerm: string;
    onSearchChange: (value: string) => void;
    selectedCategory: string | null;
    onCategoryChange: (category: string | null) => void;
    totalProviders: number;
    categoryCounts: Record<string, number>;
}

export function ProviderFilter({
    searchTerm,
    onSearchChange,
    selectedCategory,
    onCategoryChange,
    totalProviders,
    categoryCounts,
}: ProviderFilterProps) {
    return (
        <>
            {/* Search Bar */}
            <div className={styles.searchBar}>
                <SearchBar
                    value={searchTerm}
                    onChange={onSearchChange}
                    placeholder="Search by name, email, or phone..."
                    debounceMs={300}
                    style={{
                        width: 450,
                    }}
                />
            </div>

            {/* Category Filter */}
            <div className={styles.filterSection}>
                <button
                    className={`${styles.filterBtn} ${!selectedCategory ? styles.active : ""}`}
                    onClick={() => onCategoryChange(null)}
                >
                    All ({totalProviders})
                </button>
                {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                    <button
                        key={key}
                        className={`${styles.filterBtn} ${selectedCategory === key ? styles.active : ""}`}
                        onClick={() => onCategoryChange(key)}
                        style={{
                            borderLeftColor: CATEGORY_COLORS[key],
                            ...(selectedCategory === key
                                ? {
                                      backgroundColor:
                                          CATEGORY_COLORS[key] + "15",
                                  }
                                : {}),
                        }}
                    >
                        {label} ({categoryCounts[key] || 0})
                    </button>
                ))}
            </div>
        </>
    );
}
