import { useMemo, useCallback } from "react";
import { Filter } from "@components/ui";
import SearchField from "@components/form/fields/SearchField";
import SelectField from "@components/form/fields/SelectField";
import { UNIT_CHOICES } from "../../services/inventory";

export interface InventoryFilters {
    search?: string;
    unit?: string;
    is_active?: string;
    needs_reorder?: boolean;
}

interface InventoryFilterProps {
    onFilter: (filters: InventoryFilters) => void;
}

export default function InventoryFilter({ onFilter }: InventoryFilterProps) {
    // Memoize fields array to prevent infinite re-renders
    const fields = useMemo(
        () => [
            <SearchField
                key="search"
                name="search"
                label="Search"
                placeholder="Item name"
                autoSearch={true}
                style={{ width: "400px" }}
            />,
            <SelectField
                key="unit"
                name="unit"
                label="Unit"
                options={[{ value: "", label: "Any" }, ...UNIT_CHOICES]}
                style={{ width: "180px" }}
            />,
            <SelectField
                key="is_active"
                name="is_active"
                label="Status"
                options={[
                    { value: "", label: "Any" },
                    { value: "true", label: "Active" },
                    { value: "false", label: "Inactive" },
                ]}
                style={{ width: "180px" }}
            />,
            <SelectField
                key="needs_reorder"
                name="needs_reorder"
                label="Low Stock"
                options={[
                    { value: "", label: "Any" },
                    { value: "true", label: "Yes" },
                    { value: "false", label: "No" },
                ]}
                style={{ width: "180px" }}
            />,
        ],
        [],
    );

    const handleApply = useCallback(
        (values: Record<string, string>) => {
            onFilter({
                search: values.search || undefined,
                unit: values.unit || undefined,
                is_active: values.is_active || undefined,
                needs_reorder:
                    values.needs_reorder === "true"
                        ? true
                        : values.needs_reorder === "false"
                          ? false
                          : undefined,
            });
        },
        [onFilter],
    );

    const handleReset = useCallback(() => {
        onFilter({});
    }, [onFilter]);

    return (
        <Filter
            fields={fields}
            initialValues={{}}
            onApply={handleApply}
            autoApply={true}
            onReset={handleReset}
            applyLabel="Apply"
            resetLabel="Clear"
        />
    );
}
