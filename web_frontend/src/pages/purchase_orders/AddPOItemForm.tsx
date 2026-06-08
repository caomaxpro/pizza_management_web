/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import CustomForm from "@components/form/CustomForm";
import { useForm } from "@components/form/formContext";
import TextField from "@components/form/fields/TextField";
import SelectField from "@components/form/fields/SelectField";
import { Button } from "@components/ui";
import inventoryAPI from "../../services/inventory";
import styles from "./PurchaseOrderForm.module.scss";

interface AddPOItemFormProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (data: any) => void;
    isLoading?: boolean;
}

export default function AddPOItemForm({
    open,
    onClose,
    onSubmit,
    isLoading = false,
}: AddPOItemFormProps) {
    const [inventoryOptions, setInventoryOptions] = useState<
        Array<{ label: string; value: string }>
    >([]);

    useEffect(() => {
        inventoryAPI
            .list()
            .then((items) =>
                setInventoryOptions(
                    items.map((item) => ({
                        label: `${item.name} (${item.current_stock} ${item.unit})`,
                        value: String(item.id),
                    })),
                ),
            )
            .catch((err) => console.error("Failed to load inventory:", err));
    }, []);

    if (!open) return null;

    function FormBody() {
        const form = useForm()!;
        const val = (k: string) => String(form.getValue(k) ?? "");

        return (
            <div>
                <div style={{ marginBottom: 12 }}>
                    <SelectField
                        name="inventory"
                        label="Inventory Item"
                        value={val("inventory")}
                        onChange={() => {}}
                        options={inventoryOptions}
                        placeholder="Select inventory item"
                    />
                </div>

                <div style={{ marginBottom: 12 }}>
                    <TextField
                        name="quantity"
                        label="Quantity"
                        type="number"
                        value={val("quantity")}
                        onChange={(v) => form.setValue("quantity", v)}
                        placeholder="1"
                        required
                    />
                </div>

                <div style={{ marginBottom: 12 }}>
                    <TextField
                        name="actual_unit_price"
                        label="Unit Price (optional)"
                        type="number"
                        value={val("actual_unit_price")}
                        onChange={(v) => form.setValue("actual_unit_price", v)}
                        placeholder="0.00"
                    />
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                    <Button
                        type="submit"
                        variant="primary"
                        disabled={isLoading}
                    >
                        Add Item
                    </Button>
                    <Button type="button" variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.overlay}>
            <div className={styles.formContainer}>
                <h3 style={{ marginBottom: 16 }}>Add PO Item</h3>
                <CustomForm
                    initialValues={{}}
                    onSubmit={(vals) => onSubmit(vals)}
                >
                    <FormBody />
                </CustomForm>
            </div>
        </div>
    );
}
