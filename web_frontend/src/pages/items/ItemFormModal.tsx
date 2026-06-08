/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMemo, useState, useCallback } from "react";
import Modal from "@components/layout/Modal";
import ItemForm from "./ItemForm";
import itemAPI from "@services/item";
import { useItemStore } from "@store/itemStore";
import type { Item } from "@services/item";

interface ItemFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    editingItem?: Item | null;
    onSuccess?: () => void;
}

export default function ItemFormModal({
    isOpen,
    onClose,
    editingItem,
    onSuccess,
}: ItemFormModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { items, setItems } = useItemStore();

    const modalTitle = useMemo(
        () =>
            editingItem ? `Edit Item: ${editingItem.name}` : "Create New Item",
        [editingItem],
    );

    const handleSubmit = useCallback(
        async (formData: FormData) => {
            setIsLoading(true);
            setError(null);

            try {
                let response: Item;

                if (editingItem?.id) {
                    // Update existing item
                    response = await itemAPI.update(
                        editingItem.id,
                        formData as any,
                    );

                    // Update local cache
                    setItems(
                        items.map((item: Item) =>
                            item.id === editingItem.id ? response : item,
                        ),
                    );
                } else {
                    // Create new item
                    response = await itemAPI.create(formData as any);

                    // Add to cache
                    setItems([...items, response]);
                }

                onSuccess?.();
                onClose();
            } catch (err: any) {
                setError(
                    err?.response?.data?.message ||
                        err?.response?.data?.detail ||
                        err?.message ||
                        "Failed to save item",
                );
                console.error("Item save error:", err);
            } finally {
                setIsLoading(false);
            }
        },
        [editingItem, items, setItems, onClose, onSuccess],
    );

    const handleCancel = useCallback(() => {
        setError(null);
        onClose();
    }, [onClose]);

    // Transform item data for form component
    const initialData = useMemo(() => {
        if (!editingItem) return undefined;

        return {
            name: editingItem.name,
            description: editingItem.description || "",
            price: editingItem.price,
            original_price: editingItem.original_price || "",
            type: editingItem.type || "pizza",
            is_active: editingItem.is_active ?? true,
            category: editingItem.category || "",
            sub_type: editingItem.sub_type || "",
            // FK relationships
            dough: editingItem.dough || null,
            sauce: editingItem.sauce || null,
            cheese: editingItem.cheese || null,
            // M2M relationships
            toppings: editingItem.toppings || [],
            extras: editingItem.extras || [],
            // Image
            image_url: editingItem.image_url || "",
            // Add other fields from the item if available
            ...(editingItem as any),
        };
    }, [editingItem]);

    return (
        <Modal
            isOpen={isOpen}
            title={modalTitle}
            onClose={handleCancel}
            width="auto"
            titleStyle={{ fontSize: "1.5rem", fontWeight: 600 }}
        >
            <div
                style={{
                    maxHeight: "70vh",
                    overflowY: "auto",
                    padding: "0.0rem",
                }}
            >
                {error && (
                    <div
                        style={{
                            padding: "0.75rem",
                            marginBottom: "1rem",
                            backgroundColor: "#fee",
                            color: "#c33",
                            borderRadius: "4px",
                            fontSize: "0.9rem",
                        }}
                    >
                        {error}
                    </div>
                )}

                <ItemForm
                    initialData={initialData}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    onCancel={handleCancel}
                />
            </div>
        </Modal>
    );
}
