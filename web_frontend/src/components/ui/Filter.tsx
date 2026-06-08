/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useCallback, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import { FormContext } from "@components/form/formContext";
import type { FormValues } from "@components/form/formContext";
import { Button } from "./index";

export type FilterFieldComponent = ReactElement;

interface FilterProps {
    /** Pre-built filter field components — each auto-connects to formContext via its `name` prop */
    fields?: FilterFieldComponent[];
    /** Initial filter values */
    initialValues?: FormValues;
    /** Called when apply filter is clicked */
    onApply: (values: FormValues) => void;
    /** Called when reset is clicked — defaults to clearing all values */
    onReset?: (values: FormValues) => void;
    /** Extra JSX slotted after the fields */
    children?: ReactNode;
    /** CSS class name for the container */
    className?: string;
    /** Gap between fields in px (default 8) */
    fieldGap?: number;
    /** Show/hide the buttons container (default true) */
    showButtons?: boolean;
    /** Label for apply button (default "Apply") */
    applyLabel?: string;
    /** Label for reset button (default "Reset") */
    resetLabel?: string;
    /** Disable apply button */
    isLoading?: boolean;
    /** If true, call `onApply` automatically whenever field values change */
    autoApply?: boolean;
}

export const Filter = React.forwardRef<HTMLDivElement, FilterProps>(
    (
        {
            fields = [],
            initialValues = {},
            onApply,
            onReset,
            children,
            className = "",
            fieldGap = 8,
            showButtons = true,
            applyLabel = "Apply",
            resetLabel = "Reset",
            isLoading = false,
            autoApply = false,
        },
        ref,
    ) => {
        const [values, setValues] = useState<FormValues>(initialValues || {});

        // Update filter state when initialValues changes
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

        const handleApply = () => {
            onApply(values);
        };

        // When enabled, automatically fire apply on every values change
        React.useEffect(() => {
            if (autoApply) {
                onApply(values);
            }
            // Intentionally depend on values, autoApply, and onApply
        }, [values, autoApply, onApply]);

        const hasChanges = React.useMemo(() => {
            const init = initialValues || {};
            const keys = Array.from(
                new Set([...Object.keys(init), ...Object.keys(values || {})]),
            );

            const normalize = (v: any) => {
                if (v === undefined || v === null || v === "")
                    return "__undefined__";
                if (Array.isArray(v))
                    return v
                        .map((x) => String(x))
                        .sort()
                        .join("|");
                return String(v);
            };

            return keys.some(
                (k) =>
                    normalize((values as any)[k]) !==
                    normalize((init as any)[k]),
            );
        }, [values, initialValues]);

        const handleReset = () => {
            const resetValues = Object.keys(values).reduce((acc, key) => {
                acc[key] = undefined;
                return acc;
            }, {} as FormValues);

            setValues(resetValues);
            onReset?.(resetValues);
        };

        return (
            <div className={className} ref={ref}>
                <FormContext.Provider
                    value={{ values, setValue, register, getValue }}
                >
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "row",
                            flexWrap: "wrap",
                            gap: fieldGap,
                            alignItems: "flex-start",
                            marginBottom: "2em",
                        }}
                    >
                        {fields.map((field, i) => (
                            <div
                                key={
                                    ((field.props as Record<string, unknown>)
                                        ?.name as string) ?? i
                                }
                                style={{ flexShrink: 0 }}
                            >
                                {field}
                            </div>
                        ))}

                        {children}

                        {showButtons && hasChanges && (
                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "row",
                                    gap: 8,
                                    marginTop: 30,
                                    // marginLeft: "auto",
                                    alignItems: "center",
                                    alignSelf: "center",
                                }}
                            >
                                {!autoApply && (
                                    <Button
                                        type="button"
                                        variant="primary"
                                        onClick={handleApply}
                                        disabled={isLoading}
                                    >
                                        {isLoading ? "Applying..." : applyLabel}
                                    </Button>
                                )}
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handleReset}
                                    disabled={isLoading}
                                >
                                    {resetLabel}
                                </Button>
                            </div>
                        )}
                    </div>
                </FormContext.Provider>
            </div>
        );
    },
);

Filter.displayName = "Filter";

export default Filter;
