import React, { useRef } from "react";

interface ImageUploadProps {
    label: string;
    value: string | null;
    onChange: (file: File | null, preview: string | null) => void;
    error?: string;
    placeholder?: string;
    maxSizeMB?: number;
    accept?: string;
    removeLabel?: string;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
    label,
    value,
    onChange,
    error,
    placeholder = "Click to upload image",
    maxSizeMB = 5,
    accept = "image/*",
    removeLabel = "✕",
}) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [isDragging, setIsDragging] = React.useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (!file.type.startsWith("image/")) {
                onChange(null, null);
                return;
            }
            if (file.size > maxSizeMB * 1024 * 1024) {
                onChange(null, null);
                return;
            }
            const reader = new FileReader();
            reader.onload = (event) => {
                onChange(file, event.target?.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleRemove = (e: React.MouseEvent) => {
        e.stopPropagation();
        onChange(null, null);
        if (inputRef.current) inputRef.current.value = "";
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file && file.type.startsWith("image/")) {
            if (file.size <= maxSizeMB * 1024 * 1024) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    onChange(file, event.target?.result as string);
                };
                reader.readAsDataURL(file);
            }
        }
    };

    return (
        <div style={{ width: "100%" }}>
            <label
                style={{
                    display: "block",
                    fontSize: "0.95rem",
                    fontWeight: 600,
                    color: "#1f2937",
                    marginBottom: "0.75rem",
                }}
            >
                {label}
            </label>
            <div style={{ marginBottom: "0.5rem" }}>
                {value ? (
                    <div
                        style={{
                            position: "relative",
                            display: "inline-block",
                            borderRadius: "12px",
                            overflow: "hidden",
                            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                        }}
                    >
                        <img
                            src={value}
                            alt={label}
                            style={{
                                maxWidth: "180px",
                                maxHeight: "180px",
                                width: "auto",
                                height: "auto",
                                display: "block",
                            }}
                        />
                        <button
                            type="button"
                            onClick={handleRemove}
                            style={{
                                position: "absolute",
                                top: "8px",
                                right: "8px",
                                background: "rgba(0, 0, 0, 0.6)",
                                border: "none",
                                borderRadius: "50%",
                                width: "32px",
                                height: "32px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                cursor: "pointer",
                                color: "white",
                                fontSize: "18px",
                                fontWeight: "bold",
                                transition: "all 0.2s ease",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background =
                                    "rgba(0, 0, 0, 0.8)";
                                e.currentTarget.style.transform = "scale(1.1)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.background =
                                    "rgba(0, 0, 0, 0.6)";
                                e.currentTarget.style.transform = "scale(1)";
                            }}
                        >
                            {removeLabel}
                        </button>
                    </div>
                ) : (
                    <div
                        style={{
                            border: isDragging
                                ? "2px solid #3b82f6"
                                : "2px dashed #d1d5db",
                            borderRadius: "12px",
                            padding: "32px 24px",
                            textAlign: "center",
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                            backgroundColor: isDragging
                                ? "rgba(59, 130, 246, 0.05)"
                                : "#f9fafb",
                        }}
                        onClick={() => inputRef.current?.click()}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = "#3b82f6";
                            e.currentTarget.style.backgroundColor =
                                "rgba(59, 130, 246, 0.02)";
                        }}
                        onMouseLeave={(e) => {
                            if (!isDragging) {
                                e.currentTarget.style.borderColor = "#d1d5db";
                                e.currentTarget.style.backgroundColor =
                                    "#f9fafb";
                            }
                        }}
                    >
                        <div
                            style={{
                                fontSize: "48px",
                                marginBottom: "12px",
                                lineHeight: 1,
                            }}
                        >
                            📸
                        </div>
                        <p
                            style={{
                                margin: "8px 0",
                                fontSize: "0.95rem",
                                fontWeight: 600,
                                color: "#1f2937",
                            }}
                        >
                            {placeholder}
                        </p>
                        <small
                            style={{
                                display: "block",
                                color: "#6b7280",
                                fontSize: "0.85rem",
                                marginTop: "4px",
                            }}
                        >
                            PNG, JPG, WebP (max {maxSizeMB}MB)
                        </small>
                    </div>
                )}
                <input
                    ref={inputRef}
                    type="file"
                    accept={accept}
                    onChange={handleFileChange}
                    style={{ display: "none" }}
                />
            </div>
            {error && (
                <div
                    style={{
                        color: "#ef4444",
                        fontSize: "0.85rem",
                        marginTop: "6px",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                    }}
                >
                    <span>⚠️</span>
                    {error}
                </div>
            )}
        </div>
    );
};
