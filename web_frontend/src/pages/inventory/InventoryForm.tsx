/* eslint-disable @typescript-eslint/no-explicit-any */
import styles from "./InventoryForm.module.scss";
import { useForm } from "@components/form/formContext";
import TextField from "@components/form/fields/TextField";
import TextareaField from "@components/form/fields/TextareaField";
import SelectField from "@components/form/fields/SelectField";
import CustomForm2 from "@components/form/CustomForm2";
import { UNIT_CHOICES } from "../../services/inventory";

interface ProviderOption {
    id: number;
    name: string;
}

interface InventoryFormProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (data: any) => void;
    initialData?: any;
    isLoading?: boolean;
    providers?: ProviderOption[];
}

export default function InventoryForm({
    open,
    onClose,
    onSubmit,
    initialData,
    isLoading = false,
    providers = [],
}: InventoryFormProps) {
    if (!open) return null;

    function FormBody() {
        const form = useForm()!;
        const val = (k: string) => String(form.getValue(k) ?? "");

        return (
            <div>
                <h2 className={styles.title}>
                    {initialData?.id
                        ? "Edit Inventory Item"
                        : "Add Inventory Item"}
                </h2>

                <div style={{ marginBottom: 12 }}>
                    <TextField
                        name="name"
                        label="Name"
                        value={val("name")}
                        onChange={(v) => form.setValue("name", v)}
                        placeholder="e.g. Pork Meat"
                        required
                    />
                </div>

                <div style={{ marginBottom: 12 }}>
                    <TextareaField
                        name="description"
                        label="Description"
                        value={val("description")}
                        onChange={(v) => form.setValue("description", v)}
                        placeholder="Optional description"
                        rows={2}
                    />
                </div>

                <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                    <div style={{ flex: 1 }}>
                        <SelectField
                            name="unit"
                            label="Unit"
                            value={val("unit")}
                            onChange={() => {}}
                            options={UNIT_CHOICES.map((u) => ({
                                label: u.label,
                                value: u.value,
                            }))}
                            placeholder="Select unit"
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <SelectField
                            name="provider_id"
                            label="Provider (optional)"
                            value={val("provider_id")}
                            onChange={() => {}}
                            options={providers.map((p) => ({
                                label: p.name,
                                value: String(p.id),
                            }))}
                            placeholder="Select provider"
                        />
                    </div>
                </div>

                <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                    <div style={{ flex: 1 }}>
                        <TextField
                            name="current_stock"
                            label="Current Stock"
                            type="number"
                            value={val("current_stock")}
                            onChange={(v) => form.setValue("current_stock", v)}
                            placeholder="0"
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <TextField
                            name="min_threshold"
                            label="Min Threshold"
                            type="number"
                            value={val("min_threshold")}
                            onChange={(v) => form.setValue("min_threshold", v)}
                            placeholder="5"
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <TextField
                            name="max_threshold"
                            label="Max Threshold (optional)"
                            type="number"
                            value={val("max_threshold")}
                            onChange={(v) => form.setValue("max_threshold", v)}
                            placeholder="e.g. 100"
                        />
                    </div>
                </div>

                <div style={{ marginBottom: 12 }}>
                    <SelectField
                        name="is_active"
                        label="Status"
                        value={val("is_active") || "true"}
                        onChange={() => {}}
                        options={[
                            { label: "Active", value: "true" },
                            { label: "Inactive", value: "false" },
                        ]}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className={styles.overlay}>
            <div className={styles.formContainer}>
                <CustomForm2
                    initialValues={initialData || {}}
                    onSubmit={(vals) => onSubmit(vals)}
                    onCancel={onClose}
                    isLoading={isLoading}
                    submitLabel="Save"
                    cancelLabel="Cancel"
                >
                    <FormBody />
                </CustomForm2>
            </div>
        </div>
    );
}
