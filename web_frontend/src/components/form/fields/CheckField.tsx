import React from "react";
import { useForm } from "../formContext";

export interface CheckFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    value?: boolean;
    onChange?: (checked: boolean) => void;
    disabled?: boolean;
    className?: string;
}

export default function CheckField({
    name,
    label,
    icon,
    value = false,
    onChange,
    disabled = false,
    className = "",
}: CheckFieldProps) {
    const formCtx = useForm();
    const currentValue =
        formCtx && name
            ? ((formCtx.getValue(name) as boolean) ?? value)
            : value;

    const handleChange = (checked: boolean) => {
        onChange?.(checked);
        if (formCtx && name) {
            formCtx.setValue(name, checked);
        }
    };

    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, value);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className={className}>
            <label
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.5 : 1,
                }}
            >
                {icon && (
                    <span
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: "20px",
                            height: "20px",
                            flexShrink: 0,
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
                <input
                    type="checkbox"
                    checked={currentValue}
                    onChange={(e) => handleChange(e.target.checked)}
                    disabled={disabled}
                    style={{
                        cursor: disabled ? "not-allowed" : "pointer",
                        width: "16px",
                        height: "16px",
                    }}
                />
                <span>{label}</span>
            </label>
        </div>
    );
}
