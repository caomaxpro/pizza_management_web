/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Upload, Check, X, Warning } from "@phosphor-icons/react";
import { ingredientAPI } from "../../services/ingredients";
import { useIngredientImportProgress } from "../../hooks/useIngredientImportProgress";
import { useIngredientStore } from "../../store/ingredientStore";
import { Button } from "@components/ui";
import { ProgressBar } from "@components/ui/ProgressBar";
import MessageCard from "@components/form/fields/MessageCard";
import styles from "./IngredientImportReview.module.scss";

interface ImportedItem {
    index: number;
    name: string;
    description?: string;
    type: string;
    sub_type?: string;
    price: number;
    image_url?: string;
    image_source_url?: string;
    piece_image_url?: string;
    piece_image_source_url?: string;
    errors?: string[];
}

export default function IngredientImportReview() {
    const navigate = useNavigate();
    const location = useLocation();
    const { fetchAllIngredients } = useIngredientStore();
    const [items, setItems] = useState<ImportedItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
    const [previewImage, setPreviewImage] = useState<string | null>(null);
    const [importId, setImportId] = useState<string | null>(null);
    const [importProgress, setImportProgress] = useState<{
        current: number;
        total: number;
        percentage: number;
    } | null>(null);
    const [importCompleted, setImportCompleted] = useState(false);
    const [importStats, setImportStats] = useState<{
        created: number;
        errors: number;
    } | null>(null);
    const [completedItems, setCompletedItems] = useState<any[]>([]);
    // Unified progress tracking
    const [totalItems, setTotalItems] = useState(0);
    const [totalImages, setTotalImages] = useState(0);
    const [isImporting, setIsImporting] = useState(false);
    const [importStatus, setImportStatus] = useState<
        "items" | "images" | "complete" | "cancelling"
    >("items");
    const [cancelInProgress, setCancelInProgress] = useState(false);
    const [lastEscTime, setLastEscTime] = useState(0);
    const [cancelProgress, setCancelProgress] = useState<{
        step: number;
        total_steps: number;
        percentage: number;
        action: string;
    } | null>(null);

    // Get imported data from navigation state
    const importedData = (location.state as any)?.importedData;

    // Convert relative paths to absolute backend URLs
    const convertImageUrl = (
        imageUrl: string | undefined,
    ): string | undefined => {
        if (!imageUrl) return undefined;
        // If already absolute URL (http/https), return as-is
        if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
            console.log("[Image URL] Already absolute:", imageUrl);
            return imageUrl;
        }

        const apiBase =
            import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";
        const backendBase = apiBase.replace("/api", ""); // Remove /api suffix

        // If path starts with assets/, serve from assets folder
        if (imageUrl.startsWith("assets/")) {
            const fullUrl = `${backendBase}/${imageUrl}`;
            console.log("[Image URL] Asset path:", imageUrl, "→", fullUrl);
            return fullUrl;
        }

        // Otherwise assume it's in media folder
        const fullUrl = `${backendBase}/media/${imageUrl}`;
        console.log("[Image URL] Media path:", imageUrl, "→", fullUrl);
        return fullUrl;
    };

    // Compute processed items using useMemo to avoid cascading renders
    const processedData = useMemo(() => {
        if (!importedData) return { items: [], selectedSet: new Set<number>() };

        // Extract items array if nested under 'items' property (from JSON {items: [...]})
        let itemsToProcess: any[];
        if (importedData.items && Array.isArray(importedData.items)) {
            itemsToProcess = importedData.items;
        } else if (Array.isArray(importedData)) {
            itemsToProcess = importedData;
        } else {
            itemsToProcess = [importedData];
        }

        const items: ImportedItem[] = itemsToProcess.map((item, idx) => {
            const errors: string[] = [];
            const validTypes = ["dough", "sauce", "cheese", "topping", "extra"];

            // [Logging] Trace image_source_url extraction
            console.log(`[JSON Parse] Item ${idx}:`, {
                name: item.name,
                image_url: item.image_url,
                image_source_url: item.image_source_url,
                piece_image_url: item.piece_image_url,
                piece_image_source_url: item.piece_image_source_url,
            });

            // Validation
            if (!item.name || typeof item.name !== "string")
                errors.push("Missing or invalid name");
            if (!item.type || typeof item.type !== "string")
                errors.push("Missing or invalid type");
            else if (!validTypes.includes(item.type))
                errors.push(
                    `Invalid type. Must be one of: ${validTypes.join(", ")}`,
                );
            if (
                item.price === undefined ||
                item.price === null ||
                typeof item.price !== "number"
            ) {
                errors.push("Missing or invalid price");
            }

            return {
                index: idx,
                name: item.name || "Unknown",
                description: item.description,
                type: item.type || "N/A",
                sub_type: item.sub_type,
                price: item.price || 0,
                image_url: convertImageUrl(item.image_url),
                image_source_url: item.image_url,
                piece_image_url: convertImageUrl(item.piece_image_url),
                piece_image_source_url: item.piece_image_url,
                errors: errors.length > 0 ? errors : undefined,
            };
        });

        // [Logging] Log all processed items with source URLs
        console.log(
            "[Processed Data] All items after mapping:",
            items.map((i) => ({
                name: i.name,
                image_source_url: i.image_source_url,
                piece_image_source_url: i.piece_image_source_url,
            })),
        );

        // Pre-select all valid items
        const selectedSet = new Set(
            items
                .filter((item) => !item.errors || item.errors.length === 0)
                .map((_, idx) => idx),
        );

        return { items, selectedSet };
    }, [importedData]);

    // Setup WebSocket listener for import progress
    useIngredientImportProgress({
        importId,
        onProgress: (data) => {
            console.log(
                "[Progress]",
                data.percentage,
                "%",
                data.completed_ingredient,
            );
            // Track total items as they're created
            const completedItems = data.current || 0;
            setTotalItems(data.total || 0);
            // Calculate unified progress: only items phase so far
            setImportProgress({
                current: completedItems,
                total: (data.total || 0) + (totalImages || 0),
                percentage:
                    totalImages > 0
                        ? Math.round(
                              (completedItems /
                                  ((data.total || 0) + totalImages)) *
                                  100,
                          )
                        : data.percentage || 0,
            });

            // Add completed ingredient to the list
            if (data.completed_ingredient) {
                setCompletedItems((prev) => [
                    ...prev,
                    data.completed_ingredient,
                ]);
            }
        },
        onComplete: (data) => {
            console.log("[Complete]", data);
            setImportCompleted(true);
            // Don't navigate yet, just change phase to wait for images
            const created = data.total_created || 0;
            setTotalItems(created);
            setImportStatus("images");
            setImportStats({
                created: created,
                errors: data.total_errors || 0,
            });
        },
        onError: (data) => {
            console.error("[Import Error]", data);
            setError(data.error || data.message || "Import failed");
            setIsLoading(false);
            setIsImporting(false);
        },
        onCancel: (data) => {
            console.log("[Import Cancelled]", data);
            setIsImporting(false);
            setCancelInProgress(false);
            setImportProgress(null);
            setCancelProgress(null);
            setImportStatus("complete");

            // Navigate back to ingredients page after short delay
            setTimeout(() => {
                navigate("/ingredients", {
                    state: {
                        successMessage: `✓ Cancelled. Deleted ${totalItems} ingredients and their images from storage.`,
                    },
                });
            }, 500);
        },
        onCancelProgress: (data) => {
            console.log("[Cancel Progress]", data);
            setCancelProgress({
                step: data.step || 0,
                total_steps: data.total_steps || 0,
                percentage: data.percentage || 0,
                action: data.action || "Cancelling...",
            });
        },
        onImageProgress: (data) => {
            console.log("[Image Progress]", data);
            // Track total images on first image_progress message
            if (totalImages === 0) {
                setTotalImages(data.total || 0);
            }
            const processed = data.processed || 0;
            // Calculate unified progress: items already done + current image progress
            const totalWork = totalItems + (data.total || 0);
            const completedWork = totalItems + processed;
            setImportProgress({
                current: completedWork,
                total: totalWork,
                percentage:
                    totalWork > 0
                        ? Math.round((completedWork / totalWork) * 100)
                        : 0,
            });
        },
        onImageBatchComplete: (data) => {
            console.log("[Image Batch Complete]", data);
            // 🔄 Refetch to refresh store with new image URLs
            fetchAllIngredients(true).then(() => {
                console.log("[Import] Store refreshed with images");
            });
            // All images done, now navigate
            setImportStatus("complete");
            setTimeout(() => {
                navigate("/ingredients", {
                    state: {
                        successMessage: `✅ Successfully imported ${importStats?.created || 0} ingredients with ${data.processed || 0} new images and ${data.cached || 0} cached images!`,
                    },
                });
            }, 1000);
        },
    });

    // Effect to set state and check navigation
    useEffect(() => {
        if (!importedData) {
            navigate("/ingredients");
            return;
        }

        // Set the processed data
        setItems(processedData.items);
        setSelectedItems(processedData.selectedSet);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [importedData, navigate]);

    // ESC keyboard listener for cancel
    useEffect(() => {
        if (!isImporting) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                event.preventDefault();
                const now = Date.now();
                const isDoubleEsc = now - lastEscTime < 300; // Double ESC within 300ms

                if (isDoubleEsc) {
                    // Force cancel without confirmation
                    console.log(
                        "[Keyboard] Double ESC detected - force cancel",
                    );
                    setCancelInProgress(true);
                    handleCancelImport(true);
                    setLastEscTime(0);
                } else {
                    // Show confirmation dialog
                    console.log("[Keyboard] ESC pressed - show cancel dialog");
                    setLastEscTime(now);
                    handleCancelImport(false);
                }
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isImporting, importId]);

    const handleSelectAll = () => {
        const validIndices = items
            .map((item, idx) =>
                !item.errors || item.errors.length === 0 ? idx : null,
            )
            .filter((idx): idx is number => idx !== null);

        if (selectedItems.size === validIndices.length) {
            setSelectedItems(new Set());
        } else {
            setSelectedItems(new Set(validIndices));
        }
    };

    const handleSelectItem = (index: number) => {
        const newSelected = new Set(selectedItems);
        if (newSelected.has(index)) {
            newSelected.delete(index);
        } else {
            newSelected.add(index);
        }
        setSelectedItems(newSelected);
    };

    const handleRemoveItem = (index: number) => {
        setItems((prev) => prev.filter((_, i) => i !== index));
        setSelectedItems((prev) => {
            const newSelected = new Set(prev);
            newSelected.delete(index);
            return newSelected;
        });
    };

    const handleCancelImport = async (forceCancel: boolean = false) => {
        // Show confirmation if not force cancel
        const shouldProceed =
            forceCancel ||
            confirm(
                `Cancel ${
                    importStatus === "cancelling"
                        ? "cancellation"
                        : importStatus
                } phase? All ${totalItems} created items will be deleted from the database along with ${totalImages} uploaded images. This cannot be undone.`,
            );

        if (!shouldProceed) {
            return;
        }

        try {
            setCancelInProgress(true);
            setImportStatus("cancelling");
            setCancelProgress(null);
            setError(null);

            if (importId) {
                console.log(
                    `[Cancel] Cancelling ${importStatus} phase for import_id=${importId}`,
                );
                await ingredientAPI.cancelImport(importId);
                console.log("✓ Cancel request sent to backend");
            }
        } catch (err) {
            console.error("Failed to cancel import:", err);
            setError("Failed to cancel import");
            setCancelInProgress(false);
            setImportStatus(importStatus === "items" ? "items" : "images");
        }
        // UI will be updated via onCancel callback from hook
    };

    const handleBulkImport = async () => {
        if (selectedItems.size === 0) {
            setError("Select at least one item to import");
            return;
        }

        try {
            setIsLoading(true);
            setIsImporting(true);
            setError(null);
            setImportCompleted(false);
            setImportProgress(null);
            setCompletedItems([]);

            // Get selected items (excluding those with errors)
            const itemsToImport = items
                .filter((_, idx) => selectedItems.has(idx))
                .map((item) => ({
                    name: item.name,
                    description: item.description,
                    type: item.type,
                    sub_type: item.sub_type,
                    price: item.price,
                    // Send raw paths from state (now properly populated from JSON)
                    ...(item.image_source_url && {
                        image_url: item.image_source_url,
                        image_source_url: item.image_source_url,
                    }),
                    // Piece images - only if they exist
                    ...(item.piece_image_source_url && {
                        piece_image_url: item.piece_image_source_url,
                        piece_image_source_url: item.piece_image_source_url,
                    }),
                }));

            // [FE Debug Logging]
            console.log("[FE Debug] Items from state before mapping:", items);
            console.log(
                "[FE Debug] Selected indices:",
                Array.from(selectedItems),
            );
            console.log(
                "[FE Debug] itemsToImport about to send:",
                itemsToImport,
            );
            if (itemsToImport.length > 0) {
                console.log("[FE Debug] First item details:", {
                    name: itemsToImport[0]?.name,
                    image_source_url: itemsToImport[0]?.image_source_url,
                    image_url: itemsToImport[0]?.image_url,
                    piece_image_source_url:
                        itemsToImport[0]?.piece_image_source_url,
                    piece_image_url: itemsToImport[0]?.piece_image_url,
                });
            }

            // Send to backend import_json endpoint
            const response = await ingredientAPI.importJson(itemsToImport);

            console.log(
                "[Import] Started with import_id:",
                response.data.import_id,
            );

            // Set import_id to trigger WebSocket connection for progress tracking
            setImportId(response.data.import_id);

            // Show initial progress bar (0%)
            setImportProgress({
                current: 0,
                total: itemsToImport.length,
                percentage: 0,
            });

            // Don't navigate immediately - wait for WebSocket completion notification
        } catch (err: any) {
            console.error("[Import] Error:", err);
            let errorMessage = "Failed to import ingredients";

            if (err.response?.data?.error) {
                errorMessage = err.response.data.error;
            } else if (err.message) {
                errorMessage = err.message;
            }

            setError(errorMessage);
            setIsLoading(false);
            setIsImporting(false);
        }
    };

    const validItemsCount = items.filter(
        (item) => !item.errors || item.errors.length === 0,
    ).length;
    const errorsCount = items.filter(
        (item) => item.errors && item.errors.length > 0,
    ).length;
    const validIndices = items
        .map((item, idx) =>
            !item.errors || item.errors.length === 0 ? idx : null,
        )
        .filter((idx): idx is number => idx !== null);

    // Show early loading only if no data yet (initial load)
    if (!importedData && isLoading) {
        return (
            <div className={styles.container}>
                <div style={{ marginTop: "3rem" }}>
                    <ProgressBar label="📥 Importing ingredients..." />
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Loading overlay to disable interaction during import/cancel */}
            {(isImporting || importStatus === "cancelling") && (
                <div>
                    <div
                        style={{
                            position: "fixed",
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: "rgba(0, 0, 0, 0.5)",
                            zIndex: 999,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <div
                            style={{
                                backgroundColor: "white",
                                padding: "2rem",
                                borderRadius: "0.5rem",
                                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                                textAlign: "center",
                                position: "relative",
                                maxWidth: "500px",
                            }}
                        >
                            {/* Header cancel button - only show during import, not during cancellation */}
                            {importStatus !== "cancelling" && (
                                <button
                                    onClick={() => handleCancelImport(false)}
                                    disabled={cancelInProgress}
                                    style={{
                                        position: "absolute",
                                        top: "1rem",
                                        right: "1rem",
                                        background: "none",
                                        border: "none",
                                        cursor: cancelInProgress
                                            ? "not-allowed"
                                            : "pointer",
                                        fontSize: "1.5rem",
                                        color: cancelInProgress
                                            ? "#ccc"
                                            : "#ef4444",
                                        padding: "0.25rem",
                                        lineHeight: "1",
                                        opacity: cancelInProgress ? 0.5 : 1,
                                        transition: "color 0.2s, opacity 0.2s",
                                    }}
                                    title="Cancel import (or press ESC)"
                                >
                                    ✕
                                </button>
                            )}

                            <h2
                                style={{
                                    margin: "0 0 0.5rem 0",
                                    color: "#1f2937",
                                }}
                            >
                                {importStatus === "cancelling"
                                    ? "⏸️ Cancelling Import..."
                                    : "⏳ Processing Import..."}
                            </h2>

                            {/* Phase/Cancel indicator */}
                            <div
                                style={{
                                    fontSize: "0.875rem",
                                    color: "#6b7280",
                                    marginBottom: "1rem",
                                    fontWeight: "500",
                                }}
                            >
                                {importStatus === "cancelling" ? (
                                    cancelProgress ? (
                                        <>
                                            <div>
                                                Step {cancelProgress.step}/
                                                {cancelProgress.total_steps}:{" "}
                                                {cancelProgress.action}
                                            </div>
                                            <div
                                                style={{
                                                    marginTop: "0.5rem",
                                                    fontSize: "0.75rem",
                                                }}
                                            >
                                                {cancelProgress.percentage}%
                                            </div>
                                        </>
                                    ) : (
                                        "Starting cancellation..."
                                    )
                                ) : importStatus === "items" ? (
                                    "📦 [Phase 1/2] Creating Items"
                                ) : importStatus === "images" ? (
                                    "🖼️ [Phase 2/2] Uploading Images"
                                ) : (
                                    "✅ Completing"
                                )}
                            </div>

                            {importStatus === "cancelling" && cancelProgress ? (
                                <ProgressBar
                                    label={`Cancelling...`}
                                    progress={cancelProgress.percentage}
                                    showPercentage={true}
                                />
                            ) : importProgress ? (
                                <ProgressBar
                                    label={`Progress: ${importProgress.current} / ${importProgress.total} items`}
                                    progress={importProgress.percentage}
                                    showPercentage={true}
                                    showCancelButton={
                                        !cancelInProgress &&
                                        importStatus !== "complete" &&
                                        importStatus !== "cancelling"
                                    }
                                    onCancel={() => handleCancelImport(false)}
                                />
                            ) : (
                                <p style={{ color: "#6b7280" }}>
                                    {importStatus === "cancelling"
                                        ? "Processing cancellation..."
                                        : "Initializing import..."}
                                </p>
                            )}

                            {/* Keyboard hint */}
                            {importStatus !== "cancelling" && (
                                <div
                                    style={{
                                        fontSize: "0.75rem",
                                        color: "#9ca3af",
                                        marginTop: "1rem",
                                        fontStyle: "italic",
                                    }}
                                >
                                    Press ESC to cancel (double ESC to force)
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <div className={styles.header}>
                <h1>
                    <Upload size={28} style={{ marginRight: 8 }} />
                    Review Imported Items
                </h1>
                <p className={styles.subtitle}>
                    Review and confirm the items before importing to the system
                </p>
            </div>

            {/* Stats */}
            <div className={styles.stats}>
                <div className={styles.statCard}>
                    <span className={styles.statLabel}>Total Items</span>
                    <span className={styles.statValue}>{items.length}</span>
                </div>
                <div className={styles.statCard}>
                    <span className={styles.statLabel}>Valid</span>
                    <span className={`${styles.statValue} ${styles.valid}`}>
                        {validItemsCount}
                    </span>
                </div>
                {errorsCount > 0 && (
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Errors</span>
                        <span className={`${styles.statValue} ${styles.error}`}>
                            {errorsCount}
                        </span>
                    </div>
                )}
                <div className={styles.statCard}>
                    <span className={styles.statLabel}>Selected</span>
                    <span className={styles.statValue}>
                        {selectedItems.size}
                    </span>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <MessageCard
                    message={error}
                    variant="error"
                    dismissible={true}
                    onDismiss={() => setError(null)}
                    marginBottom="1.5rem"
                />
            )}

            {/* Completed Items List */}
            {completedItems.length > 0 && (
                <div
                    className={styles.completedSection}
                    style={{
                        marginBottom: "1.5rem",
                        padding: "1rem",
                        backgroundColor: "#f0f9ff",
                        border: "1px solid #0ea5e9",
                        borderRadius: "0.5rem",
                    }}
                >
                    <h3
                        style={{
                            marginBottom: "1rem",
                            color: "#0284c7",
                            margin: "0 0 1rem 0",
                        }}
                    >
                        ✅ Completed Items ({completedItems.length})
                    </h3>
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "repeat(auto-fill, minmax(200px, 1fr))",
                            gap: "0.75rem",
                            maxHeight: "300px",
                            overflowY: "auto",
                            padding: "0.5rem",
                        }}
                    >
                        {completedItems.map((item, idx) => (
                            <div
                                key={`${item.id}-${idx}`}
                                style={{
                                    padding: "0.75rem",
                                    backgroundColor: "white",
                                    border: "1px solid #06b6d4",
                                    borderRadius: "0.375rem",
                                    fontSize: "0.875rem",
                                }}
                            >
                                <div
                                    style={{
                                        fontWeight: "500",
                                        color: "#0369a1",
                                    }}
                                >
                                    {item.name}
                                </div>
                                <div
                                    style={{
                                        fontSize: "0.75rem",
                                        color: "#666",
                                        marginTop: "0.25rem",
                                    }}
                                >
                                    ${item.price.toFixed(2)} • {item.type}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Import Completed Message */}
            {importCompleted && importStats && (
                <MessageCard
                    message={`✅ Import completed! Created: ${importStats.created}, Errors: ${importStats.errors}`}
                    variant="success"
                    marginBottom="1.5rem"
                />
            )}

            {/* Items Table */}
            <div className={styles.tableWrapper}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th className={styles.checkboxCol}>
                                <input
                                    type="checkbox"
                                    checked={
                                        validIndices.length > 0 &&
                                        selectedItems.size ===
                                            validIndices.length
                                    }
                                    onChange={handleSelectAll}
                                />
                            </th>
                            <th className={styles.imageCol}>Image</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Sub-type</th>
                            <th>Price</th>
                            <th>Status</th>
                            <th className={styles.actionCol}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.map((item) => (
                            <tr
                                key={item.index}
                                className={item.errors ? styles.rowError : ""}
                            >
                                <td className={styles.checkboxCol}>
                                    <input
                                        type="checkbox"
                                        checked={selectedItems.has(item.index)}
                                        onChange={() =>
                                            handleSelectItem(item.index)
                                        }
                                        disabled={
                                            item.errors &&
                                            item.errors.length > 0
                                        }
                                    />
                                </td>
                                <td className={styles.imageCol}>
                                    {item.image_url ? (
                                        <img
                                            src={item.image_url}
                                            alt={item.name}
                                            className={styles.thumbnail}
                                            onClick={() =>
                                                setPreviewImage(
                                                    item.image_url || null,
                                                )
                                            }
                                        />
                                    ) : (
                                        <div className={styles.noImage}>—</div>
                                    )}
                                </td>
                                <td>
                                    <div className={styles.nameCell}>
                                        <span className={styles.name}>
                                            {item.name}
                                        </span>
                                        {item.description && (
                                            <span
                                                className={styles.description}
                                            >
                                                {item.description}
                                            </span>
                                        )}
                                    </div>
                                </td>
                                <td>
                                    <span className={styles.badge}>
                                        {item.type}
                                    </span>
                                </td>
                                <td>
                                    <span className={styles.badge}>
                                        {item.sub_type || "—"}
                                    </span>
                                </td>
                                <td>
                                    <span className={styles.price}>
                                        ${item.price.toFixed(2)}
                                    </span>
                                </td>
                                <td>
                                    {item.errors && item.errors.length > 0 ? (
                                        <div className={styles.errorStatus}>
                                            <Warning size={16} />
                                            <span>{item.errors[0]}</span>
                                        </div>
                                    ) : (
                                        <div className={styles.validStatus}>
                                            <Check size={16} />
                                            Valid
                                        </div>
                                    )}
                                </td>
                                <td className={styles.actionCol}>
                                    <button
                                        className={styles.removeBtn}
                                        onClick={() =>
                                            handleRemoveItem(item.index)
                                        }
                                        title="Remove item"
                                    >
                                        <X size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Actions */}
            <div className={styles.actions}>
                <Button
                    variant="outline"
                    size="md"
                    onClick={() => navigate("/ingredients")}
                >
                    Cancel
                </Button>
                <Button
                    variant="primary"
                    size="md"
                    onClick={handleBulkImport}
                    disabled={
                        selectedItems.size === 0 ||
                        validItemsCount === 0 ||
                        isLoading
                    }
                >
                    {isLoading ? "Importing..." : "Import"}{" "}
                    {selectedItems.size > 0 ? `(${selectedItems.size})` : ""}
                </Button>
            </div>

            {/* Image Preview Modal */}
            {previewImage && (
                <>
                    <div
                        className={styles.modalOverlay}
                        onClick={() => setPreviewImage(null)}
                    />
                    <div className={styles.previewModal}>
                        <button
                            className={styles.closeBtn}
                            onClick={() => setPreviewImage(null)}
                        >
                            <X size={24} />
                        </button>
                        <img
                            src={previewImage}
                            alt="Preview"
                            className={styles.previewImage}
                        />
                    </div>
                </>
            )}
        </div>
    );
}
