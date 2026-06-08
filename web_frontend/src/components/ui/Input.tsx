import React from "react";
import styles from "./Input.module.scss";

export type InputType = "text" | "number" | "email" | "password" | "search";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ label, error, helperText, className, ...props }, ref) => {
        return (
            <div className={styles.inputWrapper}>
                {label && <label className={styles.label}>{label}</label>}
                <input
                    ref={ref}
                    className={`${styles.input} ${error ? styles.inputError : ""} ${className || ""}`}
                    {...props}
                />
                {error && <span className={styles.errorText}>{error}</span>}
                {helperText && !error && (
                    <span className={styles.helperText}>{helperText}</span>
                )}
            </div>
        );
    },
);

Input.displayName = "Input";
