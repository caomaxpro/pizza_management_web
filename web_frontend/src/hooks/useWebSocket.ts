import { useEffect, useRef, useCallback, useState } from "react";

interface WebSocketMessage {
    type:
        | "item_created"
        | "item_updated"
        | "item_deleted"
        | "subscription_confirmed"
        | "error";
    item_id?: number;
    item_name?: string;
    message?: string;
}

interface UseWebSocketOptions<T = WebSocketMessage> {
    url: string;
    onOpen?: () => void;
    onClose?: () => void;
    onMessage: (data: T) => void;
    onError?: (error: Event) => void;
    reconnectAttempts?: number;
    reconnectDelay?: number;
}

export const useWebSocket = <T = WebSocketMessage>({
    url,
    onOpen,
    onClose,
    onMessage,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
}: UseWebSocketOptions<T>) => {
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectCountRef = useRef(0);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
        null,
    );
    const isManuallyClosedRef = useRef(false);
    const connectFnRef = useRef<() => void>(() => {});

    // Use state for isConnected instead of computing during render
    const [isConnected, setIsConnected] = useState(false);

    const connect = useCallback(() => {
        if (isManuallyClosedRef.current) return;

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log("✅ WebSocket connected:", url);
                reconnectCountRef.current = 0;
                wsRef.current = ws;
                setIsConnected(true);
                onOpen?.();

                // Send subscription message
                ws.send(JSON.stringify({ type: "subscribe" }));
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as T;
                    onMessage(data);
                } catch (error) {
                    console.error("Failed to parse WebSocket message:", error);
                }
            };

            ws.onerror = (error) => {
                console.error("❌ WebSocket error:", error);
                onError?.(error);
            };

            ws.onclose = () => {
                console.log("📭 WebSocket closed");
                wsRef.current = null;
                setIsConnected(false);
                onClose?.();

                // Attempt to reconnect
                if (
                    !isManuallyClosedRef.current &&
                    reconnectCountRef.current < reconnectAttempts
                ) {
                    reconnectCountRef.current++;
                    console.log(
                        `🔄 Reconnecting... attempt ${reconnectCountRef.current}/${reconnectAttempts}`,
                    );
                    // Use ref to avoid circular dependency
                    reconnectTimeoutRef.current = setTimeout(
                        connectFnRef.current,
                        reconnectDelay * reconnectCountRef.current,
                    );
                }
            };
        } catch (error) {
            console.error("Failed to create WebSocket:", error);
            onError?.(error as Event);
        }
    }, [
        url,
        onMessage,
        onOpen,
        onClose,
        onError,
        reconnectAttempts,
        reconnectDelay,
    ]);

    // Store the connect function in ref for use in timeouts
    useEffect(() => {
        connectFnRef.current = connect;
    }, [connect]);

    const disconnect = useCallback(() => {
        isManuallyClosedRef.current = true;
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const send = useCallback((data: object) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        } else {
            console.warn("WebSocket is not connected");
        }
    }, []);

    useEffect(() => {
        isManuallyClosedRef.current = false;
        connect();

        return () => {
            disconnect();
        };
    }, [url]);

    return { isConnected, send, disconnect };
};
