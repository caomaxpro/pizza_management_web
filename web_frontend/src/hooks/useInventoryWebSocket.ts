import { useCallback } from "react";
import { useWebSocket } from "./useWebSocket";
import type { InventoryItem } from "../services/inventory";

interface InventoryWSMessage {
    type:
        | "inventory_created"
        | "inventory_updated"
        | "inventory_deleted"
        | "subscription_confirmed"
        | "error";
    inventory?: InventoryItem;
    inventory_id?: number;
    message?: string;
}

const getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    if (import.meta.env.DEV) {
        return `${protocol}//${window.location.hostname}:8000/ws/inventory/updates/`;
    }
    return `${protocol}//${window.location.host}/ws/inventory/updates/`;
};

export const useInventoryWebSocket = (
    onUpdate: (item: InventoryItem) => void,
    onDelete: (id: number) => void,
    onCreate: (item: InventoryItem) => void,
) => {
    const handleMessage = useCallback(
        (msg: InventoryWSMessage) => {
            switch (msg.type) {
                case "inventory_created":
                    if (msg.inventory) {
                        onCreate(msg.inventory);
                        console.log(
                            `✨ Inventory created: ${msg.inventory.name}`,
                        );
                    }
                    break;
                case "inventory_updated":
                    if (msg.inventory) {
                        onUpdate(msg.inventory);
                        console.log(
                            `🔄 Inventory updated: ${msg.inventory.name}`,
                        );
                    }
                    break;
                case "inventory_deleted":
                    if (msg.inventory_id !== undefined) {
                        onDelete(msg.inventory_id);
                        console.log(
                            `🗑️ Inventory deleted (ID: ${msg.inventory_id})`,
                        );
                    }
                    break;
                case "subscription_confirmed":
                    console.log("✅ Subscribed to inventory updates");
                    break;
                case "error":
                    console.error("❌ Inventory WebSocket error:", msg.message);
                    break;
            }
        },
        [onUpdate, onDelete, onCreate],
    );

    const { isConnected } = useWebSocket<InventoryWSMessage>({
        url: getWebSocketUrl(),
        onMessage: handleMessage,
        reconnectAttempts: 5,
        reconnectDelay: 3000,
    });

    return { isConnected };
};
