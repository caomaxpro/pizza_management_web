import React, { useState } from "react";
import styles from "./MessageCard.module.scss";

export interface MessageCardProps {
    /**
     * Message or array of messages to display
     */
    message?: string | string[];
    /**
     * Optional title for the card
     */
    title?: string;
    /**
     * Whether the card can be dismissed by user
     */
    dismissible?: boolean;
    /**
     * Callback when card is dismissed
     */
    onDismiss?: () => void;
    /**
     * Custom CSS class name
     */
    className?: string;
    /**
     * Icon to display (optional, auto-determined by variant)
     */
    icon?: React.ReactNode | string;
    /**
     * Variant: info | error | success | warning
     */
    variant?: "info" | "error" | "success" | "warning";
    /**
     * Custom margin (e.g., "1rem", "10px 20px")
     */
    margin?: string;
    /**
     * Custom margin top
     */
    marginTop?: string;
    /**
     * Custom margin bottom
     */
    marginBottom?: string;
    /**
     * Custom margin left
     */
    marginLeft?: string;
    /**
     * Custom margin right
     */
    marginRight?: string;
    /**
     * Custom padding (e.g., "1rem", "10px 20px")
     */
    padding?: string;
    /**
     * Custom padding top
     */
    paddingTop?: string;
    /**
     * Custom padding bottom
     */
    paddingBottom?: string;
    /**
     * Custom padding left
     */
    paddingLeft?: string;
    /**
     * Custom padding right
     */
    paddingRight?: string;
    /**
     * Gap between icon and message content
     */
    gap?: string;
    /**
     * Custom width
     */
    width?: string;
    /**
     * Custom max-width
     */
    maxWidth?: string;
}

export default function MessageCard({
    message,
    title,
    dismissible = true,
    onDismiss,
    className = "",
    icon,
    variant = "info",
    margin,
    marginTop,
    marginBottom,
    marginLeft,
    marginRight,
    padding,
    paddingTop,
    paddingBottom,
    paddingLeft,
    paddingRight,
    gap,
    width,
    maxWidth,
}: MessageCardProps) {
    const [isVisible, setIsVisible] = useState(true);

    const handleDismiss = () => {
        setIsVisible(false);
        onDismiss?.();
    };

    // Build custom styles
    const customStyle: React.CSSProperties = {
        ...(margin && { margin }),
        ...(marginTop && { marginTop }),
        ...(marginBottom && { marginBottom }),
        ...(marginLeft && { marginLeft }),
        ...(marginRight && { marginRight }),
        ...(padding && { padding }),
        ...(paddingTop && { paddingTop }),
        ...(paddingBottom && { paddingBottom }),
        ...(paddingLeft && { paddingLeft }),
        ...(paddingRight && { paddingRight }),
        ...(width && { width }),
        ...(maxWidth && { maxWidth }),
    };

    if (!isVisible || !message) {
        return null;
    }

    const messages = Array.isArray(message) ? message : [message];

    let displayIcon = icon;
    if (!displayIcon) {
        switch (variant) {
            case "success":
                displayIcon = "✓";
                break;
            case "warning":
                displayIcon = "⚠";
                break;
            case "error":
                displayIcon = "✕";
                break;
            case "info":
            default:
                displayIcon = "ℹ";
        }
    }

    return (
        <div
            className={`${styles.messageCard} ${styles[variant]} ${className}`}
            role="alert"
            style={customStyle}
        >
            <div className={styles.content} style={gap ? { gap } : undefined}>
                {displayIcon && (
                    <div className={styles.icon}>
                        {typeof displayIcon === "string" ? (
                            <span>{displayIcon}</span>
                        ) : (
                            displayIcon
                        )}
                    </div>
                )}
                <div className={styles.message}>
                    {title && <div className={styles.title}>{title}</div>}
                    {messages.length === 1 ? (
                        <div className={styles.text}>{messages[0]}</div>
                    ) : (
                        <ul className={styles.list}>
                            {messages.map((msg, idx) => (
                                <li key={idx}>{msg}</li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
            {dismissible && (
                <button
                    className={styles.closeBtn}
                    onClick={handleDismiss}
                    aria-label="Dismiss message"
                    type="button"
                >
                    ×
                </button>
            )}
        </div>
    );
}
