import React from "react";
import { useForm } from "../formContext";

export interface TextareaFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    className?: string;
    rows?: number;
    maxLength?: number;
    validate?: (value: string) => string;
}

function getDefaultValidation(value: string, maxLength?: number): string {
    if (!value) return "";
    if (maxLength && value.length > maxLength) {
        return `Maximum ${maxLength} characters`;
    }
    return "";
}

export default function TextareaField({
    name,
    label,
    icon,
    value = "",
    onChange,
    placeholder,
    required = false,
    disabled = false,
    className = "",
    rows = 3,
    maxLength,
    validate,
}: TextareaFieldProps) {
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
            : getDefaultValidation(String(currentValue), maxLength)) ||
        (required && !currentValue && touched ? "This field is required" : "");

    const maxRows = 5;
    const effectiveRows = Math.min(rows, maxRows);

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
            <textarea
                value={currentValue}
                onChange={(e) => changeHandler(e.target.value)}
                placeholder={placeholder}
                required={required}
                disabled={disabled}
                rows={effectiveRows}
                maxLength={maxLength}
                onBlur={() => setTouched(true)}
                style={{
                    width: "100%",
                    padding: 8,
                    borderRadius: 6,
                    border: "1px solid #e5e7eb",
                    resize: "none",
                    overflowY: "auto",
                    // fix the visible height corresponding to row count so content scrolls inside
                    height: `${effectiveRows * 1.2}em`,
                    lineHeight: "1.2em",
                }}
            />
            {error && (
                <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>
                    {error}
                </div>
            )}
        </div>
    );
}
