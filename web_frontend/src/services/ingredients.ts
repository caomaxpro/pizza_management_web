/* eslint-disable @typescript-eslint/no-explicit-any */
import type { AxiosResponse } from "axios";
import API from "./api";

export interface Ingredient {
    id?: number;
    name: string;
    description?: string;
    price: number;
    original_price?: number;
    type: string;
    sub_type?: string;
    image_url?: string;
    piece_image_url?: string;
    is_active: boolean;
    created_at?: string;
}

export const ingredientAPI = {
    // Get all ingredients with pagination and optional filters
    list: (
        page: number = 1,
        pageSize: number = 10,
        filters?: {
            search?: string;
            type?: string;
            subType?: string;
            status?: "all" | "active" | "inactive";
            priceMin?: string;
            priceMax?: string;
        },
    ): Promise<AxiosResponse<any>> => {
        const params: any = { page, page_size: pageSize };

        if (filters) {
            if (filters.search) params.search = filters.search;
            if (filters.type) params.type = filters.type;
            if (filters.subType) params.sub_type = filters.subType;
            if (filters.status && filters.status !== "all") {
                params.status = filters.status;
            }
            if (filters.priceMin) params.price_min = filters.priceMin;
            if (filters.priceMax) params.price_max = filters.priceMax;
        }

        return API.get("/pizza/ingredients/get-paginated-items", { params });
    },

    // Get single ingredient
    get: (id: number): Promise<AxiosResponse<Ingredient>> =>
        API.get(`/pizza/ingredients/${id}/`),

    // Create ingredient (supports FormData for file uploads)
    create: (
        payload: Ingredient | FormData,
    ): Promise<AxiosResponse<Ingredient>> => {
        const config =
            payload instanceof FormData
                ? {
                      headers: { "Content-Type": "multipart/form-data" },
                      timeout: 60000, // 60s timeout for file upload + processing
                  }
                : {};
        return API.post("/pizza/ingredients/", payload, config);
    },

    // Update single ingredient (supports FormData for file uploads)
    update: (
        id: number,
        payload: Partial<Ingredient> | FormData,
    ): Promise<AxiosResponse<Ingredient>> => {
        const config =
            payload instanceof FormData
                ? {
                      headers: { "Content-Type": "multipart/form-data" },
                      timeout: 60000, // 60s timeout for file upload + processing
                  }
                : {};
        return API.patch(`/pizza/ingredients/${id}/`, payload, config);
    },

    // Update multiple ingredients (uses update_many for selected, update_all for all)
    bulkUpdate: (
        payload: Array<{ id: number; data: Partial<Ingredient> }>,
        editMode: "selected" | "all" = "selected",
    ): Promise<AxiosResponse<Ingredient[]>> => {
        const endpoint =
            editMode === "all"
                ? "/pizza/ingredients/update-all/"
                : "/pizza/ingredients/update-many/";
        // Flatten the payload structure: merge id and data into each item
        const flattenedPayload = payload.map((item) => ({
            id: item.id,
            ...item.data,
        }));
        return API.patch(endpoint, { ingredients: flattenedPayload });
    },

    // Delete ingredient
    delete: (id: number): Promise<AxiosResponse<void>> =>
        API.delete(`/pizza/ingredients/${id}/`),

    // Delete multiple ingredients
    bulkDelete: (ids: number[]): Promise<AxiosResponse<void>> =>
        API.post("/pizza/ingredients/bulk_delete/", { ids }),

    // Import ingredients from JSON array
    importJson: (ingredients: any[]): Promise<AxiosResponse<any>> =>
        API.post("/pizza/ingredients/import-json/", ingredients),

    // Cancel ongoing ingredient import
    cancelImport: (importId: string): Promise<AxiosResponse<any>> =>
        API.post(`/pizza/ingredients/import-cancel/${importId}/`, {}),
};
