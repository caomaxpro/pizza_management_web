import React from "react";
import styles from "./ToggleField.module.scss";
import { useForm } from "../formContext";

export interface ToggleOption {
    value: string;
    label: string;
    disabled?: boolean;
}

export interface ToggleFieldProps {
    name?: string;
    label?: string;
    value?: string;
    onChange?: (value: string) => void;
    options: ToggleOption[];
    disabled?: boolean;
    className?: string;
    style?: React.CSSProperties;
    size?: "sm" | "md" | "lg";
}

export default function ToggleField({
    name,
    label,
    value = "",
    onChange,
    options,
    disabled = false,
    className = "",
    style,
    size = "md",
}: ToggleFieldProps) {
    const formCtx = useForm();
    const currentValue =
        formCtx && name ? (formCtx.getValue(name) ?? value) : value;

    const handleChange = (newValue: string) => {
        if (formCtx && name) {
            formCtx.setValue(name, newValue);
        }
        onChange?.(newValue);
    };

    React.useEffect(() => {
        if (formCtx && name) {
            formCtx.register(name, value);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className={`${styles.toggleContainer} ${className}`} style={style}>
            {label && <label className={styles.label}>{label}</label>}
            <div className={`${styles.toggleGroup} ${styles[`size-${size}`]}`}>
                {options.map((option) => (
                    <button
                        key={option.value}
                        type="button"
                        className={`${styles.toggleButton} ${
                            currentValue === option.value ? styles.active : ""
                        }`}
                        onClick={() => handleChange(option.value)}
                        disabled={disabled || option.disabled}
                        aria-pressed={currentValue === option.value}
                    >
                        {option.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
