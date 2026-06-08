import React from "react";
import styles from "./ItemTableSelect.module.scss";

export interface ItemTableSelectOption {
    id: string;
    name: string;
    image?: string;
    description?: string;
}

export interface ItemTableSelectProps {
    items: ItemTableSelectOption[];
    selected: string[];
    onChange: (selected: string[]) => void;
    onPreview?: (item: ItemTableSelectOption) => void;
    label?: string;
    className?: string;
}

export const ItemTableSelect: React.FC<ItemTableSelectProps> = ({
    items,
    selected,
    onChange,
    onPreview,
    label,
    className,
}) => {
    const handleToggle = (id: string) => {
        if (selected.includes(id)) {
            onChange(selected.filter((s) => s !== id));
        } else {
            onChange([...selected, id]);
        }
    };

    return (
        <div className={`${styles.tableSelectWrapper} ${className || ""}`}>
            {label && <div className={styles.label}>{label}</div>}
            <table className={styles.table}>
                <thead>
                    <tr>
                        <th></th>
                        <th>Image</th>
                        <th>Name</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item) => (
                        <tr key={item.id}>
                            <td>
                                <input
                                    type="checkbox"
                                    checked={selected.includes(item.id)}
                                    onChange={() => handleToggle(item.id)}
                                />
                            </td>
                            <td>
                                {item.image ? (
                                    <img
                                        src={item.image}
                                        alt={item.name}
                                        className={styles.image}
                                    />
                                ) : (
                                    <span className={styles.noImage}>
                                        No image
                                    </span>
                                )}
                            </td>
                            <td>{item.name}</td>
                            <td>
                                {onPreview && (
                                    <button
                                        type="button"
                                        className={styles.previewBtn}
                                        onClick={() => onPreview(item)}
                                    >
                                        👁️ View
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
