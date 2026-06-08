/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import type { Ingredient } from "../../services/ingredients";
import CustomForm2 from "@components/form/CustomForm2";
import { useForm } from "@components/form/formContext";
import type { FormValues } from "@components/form/formContext";
import TextField from "@components/form/fields/TextField";
import TextareaField from "@components/form/fields/TextareaField";
import SelectField from "@components/form/fields/SelectField";
import FileField from "@components/form/fields/FileField";
import { Checkbox } from "@components/ui";

// Frontend copy of backend choices (keep in sync with backend constants)
const INGREDIENT_TYPE_CHOICES = [
    { value: "dough", label: "Dough" },
    { value: "sauce", label: "Sauce" },
    { value: "cheese", label: "Cheese" },
    { value: "topping", label: "Topping" },
    { value: "extra", label: "Extra" },
];

const INGREDIENT_SUB_TYPE_CHOICES = [
    { value: "veggie", label: "Vegetarian" },
    { value: "meat", label: "Meat" },
    { value: "cheese", label: "Cheese" },
];

interface IngredientFormProps {
    initialData?: Ingredient;
    onSubmit: (data: FormData) => void;
    isLoading?: boolean;
    onCancel?: () => void;
}

function IsActiveCheckbox() {
    const form = useForm()!;
    return (
        <Checkbox
            checked={!!form.getValue("is_active")}
            onChange={(e) => form.setValue("is_active", e.target.checked)}
            label="Active"
        />
    );
}

function SubTypeField() {
    const form = useForm()!;
    const typeValue = form.getValue("type");

    // Only render if type is "pizza"
    if (typeValue !== "topping") {
        return null;
    }

    return (
        <SelectField
            name="sub_type"
            label="Sub-type"
            value=""
            onChange={() => {}}
            options={INGREDIENT_SUB_TYPE_CHOICES}
        />
    );
}

export default function IngredientForm({
    initialData,
    onSubmit,
    isLoading = false,
    onCancel,
}: IngredientFormProps) {
    const handleSubmit = (data: Record<string, unknown>) => {
        const fd = new FormData();

        Object.entries(data).forEach(([k, v]) => {
            if (v === undefined || v === null) return;

            // Files: backend expects `image_file` and `piece_file`
            if (Array.isArray(v)) {
                v.forEach((item) => {
                    if (item instanceof File) fd.append(k, item);
                    else fd.append(k, String(item));
                });
            } else if (v instanceof File) {
                fd.append(k, v);
            } else if (typeof v === "boolean") {
                fd.append(k, v ? "1" : "0");
            } else {
                fd.append(k, String(v));
            }
        });

        onSubmit(fd);
    };

    const initial: FormValues | undefined = initialData
        ? {
              ...initialData,
              created_at: initialData.created_at ?? undefined,
              // image fields are URLs on model; file inputs remain empty for edit
              image_file: null,
              piece_file: null,
          }
        : undefined;

    const fields = [
        <TextField
            name="name"
            label="Name"
            value=""
            onChange={() => {}}
            required
        />,
        <TextareaField
            name="description"
            label="Description"
            value=""
            onChange={() => {}}
            rows={3}
        />,
        <TextField
            name="price"
            label="Price"
            type="number"
            value=""
            onChange={() => {}}
            required
        />,
        <TextField
            name="original_price"
            label="Original Price"
            type="number"
            value=""
            onChange={() => {}}
        />,
        <SelectField
            name="type"
            label="Type"
            value=""
            onChange={() => {}}
            options={INGREDIENT_TYPE_CHOICES}
        />,
        <SubTypeField />,
        <FileField
            name="image_file"
            label="Image"
            files={[]}
            onChange={() => {}}
            accept="image/*"
        />,
        <FileField
            name="piece_file"
            label="Piece Image"
            files={[]}
            onChange={() => {}}
            accept="image/*"
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
        >
            <IsActiveCheckbox />
        </CustomForm2>
    );
}
