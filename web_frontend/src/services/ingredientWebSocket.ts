/**
 * WebSocket service for real-time ingredient updates.
 *
 * Manages connection to Django Channels and broadcasts ingredient changes
 * (create, update, delete) to all connected clients.
 */

import { useCallback } from "react";
import { useIngredientStore } from "../store/ingredientStore";
import { useWebSocket } from "../hooks/useWebSocket";

interface WebSocketMessage {
    type:
        | "ingredient_created"
        | "ingredient_updated"
        | "ingredient_deleted"
        | "subscription_confirmed"
        | "error";
    ingredient_id?: number;
    ingredient_name?: string;
    message?: string;
}

const getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

    if (import.meta.env.DEV) {
        return `${protocol}//${window.location.hostname}:8000/ws/ingredients/updates/`;
    } else {
        return `${protocol}//${window.location.host}/ws/ingredients/updates/`;
    }
};

/**
 * Hook for managing real-time ingredient updates via WebSocket.
 *
 * Automatically connects to the WebSocket server and listens for:
 * - ingredient_created: Force-refreshes the ingredients list
 * - ingredient_updated: Force-refreshes the ingredients list
 * - ingredient_deleted: Removes the ingredient from cache
 */
export const useIngredientWebSocket = () => {
    const handleMessage = useCallback(
        (message: WebSocketMessage) => {
            console.log(
                "📬 Ingredient WS message received:",
                message.type,
                message,
            );

            // Always read actions from the store's getState() to avoid stale closures.
            // Using `store` directly as a dep would cause handleMessage (and the WS
            // hook) to be recreated on every Zustand state change.
            const { fetchAllIngredients, removeIngredientFromCache } =
                useIngredientStore.getState();

            switch (message.type) {
                case "ingredient_created":
                    fetchAllIngredients(true);
                    console.log(
                        `✨ New ingredient created: ${message.ingredient_name} (ID: ${message.ingredient_id})`,
                    );
                    break;

                case "ingredient_updated":
                    fetchAllIngredients(true);
                    console.log(
                        `🔄 Ingredient updated: ${message.ingredient_name} (ID: ${message.ingredient_id})`,
                    );
                    break;

                case "ingredient_deleted":
                    if (message.ingredient_id) {
                        removeIngredientFromCache(message.ingredient_id);
                        console.log(
                            `🗑️ Ingredient deleted (ID: ${message.ingredient_id})`,
                        );
                    }
                    break;

                case "subscription_confirmed":
                    console.log("✅ Subscribed to ingredient updates");
                    break;

                case "error":
                    console.error(
                        "❌ Ingredient WebSocket error:",
                        message.message,
                    );
                    break;

                default:
                    console.warn(
                        "Unknown ingredient WS message type:",
                        message.type,
                    );
            }
        },
        [], // No deps — reads live store state via getState()
    );

    const handleOpen = useCallback(() => {
        console.log("✅ Connected to ingredient updates WebSocket");
    }, []);

    const handleClose = useCallback(() => {
        console.log("📴 Disconnected from ingredient updates WebSocket");
    }, []);

    const handleError = useCallback((error: Event) => {
        console.error("🔌 Ingredient WebSocket error:", error);
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
