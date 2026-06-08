import { create } from "zustand";
import itemAPI from "../services/item";

export interface Item {
    id?: number;
    name: string;
    category: string;
    type?: string;
    price: number;
    original_price?: number;
    description?: string;
    is_active: boolean;
    image_url?: string;
    image?: string;
    created_at?: string;
    updated_at?: string;
}

interface ItemStore {
    items: Item[];
    currentItem: Item | null;
    loading: boolean;
    error: string | null;

    // Actions
    setItems: (items: Item[] | ((prev: Item[]) => Item[])) => void;
    setCurrentItem: (item: Item | null) => void;
    getItemById: (id: number) => Item | undefined;
    fetchItemById: (id: number) => Promise<Item | null>;
    fetchAllItems: (force?: boolean) => Promise<void>; // Fetch all items without pagination
    clearError: () => void;

    // WebSocket cache invalidation
    invalidateItemCache: (itemId: number) => Promise<void>; // re-fetch updated item
    removeItemFromCache: (itemId: number) => void;
}

export const useItemStore = create<ItemStore>((set, get) => ({
    items: [],
    currentItem: null,
    loading: false,
    error: null,

    setItems: (items) => {
        if (typeof items === "function") {
            set((state) => ({ items: items(state.items) }));
        } else {
            set({ items });
        }
    },

    setCurrentItem: (item) => set({ currentItem: item }),

    getItemById: (id) => {
        const state = get();
        return state.items.find((item) => item.id === id);
    },

    fetchItemById: async (id) => {
        set({ loading: true, error: null });
        try {
            // First, check if item exists in store
            const state = get();
            const cachedItem = state.items.find((item) => item.id === id);

            if (cachedItem) {
                set({ currentItem: cachedItem, loading: false });
                return cachedItem;
            }

            // If not in store, fetch from API
            const response = await itemAPI.get(id);
            set({ currentItem: response, loading: false });
            return response;
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : "Failed to fetch item";
            set({ error: errorMessage, loading: false });
            return null;
        }
    },

    clearError: () => set({ error: null }),

    invalidateItemCache: async (itemId) => {
        // Re-fetch the updated item and replace it in the store
        try {
            const fresh = await itemAPI.get(itemId);
            set((state) => ({
                items: state.items.map((item) =>
                    item.id === itemId ? (fresh as Item) : item,
                ),
                currentItem:
                    state.currentItem?.id === itemId
                        ? (fresh as Item)
                        : state.currentItem,
            }));
        } catch {
            // If fetch fails (e.g. item was deleted), remove from store
            set((state) => ({
                items: state.items.filter((item) => item.id !== itemId),
                currentItem:
                    state.currentItem?.id === itemId ? null : state.currentItem,
            }));
        }
    },

    removeItemFromCache: (itemId) => {
        // Remove deleted item from cache
        set((state) => ({
            items: state.items.filter((item) => item.id !== itemId),
            currentItem:
                state.currentItem?.id === itemId ? null : state.currentItem,
        }));
    },

    fetchAllItems: async (force = false) => {
        const state = get();
        // Skip if cache is populated, unless a force-refresh is requested (e.g. from batch import completion)
        if (!force && state.items.length > 0) {
            return;
        }
        set({ loading: true, error: null });
        try {
            // Fetch all items without pagination (or with large pageSize)
            const response = await itemAPI.list(1, 1000);
            const allItems = response.results || [];
            set({ items: allItems, loading: false });
        } catch (error) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : "Failed to fetch items";
            set({ error: errorMessage, loading: false });
        }
    },
}));
