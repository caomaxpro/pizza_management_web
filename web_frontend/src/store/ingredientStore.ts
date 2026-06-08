import { create } from "zustand";
import { ingredientAPI, type Ingredient } from "../services/ingredients";

interface IngredientStore {
    ingredients: Ingredient[];
    currentIngredient: Ingredient | null;
    loading: boolean;
    error: string | null;

    // Actions
    setIngredients: (
        ingredients: Ingredient[] | ((prev: Ingredient[]) => Ingredient[]),
    ) => void;
    setCurrentIngredient: (ingredient: Ingredient | null) => void;
    getIngredientById: (id: number) => Ingredient | undefined;
    fetchIngredientById: (id: number) => Promise<Ingredient | null>;
    fetchAllIngredients: (force?: boolean) => Promise<void>; // Fetch all ingredients without pagination
    clearError: () => void;

    // WebSocket cache invalidation
    invalidateIngredientCache: (ingredientId: number) => void;
    removeIngredientFromCache: (ingredientId: number) => void;
    updateIngredientInCache: (ingredient: Ingredient) => void;
}

export const useIngredientStore = create<IngredientStore>((set, get) => ({
    ingredients: [],
    currentIngredient: null,
    loading: false,
    error: null,

    setIngredients: (ingredients) => {
        if (typeof ingredients === "function") {
            set((state) => ({ ingredients: ingredients(state.ingredients) }));
        } else {
            set({ ingredients });
        }
    },

    setCurrentIngredient: (ingredient) =>
        set({ currentIngredient: ingredient }),

    getIngredientById: (id) => {
        const state = get();
        return state.ingredients.find((ing) => ing.id === id);
    },

    fetchIngredientById: async (id) => {
        set({ loading: true, error: null });
        try {
            // First, check if ingredient exists in store
            const state = get();
            const cachedIngredient = state.ingredients.find(
                (ing) => ing.id === id,
            );

            if (cachedIngredient) {
                set({ currentIngredient: cachedIngredient, loading: false });
                return cachedIngredient;
            }

            // If not in store, fetch from API
            const response = await ingredientAPI.get(id);
            const ingredient = response.data;
            set({ currentIngredient: ingredient, loading: false });
            return ingredient;
        } catch (error) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : "Failed to fetch ingredient";
            set({ error: errorMessage, loading: false });
            return null;
        }
    },

    fetchAllIngredients: async (force = false) => {
        const state = get();
        // Skip if cache is populated, unless a force-refresh is requested (e.g. from WS event)
        if (!force && state.ingredients.length > 0) {
            return;
        }
        set({ loading: true, error: null });
        try {
            // Fetch all ingredients without pagination (or with large pageSize)
            const response = await ingredientAPI.list(1, 1000);
            const allIngredients = response.data.results || [];
            set({ ingredients: allIngredients, loading: false });
        } catch (error) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : "Failed to fetch ingredients";
            set({ error: errorMessage, loading: false });
        }
    },

    clearError: () => set({ error: null }),

    invalidateIngredientCache: (ingredientId) => {
        // Remove ingredient from cache and fetch fresh data on next access
        set((state) => ({
            ingredients: state.ingredients.filter(
                (ing) => ing.id !== ingredientId,
            ),
            currentIngredient:
                state.currentIngredient?.id === ingredientId
                    ? null
                    : state.currentIngredient,
        }));
    },

    removeIngredientFromCache: (ingredientId) => {
        // Remove deleted ingredient from cache
        set((state) => ({
            ingredients: state.ingredients.filter(
                (ing) => ing.id !== ingredientId,
            ),
            currentIngredient:
                state.currentIngredient?.id === ingredientId
                    ? null
                    : state.currentIngredient,
        }));
    },

    updateIngredientInCache: (ingredient) => {
        // Replace a single ingredient in cache with fresh data from API response
        set((state) => ({
            ingredients: state.ingredients.map((ing) =>
                ing.id === ingredient.id ? ingredient : ing,
            ),
            currentIngredient:
                state.currentIngredient?.id === ingredient.id
                    ? ingredient
                    : state.currentIngredient,
        }));
    },
}));

export type { Ingredient };
