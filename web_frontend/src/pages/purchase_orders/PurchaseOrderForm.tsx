/* eslint-disable @typescript-eslint/no-explicit-any */
import styles from "./PurchaseOrderForm.module.scss";
import { useForm } from "@components/form/formContext";
import TextField from "@components/form/fields/TextField";
import TextareaField from "@components/form/fields/TextareaField";
import SelectField from "@components/form/fields/SelectField";
import DateField from "@components/form/fields/DateField";
import FileField from "@components/form/fields/FileField";
import CustomForm2 from "@components/form/CustomForm2";

interface ProviderOption {
    id: number;
    name: string;
}

interface PurchaseOrderFormProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (data: any) => void;
    initialData?: any;
    isLoading?: boolean;
    providers?: ProviderOption[];
}

export default function PurchaseOrderForm({
    open,
    onClose,
    onSubmit,
    initialData,
    isLoading = false,
    providers = [],
}: PurchaseOrderFormProps) {
    if (!open) return null;

    function FormBody() {
        const form = useForm()!;

        // Helper to read values safely
        const val = (k: string) => String(form.getValue(k) ?? "");

        return (
            <div>
                <div style={{ marginBottom: 12 }}>
                    <TextField
                        name="order_number"
                        label="PO Number"
                        value={val("order_number")}
                        onChange={(v) => form.setValue("order_number", v)}
                        placeholder="PO-001"
                        required
                    />
                </div>

                <div style={{ marginBottom: 12 }}>
                    <SelectField
                        name="provider"
                        label="Provider"
                        value={val("provider")}
                        onChange={() => {}}
                        options={providers.map((p) => ({
                            label: p.name,
                            value: String(p.id),
                        }))}
                        placeholder="Select provider"
                    />
                </div>

                <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                    <div style={{ flex: 1 }}>
                        <DateField
                            name="order_date"
                            label="Order Date"
                            value={val("order_date")}
                            onChange={() => {}}
                            type="date"
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <DateField
                            name="expected_delivery_date"
                            label="Expected Delivery"
                            value={val("expected_delivery_date")}
                            onChange={() => {}}
                            type="date"
                        />
                    </div>
                </div>

                <div style={{ marginBottom: 12 }}>
                    <label className={styles.fieldLabel}>Status</label>
                    <select
                        name="status"
                        value={val("status") || "pending"}
                        onChange={(e) =>
                            form.setValue("status", e.target.value)
                        }
                    >
                        <option value="pending">Pending</option>
                        <option value="received">Received</option>
                        <option value="cancelled">Cancelled</option>
                    </select>
                </div>

                <div style={{ marginBottom: 12 }}>
                    <TextareaField
                        name="notes"
                        label="Notes"
                        value={val("notes")}
                        onChange={(v) => form.setValue("notes", v)}
                        placeholder="Order notes"
                        rows={3}
                    />
                </div>

                <div style={{ marginBottom: 12 }}>
                    <FileField
                        name="receipt_files"
                        label="Receipts / Files"
                        multiple
                        onChange={() => {}}
                        accept="*/*"
                        preview
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
                    submitLabel="Submit"
                    cancelLabel="Cancel"
                >
                    <FormBody />
                </CustomForm2>
            </div>
        </div>
    );
}
