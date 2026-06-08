import React from "react";
import styles from "./ProgressBar.module.scss";

export interface ProgressBarProps {
    /** Label/message to display above the progress bar */
    label?: string;
    /** Current progress percentage (0-100). If omitted, shows indeterminate animation */
    progress?: number;
    /** Show percentage text */
    showPercentage?: boolean;
    /** Show cancel button */
    showCancelButton?: boolean;
    /** Callback when cancel button is clicked */
    onCancel?: () => void;
}

export const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
    (
        {
            label = "Creating ingredient...",
            progress,
            showPercentage = false,
            showCancelButton = false,
            onCancel,
        },
        ref,
    ) => {
        const isIndeterminate = progress === undefined;
        const progressValue = Math.min(100, Math.max(0, progress || 0));

        return (
            <div ref={ref} className={styles.container}>
                {label && <div className={styles.label}>{label}</div>}
                <div
                    className={`${styles.progressBar} ${
                        isIndeterminate ? styles.indeterminate : ""
                    }`}
                >
                    <div
                        className={styles.fill}
                        style={
                            !isIndeterminate
                                ? {
                                      width: `${progressValue}%`,
                                  }
                                : undefined
                        }
                    />
                    {showPercentage && !isIndeterminate && (
                        <div className={styles.percentageText}>
                            {progressValue}%
                        </div>
                    )}
                </div>
                {showCancelButton && (
                    <button
                        onClick={onCancel}
                        style={{
                            marginTop: "0.75rem",
                            padding: "0.5rem 1rem",
                            backgroundColor: "#ef4444",
                            color: "white",
                            border: "none",
                            borderRadius: "0.375rem",
                            cursor: "pointer",
                            fontSize: "0.875rem",
                            fontWeight: "500",
                        }}
                    >
                        Cancel Import
                    </button>
                )}
            </div>
        );
    },
);

ProgressBar.displayName = "ProgressBar";
