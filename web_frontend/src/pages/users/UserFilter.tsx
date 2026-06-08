import { useState, useCallback } from "react";
import { Input, Select, Button } from "../../components/ui";
import styles from "./UserFilter.module.scss";

export interface UserFilterOptions {
    search: string;
    role: "all" | "admin" | "manager" | "staff";
    status: "all" | "active" | "inactive";
}

export interface UserFilterProps {
    filters: UserFilterOptions;
    onApplyFilters: (filters: UserFilterOptions) => void;
}

const ROLE_OPTIONS = [
    { value: "all", label: "All Roles" },
    { value: "admin", label: "Admin" },
    { value: "manager", label: "Manager" },
    { value: "staff", label: "Staff" },
];

const STATUS_OPTIONS = [
    { value: "all", label: "All Status" },
    { value: "active", label: "Active Only" },
    { value: "inactive", label: "Inactive Only" },
];

export default function UserFilter({
    filters,
    onApplyFilters,
}: UserFilterProps) {
    const [localFilters, setLocalFilters] =
        useState<UserFilterOptions>(filters);

    const handleSearchChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            setLocalFilters({ ...localFilters, search: e.target.value });
        },
        [localFilters],
    );

    const handleRoleChange = useCallback(
        (value: string | string[]) => {
            setLocalFilters({
                ...localFilters,
                role: (typeof value === "string"
                    ? value
                    : value[0] || "all") as UserFilterOptions["role"],
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
                    : value[0] || "all") as UserFilterOptions["status"],
            });
        },
        [localFilters],
    );

    const handleApply = () => {
        onApplyFilters(localFilters);
    };

    return (
        <div className={styles.filterBox}>
            <h3 className={styles.filterTitle}>Filters</h3>
            <div className={styles.filterGrid}>
                <div>
                    <label className={styles.filterLabel}>Search</label>
                    <Input
                        className={styles.filterInput}
                        placeholder="Search by email..."
                        value={localFilters.search}
                        onChange={handleSearchChange}
                    />
                </div>
                <div>
                    <label className={styles.filterLabel}>Role</label>
                    <Select
                        className={styles.filterSelect}
                        value={localFilters.role}
                        onChange={handleRoleChange}
                        options={ROLE_OPTIONS}
                    />
                </div>
                <div>
                    <label className={styles.filterLabel}>Status</label>
                    <Select
                        className={styles.filterSelect}
                        value={localFilters.status}
                        onChange={handleStatusChange}
                        options={STATUS_OPTIONS}
                    />
                </div>
            </div>
            <div className={styles.filterActions}>
                <Button variant="primary" onClick={handleApply}>
                    Apply Filters
                </Button>
            </div>
        </div>
    );
}
