/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useRef } from "react";

export interface ImportProgressMessage {
    type:
        | "import_progress"
        | "import_completed"
        | "import_error"
        | "import_subscription_confirmed"
        | "import_cancelled"
        | "import_cancel_progress"
        | "image_progress"
        | "image_batch_completed"
        | "ping"
        | "pong";
    current?: number;
    total?: number;
    total_steps?: number;
    step?: number;
    percentage?: number;
    total_created?: number;
    total_errors?: number;
    processed?: number;
    cached?: number;
    failed?: number;
    action?: string;
    message?: string;
    error?: string;
    import_id?: string;
    completed_ingredient?: {
        id?: number;
        name?: string;
        price?: number;
        type?: string;
        image_url?: string;
        [key: string]: any;
    };
}

interface UseIngredientImportProgressOptions {
    importId: string | null;
    onProgress?: (data: ImportProgressMessage) => void;
    onComplete?: (data: ImportProgressMessage) => void;
    onCancel?: (data: ImportProgressMessage) => void;
    onCancelProgress?: (data: ImportProgressMessage) => void;
    onError?: (data: ImportProgressMessage) => void;
    onImageProgress?: (data: ImportProgressMessage) => void;
    onImageBatchComplete?: (data: ImportProgressMessage) => void;
}

/**
 * Hook for tracking ingredient import progress via WebSocket
 * Connects to /ws/ingredients/import/{import_id}/ endpoint
 */
export const useIngredientImportProgress = ({
    importId,
    onProgress,
    onComplete,
    onCancel,
    onCancelProgress,
    onError,
    onImageProgress,
    onImageBatchComplete,
}: UseIngredientImportProgressOptions) => {
    const [isConnected, setIsConnected] = useState(false);
    const [progress, setProgress] = useState<ImportProgressMessage | null>(
        null,
    );

    // Use refs to avoid triggering reconnection when callbacks change
    const onProgressRef = useRef(onProgress);
    const onCompleteRef = useRef(onComplete);
    const onCancelRef = useRef(onCancel);
    const onCancelProgressRef = useRef(onCancelProgress);
    const onErrorRef = useRef(onError);
    const onImageProgressRef = useRef(onImageProgress);
    const onImageBatchCompleteRef = useRef(onImageBatchComplete);

    // Update refs whenever callbacks change (but don't trigger reconnection)
    useEffect(() => {
        onProgressRef.current = onProgress;
        onCompleteRef.current = onComplete;
        onCancelRef.current = onCancel;
        onCancelProgressRef.current = onCancelProgress;
        onErrorRef.current = onError;
        onImageProgressRef.current = onImageProgress;
        onImageBatchCompleteRef.current = onImageBatchComplete;
    }, [
        onProgress,
        onComplete,
        onCancel,
        onCancelProgress,
        onError,
        onImageProgress,
        onImageBatchComplete,
    ]);

    useEffect(() => {
        if (!importId) {
            console.log(
                "Import ID not provided, skipping WebSocket connection",
            );
            return;
        }

        let isMounted = true;
        let ws: WebSocket | null = null;
        let heartbeatInterval: ReturnType<typeof setInterval> | null = null;

        const startHeartbeat = () => {
            // Send ping every 5 seconds to keep connection alive during async image processing
            heartbeatInterval = setInterval(() => {
                if (ws && ws.readyState === WebSocket.OPEN && isMounted) {
                    ws.send(JSON.stringify({ type: "ping" }));
                    console.log("💓 Heartbeat sent - keeping connection alive");
                }
            }, 5000);
        };

        const stopHeartbeat = () => {
            if (heartbeatInterval) {
                clearInterval(heartbeatInterval);
                heartbeatInterval = null;
            }
        };

        const connectWebSocket = () => {
            if (!isMounted) return;

            try {
                // Determine protocol based on current page protocol
                const protocol =
                    window.location.protocol === "https:" ? "wss:" : "ws:";
                const host = import.meta.env.DEV
                    ? `${window.location.hostname}:8000`
                    : window.location.host;
                const url = `${protocol}//${host}/ws/ingredients/import/${importId}/`;

                console.log(`🔗 Connecting to import progress: ${url}`);
                ws = new WebSocket(url);

                ws.onopen = () => {
                    if (!isMounted) return;
                    console.log("✅ Import progress WebSocket connected");
                    setIsConnected(true);

                    // Send subscription message
                    ws!.send(JSON.stringify({ type: "subscribe" }));

                    // Start heartbeat to prevent idle timeout during async image processing
                    startHeartbeat();
                    console.log(
                        "💓 Starting heartbeat to maintain connection during image processing",
                    );
                };

                ws.onmessage = (event) => {
                    if (!isMounted) return;
                    try {
                        const data: ImportProgressMessage = JSON.parse(
                            event.data,
                        );
                        console.log("📊 Import progress update:", data);

                        setProgress(data);

                        // Handle different message types using switch for clarity
                        switch (data.type) {
                            case "import_progress":
                                onProgressRef.current?.(data);
                                break;
                            case "import_completed":
                                console.log("✓ Import completed!");
                                onCompleteRef.current?.(data);
                                break;
                            case "import_cancelled":
                                console.log(
                                    "🛑 Import cancelled:",
                                    data.message,
                                );
                                onCancelRef.current?.(data);
                                break;
                            case "import_cancel_progress":
                                console.log(
                                    `⏸️ Cancel progress ${data.step}/${data.total_steps}: ${data.action}`,
                                );
                                onCancelProgressRef.current?.(data);
                                break;
                            case "import_error":
                                console.error("✗ Import error:", data.error);
                                onErrorRef.current?.(data);
                                break;
                            case "image_progress":
                                console.log("🖼️ Image progress:", {
                                    processed: data.processed,
                                    total: data.total,
                                    percentage: data.percentage,
                                });
                                onImageProgressRef.current?.(data);
                                break;
                            case "image_batch_completed":
                                console.log("🖼️ Image batch completed:", {
                                    processed: data.processed,
                                    cached: data.cached,
                                    failed: data.failed,
                                });
                                stopHeartbeat();
                                // Call image batch complete callback
                                onImageBatchCompleteRef.current?.(data);
                                break;
                            case "import_subscription_confirmed":
                                // subscription acknowledgement, no-op by default
                                break;
                            case "ping":
                            case "pong":
                                // Heartbeat acknowledgement - no action needed
                                break;
                            default:
                                console.warn(
                                    "Unhandled import progress message type:",
                                    data.type,
                                );
                        }
                    } catch (error) {
                        console.error(
                            "Failed to parse import progress message:",
                            error,
                        );
                    }
                };

                ws.onerror = (error) => {
                    if (!isMounted) return;
                    console.error("❌ Import progress WebSocket error:", error);
                };

                ws.onclose = () => {
                    if (!isMounted) return;
                    console.log("📭 Import progress WebSocket closed");
                    setIsConnected(false);
                };
            } catch (error) {
                if (!isMounted) return;
                console.error("Failed to create WebSocket:", error);
            }
        };

        connectWebSocket();

        return () => {
            isMounted = false;
            if (ws) {
                ws.close();
                ws = null;
            }
        };
    }, [importId]); // Only importId - callbacks handled via refs

    return { isConnected, progress };
};
