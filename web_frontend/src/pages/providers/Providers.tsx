import { useState, useEffect } from "react";
import { X } from "@phosphor-icons/react";
import styles from "./Providers.module.scss";
import { Button } from "../../components/ui/Button";
import { ProviderFilter } from "./ProviderFilter";
import { ProvidersList } from "./ProvidersList";
import providerAPI, {
    type Provider as APIProvider,
} from "../../services/provider";

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

interface FormData {
    name: string;
    category: "fresh" | "canned" | "bottled" | "dairy" | "equipment" | "other";
    phone: string;
    email: string;
    address: string;
    isActive: boolean;
}

const CATEGORY_LABELS: Record<string, string> = {
    fresh: "Fresh Ingredients",
    canned: "Canned/Packaged",
    bottled: "Beverages/Oils",
    dairy: "Dairy Products",
    equipment: "Equipment/Supplies",
    other: "Other",
};

export default function Providers() {
    const [providers, setProviders] = useState<Provider[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedCategory, setSelectedCategory] = useState<string | null>(
        null,
    );
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(
        null,
    );
    const [sortBy, setSortBy] = useState<string>("name");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [formData, setFormData] = useState<FormData>({
        name: "",
        category: "fresh",
        phone: "",
        email: "",
        address: "",
        isActive: true,
    });

    // Fetch providers on component mount
    useEffect(() => {
        loadProviders();
    }, []);

    // Auto-hide success message after 3 seconds
    useEffect(() => {
        if (successMessage) {
            const timer = setTimeout(() => setSuccessMessage(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMessage]);

    const loadProviders = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await providerAPI.list();
            // Convert snake_case to camelCase
            const converted = data.map((p: APIProvider) => ({
                id: p.id,
                name: p.name,
                category: p.category,
                phone: p.phone,
                email: p.email,
                address: p.address,
                isActive: p.is_active,
                createdAt: p.created_at,
            }));
            setProviders(converted);
        } catch (err) {
            console.error("Failed to load providers:", err);
            setError("Failed to load providers. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    // Filter, sort, and paginate providers
    const filteredAndSortedProviders = providers
        .filter((provider) => {
            const matchesSearch =
                provider.name
                    .toLowerCase()
                    .includes(searchTerm.toLowerCase()) ||
                provider.email
                    ?.toLowerCase()
                    .includes(searchTerm.toLowerCase()) ||
                provider.phone?.includes(searchTerm);
            const matchesCategory =
                !selectedCategory || provider.category === selectedCategory;
            return matchesSearch && matchesCategory;
        })
        .sort((a, b) => {
            let aValue: string | number | boolean = "";
            let bValue: string | number | boolean = "";

            switch (sortBy) {
                case "name":
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case "category":
                    aValue = a.category.toLowerCase();
                    bValue = b.category.toLowerCase();
                    break;
                case "isActive":
                    aValue = a.isActive ? 1 : 0;
                    bValue = b.isActive ? 1 : 0;
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });

    const totalCount = filteredAndSortedProviders.length;
    const totalPages = Math.ceil(totalCount / pageSize);
    const startIdx = (currentPage - 1) * pageSize;
    const paginatedProviders = filteredAndSortedProviders.slice(
        startIdx,
        startIdx + pageSize,
    );

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name.trim()) {
            setError("Provider name is required");
            return;
        }

        try {
            setError(null);
            if (editingId) {
                // Update existing provider
                await providerAPI.partialUpdate(editingId, {
                    name: formData.name,
                    category: formData.category,
                    phone: formData.phone,
                    email: formData.email,
                    address: formData.address,
                    is_active: formData.isActive,
                });
                setSuccessMessage("Provider updated successfully");
            } else {
                // Create new provider
                await providerAPI.create({
                    name: formData.name,
                    category: formData.category,
                    phone: formData.phone,
                    email: formData.email,
                    address: formData.address,
                    is_active: formData.isActive,
                });
                setSuccessMessage("Provider created successfully");
            }

            resetForm();
            setShowForm(false);
            await loadProviders();
        } catch (err) {
            console.error("Failed to save provider:", err);
            setError("Failed to save provider. Please try again.");
        }
    };

    const resetForm = () => {
        setFormData({
            name: "",
            category: "fresh",
            phone: "",
            email: "",
            address: "",
            isActive: true,
        });
        setEditingId(null);
    };

    const handleEdit = (provider: Provider) => {
        setFormData({
            name: provider.name,
            category: provider.category,
            phone: provider.phone || "",
            email: provider.email || "",
            address: provider.address || "",
            isActive: provider.isActive,
        });
        setEditingId(provider.id);
        setShowForm(true);
    };

    const handleDelete = async (id: number) => {
        try {
            setError(null);
            await providerAPI.delete(id);
            setSuccessMessage("Provider deleted successfully");
            setShowDeleteConfirm(null);
            await loadProviders();
        } catch (err) {
            console.error("Failed to delete provider:", err);
            setError("Failed to delete provider. Please try again.");
        }
    };

    const handleCancel = () => {
        resetForm();
        setShowForm(false);
    };

    const handleSelectAll = () => {
        if (selectedIds.size === paginatedProviders.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedProviders.map((p) => p.id)));
        }
    };

    const handleSelectOne = (id: number) => {
        setSelectedIds((prev) => {
            const newSelected = new Set(prev);
            if (newSelected.has(id)) {
                newSelected.delete(id);
            } else {
                newSelected.add(id);
            }
            return newSelected;
        });
    };

    const handleBulkDelete = async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} providers?`)) return;
        try {
            setError(null);
            await providerAPI.deleteMany(Array.from(selectedIds));
            setSuccessMessage(
                `${selectedIds.size} provider(s) deleted successfully`,
            );
            setSelectedIds(new Set());
            await loadProviders();
        } catch (err) {
            console.error("Failed to delete providers:", err);
            setError("Failed to delete providers. Please try again.");
        }
    };

    const handleColumnSort = (column: string) => {
        if (sortBy === column) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortBy(column);
            setSortOrder("asc");
        }
        setCurrentPage(1);
    };

    const handlePageChange = (page: number) => {
        if (page >= 1 && page <= totalPages) setCurrentPage(page);
    };

    const handlePageSizeChange = (size: number) => {
        setPageSize(size);
        setCurrentPage(1);
    };

    // Get category counts
    const categoryCounts: Record<string, number> = {
        fresh: 0,
        canned: 0,
        bottled: 0,
        dairy: 0,
        equipment: 0,
        other: 0,
    };
    providers.forEach((p) => {
        categoryCounts[p.category]++;
    });

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.headerTop}>
                    <div>
                        <h1>Providers</h1>
                        <p className={styles.subtitle}>
                            Manage suppliers and providers
                        </p>
                    </div>
                    <Button
                        variant="primary"
                        size="md"
                        onClick={() => setShowForm(true)}
                    >
                        Add Provider
                    </Button>
                </div>

                {/* Bulk Actions */}
                {selectedIds.size > 0 && (
                    <div className={styles.bulkActions}>
                        <span>{selectedIds.size} selected</span>
                        <Button
                            variant="outline"
                            size="md"
                            onClick={handleBulkDelete}
                        >
                            Delete
                        </Button>
                    </div>
                )}

                {/* Filter Section */}
                <ProviderFilter
                    searchTerm={searchTerm}
                    onSearchChange={setSearchTerm}
                    selectedCategory={selectedCategory}
                    onCategoryChange={setSelectedCategory}
                    totalProviders={providers.length}
                    categoryCounts={categoryCounts}
                />
            </div>

            {/* Error Message */}
            {error && (
                <div
                    style={{
                        padding: "1rem",
                        backgroundColor: "#fee2e2",
                        color: "#991b1b",
                        borderRadius: "0.5rem",
                        marginBottom: "1rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <span>{error}</span>
                    <button
                        onClick={() => setError(null)}
                        style={{
                            background: "none",
                            border: "none",
                            color: "#991b1b",
                            cursor: "pointer",
                            padding: "0",
                        }}
                    >
                        <X size={20} />
                    </button>
                </div>
            )}

            {/* Success Message */}
            {successMessage && (
                <div
                    style={{
                        padding: "1rem",
                        backgroundColor: "#dcfce7",
                        color: "#166534",
                        borderRadius: "0.5rem",
                        marginBottom: "1rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <span>{successMessage}</span>
                    <button
                        onClick={() => setSuccessMessage(null)}
                        style={{
                            background: "none",
                            border: "none",
                            color: "#166534",
                            cursor: "pointer",
                            padding: "0",
                        }}
                    >
                        <X size={20} />
                    </button>
                </div>
            )}

            {/* Providers Table */}
            <div className={styles.content}>
                <ProvidersList
                    loading={loading}
                    paginatedProviders={paginatedProviders}
                    totalCount={totalCount}
                    currentPage={currentPage}
                    pageSize={pageSize}
                    totalPages={totalPages}
                    sortBy={sortBy}
                    sortOrder={sortOrder}
                    selectedIds={selectedIds}
                    onSelectAll={handleSelectAll}
                    onSelectOne={handleSelectOne}
                    onColumnSort={handleColumnSort}
                    onEdit={handleEdit}
                    onDeleteClick={(id) => setShowDeleteConfirm(id)}
                    onPageChange={handlePageChange}
                    onPageSizeChange={handlePageSizeChange}
                />
            </div>
            {/* Add/Edit Modal */}
            {showForm && (
                <div
                    className={styles.modalOverlay}
                    onClick={() => handleCancel()}
                >
                    <div
                        className={styles.modal}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className={styles.modalHeader}>
                            <h2>
                                {editingId
                                    ? "Edit Provider"
                                    : "Add New Provider"}
                            </h2>
                            <button
                                className={styles.closeBtn}
                                onClick={handleCancel}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className={styles.form}>
                            <div className={styles.formGroup}>
                                <label htmlFor="name">Provider Name *</label>
                                <input
                                    id="name"
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            name: e.target.value,
                                        })
                                    }
                                    placeholder="Enter provider name"
                                    required
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="category">Category *</label>
                                <select
                                    id="category"
                                    value={formData.category}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            category: e.target
                                                .value as Provider["category"],
                                        })
                                    }
                                >
                                    {Object.entries(CATEGORY_LABELS).map(
                                        ([key, label]) => (
                                            <option key={key} value={key}>
                                                {label}
                                            </option>
                                        ),
                                    )}
                                </select>
                            </div>

                            <div className={styles.formRow}>
                                <div className={styles.formGroup}>
                                    <label htmlFor="phone">Phone</label>
                                    <input
                                        id="phone"
                                        type="tel"
                                        value={formData.phone}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                phone: e.target.value,
                                            })
                                        }
                                        placeholder="Phone number"
                                    />
                                </div>

                                <div className={styles.formGroup}>
                                    <label htmlFor="email">Email</label>
                                    <input
                                        id="email"
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                email: e.target.value,
                                            })
                                        }
                                        placeholder="Email address"
                                    />
                                </div>
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="address">Address</label>
                                <textarea
                                    id="address"
                                    value={formData.address}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            address: e.target.value,
                                        })
                                    }
                                    placeholder="Complete address"
                                    rows={3}
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="isActive">
                                    <input
                                        id="isActive"
                                        type="checkbox"
                                        checked={formData.isActive}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                isActive: e.target.checked,
                                            })
                                        }
                                    />
                                    <span>Mark as Active</span>
                                </label>
                            </div>

                            <div className={styles.formActions}>
                                <Button
                                    variant="secondary"
                                    size="md"
                                    type="button"
                                    onClick={handleCancel}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    variant="primary"
                                    size="md"
                                    type="submit"
                                >
                                    {editingId
                                        ? "Update Provider"
                                        : "Add Provider"}
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm !== null && (
                <div
                    className={styles.modalOverlay}
                    onClick={() => setShowDeleteConfirm(null)}
                >
                    <div
                        className={styles.confirmModal}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3>Delete Provider?</h3>
                        <p>
                            Are you sure you want to delete{" "}
                            <strong>
                                {
                                    providers.find(
                                        (p) => p.id === showDeleteConfirm,
                                    )?.name
                                }
                            </strong>
                            ?
                        </p>
                        <div className={styles.confirmActions}>
                            <Button
                                variant="secondary"
                                size="md"
                                onClick={() => setShowDeleteConfirm(null)}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="primary"
                                size="md"
                                onClick={() => handleDelete(showDeleteConfirm)}
                            >
                                Delete
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
