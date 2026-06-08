import React from "react";
import { Input } from "@components/ui";
import { useForm } from "../formContext";
import * as icons from "@assets/icons";
import styles from "./SearchField.module.scss";

export interface SearchFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    value?: string;
    onChange?: (value: string) => void;
    /** Callback fired when search is triggered (Enter key or button click) */
    onSearch?: (value: string) => void;
    /** If true, search is triggered on every keystroke. Default: false */
    autoSearch?: boolean;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
    style?: React.CSSProperties;
    isLoading?: boolean;
}

export default function SearchField({
    name,
    label,
    icon,
    value = "",
    onChange,
    onSearch,
    autoSearch = false,
    placeholder,
    disabled = false,
    className = "",
    style,
    isLoading = false,
}: SearchFieldProps) {
    // Integrate with CustomForm when `name` is provided
    const formCtx = useForm();
    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, value);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const currentValue =
        formCtx && name ? (formCtx.getValue(name) ?? value) : value;

    const handleChange = (newValue: string) => {
        onChange?.(newValue);
        if (formCtx && name) formCtx.setValue(name, newValue);

        // Auto search on keystroke if enabled
        if (autoSearch) {
            onSearch?.(newValue);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        // Trigger search on Enter
        if (!autoSearch && e.key === "Enter") {
            e.preventDefault();
            onSearch?.(currentValue);
        }
    };

    const handleSearchClick = () => {
        onSearch?.(currentValue);
    };

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
                </label>
            )}

            {autoSearch ? (
                // Auto search mode: just input field
                <Input
                    type="text"
                    value={currentValue}
                    onChange={(e) => handleChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder || "Type to search..."}
                    disabled={disabled}
                />
            ) : (
                // Manual search mode: input + button
                <div className={styles.searchContainer}>
                    <Input
                        type="text"
                        value={currentValue}
                        onChange={(e) => handleChange(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder || "Enter search term..."}
                        disabled={disabled}
                    />
                    <button
                        type="button"
                        className={styles.searchButton}
                        onClick={handleSearchClick}
                        disabled={disabled || isLoading}
                        title={
                            autoSearch
                                ? "Auto search enabled"
                                : "Press Enter or click to search"
                        }
                    >
                        {isLoading ? (
                            <span style={{ opacity: 0.6 }}>⏳</span>
                        ) : (
                            <img src={icons.icons8Search} alt="Search" />
                        )}
                    </button>
                </div>
            )}
        </div>
    );
}
