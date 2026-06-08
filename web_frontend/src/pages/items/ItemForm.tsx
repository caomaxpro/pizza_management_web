import React from "react";
import CustomForm2 from "@components/form/CustomForm2";
import { useForm } from "@components/form/formContext";
import type { FormValues } from "@components/form/formContext";
import { useIngredientStore } from "../../store/ingredientStore";
import SelectField from "@components/form/fields/SelectField";
import TextField from "@components/form/fields/TextField";
import TextareaField from "@components/form/fields/TextareaField";
import FileField from "@components/form/fields/FileField";
import CheckField from "@components/form/fields/CheckField";
import styles from "./ItemForm.module.scss";
import * as icons from "@assets/icons";

// Keep frontend choices in sync with backend `shared/constants.py`
const ITEM_TYPE_CHOICES = [
    { value: "pizza", label: "Pizza" },
    { value: "drink", label: "Drink" },
    { value: "salad", label: "Salad" },
    { value: "sides", label: "Sides" },
    { value: "other", label: "Other" },
];

const PIZZA_SUB_TYPE_CHOICES = [
    { value: "veggie", label: "Vegetarian" },
    { value: "meat", label: "Meat" },
    { value: "cheese", label: "Cheese" },
];

interface ItemFormProps {
    initialData?: Record<string, unknown>;
    onSubmit: (data: FormData) => void;
    isLoading?: boolean;
    onCancel?: () => void;
}

// Conditionally renders only when type === "pizza" — self-connects via formContext
function SubTypeField({
    options,
    className,
}: {
    options: { value: string; label: string }[];
    className?: string;
}) {
    const form = useForm()!;
    if (form.getValue("type") !== "pizza") return null;
    return (
        <SelectField
            name="sub_type"
            label="Sub-type"
            icon={icons.pizza}
            value=""
            onChange={() => {}}
            options={options}
            placeholder="Optional - pizza sub-type"
            className={className}
        />
    );
}

