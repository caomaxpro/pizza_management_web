import React, { useState, useEffect } from "react";
import { useDebounce } from "../../hooks/useDebounce";
import searchIcon from "../../assets/icons/icons8-search.svg";
import styles from "./SearchBar.module.scss";

export interface SearchBarProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    debounceMs?: number;
    style?: React.CSSProperties;
}

export const SearchBar: React.FC<SearchBarProps> = ({
    value,
    onChange,
    placeholder = "Search...",
    className = "",
    debounceMs = 300,
    style = {},
}) => {
    const [displayValue, setDisplayValue] = useState(value);
    const debouncedValue = useDebounce(displayValue, debounceMs);

    // Update display value when parent updates value
    useEffect(() => {
        setDisplayValue(value);
    }, [value]);

    // Call onChange when debounced value changes
    useEffect(() => {
        if (debouncedValue !== value) {
            onChange(debouncedValue);
        }
    }, [debouncedValue, value, onChange]);

    return (
        <div
            className={`${styles.searchBarWrapper} ${className}`}
            style={style}
        >
            <img src={searchIcon} alt="search" className={styles.searchIcon} />
            <input
                type="text"
                value={displayValue}
                onChange={(e) => setDisplayValue(e.target.value)}
                placeholder={placeholder}
                className={styles.input}
            />
        </div>
    );
};

export default SearchBar;
