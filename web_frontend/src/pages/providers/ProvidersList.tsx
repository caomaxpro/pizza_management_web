import CustomListTable, {
    type CustomListColumn,
} from "../../components/ui/CustomListTable";
import { Button } from "../../components/ui";
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

interface Provider {
    id: number;
    name: string;
    category: "fresh" | "canned" | "bottled" | "dairy" | "equipment" | "other";
    phone?: string;
    email?: string;
    address?: string;
    isActive: boolean;
    createdAt: string;
}

interface ProvidersListProps {
    loading: boolean;
    paginatedProviders: Provider[];
    totalCount: number;
    currentPage: number;
    pageSize: number;
    totalPages: number;
    sortBy: string;
    sortOrder: "asc" | "desc";
    selectedIds: Set<number>;
    onSelectAll: () => void;
    onSelectOne: (id: number) => void;
    onColumnSort: (column: string) => void;
    onEdit: (provider: Provider) => void;
    onDeleteClick: (id: number) => void;
    onPageChange: (page: number) => void;
    onPageSizeChange: (size: number) => void;
}

export function ProvidersList({
    loading,
    paginatedProviders,
    totalCount,
    currentPage,
    pageSize,
    totalPages,
    sortBy,
    sortOrder,
    selectedIds,
    onSelectAll,
    onSelectOne,
    onColumnSort,
    onEdit,
    onDeleteClick,
    onPageChange,
    onPageSizeChange,
}: ProvidersListProps) {
    // startIdx and getSortIcon removed (unused after switching to CustomListTable)

    const columns: CustomListColumn[] = [
        {
            key: "name",
            title: "Name",
            sortable: true,
            render: (p: Provider) => <strong>{p.name}</strong>,
        },
        {
            key: "category",
            title: "Category",
            sortable: true,
            render: (p: Provider) => (
                <span
                    className={styles.badge}
                    style={{ backgroundColor: CATEGORY_COLORS[p.category] }}
                >
                    {CATEGORY_LABELS[p.category]}
                </span>
            ),
        },
        {
            key: "phone",
            title: "Phone",
            render: (p: Provider) => p.phone || "-",
        },
        {
            key: "email",
            title: "Email",
            render: (p: Provider) => p.email || "-",
        },
        {
            key: "address",
            title: "Address",
            render: (p: Provider) => (
                <div
                    style={{
                        maxWidth: 200,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                    title={p.address}
                >
                    {p.address || "-"}
                </div>
            ),
        },
        {
            key: "isActive",
            title: "Status",
            sortable: true,
            render: (p: Provider) => (
                <span
                    className={`${styles.statusBadge} ${p.isActive ? styles.active : styles.inactive}`}
                >
                    {p.isActive ? "Active" : "Inactive"}
                </span>
            ),
        },
        {
            key: "actions",
            title: "Actions",
            render: (p: Provider) => (
                <div style={{ display: "flex", gap: 8 }}>
                    <Button
                        size="sm"
                        variant="outline"
                        className={styles.btnView}
                        onClick={() => onEdit(p)}
                    >
                        View
                    </Button>
                    <Button
                        size="sm"
                        variant="secondary"
                        className={styles.btnEdit}
                        onClick={() => onEdit(p)}
                    >
                        Edit
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className={styles.btnDelete}
                        onClick={() => onDeleteClick(p.id)}
                    >
                        Delete
                    </Button>
                </div>
            ),
            headerClassName: styles.actionsCol,
            className: styles.actionsCol,
            width: 160,
        },
    ];

    if (loading) {
        return (
            <div className={styles.emptyState}>
                <p>Loading providers...</p>
            </div>
        );
    }

    if (paginatedProviders.length === 0) {
        return (
            <div className={styles.emptyState}>
                <p>No providers found</p>
            </div>
        );
    }

    return (
        <CustomListTable
            columns={columns}
            data={paginatedProviders}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onColumnSort}
            selectedIds={new Set(Array.from(selectedIds))}
            onSelectAll={onSelectAll}
            onSelectOne={(id) => onSelectOne(Number(id))}
            showCheckboxes
            currentPage={currentPage}
            totalPages={totalPages}
            totalCount={totalCount}
            pageSize={pageSize}
            onPageChange={onPageChange}
            onPageSizeChange={(e) => onPageSizeChange(Number(e.target.value))}
            pageSizeOptions={[10, 20, 50, 100]}
        />
    );
}
