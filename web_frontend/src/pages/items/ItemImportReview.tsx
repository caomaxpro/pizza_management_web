/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Upload, Check, X, Warning } from "@phosphor-icons/react";
import itemAPI from "../../services/item";
import { useItemImportProgress } from "../../hooks/useItemImportProgress";
import { useItemStore } from "../../store/itemStore";
import { Button } from "@components/ui";
import { ProgressBar } from "@components/ui/ProgressBar";
import MessageCard from "@components/form/fields/MessageCard";
import styles from "./ItemImportReview.module.scss";

interface ImportedItem {
    index: number;
    name: string;
    description?: string;
    price: number;
    image_url?: string;
    image_source_url?: string;
    type?: string;
    sub_type?: string;
    errors?: string[];
}

export default function ItemImportReview() {
    const navigate = useNavigate();
    const location = useLocation();
    const { fetchAllItems } = useItemStore();
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
    const [importStats, setImportStats] = useState<{
        created: number;
        errors: number;
    } | null>(null);
    // Unified progress tracking
    const [totalItems, setTotalItems] = useState(0);
    const [totalImages, setTotalImages] = useState(0);
    const [isImporting, setIsImporting] = useState(false);
    const [importStatus, setImportStatus] = useState<
        "items" | "images" | "complete" | "cancelling"
    >("items");
    const [cancelInProgress, setCancelInProgress] = useState(false);
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

            // [Logging] Trace image_source_url extraction
            console.log(`[JSON Parse] Item ${idx}:`, {
                name: item.name,
                raw_image_url: item.image_url,
                raw_image_source_url: item.image_source_url,
            });

            // Validation
            if (!item.name || typeof item.name !== "string")
                errors.push("Missing or invalid name");
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
                price: item.price || 0,
                type: item.type,
                sub_type: item.sub_type,
                image_url: convertImageUrl(item.image_url),
                image_source_url: item.image_url,
                errors: errors.length > 0 ? errors : undefined,
            };
        });

        // [Logging] Log all processed items with source URLs
        console.log(
            "[Processed Data] All items after mapping:",
            items.map((i) => ({
                name: i.name,
                image_source_url: i.image_source_url,
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
    useItemImportProgress({
        importId,
        onProgress: (data) => {
            console.log(
                "[Progress]",
                data.percentage,
                "%",
                data.completed_item,
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
        },
        onComplete: (data) => {
            console.log("[Complete]", data);
            // Don't navigate yet, just change phase to wait for images
            const created = data.total_created || 0;
            setTotalItems(created);
            setImportStats({
                created: created,
                errors: data.total_errors || 0,
            });
            setImportStatus("images");
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

            // Navigate back to items page after short delay
            setTimeout(() => {
                navigate("/items", {
                    state: {
                        successMessage: `✓ Cancelled. Deleted ${totalItems} items and their images from storage.`,
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
            fetchAllItems(true).then(() => {
                console.log("[Import] Store refreshed with images");
            });
            // All images done, now navigate
            setImportStatus("complete");
            setTimeout(() => {
                navigate("/items", {
                    state: {
                        successMessage: `✅ Successfully imported ${importStats?.created || 0} items with ${data.processed || 0} new images and ${data.cached || 0} cached images!`,
                    },
                });
            }, 1000);
        },
    });

    // Effect to set state and check navigation
    useEffect(() => {
        if (!importedData) {
            navigate("/items");
            return;
        }

        // Set the processed data
        setItems(processedData.items);
        setSelectedItems(processedData.selectedSet);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [importedData, navigate]);

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
                await itemAPI.cancelImport(importId);
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
            setImportProgress(null);
            // completed items list removed — we rely on importProgress/importStats now

            // Get selected items (excluding those with errors)
            const itemsToImport = items
                .filter((_, idx) => selectedItems.has(idx))
                .map((item) => ({
                    name: item.name,
                    description: item.description,
                    price: item.price,
                    type: item.type,
                    sub_type: item.sub_type,
                    // Send raw paths from state (now properly populated from JSON)
                    ...(item.image_source_url && {
                        image_url: item.image_source_url,
                        image_source_url: item.image_source_url,
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
                });
            }

            // Send to backend import_json endpoint
            const response = await itemAPI.importJson(itemsToImport);

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
            let errorMessage = "Failed to import items";

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
                    <ProgressBar label="📥 Importing items..." />
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Loading/Cancellation overlay to disable interaction during import */}
            {(isImporting || importStatus === "cancelling") && (
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
                        }}
                    >
                        {importStatus === "cancelling" ? (
                            <>
                                <h2
                                    style={{
                                        margin: "0 0 1rem 0",
                                        color: "#1f2937",
                                    }}
                                >
                                    ⏸️ Cancelling Import...
                                </h2>
                                {cancelProgress && (
                                    <div>
                                        <p
                                            style={{
                                                margin: "0.5rem 0",
                                                color: "#374151",
                                            }}
                                        >
                                            Step {cancelProgress.step}/
                                            {cancelProgress.total_steps}:{" "}
                                            {cancelProgress.action}
                                        </p>
                                        <ProgressBar
                                            label={`${cancelProgress.percentage}%`}
                                            progress={cancelProgress.percentage}
                                            showPercentage={true}
                                            showCancelButton={false}
                                        />
                                    </div>
                                )}
                                {!cancelProgress && (
                                    <p style={{ color: "#6b7280" }}>
                                        Initializing cancellation...
                                    </p>
                                )}
                            </>
                        ) : (
                            <>
                                <h2
                                    style={{
                                        margin: "0 0 1rem 0",
                                        color: "#1f2937",
                                    }}
                                >
                                    ⏳ Processing Import...
                                </h2>
                                {importProgress && (
                                    <ProgressBar
                                        label={`Progress: ${importProgress.current} / ${importProgress.total} items`}
                                        progress={importProgress.percentage}
                                        showPercentage={true}
                                        showCancelButton={
                                            importStatus !== "complete"
                                        }
                                        onCancel={
                                            importStatus !== "complete"
                                                ? handleCancelImport
                                                : undefined
                                        }
                                    />
                                )}
                                {!importProgress && (
                                    <p style={{ color: "#6b7280" }}>
                                        Initializing import...
                                    </p>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Header */}
            <div className={styles.header}>
                <h1>Review Items for Import</h1>
                <p>
                    Review the items before importing. You can select/deselect
                    items individually or use the select all button.
                </p>
            </div>

            {/* Error Message */}
            {error && (
                <MessageCard
                    variant="error"
                    message={error}
                    onDismiss={() => setError(null)}
                />
            )}

            {/* Summary Stats */}
            {items.length > 0 && (
                <div className={styles.summary}>
                    <div className={styles.stats}>
                        <div>
                            <strong>Total:</strong> {items.length} items
                        </div>
                        <div>
                            <strong>Valid:</strong> {validItemsCount} items
                            <Check color="#4caf50" weight="bold" />
                        </div>
                        {errorsCount > 0 && (
                            <div>
                                <strong>Errors:</strong> {errorsCount} items
                                <Warning color="#ff9800" weight="bold" />
                            </div>
                        )}
                        <div>
                            <strong>Selected:</strong> {selectedItems.size}{" "}
                            items
                        </div>
                    </div>

                    <Button
                        variant={
                            selectedItems.size === validIndices.length
                                ? "outline"
                                : "secondary"
                        }
                        size="sm"
                        onClick={handleSelectAll}
                    >
                        {selectedItems.size === validIndices.length
                            ? "Deselect All"
                            : "Select All Valid"}
                    </Button>
                </div>
            )}

            {/* Items List */}
            {items.length > 0 ? (
                <div className={styles.itemsList}>
                    {items.map((item, idx) => {
                        const hasErrors = item.errors && item.errors.length > 0;
                        const isSelected = selectedItems.has(idx);

                        return (
                            <div
                                key={idx}
                                className={`${styles.itemCard} ${
                                    hasErrors ? styles.itemCardError : ""
                                }`}
                            >
                                <div className={styles.checkbox}>
                                    {!hasErrors && (
                                        <input
                                            type="checkbox"
                                            checked={isSelected}
                                            onChange={() =>
                                                handleSelectItem(idx)
                                            }
                                        />
                                    )}
                                </div>

                                <div className={styles.content}>
                                    {item.image_url && (
                                        <img
                                            src={item.image_url}
                                            alt={item.name}
                                            className={styles.itemImage}
                                            onClick={() => {
                                                if (item.image_url) {
                                                    setPreviewImage(
                                                        item.image_url,
                                                    );
                                                }
                                            }}
                                        />
                                    )}

                                    <div className={styles.itemInfo}>
                                        <h3>{item.name}</h3>
                                        {item.description && (
                                            <p className={styles.description}>
                                                {item.description}
                                            </p>
                                        )}
                                        <div className={styles.meta}>
                                            <span className={styles.badge}>
                                                {item.type}
                                            </span>
                                            <span className={styles.price}>
                                                ${item.price.toFixed(2)}
                                            </span>
                                        </div>

                                        {item.type && (
                                            <div
                                                style={{
                                                    fontSize: "12px",
                                                    color: "#666",
                                                }}
                                            >
                                                Type: {item.type}
                                                {item.sub_type &&
                                                    ` (${item.sub_type})`}
                                            </div>
                                        )}

                                        {hasErrors && item.errors && (
                                            <div className={styles.errors}>
                                                <X color="#d32f2f" />
                                                {item.errors.map((error, i) => (
                                                    <div key={i}>{error}</div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className={styles.actions}>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleRemoveItem(idx)}
                                    >
                                        Remove
                                    </Button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <MessageCard
                    variant="info"
                    message="No items to import. Please load a JSON file first."
                />
            )}

            {/* Action Buttons */}
            <div className={styles.actions}>
                <Button
                    variant="outline"
                    size="md"
                    onClick={() => navigate("/items")}
                >
                    Cancel
                </Button>
                <Button
                    variant="primary"
                    size="md"
                    disabled={
                        selectedItems.size === 0 || isLoading || isImporting
                    }
                    onClick={handleBulkImport}
                >
                    {isLoading || isImporting ? (
                        <>
                            <Upload /> Importing...
                        </>
                    ) : (
                        <>
                            <Upload /> Import {selectedItems.size} Items
                        </>
                    )}
                </Button>
            </div>

            {/* Image Preview Modal */}
            {previewImage && (
                <div
                    className={styles.imagePreview}
                    onClick={() => setPreviewImage(null)}
                >
                    <img src={previewImage} alt="Preview" />
                </div>
            )}
        </div>
    );
}
