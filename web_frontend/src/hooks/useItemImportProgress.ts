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
    percentage?: number;
    total_created?: number;
    total_errors?: number;
    processed?: number;
    cached?: number;
    failed?: number;
    message?: string;
    error?: string;
    import_id?: string;
    step?: number;
    total_steps?: number;
    action?: string;
    completed_item?: {
        id?: number;
        name?: string;
        price?: number;
        category?: string;
        image_url?: string;
        [key: string]: any;
    };
}

interface UseItemImportProgressOptions {
    importId: string | null;
    onProgress?: (data: ImportProgressMessage) => void;
    onComplete?: (data: ImportProgressMessage) => void;
    onCancel?: (data: ImportProgressMessage) => void;
    onError?: (data: ImportProgressMessage) => void;
    onCancelProgress?: (data: ImportProgressMessage) => void;
    onImageProgress?: (data: ImportProgressMessage) => void;
    onImageBatchComplete?: (data: ImportProgressMessage) => void;
}

/**
 * Hook for tracking item import progress via WebSocket
 * Connects to /ws/items/import/{import_id}/ endpoint
 */
export const useItemImportProgress = ({
    importId,
    onProgress,
    onComplete,
    onCancel,
    onError,
    onCancelProgress,
    onImageProgress,
    onImageBatchComplete,
}: UseItemImportProgressOptions) => {
    const [isConnected, setIsConnected] = useState(false);
    const [progress, setProgress] = useState<ImportProgressMessage | null>(
        null,
    );

    // Use refs to avoid triggering reconnection when callbacks change
    const onProgressRef = useRef(onProgress);
    const onCompleteRef = useRef(onComplete);
    const onCancelRef = useRef(onCancel);
    const onErrorRef = useRef(onError);
    const onCancelProgressRef = useRef(onCancelProgress);
    const onImageProgressRef = useRef(onImageProgress);
    const onImageBatchCompleteRef = useRef(onImageBatchComplete);

    // Update refs whenever callbacks change (but don't trigger reconnection)
    useEffect(() => {
        onProgressRef.current = onProgress;
        onCompleteRef.current = onComplete;
        onCancelRef.current = onCancel;
        onErrorRef.current = onError;
        onCancelProgressRef.current = onCancelProgress;
        onImageProgressRef.current = onImageProgress;
        onImageBatchCompleteRef.current = onImageBatchComplete;
    }, [
        onProgress,
        onComplete,
        onCancel,
        onError,
        onCancelProgress,
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
                const url = `${protocol}//${host}/ws/items/import/${importId}/`;

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
                                    "⏸️ Cancel progress:",
                                    data.step,
                                    "/",
                                    data.total_steps,
                                );
                                onCancelProgressRef.current?.(data);
                                break;
                            case "import_error":
                                console.error("✗ Import error:", data.error);
                                onErrorRef.current?.(data);
                                break;
                            case "import_subscription_confirmed":
                                // subscription acknowledgement, no-op by default
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
                                // Call image batch complete callback
                                onImageBatchCompleteRef.current?.(data);
                                stopHeartbeat();
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
                    stopHeartbeat();
                };

                ws.onclose = () => {
                    if (!isMounted) return;
                    console.log("📭 Import progress WebSocket closed");
                    setIsConnected(false);
                    stopHeartbeat();
                };
            } catch (error) {
                if (!isMounted) return;
                console.error("Failed to create WebSocket:", error);
            }
        };

        connectWebSocket();

        return () => {
            isMounted = false;
            stopHeartbeat();
            if (ws) {
                ws.close();
                ws = null;
            }
        };
    }, [importId]); // Only importId - callbacks handled via refs

    return { isConnected, progress };
};
