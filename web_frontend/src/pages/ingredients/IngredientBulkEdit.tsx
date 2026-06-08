import { useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { ingredientAPI, type Ingredient } from "../../services/ingredients";
import { Button, Input, Select } from "../../components/ui";
import styles from "./IngredientBulkEdit.module.scss";

export default function IngredientBulkEdit() {
    const navigate = useNavigate();
    const location = useLocation();
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editMode, setEditMode] = useState<"selected" | "all">("all");

    // Get selected ingredient IDs from route state
    const selectedIds: number[] =
        (location.state as { selectedIds?: number[] })?.selectedIds || [];
    const [bulkOperationMode, setBulkOperationMode] = useState<
        "set-exact-price" | "set-exact-status" | "adjust-prices"
    >("adjust-prices");
    const [bulkValue, setBulkValue] = useState<string>("");
    const [priceAdjustmentType, setPriceAdjustmentType] = useState<
        | "increase-percent"
        | "decrease-percent"
        | "increase-amount"
        | "decrease-amount"
        | "revert-to-original"
    >("increase-percent");
    const [priceAdjustmentValue, setPriceAdjustmentValue] =
        useState<string>("");

    const hasPriceChanges = ingredients.some((ing) => {
        // If no original price, consider it no change
        if (!ing.original_price) return false;
        // Check if current price differs from original price
        return ing.price !== ing.original_price;
    });

    const fetchIngredients = async () => {
        try {
            // If selected IDs provided, only load those ingredients
            if (selectedIds.length > 0) {
                setEditMode("selected");
                const responses = await Promise.all(
                    selectedIds.map((id) => ingredientAPI.get(id)),
                );
                setIngredients(responses.map((res) => res.data));
            } else {
                // Otherwise load all ingredients
                setEditMode("all");
                const response = await ingredientAPI.list();
                setIngredients(response.data?.results || response.data);
            }
        } catch (err) {
            setError("Failed to load ingredients");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchIngredients();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Reset revert-to-original selection if prices have no changes
    useEffect(() => {
        if (!hasPriceChanges && priceAdjustmentType === "revert-to-original") {
            setPriceAdjustmentType("increase-percent");
        }
    }, [hasPriceChanges, priceAdjustmentType]);

    const handleIngredientsChange = (
        id: number,
        field: keyof Ingredient,
        value: unknown,
    ) => {
        setIngredients((prev) =>
            prev.map((ing) =>
                ing.id === id ? { ...ing, [field]: value } : ing,
            ),
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (ingredients.length === 0) {
            alert("No ingredients to update");
            return;
        }

        try {
            setIsSubmitting(true);
            const updates = ingredients.map((ing) => ({
                id: ing.id!,
                data: ing,
            }));

            await ingredientAPI.bulkUpdate(updates, editMode);
            navigate("/ingredients");
        } catch (err) {
            setError("Failed to update ingredients");
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleApplyBulkChange = () => {
        if (bulkValue === "") return;

        setIngredients((prev) =>
            prev.map((ing) => {
                if (bulkOperationMode === "set-exact-price") {
                    return {
                        ...ing,
                        price: parseFloat(bulkValue) || ing.price,
                    };
                } else if (bulkOperationMode === "set-exact-status") {
                    return {
                        ...ing,
                        is_active: bulkValue === "true",
                    };
                }
                return ing;
            }),
        );

        setBulkValue("");
    };

    const handleApplyBulkOperation = () => {
        if (
            bulkOperationMode === "set-exact-price" ||
            bulkOperationMode === "set-exact-status"
        ) {
            handleApplyBulkChange();
        } else {
            handleApplyPriceAdjustment();
        }
    };

    const handleApplyPriceAdjustment = () => {
        // Handle revert operation
        if (priceAdjustmentType === "revert-to-original") {
            const withOriginal = ingredients.filter(
                (ing) => ing.original_price,
            );
            const withoutOriginal = ingredients.filter(
                (ing) => !ing.original_price,
            );

            if (withOriginal.length === 0) {
                alert("No ingredients have an original price to revert to");
                return;
            }

            if (withoutOriginal.length > 0) {
                alert(
                    `${withoutOriginal.length} ingredient(s) don't have an original price and will be skipped`,
                );
            }

            setIngredients((prev) =>
                prev.map((ing) => {
                    if (ing.original_price) {
                        return {
                            ...ing,
                            price: ing.original_price,
                        };
                    }
                    return ing;
                }),
            );
            return;
        }

        // Handle percentage/amount adjustment operations
        if (
            priceAdjustmentValue === "" ||
            parseFloat(priceAdjustmentValue) <= 0
        ) {
            alert("Please enter a valid value greater than 0");
            return;
        }

        const adjValue = parseFloat(priceAdjustmentValue);

        setIngredients((prev) =>
            prev.map((ing) => {
                let newPrice = ing.price;

                if (priceAdjustmentType === "increase-percent") {
                    newPrice = ing.price + (ing.price * adjValue) / 100;
                } else if (priceAdjustmentType === "decrease-percent") {
                    newPrice = ing.price - (ing.price * adjValue) / 100;
                } else if (priceAdjustmentType === "increase-amount") {
                    newPrice = ing.price + adjValue;
                } else if (priceAdjustmentType === "decrease-amount") {
                    newPrice = ing.price - adjValue;
                }

                // Ensure price is not less than 0
                newPrice = Math.max(0, newPrice);

                return {
                    ...ing,
                    price: parseFloat(newPrice.toFixed(2)),
                };
            }),
        );

        setPriceAdjustmentValue("");
    };

    if (loading) {
        return (
            <div className={styles.container}>
                <div style={{ textAlign: "center", padding: "2rem" }}>
                    ⏳ Loading ingredients...
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>Bulk Edit Ingredients</h1>
                <p className={styles.subtitle}>
                    {editMode === "selected"
                        ? `Editing ${ingredients.length} selected ingredient${ingredients.length !== 1 ? "s" : ""}`
                        : "Edit all ingredients with powerful batch operations"}
                </p>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            <form onSubmit={handleSubmit} className={styles.form}>
                {/* Bulk Operations */}
                <div className={styles.bulkOps}>
                    {/* Operation Mode Selector */}
                    <div className={styles.bulkOpsGroup}>
                        <div className={styles.buttonGroup}>
                            <button
                                type="button"
                                className={`${styles.tabBtn} ${
                                    bulkOperationMode === "set-exact-price"
                                        ? styles.active
                                        : ""
                                }`}
                                onClick={() =>
                                    setBulkOperationMode("set-exact-price")
                                }
                            >
                                Set Exact Price
                            </button>
                            <button
                                type="button"
                                className={`${styles.tabBtn} ${
                                    bulkOperationMode === "set-exact-status"
                                        ? styles.active
                                        : ""
                                }`}
                                onClick={() =>
                                    setBulkOperationMode("set-exact-status")
                                }
                            >
                                Set Status
                            </button>
                            <button
                                type="button"
                                className={`${styles.tabBtn} ${
                                    bulkOperationMode === "adjust-prices"
                                        ? styles.active
                                        : ""
                                }`}
                                onClick={() =>
                                    setBulkOperationMode("adjust-prices")
                                }
                            >
                                Adjust Prices
                            </button>
                        </div>
                    </div>

                    {/* Set Exact Price Mode */}
                    {bulkOperationMode === "set-exact-price" && (
                        <div className={styles.bulkOpsGroup}>
                            <div className={styles.bulkOpsRow}>
                                <Input
                                    type="number"
                                    step="0.01"
                                    value={bulkValue}
                                    onChange={(e) =>
                                        setBulkValue(e.target.value)
                                    }
                                    placeholder="Enter new price"
                                />
                            </div>
                        </div>
                    )}

                    {/* Set Status Mode */}
                    {bulkOperationMode === "set-exact-status" && (
                        <div className={styles.bulkOpsGroup}>
                            <div className={styles.bulkOpsRow}>
                                <Select
                                    value={bulkValue}
                                    onChange={(value) =>
                                        setBulkValue(value as string)
                                    }
                                >
                                    <option value="">Select status</option>
                                    <option value="true">Active</option>
                                    <option value="false">Inactive</option>
                                </Select>
                            </div>
                        </div>
                    )}

                    {/* Adjust Prices Mode */}
                    {bulkOperationMode === "adjust-prices" && (
                        <div className={styles.bulkOpsGroup}>
                            <div className={styles.priceAdjustmentOptions}>
                                <div className={styles.buttonGroup}>
                                    <button
                                        type="button"
                                        className={`${styles.tabBtn} ${
                                            priceAdjustmentType ===
                                            "increase-percent"
                                                ? styles.active
                                                : ""
                                        }`}
                                        onClick={() =>
                                            setPriceAdjustmentType(
                                                "increase-percent",
                                            )
                                        }
                                    >
                                        Increase by %
                                    </button>
                                    <button
                                        type="button"
                                        className={`${styles.tabBtn} ${
                                            priceAdjustmentType ===
                                            "decrease-percent"
                                                ? styles.active
                                                : ""
                                        }`}
                                        onClick={() =>
                                            setPriceAdjustmentType(
                                                "decrease-percent",
                                            )
                                        }
                                    >
                                        Decrease by %
                                    </button>
                                    <button
                                        type="button"
                                        className={`${styles.tabBtn} ${
                                            priceAdjustmentType ===
                                            "increase-amount"
                                                ? styles.active
                                                : ""
                                        }`}
                                        onClick={() =>
                                            setPriceAdjustmentType(
                                                "increase-amount",
                                            )
                                        }
                                    >
                                        Increase by $
                                    </button>
                                    <button
                                        type="button"
                                        className={`${styles.tabBtn} ${
                                            priceAdjustmentType ===
                                            "decrease-amount"
                                                ? styles.active
                                                : ""
                                        }`}
                                        onClick={() =>
                                            setPriceAdjustmentType(
                                                "decrease-amount",
                                            )
                                        }
                                    >
                                        Decrease by $
                                    </button>
                                    {hasPriceChanges && (
                                        <button
                                            type="button"
                                            className={`${styles.tabBtn} ${
                                                priceAdjustmentType ===
                                                "revert-to-original"
                                                    ? styles.active
                                                    : ""
                                            }`}
                                            onClick={() =>
                                                setPriceAdjustmentType(
                                                    "revert-to-original",
                                                )
                                            }
                                        >
                                            Revert to Original Price
                                        </button>
                                    )}
                                </div>
                                <div className={styles.bulkOpsRow}>
                                    {priceAdjustmentType !==
                                        "revert-to-original" && (
                                        <Input
                                            type="number"
                                            step="0.01"
                                            value={priceAdjustmentValue}
                                            onChange={(e) =>
                                                setPriceAdjustmentValue(
                                                    e.target.value,
                                                )
                                            }
                                            placeholder={
                                                priceAdjustmentType.includes(
                                                    "percent",
                                                )
                                                    ? "Enter %"
                                                    : "Enter amount"
                                            }
                                            min="0"
                                        />
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Unified Apply Button */}
                    {(((bulkOperationMode === "set-exact-price" ||
                        bulkOperationMode === "set-exact-status") &&
                        bulkValue !== "") ||
                        (bulkOperationMode === "adjust-prices" &&
                            (priceAdjustmentType === "revert-to-original" ||
                                priceAdjustmentValue !== ""))) && (
                        <div
                            style={{
                                marginTop: "1rem",
                                display: "flex",
                                gap: "0.5rem",
                                paddingBottom: "1.5rem",
                            }}
                        >
                            <Button
                                type="button"
                                onClick={handleApplyBulkOperation}
                                variant="primary"
                                size="md"
                            >
                                Apply
                            </Button>
                        </div>
                    )}
                </div>

                {/* Ingredients Table */}
                <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Price (₫)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ingredients.map((ing) => (
                                <tr key={ing.id}>
                                    <td>{ing.name}</td>
                                    <td>{ing.type}</td>
                                    <td>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={ing.price}
                                            onChange={(e) =>
                                                handleIngredientsChange(
                                                    ing.id!,
                                                    "price",
                                                    parseFloat(e.target.value),
                                                )
                                            }
                                            className={styles.numberInput}
                                        />
                                    </td>
                                    <td>
                                        <select
                                            value={
                                                ing.is_active
                                                    ? "active"
                                                    : "inactive"
                                            }
                                            onChange={(e) =>
                                                handleIngredientsChange(
                                                    ing.id!,
                                                    "is_active",
                                                    e.target.value === "active",
                                                )
                                            }
                                            className={styles.statusSelect}
                                        >
                                            <option value="active">
                                                Active
                                            </option>
                                            <option value="inactive">
                                                Inactive
                                            </option>
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Actions */}
                <div className={styles.actions}>
                    <Button
                        type="button"
                        onClick={() => navigate("/ingredients")}
                        variant="outline"
                        size="md"
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        disabled={isSubmitting}
                        variant="secondary"
                        size="md"
                        isLoading={isSubmitting}
                    >
                        {isSubmitting ? "Saving..." : "Save Changes"}
                    </Button>
                </div>
            </form>
        </div>
    );
}