export default function ItemForm({
    onSubmit,
    initialData,
    isLoading = false,
    onCancel,
}: ItemFormProps) {
    const { ingredients, fetchAllIngredients } = useIngredientStore();

    React.useEffect(() => {
        void fetchAllIngredients();
    }, [fetchAllIngredients]);

    const doughOptions = React.useMemo(
        () =>
            ingredients
                .filter((i) => i.type === "dough")
                .map((i) => ({ value: String(i.id), label: i.name })),
        [ingredients],
    );

    const sauceOptions = React.useMemo(
        () =>
            ingredients
                .filter((i) => i.type === "sauce")
                .map((i) => ({ value: String(i.id), label: i.name })),
        [ingredients],
    );

    const cheeseOptions = React.useMemo(
        () =>
            ingredients
                .filter((i) => i.type === "cheese")
                .map((i) => ({ value: String(i.id), label: i.name })),
        [ingredients],
    );

    const toppingOptions = React.useMemo(
        () =>
            ingredients
                .filter((i) => i.type === "topping")
                .map((i) => ({ value: String(i.id), label: i.name })),
        [ingredients],
    );

    const extraOptions = React.useMemo(
        () =>
            ingredients
                .filter((i) => i.type === "extra")
                .map((i) => ({ value: String(i.id), label: i.name })),
        [ingredients],
    );

    const handleSubmit = (data: Record<string, unknown>) => {
        const fd = new FormData();

        Object.entries(data).forEach(([k, v]) => {
            if (v === undefined || v === null) return;

            if (Array.isArray(v)) {
                v.forEach((item) => {
                    if (item instanceof File) fd.append(k, item);
                    else fd.append(k, String(item));
                });
                return;
            }

            if (v instanceof File) {
                fd.append(k, v);
            } else if (typeof v === "boolean") {
                fd.append(k, v ? "1" : "0");
            } else if (typeof v === "object") {
                // FK field still an object — extract id as fallback
                const id = (v as Record<string, unknown>).id;
                if (id !== undefined && id !== null) fd.append(k, String(id));
            } else {
                fd.append(k, String(v));
            }
        });

        onSubmit(fd);
    };

    const extractId = (v: unknown) =>
        v && typeof v === "object" ? ((v as { id?: unknown }).id ?? v) : v;

    const initial: FormValues = React.useMemo(() => {
        if (!initialData) {
            // Create mode - empty values
            return {
                name: "",
                price: "",
                original_price: "",
                description: "",
                type: "pizza",
                sub_type: "",
                dough: null,
                sauce: null,
                cheese: null,
                toppings: [],
                extras: [],
                is_active: true,
                image_url: "",
                image_file: null,
            };
        }

        // Edit mode - fill all values from item
        // Select options use String(id), so IDs must be strings for === matching to work
        const toStringId = (v: unknown) => {
            const id = extractId(v);
            return id != null ? String(id) : null;
        };
        return {
            name: initialData.name || "",
            price: initialData.price || "",
            original_price: initialData.original_price || "",
            description: initialData.description || "",
            type: initialData.type || "pizza",
            sub_type: initialData.sub_type || "",
            // API returns full nested objects for FK fields — extract IDs as strings
            dough: toStringId(initialData.dough),
            sauce: toStringId(initialData.sauce),
            cheese: toStringId(initialData.cheese),
            toppings: Array.isArray(initialData.toppings)
                ? (initialData.toppings as { id?: unknown }[]).map((t) =>
                      String(t.id ?? t),
                  )
                : [],
            extras: Array.isArray(initialData.extras)
                ? (initialData.extras as { id?: unknown }[]).map((t) =>
                      String(t.id ?? t),
                  )
                : [],
            is_active: initialData.is_active ?? true,
            image_url: initialData.image_url || "",
            image_file: null,
        };
    }, [initialData]);

    // Debug: Log initial values
    React.useEffect(() => {
        if (initialData) {
            console.log("[ItemForm] Raw initialData prop:", initialData);
            console.log("[ItemForm] Processed initial object:", initial);
            console.log(
                "[ItemForm] Dough value:",
                initial.dough,
                "| Type:",
                typeof initial.dough,
            );
            console.log(
                "[ItemForm] Sauce value:",
                initial.sauce,
                "| Type:",
                typeof initial.sauce,
            );
            console.log(
                "[ItemForm] Cheese value:",
                initial.cheese,
                "| Type:",
                typeof initial.cheese,
            );
            console.log(
                "[ItemForm] Toppings array:",
                initial.toppings,
                "| Length:",
                Array.isArray(initial.toppings)
                    ? initial.toppings.length
                    : "not array",
            );
            console.log(
                "[ItemForm] Extras array:",
                initial.extras,
                "| Length:",
                Array.isArray(initial.extras)
                    ? initial.extras.length
                    : "not array",
            );
        } else {
            console.log("[ItemForm] Create mode - no initialData provided");
        }
    }, [initialData, initial]);

    const fields = [
        <TextField
            name="name"
            label="Name"
            icon={icons.ingredient}
            value=""
            onChange={() => {}}
            placeholder="Item name"
            required
            className={styles.fieldControl}
        />,
        <TextField
            name="price"
            label="Price"
            icon={icons.icons8Search}
            type="number"
            value=""
            onChange={() => {}}
            placeholder="Sale price — visible to customers"
            required
            className={styles.fieldControl}
        />,
        <TextField
            name="original_price"
            label="Original Price"
            icon={icons.icons8Search}
            type="number"
            value=""
            onChange={() => {}}
            placeholder="Original price — stored for rollback"
            className={styles.fieldControl}
        />,
        <TextareaField
            name="description"
            label="Description"
            value=""
            onChange={() => {}}
            placeholder="Describe the item"
            rows={3}
            className={styles.fieldControl}
        />,
        <SelectField
            name="type"
            label="Type"
            icon={icons.category}
            value=""
            onChange={() => {}}
            options={ITEM_TYPE_CHOICES}
            className={styles.fieldControl}
        />,
        // Conditionally visible — reads form context internally
        <SubTypeField
            options={PIZZA_SUB_TYPE_CHOICES}
            className={styles.fieldControl}
        />,
        <SelectField
            name="dough"
            label="Dough"
            icon={icons.dough}
            value=""
            onChange={() => {}}
            options={doughOptions}
            className={styles.fieldControl}
        />,
        <SelectField
            name="sauce"
            label="Sauce"
            icon={icons.sauce}
            value=""
            onChange={() => {}}
            options={sauceOptions}
            className={styles.fieldControl}
        />,
        <SelectField
            name="cheese"
            label="Cheese"
            icon={icons.cheese}
            value=""
            onChange={() => {}}
            options={cheeseOptions}
            className={styles.fieldControl}
        />,
        <SelectField
            name="toppings"
            label="Toppings"
            icon={icons.topping}
            value=""
            onChange={() => {}}
            options={toppingOptions}
            multi
            className={styles.fieldControl}
        />,
        <SelectField
            name="extras"
            label="Extras"
            icon={icons.extras}
            value=""
            onChange={() => {}}
            options={extraOptions}
            multi
            className={styles.fieldControl}
        />,
        <FileField
            name="image_file"
            label="Image"
            files={[]}
            onChange={() => {}}
            fileType={"image"}
            accept="image/*"
            className={styles.fieldControl}
        />,
        <CheckField
            name="is_active"
            label="Active"
            value={true}
            onChange={() => {}}
            className={styles.fieldControl}
        />,
    ];

    return (
        <CustomForm2
            fields={fields}
            initialValues={initial}
            onSubmit={handleSubmit}
            onCancel={onCancel}
            isLoading={isLoading}
            submitLabel="Submit"
            className={styles.formContainer}
        />
    );
}
