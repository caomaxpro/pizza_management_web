import React from "react";
import { Input } from "@components/ui";
import { useForm } from "../formContext";

export type TextFieldType =
    | "text"
    | "password"
    | "email"
    | "number"
    | "tel"
    | "url"
    | "search";

export interface TextFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    value: string;
    onChange: (value: string) => void;
    type?: TextFieldType;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    className?: string;
    style?: React.CSSProperties;
    /**
     * Custom validation handler. Receives value, returns error message or empty string if valid.
     */
    validate?: (value: string) => string;
}

function getDefaultValidation(type: TextFieldType, value: string): string {
    if (!value) return "";
    switch (type) {
        case "email": {
            // Simple email regex
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(value) ? "" : "Invalid email format";
        }
        case "url": {
            try {
                new URL(value);
                return "";
            } catch {
                return "Invalid URL";
            }
        }
        case "number": {
            return isNaN(Number(value)) ? "Must be a number" : "";
        }
        case "tel": {
            // Accepts digits, spaces, dashes, parentheses, plus
            const re = /^[0-9\s\-()+]+$/;
            return re.test(value) ? "" : "Invalid phone number";
        }
        default:
            return "";
    }
}

export default function TextField({
    name,
    label,
    icon,
    value = "",
    onChange,
    type = "text",
    placeholder,
    required = false,
    disabled = false,
    className = "",
    style,
    validate,
}: TextFieldProps) {
    const [touched, setTouched] = React.useState(false);
    // integrate with CustomForm when `name` is provided
    const formCtx = useForm();
    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, value);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    const currentValue =
        formCtx && name ? (formCtx.getValue(name) ?? value) : value;
    const changeHandler = (val: string) => {
        if (formCtx && name) formCtx.setValue(name, val);
        else onChange(val);
    };
    const error =
        (validate
            ? validate(String(currentValue))
            : getDefaultValidation(type, String(currentValue))) ||
        (required && !currentValue && touched ? "This field is required" : "");

    return (
        <div className={className} style={style}>
            {label && (
                <label
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        marginBottom: 8,
                    }}
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
                onBlur={() => setTouched(true)}
                autoComplete={type === "password" ? "new-password" : undefined}
            />
            {error && (
                <div style={{ color: "red", fontSize: 12, marginTop: 2 }}>
                    {error}
                </div>
            )}
        </div>
    );
}
