/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
    CheckCircle,
    XCircle,
    PencilSimple,
    Pizza,
} from "@phosphor-icons/react";
import { ingredientAPI, type Ingredient } from "../../services/ingredients";
import MessageCard from "@components/form/fields/MessageCard";
import styles from "./IngredientDetail.module.scss";

export default function IngredientDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const [ingredient, setIngredient] = useState<Ingredient | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Get success message from navigation state (if user just created an ingredient)
    const successMessage = (location.state as any)?.successMessage || null;
    const newData = (location.state as any)?.newData || null;

    useEffect(() => {
        if (!id) {
            setError("Invalid ingredient ID");
            setLoading(false);
            return;
        }

        const fetchIngredient = async () => {
            try {
                setLoading(true);

                // If we just created this ingredient, use the new data immediately
                if (newData && newData.id === Number(id)) {
                    console.log(
                        "[IngredientDetail] Using newly created data:",
                        newData,
                    );
                    setIngredient(newData);
                    setError(null);
                    setLoading(false);
                    return;
                }

                const response = await ingredientAPI.get(Number(id));
                console.log(
                    "[IngredientDetail] Fetched ingredient detail:",
                    response.data,
                );
                setIngredient(response.data);
                setError(null);
            } catch (err) {
                setError("Failed to load ingredient details");
                console.error(
                    "[IngredientDetail] Failed to fetch ingredient:",
                    err,
                );
            } finally {
                setLoading(false);
            }
        };

        fetchIngredient();
    }, [id, newData]);

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>
                    ⏳ Loading ingredient details...
                </div>
            </div>
        );
    }

    if (error || !ingredient) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>
                    {error || "Ingredient not found"}
                </div>
                <button
                    className={styles.backBtn}
                    onClick={() => navigate("/ingredients")}
                >
                    ← Back to List
                </button>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <button
                    className={styles.backBtn}
                    onClick={() => navigate("/ingredients")}
                >
                    ← Back to List
                </button>
                <h1>
                    <Pizza size={32} weight="fill" style={{ marginRight: 8 }} />
                    Ingredient Details
                </h1>
            </div>

            {/* Success Message */}
            {successMessage && (
                <MessageCard
                    message={successMessage}
                    variant="success"
                    dismissible={true}
                    marginTop="10px"
                    marginBottom="10px"
                />
            )}

            {/* Detail Card */}
            <div className={styles.detailCard}>
                {/* Image Section */}
                <div className={styles.imageSection}>
                    {ingredient.image_url ? (
                        <img
                            src={ingredient.image_url}
                            alt={ingredient.name}
                            className={styles.detailImage}
                        />
                    ) : (
                        <div className={styles.noImage}>No Image Available</div>
                    )}
                </div>

                {/* Info Section */}
                <div className={styles.infoSection}>
                    <div className={styles.titleGroup}>
                        <h2>{ingredient.name}</h2>
                        {ingredient.sub_type && (
                            <div className={styles.subType}>
                                {ingredient.sub_type}
                            </div>
                        )}
                    </div>

                    {/* Status Badge */}
                    <div className={styles.statusGroup}>
                        <span
                            className={
                                ingredient.is_active
                                    ? styles.badgeActive
                                    : styles.badgeInactive
                            }
                        >
                            {ingredient.is_active ? (
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
                            <span className={styles.value}>
                                {ingredient.type}
                            </span>
                        </div>

                        <div className={styles.detailItem}>
                            <span className={styles.label}>Price:</span>
                            <span className={styles.value}>
                                ${ingredient.price.toLocaleString()}
                            </span>
                        </div>

                        {ingredient.original_price &&
                            ingredient.original_price !== ingredient.price && (
                                <div className={styles.detailItem}>
                                    <span className={styles.label}>
                                        Original Price:
                                    </span>
                                    <span className={styles.value}>
                                        $
                                        {ingredient.original_price.toLocaleString()}
                                    </span>
                                </div>
                            )}

                        {ingredient.description && (
                            <div className={styles.detailItem}>
                                <span className={styles.label}>
                                    Description:
                                </span>
                                <span className={styles.value}>
                                    {ingredient.description}
                                </span>
                            </div>
                        )}

                        <div className={styles.detailItem}>
                            <span className={styles.label}>Created:</span>
                            <span className={styles.value}>
                                {ingredient.created_at
                                    ? new Date(
                                          ingredient.created_at,
                                      ).toLocaleDateString()
                                    : "N/A"}
                            </span>
                        </div>

                        {ingredient.piece_image_url && (
                            <div className={styles.detailItem}>
                                <span className={styles.label}>
                                    Piece Image:
                                </span>
                                <img
                                    src={ingredient.piece_image_url}
                                    alt={`${ingredient.name} piece`}
                                    className={styles.pieceImage}
                                />
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className={styles.actions}>
                        <button
                            className={styles.editBtn}
                            onClick={() =>
                                navigate(`/ingredients/${ingredient.id}/edit`)
                            }
                        >
                            <PencilSimple size={18} /> Edit
                        </button>
                        <button
                            className={styles.backBtn}
                            onClick={() => navigate("/ingredients")}
                        >
                            ← Back
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
