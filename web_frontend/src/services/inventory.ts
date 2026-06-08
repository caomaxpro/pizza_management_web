/* eslint-disable @typescript-eslint/no-explicit-any */
import api from "./api";

export interface InventoryProvider {
    id: number;
    name: string;
    category: string;
    category_display?: string;
}

export interface InventoryItem {
    id: number;
    name: string;
    description?: string;
    unit: string;
    current_stock: number;
    min_threshold: number;
    max_threshold?: number;
    provider?: InventoryProvider;
    provider_id?: number;
    is_active: boolean;
    stock_percentage?: number;
    needs_reorder?: boolean;
    created_at: string;
    updated_at: string;
}

export interface InventoryLog {
    id: number;
    inventory: number;
    inventory_name?: string;
    inventory_unit?: string;
    quantity_change: number;
    reason_type: "receipt" | "stock_take";
    reason_type_display?: string;
    reason_detail?: string | null;
    created_at: string;
}

export interface BulkLogEntry {
    inventory_id: number;
    quantity_change: number;
    reason_type: "receipt" | "stock_take";
    reason_detail?: string;
}

export const UNIT_CHOICES = [
    { value: "kg", label: "Kilogram (kg)" },
    { value: "g", label: "Gram (g)" },
    { value: "ml", label: "Milliliter (ml)" },
    { value: "l", label: "Liter (l)" },
    { value: "pcs", label: "Piece (pcs)" },
    { value: "box", label: "Box" },
    { value: "bag", label: "Bag" },
    { value: "pouch", label: "Pouch" },
    { value: "packet", label: "Packet" },
    { value: "bottle", label: "Bottle" },
    { value: "dozen", label: "Dozen" },
];

const inventoryAPI = {
    async list(params?: Record<string, any>): Promise<InventoryItem[]> {
        const res = await api.get("/inventory/", { params });
        return Array.isArray(res.data)
            ? res.data
            : (res.data.results ?? res.data);
    },

    async get(id: number): Promise<InventoryItem> {
        const res = await api.get(`/inventory/${id}/`);
        return res.data;
    },

    async create(data: Partial<InventoryItem>): Promise<InventoryItem> {
        const res = await api.post("/inventory/", data);
        return res.data;
    },

    async update(
        id: number,
        data: Partial<InventoryItem>,
    ): Promise<InventoryItem> {
        const res = await api.patch(`/inventory/${id}/`, data);
        return res.data;
    },

    async delete(id: number): Promise<void> {
        await api.delete(`/inventory/${id}/`);
    },

    async deleteMany(ids: number[]): Promise<void> {
        await api.post("/inventory/delete-many/", { ids });
    },

    async getLowStock(): Promise<InventoryItem[]> {
        const res = await api.get("/inventory/low-stock/");
        return Array.isArray(res.data)
            ? res.data
            : (res.data.results ?? res.data);
    },

    async getLogs(inventoryId: number): Promise<InventoryLog[]> {
        const res = await api.get("/inventory-log/", {
            params: { inventory: inventoryId },
        });
        return Array.isArray(res.data)
            ? res.data
            : (res.data.results ?? res.data);
    },

    async adjustStock(
        id: number,
        quantity: number,
        reason: string,
    ): Promise<InventoryItem> {
        // Uses the update stock endpoint via update_stock action
        const res = await api.patch(`/inventory/${id}/`, {
            current_stock_adjustment: quantity,
            reason,
        });
        return res.data;
    },

    async bulkCreateLogs(entries: BulkLogEntry[]): Promise<InventoryLog[]> {
        const res = await api.post("/inventory-log/bulk-create/", { entries });
        return res.data;
    },

    async revertLogs(logIds: number[]): Promise<InventoryLog[]> {
        const res = await api.post("/inventory/revert-logs/", {
            log_ids: logIds,
        });
        return res.data;
    },
};

export default inventoryAPI;
