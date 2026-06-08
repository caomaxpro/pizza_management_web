import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, Pizza } from "@phosphor-icons/react";
import { useItemStore } from "../../store/itemStore";
import { Button } from "../../components/ui";
import styles from "./ItemDetail.module.scss";

export default function ItemDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const {
        currentItem: item,
        loading,
        error,
        fetchItemById,
        clearError,
    } = useItemStore();

    useEffect(() => {
        if (id) {
            clearError();
            fetchItemById(Number(id));
        }
    }, [id, fetchItemById, clearError]);

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>⏳ Loading item details...</div>
            </div>
        );
    }

    if (error || !item) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>{error || "Item not found"}</div>
                <Button
                    variant="secondary"
                    className={styles.backBtn}
                    onClick={() => navigate("/items")}
                >
                    ← Back to List
                </Button>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <Button
                    variant="secondary"
                    className={styles.backBtn}
                    onClick={() => navigate("/items")}
                >
                    ← Back to List
                </Button>
                <h1>
                    <Pizza size={32} weight="fill" style={{ marginRight: 8 }} />
                    Item Details
                </h1>
            </div>

            {/* Detail Card */}
            <div className={styles.detailCard}>
                {/* Image Section */}
                <div className={styles.imageSection}>
                    {item.image_url || item.image ? (
                        <img
                            src={item.image_url || item.image}
                            alt={item.name}
                            className={styles.detailImage}
                        />
                    ) : (
                        <div className={styles.noImage}>No Image Available</div>
                    )}
                </div>

                {/* Info Section */}
                <div className={styles.infoSection}>
                    <div className={styles.titleGroup}>
                        <h2>{item.name}</h2>
                        {item.type && (
                            <div className={styles.subType}>{item.type}</div>
                        )}
                    </div>

                    {/* Status Badge */}
                    <div className={styles.statusGroup}>
                        <span
                            className={
                                item.is_active
                                    ? styles.badgeActive
                                    : styles.badgeInactive
                            }
                        >
                            {item.is_active ? (
                                <>
                                    <CheckCircle size={16} weight="fill" />{" "}
                                    Active
                                </>
                            ) : (
                                <>
                                    <XCircle size={16} weight="fill" /> Inactive
                                </>
                            )}
                        </span>
                    </div>

                    {/* Details Grid */}
                    <div className={styles.detailsGrid}>
                        <div className={styles.detailItem}>
                            <span className={styles.label}>Type:</span>
                            <span className={styles.value}>{item.type}</span>
                        </div>
                        <div className={styles.detailItem}>
                            <span className={styles.label}>Price:</span>
                            <span className={styles.value}>
                                ${item.price.toLocaleString()}
                            </span>
                        </div>
                        {item.original_price &&
                            item.original_price !== item.price && (
                                <div className={styles.detailItem}>
                                    <span className={styles.label}>
                                        Original Price:
                                    </span>
                                    <span className={styles.value}>
                                        ${item.original_price.toLocaleString()}
                                    </span>
                                </div>
                            )}
                        {item.description && (
                            <div className={styles.detailItem}>
                                <span className={styles.label}>
                                    Description:
                                </span>
                                <span className={styles.value}>
                                    {item.description}
                                </span>
                            </div>
                        )}
                        <div className={styles.detailItem}>
                            <span className={styles.label}>Created:</span>
                            <span className={styles.value}>
                                {item.created_at
                                    ? new Date(
                                          item.created_at,
                                      ).toLocaleDateString()
                                    : "N/A"}
                            </span>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className={styles.actions}>
                        <Button
                            variant="primary"
                            className={styles.editBtn}
                            onClick={() => navigate(`/items/${item.id}/edit`)}
                        >
                            Edit
                        </Button>
                        <Button
                            variant="secondary"
                            className={styles.backBtn}
                            onClick={() => navigate("/items")}
                        >
                            Back
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
