/* eslint-disable @typescript-eslint/no-explicit-any */
import API from "./api";

export interface Provider {
    id: number;
    name: string;
    category: "fresh" | "canned" | "bottled" | "dairy" | "equipment" | "other";
    category_display?: string;
    phone?: string;
    email?: string;
    address?: string;
    is_active: boolean;
    purchase_order_count?: number;
    created_at: string;
    updated_at?: string;
}

export interface ProviderListResponse {
    results: Provider[];
    count?: number;
}

const PROVIDER_API_URL = "/provider";

const providerAPI = {
    /**
     * Fetch all providers with optional filtering
     */
    list: async (filters?: {
        category?: string;
        search?: string;
        is_active?: boolean;
        ordering?: string;
    }): Promise<Provider[]> => {
        try {
            const params: any = {};

            if (filters) {
                if (filters.category) params.category = filters.category;
                if (filters.search) params.search = filters.search;
                if (filters.is_active !== undefined)
                    params.is_active = filters.is_active;
                if (filters.ordering) params.ordering = filters.ordering;
            }

            const response = await API.get(`${PROVIDER_API_URL}/`, { params });
            // Handle both array and object response formats
            return Array.isArray(response.data)
                ? response.data
                : response.data.results || [];
        } catch (error) {
            console.error("Failed to fetch providers:", error);
            throw error;
        }
    },

    /**
     * Fetch single provider by ID
     */
    get: async (id: number): Promise<Provider> => {
        try {
            const response = await API.get(`${PROVIDER_API_URL}/${id}/`);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch provider ${id}:`, error);
            throw error;
        }
    },

    /**
     * Create new provider
     */
    create: async (
        data: Omit<
            Provider,
            | "id"
            | "created_at"
            | "updated_at"
            | "purchase_order_count"
            | "category_display"
        >,
    ): Promise<Provider> => {
        try {
            // Map camelCase to snake_case for API
            const payload = {
                name: data.name,
                category: data.category,
                phone: data.phone || "",
                email: data.email || "",
                address: data.address || "",
                is_active: data.is_active,
            };

            const response = await API.post(`${PROVIDER_API_URL}/`, payload);
            return response.data;
        } catch (error) {
            console.error("Failed to create provider:", error);
            throw error;
        }
    },

    /**
     * Update provider (full update)
     */
    update: async (
        id: number,
        data: Partial<
            Omit<
                Provider,
                | "id"
                | "created_at"
                | "updated_at"
                | "purchase_order_count"
                | "category_display"
            >
        >,
    ): Promise<Provider> => {
        try {
            // Map camelCase to snake_case for API
            const payload: any = {};
            if (data.name !== undefined) payload.name = data.name;
            if (data.category !== undefined) payload.category = data.category;
            if (data.phone !== undefined) payload.phone = data.phone || "";
            if (data.email !== undefined) payload.email = data.email || "";
            if (data.address !== undefined)
                payload.address = data.address || "";
            if (data.is_active !== undefined)
                payload.is_active = data.is_active;

            const response = await API.put(
                `${PROVIDER_API_URL}/${id}/`,
                payload,
            );
            return response.data;
        } catch (error) {
            console.error(`Failed to update provider ${id}:`, error);
            throw error;
        }
    },

    /**
     * Partial update provider
     */
    partialUpdate: async (
        id: number,
        data: Partial<
            Omit<
                Provider,
                | "id"
                | "created_at"
                | "updated_at"
                | "purchase_order_count"
                | "category_display"
            >
        >,
    ): Promise<Provider> => {
        try {
            // Map camelCase to snake_case for API
            const payload: any = {};
            if (data.name !== undefined) payload.name = data.name;
            if (data.category !== undefined) payload.category = data.category;
            if (data.phone !== undefined) payload.phone = data.phone || "";
            if (data.email !== undefined) payload.email = data.email || "";
            if (data.address !== undefined)
                payload.address = data.address || "";
            if (data.is_active !== undefined)
                payload.is_active = data.is_active;

            const response = await API.patch(
                `${PROVIDER_API_URL}/${id}/`,
                payload,
            );
            return response.data;
        } catch (error) {
            console.error(`Failed to update provider ${id}:`, error);
            throw error;
        }
    },

    /**
     * Delete provider
     */
    delete: async (id: number): Promise<void> => {
        try {
            await API.delete(`${PROVIDER_API_URL}/${id}/`);
        } catch (error) {
            console.error(`Failed to delete provider ${id}:`, error);
            throw error;
        }
    },

    /**
     * Delete multiple providers
     */
    deleteMany: async (ids: number[]): Promise<void> => {
        try {
            await API.delete(`${PROVIDER_API_URL}/delete-many/`, {
                data: { ids },
            });
        } catch (error) {
            console.error("Failed to delete providers:", error);
            throw error;
        }
    },

    /**
     * Update multiple providers
     */
    updateMany: async (
        updates: Array<{
            id: number;
            data: Partial<
                Omit<
                    Provider,
                    | "id"
                    | "created_at"
                    | "updated_at"
                    | "purchase_order_count"
                    | "category_display"
                >
            >;
        }>,
    ): Promise<Provider[]> => {
        try {
            const payload = updates.map((update) => ({
                id: update.id,
                ...update.data,
            }));

            const response = await API.patch(
                `${PROVIDER_API_URL}/update-many/`,
                { providers: payload },
            );
            return response.data;
        } catch (error) {
            console.error("Failed to update providers:", error);
            throw error;
        }
    },
};

export default providerAPI;
