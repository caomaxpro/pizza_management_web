import React from "react";
import { Input } from "@components/ui";
import { useForm } from "../formContext";

export type DateFieldType =
    | "date"
    | "time"
    | "datetime-local"
    | "month"
    | "week";

export interface DateFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    value: string;
    onChange: (value: string) => void;
    type?: DateFieldType;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    className?: string;
    min?: string;
    max?: string;
    /**
     * Custom validation handler. Receives value, returns error message or empty string if valid.
     */
    validate?: (value: string) => string;
}

function getDefaultValidation(
    _type: DateFieldType,
    value: string,
    min?: string,
    max?: string,
): string {
    if (!value) return "";
    // Only basic min/max check for now
    if (min && value < min) return `Value must be after ${min}`;
    if (max && value > max) return `Value must be before ${max}`;
    return "";
}

export default function DateField({
    name,
    label,
    icon,
    value = "",
    onChange,
    type = "date",
    placeholder,
    required = false,
    disabled = false,
    className = "",
    min,
    max,
    validate,
}: DateFieldProps) {
    const [touched, setTouched] = React.useState(false);
    const formCtx = useForm();
    const currentValue =
        formCtx && name ? (formCtx.getValue(name) ?? value) : value;
    const changeHandler = (val: string) => {
        if (formCtx && name) formCtx.setValue(name, val);
        else onChange(val);
    };

    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, value);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const error =
        (validate
            ? validate(String(currentValue))
            : getDefaultValidation(type, String(currentValue), min, max)) ||
        (required && !currentValue && touched ? "This field is required" : "");

    return (
        <div className={className}>
            {label && (
                <label
                    style={{ display: "flex", alignItems: "center", gap: 8 }}
                >
                    {icon && (
                        <span
                            style={{
                                display: "inline-block",
                                width: 20,
                                height: 20,
                            }}
                        >
                            {typeof icon === "string" ? (
                                <img
                                    src={icon}
                                    style={{ width: 20, height: 20 }}
                                    aria-hidden
                                />
                            ) : (
                                icon
                            )}
                        </span>
                    )}
                    <span>{label}</span>
                    {required && <span style={{ color: "red" }}> *</span>}
                </label>
            )}
            <Input
                type={type}
                value={currentValue}
                onChange={(e) => changeHandler(e.target.value)}
                placeholder={placeholder}
                required={required}
                disabled={disabled}
                min={min}
                max={max}
                onBlur={() => setTouched(true)}
            />
            {error && (
                <div style={{ color: "red", fontSize: 12, marginTop: 2 }}>
                    {error}
                </div>
            )}
        </div>
    );
}
