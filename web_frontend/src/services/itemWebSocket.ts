/**
 * WebSocket service for real-time item updates.
 *
 * Manages connection to Django Channels and broadcasts item changes
 * (create, update, delete) to all connected clients.
 */

import { useCallback } from "react";
import { useItemStore } from "../store/itemStore";
import { useWebSocket } from "../hooks/useWebSocket";

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

// Get the WebSocket URL based on current environment
const getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

    // Check if we're in development or production
    if (import.meta.env.DEV) {
        // Development: connect to local backend
        return `${protocol}//${window.location.hostname}:8000/ws/items/updates/`;
    } else {
        // Production: connect to same host
        return `${protocol}//${window.location.host}/ws/items/updates/`;
    }
};

/**
 * Hook for managing real-time item updates via WebSocket.
 *
 * Automatically connects to the WebSocket server and listens for:
 * - item_created: Invalidates the items list cache
 * - item_updated: Invalidates the specific item's cache
 * - item_deleted: Removes the item from cache
 *
 * Usage in a component:
 * ```tsx
 * export const SomeComponent = () => {
 *   const { isConnected } = useItemWebSocket();
 *   return <div>{isConnected ? "Connected" : "Connecting..."}</div>
 * }
 * ```
 */
export const useItemWebSocket = () => {
    const store = useItemStore();

    const handleMessage = useCallback(
        (message: WebSocketMessage) => {
            console.log(
                "📬 WebSocket message received:",
                message.type,
                message,
            );

            switch (message.type) {
                case "item_created":
                    // For new items, invalidate the entire list
                    // Next fetch will get fresh data from API
                    store.setItems([]);
                    console.log(
                        `✨ New item created: ${message.item_name} (ID: ${message.item_id})`,
                    );
                    break;

                case "item_updated":
                    // Re-fetch the updated item and replace it in the store
                    if (message.item_id) {
                        void store.invalidateItemCache(message.item_id);
                        console.log(
                            `🔄 Item updated: ${message.item_name} (ID: ${message.item_id})`,
                        );
                    }
                    break;

                case "item_deleted":
                    // Remove the deleted item from cache
                    if (message.item_id) {
                        store.removeItemFromCache(message.item_id);
                        console.log(`🗑️ Item deleted (ID: ${message.item_id})`);
                    }
                    break;

                case "subscription_confirmed":
                    console.log("✅ Subscribed to item updates");
                    break;

                case "error":
                    console.error("❌ WebSocket error:", message.message);
                    break;

                default:
                    console.warn("Unknown message type:", message.type);
            }
        },
        [store],
    );

    const handleOpen = useCallback(() => {
        console.log("✅ Connected to item updates WebSocket");
    }, []);

    const handleClose = useCallback(() => {
        console.log("📴 Disconnected from item updates WebSocket");
    }, []);

    const handleError = useCallback((error: Event) => {
        console.error("🔌 WebSocket error:", error);
    }, []);

    const { isConnected, send } = useWebSocket({
        url: getWebSocketUrl(),
        onOpen: handleOpen,
        onClose: handleClose,
        onMessage: handleMessage,
        onError: handleError,
        reconnectAttempts: 5,
        reconnectDelay: 3000,
    });

    return { isConnected, send };
};
