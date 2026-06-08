import React from "react";
import styles from "./Checkbox.module.css";

export interface CheckboxProps extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    "type"
> {
    label?: string;
    error?: string;
    containerClassName?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
    (
        {
            label,
            error,
            containerClassName,
            disabled = false,
            checked = false,
            className = "",
            ...props
        },
        ref,
    ) => {
        return (
            <div
                className={`${styles.checkboxContainer} ${containerClassName || ""}`}
            >
                <label
                    className={`${styles.checkboxLabel} ${disabled ? styles.disabled : ""}`}
                >
                    <input
                        ref={ref}
                        type="checkbox"
                        className={`${styles.checkboxInput} ${className}`}
                        disabled={disabled}
                        checked={checked}
                        {...props}
                    />
                    <span className={styles.checkboxCustom}>
                        <svg
                            className={styles.checkmark}
                            viewBox="0 0 24 24"
                            width="16"
                            height="16"
                            stroke="currentColor"
                            strokeWidth="3"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </span>
                    {label && <span className={styles.labelText}>{label}</span>}
                </label>
                {error && <span className={styles.errorText}>{error}</span>}
            </div>
        );
    },
);

Checkbox.displayName = "Checkbox";

export default Checkbox;
