/* eslint-disable @typescript-eslint/no-explicit-any */
import api from "./api";

export interface PurchaseOrder {
    id: number;
    order_number: string;
    provider: { id: number; name: string };
    order_date: string;
    expected_delivery_date?: string;
    actual_delivery_date?: string;
    status: string;
    total_cost: number;
    notes?: string;
    receipt_files: string[];
    created_at: string;
    updated_at: string;
}

export interface PurchaseOrderItem {
    id?: number;
    purchase_order?: number;
    inventory: number | { id: number; name: string };
    quantity: number;
    actual_unit_price?: number;
    total_price?: number;
    created_at?: string;
}

const purchaseOrderAPI = {
    async list(params?: Record<string, any>): Promise<PurchaseOrder[]> {
        const res = await api.get("/purchase-orders/", { params });
        return res.data;
    },
    async get(id: number): Promise<PurchaseOrder> {
        const res = await api.get(`/purchase-orders/${id}/`);
        return res.data;
    },
    async create(data: Partial<PurchaseOrder>): Promise<PurchaseOrder> {
        const res = await api.post("/purchase-orders/", data);
        return res.data;
    },
    async update(
        id: number,
        data: Partial<PurchaseOrder>,
    ): Promise<PurchaseOrder> {
        const res = await api.patch(`/purchase-orders/${id}/`, data);
        return res.data;
    },
    async delete(id: number): Promise<void> {
        await api.delete(`/purchase-orders/${id}/`);
    },
    async bulkDelete(ids: number[]): Promise<void> {
        await api.post(`/purchase-orders/bulk-delete/`, { ids });
    },

    // PO Item methods
    async getItem(poId: number, itemId: number): Promise<PurchaseOrderItem> {
        const res = await api.get(`/purchase-orders/${poId}/items/${itemId}/`);
        return res.data;
    },

    async createItem(
        poId: number,
        data: Partial<PurchaseOrderItem>,
    ): Promise<PurchaseOrderItem> {
        const res = await api.post(`/purchase-orders/${poId}/items/`, data);
        return res.data;
    },

    async updateItem(
        poId: number,
        itemId: number,
        data: Partial<PurchaseOrderItem>,
    ): Promise<PurchaseOrderItem> {
        const res = await api.patch(
            `/purchase-orders/${poId}/items/${itemId}/`,
            data,
        );
        return res.data;
    },

    async deleteItem(poId: number, itemId: number): Promise<void> {
        await api.delete(`/purchase-orders/${poId}/items/${itemId}/`);
    },
};

export default purchaseOrderAPI;
