import React from "react";
import styles from "./Button.module.scss";

export type ButtonVariant = "primary" | "secondary" | "outline";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    children: React.ReactNode;
    isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            variant = "primary",
            size = "lg",
            isLoading = false,
            disabled,
            children,
            className,
            ...props
        },
        ref,
    ) => {
        return (
            <button
                ref={ref}
                className={`${styles.button} ${styles[variant]} ${styles[size]} ${className || ""}`}
                disabled={disabled || isLoading}
                {...props}
            >
                {isLoading ? "Loading..." : children}
            </button>
        );
    },
);

Button.displayName = "Button";
