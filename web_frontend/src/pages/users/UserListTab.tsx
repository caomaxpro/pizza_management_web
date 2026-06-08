import { useCallback, useEffect, useState } from "react";
import { Eye, PlusCircle, Trash } from "@phosphor-icons/react";
import { Button } from "../../components/ui";
import CustomListTable, {
    type CustomListColumn,
} from "../../components/ui/CustomListTable";
import styles from "./Users.module.scss";
import UserFilter, { type UserFilterOptions } from "./UserFilter";
import UserFormModal from "./UserFormModal";
import AssignTaskModal from "./AssignTaskModal";
import UserDetailsModal from "./UserDetailsModal";
import { usersAPI } from "../../services/users";
import type { User } from "../../types/user";

const ROLE_BADGE: Record<string, string> = {
    admin: styles.adminBadge,
    manager: styles.managerBadge,
    staff: styles.staffBadge,
    user: styles.userBadge,
};

export default function UserListTab() {
    const [users, setUsers] = useState<User[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [appliedFilters, setAppliedFilters] = useState<UserFilterOptions>({
        search: "",
        role: "all",
        status: "all",
    });
    // null = closed, undefined = create mode, User = edit mode
    const [modalUser, setModalUser] = useState<User | null | undefined>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<string>("username");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [selectedIds, setSelectedIds] = useState<Set<number | string>>(
        new Set(),
    );
    // null = closed, User = open for that user
    const [assignUser, setAssignUser] = useState<User | null>(null);
    // null = closed, User = open for viewing details
    const [detailsUser, setDetailsUser] = useState<User | null>(null);

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const ordering = sortOrder === "desc" ? `-${sortBy}` : sortBy;
            const res = await usersAPI.list({
                search: appliedFilters.search || undefined,
                role:
                    appliedFilters.role !== "all"
                        ? appliedFilters.role
                        : undefined,
                status:
                    appliedFilters.status !== "all"
                        ? appliedFilters.status
                        : undefined,
                ordering,
                page: currentPage,
                page_size: pageSize,
            });
            setUsers(res.data.results);
            setTotalCount(res.data.count);
        } catch (err: unknown) {
            const msg =
                (err as { response?: { data?: { detail?: string } } })?.response
                    ?.data?.detail ?? "Failed to load users.";
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [appliedFilters, currentPage, pageSize, sortBy, sortOrder]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [appliedFilters]);

    const totalPages = Math.ceil(totalCount / pageSize);

    const handleFormSuccess = (saved: User) => {
        setUsers((prev) => {
            const idx = prev.findIndex((u) => u.id === saved.id);
            return idx >= 0
                ? prev.map((u) => (u.id === saved.id ? saved : u))
                : [saved, ...prev];
        });
        fetchUsers();
    };

    const handleDelete = async (user: User) => {
        if (
            !confirm(
                `Delete user "${user.username ?? user.email}"? This cannot be undone.`,
            )
        )
            return;
        setActionError(null);
        try {
            await usersAPI.delete(user.id);
            setUsers((prev) => prev.filter((u) => u.id !== user.id));
        } catch (err: unknown) {
            const msg =
                (err as { response?: { data?: { detail?: string } } })?.response
                    ?.data?.detail ?? "Failed to delete user.";
            setActionError(msg);
        }
    };

    const handleSort = useCallback(
        (column: string) => {
            if (sortBy === column) {
                // Toggle sort order
                setSortOrder(sortOrder === "asc" ? "desc" : "asc");
            } else {
                // New column, sort ascending
                setSortBy(column);
                setSortOrder("asc");
            }
            setCurrentPage(1);
        },
        [sortBy, sortOrder],
    );

    const handlePageSizeChange = useCallback(
        (e: React.ChangeEvent<HTMLSelectElement>) => {
            setPageSize(Number(e.target.value));
            setCurrentPage(1);
        },
        [],
    );

    const handleSelectAll = useCallback(() => {
        if (selectedIds.size === users.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(users.map((u) => u.id)));
        }
    }, [selectedIds.size, users]);

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
        if (!confirm(`Delete ${selectedIds.size} users?`)) return;
        try {
            const idsToDelete = Array.from(selectedIds).map((v) => Number(v));
            await Promise.all(idsToDelete.map((id) => usersAPI.delete(id)));
            setUsers((prev) =>
                prev.filter((u) => !idsToDelete.includes(Number(u.id))),
            );
            setSelectedIds(new Set());
        } catch {
            setActionError("Failed to delete users.");
        }
    }, [selectedIds]);

    const columns: CustomListColumn[] = [
        {
            key: "username",
            title: "Username",
            sortable: true,
            render: (row: User) => row.username ?? "—",
        },
        {
            key: "role",
            title: "Role",
            sortable: true,
            render: (row: User) => (
                <span
                    className={
                        ROLE_BADGE[row.role ?? "user"] ?? styles.userBadge
                    }
                >
                    {row.role ?? "user"}
                </span>
            ),
        },
        {
            key: "is_active",
            title: "Status",
            sortable: true,
            render: (row: User) => (
                <span
                    className={
                        row.is_active
                            ? styles.activeBadge
                            : styles.inactiveBadge
                    }
                >
                    {row.is_active ? "Active" : "Inactive"}
                </span>
            ),
        },
        {
            key: "assign",
            title: "Assign",
            render: (row: User) => (
                <Button
                    size="sm"
                    variant="outline"
                    className={styles.assignBtn}
                    disabled={row.role !== "staff"}
                    onClick={() => setAssignUser(row)}
                >
                    Assign
                </Button>
            ),
        },
        {
            key: "actions",
            title: "Actions",
            align: "right",
            render: (row: User) => (
                <span className={styles.actions}>
                    <Button
                        size="sm"
                        variant="outline"
                        className={styles.viewBtn}
                        onClick={() => setDetailsUser(row)}
                    >
                        <Eye size={16} /> View
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className={styles.editBtn}
                        onClick={() => setModalUser(row)}
                    >
                        Edit
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className={styles.deleteBtn}
                        onClick={() => handleDelete(row)}
                    >
                        <Trash size={16} /> Delete
                    </Button>
                </span>
            ),
        },
    ];

    return (
        <>
            {/* ── List header ── */}
            <div className={styles.listHeader}>
                {actionError && (
                    <div className={styles.error}>{actionError}</div>
                )}
                <Button
                    variant="primary"
                    onClick={() => setModalUser(undefined)}
                >
                    <PlusCircle size={18} weight="fill" /> New User
                </Button>
            </div>

            <UserFilter
                filters={appliedFilters}
                onApplyFilters={setAppliedFilters}
            />

            {/* Bulk Actions */}
            {selectedIds.size > 0 && (
                <div className={styles.bulkActions}>
                    <span>{selectedIds.size} selected</span>
                    <Button
                        variant="outline"
                        size="md"
                        onClick={handleBulkDelete}
                    >
                        <Trash size={18} /> Delete
                    </Button>
                </div>
            )}

            {loading && users.length === 0 ? (
                <div className={styles.loading}>Loading users…</div>
            ) : error ? (
                <div className={styles.error}>{error}</div>
            ) : (
                <CustomListTable
                    columns={columns}
                    data={users}
                    rowKey={(row) => row.id}
                    sortBy={sortBy}
                    sortOrder={sortOrder}
                    onSort={handleSort}
                    selectedIds={selectedIds}
                    onSelectAll={handleSelectAll}
                    onSelectOne={handleSelectOne}
                    showCheckboxes
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalCount={totalCount}
                    pageSize={pageSize}
                    onPageChange={setCurrentPage}
                    onPageSizeChange={handlePageSizeChange}
                    pageSizeOptions={[10, 20, 50, 100]}
                />
            )}

            <UserFormModal
                isOpen={modalUser !== null}
                user={modalUser}
                onClose={() => setModalUser(null)}
                onSuccess={handleFormSuccess}
            />

            <AssignTaskModal
                isOpen={assignUser !== null}
                user={assignUser}
                onClose={() => setAssignUser(null)}
                onSuccess={(updated) => {
                    setUsers((prev) =>
                        prev.map((u) => (u.id === updated.id ? updated : u)),
                    );
                    setAssignUser(null);
                }}
            />

            <UserDetailsModal
                isOpen={detailsUser !== null}
                user={detailsUser}
                onClose={() => setDetailsUser(null)}
                onEdit={(user) => {
                    setDetailsUser(null);
                    setModalUser(user);
                }}
            />
        </>
    );
}
