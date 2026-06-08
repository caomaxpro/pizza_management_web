/* eslint-disable @typescript-eslint/no-explicit-any */
import API from "./api";

export interface Item {
    id?: number;
    name: string;
    description?: string;
    price: number;
    original_price?: number;
    category: string;
    type?: string;
    sub_type?: string;
    dough?: number | string;
    sauce?: number | string;
    cheese?: number | string;
    toppings?: any[];
    extras?: any[];
    image_url?: string;
    image?: string;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface ItemListResponse {
    count: number;
    next?: string;
    previous?: string;
    results: Item[];
}

const PIZZA_API_URL = "/pizza/items";

const itemAPI = {
    /**
     * Fetch list of items with pagination and optional filters
     */
    list: async (
        page: number = 1,
        pageSize: number = 20,
        filters?: {
            search?: string;
            category?: string;
            status?: "all" | "active" | "inactive";
            priceMin?: string;
            priceMax?: string;
            sortBy?: string;
            sortOrder?: "asc" | "desc";
        },
    ): Promise<ItemListResponse> => {
        try {
            const params: any = { page, page_size: pageSize };

            if (filters) {
                if (filters.search) params.search = filters.search;
                if (filters.category) params.category = filters.category;
                if (filters.status && filters.status !== "all") {
                    params.status = filters.status;
                }
                if (filters.priceMin) params.price_min = filters.priceMin;
                if (filters.priceMax) params.price_max = filters.priceMax;
                if (filters.sortBy) params.sort_by = filters.sortBy;
                if (filters.sortOrder) params.sort_order = filters.sortOrder;
            }

            const response = await API.get(
                `${PIZZA_API_URL}/get-paginated-items/`,
                { params },
            );
            return response.data;
        } catch (error) {
            console.error("Failed to fetch items:", error);
            throw error;
        }
    },

    /**
     * Fetch single item by ID
     */
    get: async (id: number): Promise<Item> => {
        try {
            const response = await API.get(`${PIZZA_API_URL}/${id}/`);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch item ${id}:`, error);
            throw error;
        }
    },

    /**
     * Create new item
     */
    create: async (data: FormData | Omit<Item, "id">): Promise<Item> => {
        try {
            const response = await API.post(`${PIZZA_API_URL}/`, data);
            return response.data;
        } catch (error) {
            console.error("Failed to create item:", error);
            throw error;
        }
    },

    /**
     * Update existing item
     */
    update: async (
        id: number,
        data: FormData | Partial<Item>,
    ): Promise<Item> => {
        try {
            const response = await API.patch(`${PIZZA_API_URL}/${id}/`, data);
            return response.data;
        } catch (error) {
            console.error(`Failed to update item ${id}:`, error);
            throw error;
        }
    },

    /**
     * Delete single item
     */
    delete: async (id: number): Promise<void> => {
        try {
            await API.delete(`${PIZZA_API_URL}/${id}/`);
        } catch (error) {
            console.error(`Failed to delete item ${id}:`, error);
            throw error;
        }
    },

    /**
     * Bulk delete items
     */
    bulkDelete: async (ids: number[]): Promise<void> => {
        try {
            await API.post(`${PIZZA_API_URL}/delete-many/`, {
                ids,
            });
        } catch (error) {
            console.error("Failed to bulk delete items:", error);
            throw error;
        }
    },

    /**
     * Search items by name
     */
    search: async (
        query: string,
        page: number = 1,
        pageSize: number = 20,
    ): Promise<ItemListResponse> => {
        try {
            const response = await API.get(
                `${PIZZA_API_URL}/get-paginated-items/`,
                {
                    params: {
                        search: query,
                        page,
                        page_size: pageSize,
                    },
                },
            );
            return response.data;
        } catch (error) {
            console.error("Failed to search items:", error);
            throw error;
        }
    },

    /**
     * Filter items by category, price, status
     */
    filter: async (
        filters: {
            category?: string;
            min_price?: number;
            max_price?: number;
            is_active?: boolean;
        },
        page: number = 1,
        pageSize: number = 20,
    ): Promise<ItemListResponse> => {
        try {
            const response = await API.get(`${PIZZA_API_URL}/filter-items/`, {
                params: {
                    ...filters,
                    page,
                    page_size: pageSize,
                },
            });
            return response.data;
        } catch (error) {
            console.error("Failed to filter items:", error);
            throw error;
        }
    },

    /**
     * Bulk update items
     */
    bulkUpdate: async (ids: number[], data: Partial<Item>): Promise<Item[]> => {
        try {
            const response = await API.patch(`${PIZZA_API_URL}/update-many/`, {
                ids,
                ...data,
            });
            return response.data;
        } catch (error) {
            console.error("Failed to bulk update items:", error);
            throw error;
        }
    },

    /**
     * Import items from JSON (async)
     * Returns import_id for WebSocket tracking
     */
    importJson: async (items: Partial<Item>[]): Promise<any> => {
        try {
            const response = await API.post(`${PIZZA_API_URL}/import-json/`, {
                items,
            });
            return response;
        } catch (error) {
            console.error("Failed to import items:", error);
            throw error;
        }
    },

    /**
     * Cancel ongoing item import
     */
    cancelImport: async (importId: string): Promise<void> => {
        try {
            await API.post(`${PIZZA_API_URL}/cancel-import/`, {
                import_id: importId,
            });
        } catch (error) {
            console.error(`Failed to cancel import ${importId}:`, error);
            throw error;
        }
    },
};

export default itemAPI;
