import { type Ingredient } from "../../services/ingredients";
import { CheckCircle, XCircle } from "@phosphor-icons/react";
import styles from "./IngredientList.module.scss";

export interface IngredientRowProps {
    ing: Ingredient;
    isSelected: boolean;
    onSelect: (id: number) => void;
    onView: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number) => void;
}

export default function IngredientRow({
    ing,
    isSelected,
    onSelect,
    onView,
    onEdit,
    onDelete,
}: IngredientRowProps) {
    return (
        <tr>
            <td className={styles.checkboxCol} style={{ height: "80px" }}>
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onSelect(ing.id!)}
                />
            </td>
            <td className={styles.imageCol}>
                {ing.image_url ? (
                    <img
                        src={ing.image_url}
                        alt={ing.name}
                        className={styles.thumbnail}
                    />
                ) : (
                    <div className={styles.noImage}>No Image</div>
                )}
            </td>
            <td
                onClick={() => onView(ing.id!)}
                className={styles.clickableCell}
                style={{ cursor: "pointer" }}
            >
                <strong>{ing.name}</strong>
                {ing.sub_type && (
                    <div className={styles.subType}>{ing.sub_type}</div>
                )}
            </td>
            <td>
                <span className={styles.badge}>{ing.type}</span>
            </td>
            <td>${ing.price.toLocaleString()}</td>
            <td>
                <span
                    className={
                        ing.is_active
                            ? styles.badgeActive
                            : styles.badgeInactive
                    }
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        width: "fit-content",
                    }}
                >
                    {ing.is_active ? (
                        <>
                            <CheckCircle size={16} weight="fill" />
                            Active
                        </>
                    ) : (
                        <>
                            <XCircle size={16} weight="fill" />
                            Inactive
                        </>
                    )}
                </span>
            </td>
            <td>
                <div className={styles.actions}>
                    <button
                        className={styles.viewBtn}
                        onClick={() => onView(ing.id!)}
                        title="View Details"
                    >
                        👁️
                    </button>
                    <button
                        className={styles.editBtn}
                        onClick={() => onEdit(ing.id!)}
                        title="Edit"
                    >
                        ✏️
                    </button>
                    <button
                        className={styles.deleteBtn}
                        onClick={() => onDelete(ing.id!)}
                        title="Delete"
                    >
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    );
}
