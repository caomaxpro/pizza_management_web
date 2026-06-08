/**
 * Utility function to clear all app cache, storage, and cookies on logout
 * Ensures complete clean state when user logs out
 */

import { useItemStore } from "../store/itemStore";
import { useIngredientStore } from "../store/ingredientStore";

export const clearAllCache = () => {
    console.log("[ClearCache] Starting complete cache cleanup...");

    // 1. Clear all localStorage
    localStorage.clear();
    console.log("[ClearCache] ✓ localStorage cleared");

    // 2. Clear all sessionStorage
    sessionStorage.clear();
    console.log("[ClearCache] ✓ sessionStorage cleared");

    // 3. Clear all cookies
    document.cookie.split(";").forEach((c) => {
        const eqPos = c.indexOf("=");
        const name = eqPos > -1 ? c.substr(0, eqPos).trim() : c.trim();
        if (name) {
            // Clear cookie with different date formats for compatibility
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`;
        }
    });
    console.log("[ClearCache] ✓ All cookies cleared");

    // 4. Clear all Zustand stores
    try {
        // Clear item store
        useItemStore.setState({
            items: [],
            currentItem: null,
            loading: false,
            error: null,
        });
        console.log("[ClearCache] ✓ Item store cleared");

        // Clear ingredient store
        useIngredientStore.setState({
            ingredients: [],
            currentIngredient: null,
            loading: false,
            error: null,
        });
        console.log("[ClearCache] ✓ Ingredient store cleared");
    } catch (error) {
        console.error("[ClearCache] Error clearing Zustand stores:", error);
    }

    // 5. Clear IndexedDB if used
    if ("indexedDB" in window) {
        // Common app database names to clear
        const commonDbNames = [
            "pizza_app_db",
            "app_cache",
            "pizza_cache",
            "app_data",
        ];

        commonDbNames.forEach((dbName) => {
            try {
                const deleteRequest = indexedDB.deleteDatabase(dbName);
                deleteRequest.onsuccess = () => {
                    console.log(`[ClearCache] ✓ IndexedDB "${dbName}" deleted`);
                };
                deleteRequest.onerror = () => {
                    console.log(
                        `[ClearCache] IndexedDB "${dbName}" not found (OK)`,
                    );
                };
            } catch {
                console.log(`[ClearCache] IndexedDB cleanup for "${dbName}"`);
            }
        });
    }

    console.log("[ClearCache] ✅ Complete cache cleanup finished!");
};
