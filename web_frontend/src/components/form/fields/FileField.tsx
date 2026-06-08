import React from "react";
import { useForm } from "../formContext";
import { FILE_TYPES } from "./fileTypes";
import type { FileTypeKey } from "./fileTypes";

export type { FileTypeKey };
export { FILE_TYPES };

export interface FileFieldProps {
    name?: string;
    label?: string;
    icon?: string | React.ReactNode;
    files?: File[];
    onChange: (files: File[]) => void;
    fileType?: FileTypeKey | FileTypeKey[]; // Predefined types
    accept?: string; // Custom accept string (fallback)
    multiple?: boolean;
    maxFiles?: number;
    maxSizeBytes?: number; // per file
    className?: string;
    preview?: boolean;
    validate?: (files: File[]) => string;
}

export default function FileField({
    name,
    label,
    icon,
    files = [],
    onChange,
    fileType,
    accept,
    multiple = false,
    maxFiles,
    maxSizeBytes,
    className = "",
    preview = true,
    validate,
}: FileFieldProps) {
    const formCtx = useForm();
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const [localFiles, setLocalFiles] = React.useState<File[]>(
        formCtx && name ? ((formCtx.getValue(name) as File[]) ?? files) : files,
    );
    const [error, setError] = React.useState("");
    const [isDragging, setIsDragging] = React.useState(false);

    // Keep object URLs for previews
    const [previews, setPreviews] = React.useState<string[]>([]);

    React.useEffect(() => {
        if (formCtx && name) formCtx.register(name, files);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    React.useEffect(() => {
        // prefer form value when available
        if (formCtx && name) {
            const v = formCtx.getValue(name) as File[] | undefined;
            if (v !== undefined) setLocalFiles(v || []);
            else setLocalFiles(files || []);
        } else {
            setLocalFiles(files || []);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [files]);

    React.useEffect(() => {
        // generate previews for image files
        if (!preview) return;
        const urls = localFiles
            .filter((f) => f.type.startsWith("image/"))
            .map((f) => URL.createObjectURL(f));
        setPreviews(urls);

        return () => {
            urls.forEach((u) => URL.revokeObjectURL(u));
        };
    }, [localFiles, preview]);

    // Get accept string for HTML input element
    const getAcceptString = (): string => {
        if (fileType) {
            const types = Array.isArray(fileType) ? fileType : [fileType];
            const allMime = types.flatMap((t) => FILE_TYPES[t]?.mime || []);
            const allExt = types.flatMap((t) => FILE_TYPES[t]?.ext || []);
            return [...allMime, ...allExt].join(",");
        }
        return accept || "";
    };
    const getAllowedTypes = (): { mime: string[]; ext: string[] } => {
        // If fileType is provided, use predefined types
        if (fileType) {
            const types = Array.isArray(fileType) ? fileType : [fileType];
            const allMime = types.flatMap((t) => FILE_TYPES[t]?.mime || []);
            const allExt = types.flatMap((t) => FILE_TYPES[t]?.ext || []);
            return { mime: allMime, ext: allExt };
        }

        // Fallback to custom accept string
        if (!accept) return { mime: [], ext: [] };

        const acceptTypes = accept
            .split(",")
            .map((t) => t.trim().toLowerCase());
        const mime: string[] = [];
        const ext: string[] = [];

        acceptTypes.forEach((t) => {
            if (t.startsWith(".")) {
                ext.push(t);
            } else {
                mime.push(t);
            }
        });

        return { mime, ext };
    };

    // Check if file matches accepted types
    const isFileTypeAllowed = (file: File): boolean => {
        const { mime: allowedMime, ext: allowedExt } = getAllowedTypes();
        if (allowedMime.length === 0 && allowedExt.length === 0) return true;

        const fileMimeType = file.type.toLowerCase();
        const fileName = file.name.toLowerCase();

        // Check MIME types
        const mimeMatches = allowedMime.some((m) => {
            if (m.endsWith("/*")) {
                return fileMimeType.startsWith(m.replace("/*", ""));
            }
            return fileMimeType === m;
        });

        // Check extensions
        const extMatches = allowedExt.some((e) => fileName.endsWith(e));

        // If we have both MIME and ext rules, accept if either matches
        if (allowedMime.length > 0 && allowedExt.length > 0) {
            return mimeMatches || extMatches;
        }

        // If only MIME rules, check MIME
        if (allowedMime.length > 0) {
            return mimeMatches;
        }

        // If only ext rules, check ext
        return extMatches;
    };

    const runValidation = (candidate: File[]) => {
        // Check file types first
        const invalidTypeFile = candidate.find((f) => !isFileTypeAllowed(f));
        if (invalidTypeFile) {
            const { mime, ext } = getAllowedTypes();
            const allowedLabel = fileType
                ? Array.isArray(fileType)
                    ? fileType.map((t) => FILE_TYPES[t]?.label).join(", ")
                    : FILE_TYPES[fileType]?.label
                : `${mime.length > 0 ? mime.join(", ") : ""}${ext.length > 0 ? (mime.length > 0 ? ", " : "") + ext.join(", ") : ""}`;
            return `File type not allowed: ${invalidTypeFile.name}. Accepted: ${allowedLabel}`;
        }

        if (validate) {
            return validate(candidate);
        }
        if (maxFiles && candidate.length > maxFiles) {
            return `Maximum ${maxFiles} files allowed`;
        }
        if (maxSizeBytes) {
            const oversized = candidate.find((f) => f.size > maxSizeBytes);
            if (oversized) return `File ${oversized.name} exceeds size limit`;
        }
        return "";
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files ? Array.from(e.target.files) : [];
        const combined = multiple ? [...localFiles, ...selected] : selected;
        const valError = runValidation(combined);
        setError(valError);
        if (!valError) {
            setLocalFiles(combined);
            onChange(combined);
            if (formCtx && name) formCtx.setValue(name, combined);
        }
        // reset input value so same file can be selected again if removed
        e.currentTarget.value = "";
    };

    const removeAt = (index: number) => {
        const next = [...localFiles];
        next.splice(index, 1);
        const valError = runValidation(next);
        setError(valError);
        setLocalFiles(next);
        onChange(next);
        if (formCtx && name) formCtx.setValue(name, next);
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
        const droppedFiles = e.dataTransfer.files
            ? Array.from(e.dataTransfer.files)
            : [];
        const combined = multiple
            ? [...localFiles, ...droppedFiles]
            : droppedFiles;
        const valError = runValidation(combined);
        setError(valError);
        if (!valError) {
            setLocalFiles(combined);
            onChange(combined);
            if (formCtx && name) formCtx.setValue(name, combined);
        }
    };

    return (
        <div className={className} style={{ width: "100%" }}>
            {label && (
                <label
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontSize: "0.95rem",
                        fontWeight: 600,
                        color: "#1f2937",
                        marginBottom: "0.75rem",
                    }}
                >
                    {icon && (
                        <span
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                width: "20px",
                                height: "20px",
                                flexShrink: 0,
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

            <div
                style={{
                    border: isDragging
                        ? "2px solid #3b82f6"
                        : "2px dashed #d1d5db",
                    borderRadius: "12px",
                    padding: "24px",
                    marginBottom: "12px",
                    cursor: "pointer",
                    textAlign: "center",
                    transition: "all 0.2s ease",
                    backgroundColor: isDragging
                        ? "rgba(59, 130, 246, 0.05)"
                        : "#f9fafb",
                }}
                onClick={() => fileInputRef.current?.click()}
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
                        e.currentTarget.style.backgroundColor = "#f9fafb";
                    }
                }}
            >
                <div
                    style={{
                        display: "flex",
                        gap: "16px",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    <div>
                        <div
                            style={{
                                fontSize: "36px",
                                marginBottom: "8px",
                                lineHeight: 1,
                            }}
                        >
                            📁
                        </div>
                    </div>
                    <div>
                        <p
                            style={{
                                margin: "0 0 4px 0",
                                fontSize: "0.95rem",
                                fontWeight: 600,
                                color: "#1f2937",
                            }}
                        >
                            {multiple
                                ? "Drop files or click to select"
                                : "Click to select file"}
                        </p>
                        <small
                            style={{
                                display: "block",
                                color: "#6b7280",
                                fontSize: "0.85rem",
                            }}
                        >
                            {fileType
                                ? Array.isArray(fileType)
                                    ? `Accepted: ${fileType.map((t) => FILE_TYPES[t]?.label).join(", ")}`
                                    : `Accepted: ${FILE_TYPES[fileType]?.label}`
                                : accept
                                  ? `Accepted: ${accept}`
                                  : ""}
                            {(fileType || accept) && maxSizeBytes ? " • " : ""}
                            {maxSizeBytes
                                ? `Max ${(maxSizeBytes / 1024 / 1024).toFixed(1)}MB`
                                : ""}
                            {(fileType || accept || maxSizeBytes) && maxFiles
                                ? " • "
                                : ""}
                            {maxFiles &&
                                `Max ${maxFiles} file${maxFiles > 1 ? "s" : ""}`}
                        </small>
                    </div>
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={getAcceptString()}
                    multiple={multiple}
                    onChange={handleInputChange}
                    style={{ display: "none" }}
                />
            </div>

            {error && (
                <div
                    style={{
                        color: "#ef4444",
                        fontSize: "0.85rem",
                        marginBottom: "12px",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: "8px 12px",
                        backgroundColor: "#fef2f2",
                        borderRadius: "8px",
                        border: "1px solid #fecaca",
                    }}
                >
                    <span>⚠️</span>
                    {error}
                </div>
            )}

            {localFiles.length > 0 && (
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fill, minmax(140px, 1fr))",
                        gap: "12px",
                    }}
                >
                    {localFiles.map((f, i) => (
                        <div
                            key={i}
                            style={{
                                borderRadius: "12px",
                                overflow: "hidden",
                                backgroundColor: "#f9fafb",
                                border: "1px solid #e5e7eb",
                                transition: "all 0.2s ease",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.boxShadow =
                                    "0 4px 12px rgba(0, 0, 0, 0.1)";
                                e.currentTarget.style.transform =
                                    "translateY(-2px)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.boxShadow = "none";
                                e.currentTarget.style.transform =
                                    "translateY(0)";
                            }}
                        >
                            {preview && f.type.startsWith("image/") ? (
                                <img
                                    src={previews[i]}
                                    alt={f.name}
                                    style={{
                                        width: "100%",
                                        height: "120px",
                                        objectFit: "cover",
                                    }}
                                />
                            ) : (
                                <div
                                    style={{
                                        height: "120px",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        padding: "12px",
                                        textAlign: "center",
                                    }}
                                >
                                    <div
                                        style={{
                                            fontSize: "28px",
                                            lineHeight: 1,
                                        }}
                                    >
                                        📄
                                    </div>
                                </div>
                            )}
                            <div style={{ padding: "12px" }}>
                                <p
                                    style={{
                                        margin: "0 0 8px 0",
                                        fontSize: "0.85rem",
                                        fontWeight: 600,
                                        color: "#1f2937",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                    }}
                                    title={f.name}
                                >
                                    {f.name}
                                </p>
                                <small
                                    style={{
                                        color: "#6b7280",
                                        fontSize: "0.75rem",
                                    }}
                                >
                                    {(f.size / 1024 / 1024).toFixed(2)}MB
                                </small>
                                <div
                                    style={{
                                        display: "flex",
                                        gap: "6px",
                                        marginTop: "8px",
                                    }}
                                >
                                    <button
                                        onClick={() => removeAt(i)}
                                        style={{
                                            flex: 1,
                                            padding: "6px 8px",
                                            backgroundColor: "#ef4444",
                                            color: "white",
                                            border: "none",
                                            borderRadius: "6px",
                                            fontSize: "0.75rem",
                                            fontWeight: 600,
                                            cursor: "pointer",
                                            transition: "all 0.2s ease",
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.backgroundColor =
                                                "#dc2626";
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.backgroundColor =
                                                "#ef4444";
                                        }}
                                    >
                                        Remove
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
