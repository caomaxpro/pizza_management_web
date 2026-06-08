/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef, useState } from "react";
import { CheckSquare } from "phosphor-react";
import { SearchBar } from "../../ui/SearchBar";
import styles from "./SelectField.module.scss";
import { useForm } from "../formContext";

// ──────────────────────────────────────────────────────────────────────────────
// Select Component (merged from Select.tsx)
// ──────────────────────────────────────────────────────────────────────────────

export interface SelectOption {
    value: string;
    label: string;
    disabled?: boolean;
}

export interface SelectProps extends Omit<
    React.SelectHTMLAttributes<HTMLSelectElement>,
    "multiple" | "onChange" | "value"
> {
    label?: string;
    error?: string;
    options?: SelectOption[];
    children?: React.ReactNode;
    multi?: boolean;
    value?: string | string[];
    onChange?: (
        value: string | string[],
        event?: React.ChangeEvent<any>,
    ) => void;
    placeholder?: string;
    wrapperBgColor?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
    (
        {
            label,
            error,
            options,
            className,
            multi,
            value,
            onChange,
            placeholder,
            wrapperBgColor,
            ...props
        },
        ref,
    ) => {
        const [open, setOpen] = useState(false);
        const [searchTerm, setSearchTerm] = useState("");
        const wrapperRef = useRef<HTMLDivElement>(null);
        const searchInputRef = useRef<HTMLInputElement>(null);

        // Close dropdown on outside click
        React.useEffect(() => {
            if (!open) return;
            const handleClick = (e: MouseEvent) => {
                if (
                    wrapperRef.current &&
                    !wrapperRef.current.contains(e.target as Node)
                ) {
                    setOpen(false);
                }
            };
            document.addEventListener("mousedown", handleClick);
            return () => document.removeEventListener("mousedown", handleClick);
        }, [open]);

        // Filter options based on search term
        const filteredOptions = options?.filter((opt) =>
            opt.label.toLowerCase().includes(searchTerm.toLowerCase()),
        );

        // For multi-select, value is string[]
        const selectedValues = multi
            ? Array.isArray(value)
                ? value
                : []
            : value;

        // Always declare tagsContainerRef at top-level to avoid conditional hook call
        const tagsContainerRef = React.useRef<HTMLDivElement>(null);

        // Always call useEffect, but only run logic if multi is true
        React.useEffect(() => {
            if (multi && tagsContainerRef.current) {
                tagsContainerRef.current.scrollLeft =
                    tagsContainerRef.current.scrollWidth;
            }
        }, [
            multi,
            Array.isArray(selectedValues)
                ? selectedValues.join()
                : selectedValues,
        ]);

        // Custom dropdown for both single and multi
        return (
            <div
                className={styles.selectWrapper}
                ref={wrapperRef}
                tabIndex={-1}
            >
                {label && <label className={styles.selectLabel}>{label}</label>}
                <div
                    className={
                        multi
                            ? `${styles.select} ${styles.selectContainer} ${error ? styles.selectError : ""} ${className || ""}`
                            : `${styles.select} ${styles.singleSelect} ${error ? styles.selectError : ""} ${className || ""}`
                    }
                    style={
                        wrapperBgColor
                            ? ({
                                  //   "--select-bg": wrapperBgColor,
                                  backgroundColor: wrapperBgColor,
                              } as React.CSSProperties)
                            : undefined
                    }
                    tabIndex={0}
                    onClick={() => {
                        setOpen((prev) => !prev);
                        if (!multi) return;
                        setTimeout(() => searchInputRef.current?.focus(), 0);
                    }}
                >
                    {multi ? (
                        <div
                            ref={tagsContainerRef}
                            className={styles.tagsScroll}
                        >
                            {Array.isArray(selectedValues) &&
                            selectedValues.length > 0 ? (
                                options
                                    ?.filter((opt) =>
                                        selectedValues.includes(opt.value),
                                    )
                                    .map((opt) => (
                                        <span
                                            key={opt.value}
                                            className={styles.tag}
                                        >
                                            {opt.label}
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    const arr = Array.isArray(
                                                        selectedValues,
                                                    )
                                                        ? selectedValues
                                                        : [];
                                                    const newVals = arr.filter(
                                                        (v) => v !== opt.value,
                                                    );
                                                    onChange?.(
                                                        newVals,
                                                        e as any,
                                                    );
                                                }}
                                                style={{
                                                    background: "none",
                                                    border: "none",
                                                    cursor: "pointer",
                                                    padding: "2px 6px",
                                                    marginLeft: "6px",
                                                    fontSize: "20px",
                                                    color: "currentColor",
                                                    display: "inline-flex",
                                                    alignItems: "center",
                                                    justifyContent: "center",
                                                    borderRadius: "50%",
                                                    width: "24px",
                                                    height: "24px",
                                                    flexShrink: 0,
                                                    transition: "all 0.2s ease",
                                                }}
                                                onMouseEnter={(e) => {
                                                    const btn = e.currentTarget;
                                                    btn.style.background =
                                                        "rgba(0, 0, 0, 0.1)";
                                                }}
                                                onMouseLeave={(e) => {
                                                    const btn = e.currentTarget;
                                                    btn.style.background =
                                                        "none";
                                                }}
                                                className={styles.tagClose}
                                                aria-label="Remove"
                                            >
                                                ×
                                            </button>
                                        </span>
                                    ))
                            ) : (
                                <span className={styles.placeholder}>
                                    {placeholder || "Select..."}
                                </span>
                            )}
                        </div>
                    ) : (
                        <span className={styles.singleSelectedValue}>
                            {options?.find((opt) => opt.value === value)
                                ?.label || (
                                <span className={styles.placeholder}>
                                    {placeholder || "Select..."}
                                </span>
                            )}
                        </span>
                    )}
                    <span
                        className={`${styles.dropdown} ${open ? styles.dropdownOpen : styles.dropdownClosed}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            setOpen((prev) => !prev);
                            if (!open) {
                                setTimeout(
                                    () => searchInputRef.current?.focus(),
                                    0,
                                );
                            }
                        }}
                    >
                        ▼
                    </span>
                    {open && (
                        <div
                            className={styles.dropdownContainer}
                            onClick={(e) => e.stopPropagation()}
                        >
                            {multi && (
                                <div className={styles.searchHeader}>
                                    <SearchBar
                                        value={searchTerm}
                                        onChange={setSearchTerm}
                                        placeholder="Search..."
                                        className={styles.searchInput}
                                    />
                                </div>
                            )}
                            {filteredOptions?.map((opt) => (
                                <label
                                    key={opt.value}
                                    className={`${styles.optionLabel} ${opt.disabled ? styles.optionLabelDisabled : styles.optionLabelEnabled}`}
                                    style={{
                                        cursor: opt.disabled
                                            ? "not-allowed"
                                            : "pointer",
                                    }}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        if (opt.disabled) return;
                                        if (multi) {
                                            const arr = Array.isArray(
                                                selectedValues,
                                            )
                                                ? selectedValues
                                                : [];
                                            const checked = arr.includes(
                                                opt.value,
                                            );
                                            const newVals = checked
                                                ? arr.filter(
                                                      (v) => v !== opt.value,
                                                  )
                                                : [...arr, opt.value];
                                            onChange?.(newVals, e);
                                        } else {
                                            onChange?.(opt.value, e);
                                            setOpen(false);
                                        }
                                    }}
                                >
                                    {multi ? (
                                        <span
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                            }}
                                        >
                                            <CheckSquare
                                                color={
                                                    Array.isArray(
                                                        selectedValues,
                                                    ) &&
                                                    selectedValues.includes(
                                                        opt.value,
                                                    )
                                                        ? "#929091"
                                                        : "#d1d5db"
                                                }
                                                weight={
                                                    Array.isArray(
                                                        selectedValues,
                                                    ) &&
                                                    selectedValues.includes(
                                                        opt.value,
                                                    )
                                                        ? "fill"
                                                        : "regular"
                                                }
                                                size={24}
                                            />
                                        </span>
                                    ) : null}
                                    <span style={{ marginLeft: multi ? 8 : 0 }}>
                                        {opt.label}
                                    </span>
                                </label>
                            ))}
                            {filteredOptions &&
                                filteredOptions.length === 0 && (
                                    <div className={styles.noResults}>
                                        No results found
                                    </div>
                                )}
                            {props.children}
                        </div>
                    )}
                </div>
                {error && <span className={styles.errorText}>{error}</span>}
            </div>
        );
    },
);

Select.displayName = "Select";

// ──────────────────────────────────────────────────────────────────────────────
// SelectField Component
// ──────────────────────────────────────────────────────────────────────────────

export interface SelectFieldOption {
    value: string;
    label: string;
    disabled?: boolean;
}

export interface SelectFieldProps {
    name?: string;
    label?: string;
    icon?: string | any;
    value?: string | string[];
    onChange?: (value: string | string[]) => void;
    options: SelectFieldOption[];
    placeholder?: string;
    disabled?: boolean;
    className?: string;
    style?: React.CSSProperties;
    multi?: boolean;
    variant?: "default" | "toggle";
    selectWrapperBackgroundColor?: string;
}

export default function SelectField({
    name,
    label,
    icon,
    value = "",
    onChange,
    options,
    placeholder,
    disabled = false,
    className = "",
    style,
    multi = false,
    variant = "default",
    selectWrapperBackgroundColor,
}: SelectFieldProps) {
    const stringOptions = options.map((opt) => ({
        ...opt,
        value: String(opt.value),
    }));

    const handleChange = (selected: any) => {
        if (multi) {
            if (Array.isArray(selected)) {
                changeHandler(
                    selected.map((opt) =>
                        typeof opt === "string" ? opt : String(opt.value),
                    ),
                );
            } else if (selected) {
                changeHandler([
                    typeof selected === "string"
                        ? selected
                        : String(selected.value),
                ]);
            } else {
                changeHandler([]);
            }
        } else {
            if (typeof selected === "string") {
                changeHandler(selected);
            } else if (selected && typeof selected.value === "string") {
                changeHandler(selected.value);
            } else {
                changeHandler("");
            }
        }
    };

    const formCtx = useForm();
    const currentValue =
        formCtx && name ? (formCtx.getValue(name) ?? value) : value;
    const changeHandler = (val: string | string[]) => {
        if (formCtx && name) formCtx.setValue(name, val);
        onChange?.(val);
    };

    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, value);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    if (variant === "toggle") {
        return (
            <div
                className={`${styles.selectFieldContainer} ${className}`}
                style={style}
            >
                {label && <label className={styles.fieldLabel}>{label}</label>}
                <div className={styles.toggleGroup}>
                    {stringOptions.map((option) => (
                        <button
                            key={option.value}
                            type="button"
                            className={`${styles.toggleButton} ${
                                currentValue === option.value
                                    ? styles.active
                                    : ""
                            }`}
                            onClick={() =>
                                !disabled &&
                                !option.disabled &&
                                handleChange(option.value)
                            }
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

    return (
        <div
            className={`${styles.selectFieldContainer} ${className}`}
            style={style}
        >
            {label && (
                <label className={styles.fieldLabel}>
                    {icon && (
                        <span className={styles.labelIcon}>
                            {typeof icon === "string" ? (
                                <img src={icon} aria-hidden />
                            ) : (
                                icon
                            )}
                        </span>
                    )}
                    <span>{label}</span>
                </label>
            )}
            <Select
                value={currentValue}
                onChange={(s: any) => handleChange(s)}
                options={stringOptions}
                placeholder={placeholder}
                disabled={disabled}
                multi={multi}
                wrapperBgColor={selectWrapperBackgroundColor}
            />
        </div>
    );
}
