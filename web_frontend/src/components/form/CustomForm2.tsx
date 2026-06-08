/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useCallback, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import { FormContext } from "./formContext";
import type { FormValues } from "./formContext";
import { Button } from "@components/ui";

// Any field component that connects to formContext via `name` prop
export type FieldComponent = ReactElement;

interface CustomForm2Props {
    /** Pre-built field components — each auto-connects to formContext via its `name` prop. Optional when using children pattern. */
    fields?: FieldComponent[];
    initialValues?: FormValues;
    onSubmit: (values: FormValues) => void;
    /** Extra JSX slotted after the fields (e.g. custom sections) or can be used as main content when fields is omitted */
    children?: ReactNode;
    isLoading?: boolean;
    submitLabel?: string;
    onCancel?: () => void;
    cancelLabel?: string;
    className?: string;
    /** Gap between fields in px (default 12) */
    fieldGap?: number;
}

export default function CustomForm2({
    fields = [],
    initialValues = {},
    onSubmit,
    children,
    isLoading = false,
    submitLabel = "Save",
    onCancel,
    cancelLabel = "Cancel",
    className,
    fieldGap = 12,
}: CustomForm2Props) {
    const [values, setValues] = useState<FormValues>(initialValues || {});

    // Update form state when initialValues changes (e.g., switching between items)
    React.useEffect(() => {
        if (initialValues && Object.keys(initialValues).length > 0) {
            setValues(initialValues);
        }
    }, [initialValues]);

    const setValue = useCallback((name: string, value: any) => {
        setValues((prev) => ({ ...prev, [name]: value }));
    }, []);

    const register = useCallback((name: string, initial?: any) => {
        setValues((prev) =>
            name in prev ? prev : { ...prev, [name]: initial },
        );
    }, []);

    const getValue = useCallback((name: string) => values[name], [values]);

    const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault();
        onSubmit(values);
    };

    return (
        <FormContext.Provider value={{ values, setValue, register, getValue }}>
            <form onSubmit={handleSubmit} className={className}>
                {fields.map((field, i) => (
                    <div
                        key={
                            ((field.props as Record<string, unknown>)
                                ?.name as string) ?? i
                        }
                        style={{ marginBottom: fieldGap }}
                    >
                        {field}
                    </div>
                ))}

                {children}

                <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                    <Button
                        type="submit"
                        variant="primary"
                        disabled={isLoading}
                    >
                        {isLoading ? "Saving..." : submitLabel}
                    </Button>
                    {onCancel && (
                        <Button
                            type="button"
                            variant="outline"
                            onClick={onCancel}
                            disabled={isLoading}
                        >
                            {cancelLabel}
                        </Button>
                    )}
                </div>
            </form>
        </FormContext.Provider>
    );
}
