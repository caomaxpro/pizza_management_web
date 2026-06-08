/* eslint-disable @typescript-eslint/no-explicit-any */
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { ingredientAPI, type Ingredient } from "../../services/ingredients";
import { useIngredientStore } from "../../store/ingredientStore";
import IngredientForm from "./IngredientForm";

export default function IngredientEdit() {
    const navigate = useNavigate();
    const { id } = useParams();
    const [ingredient, setIngredient] = useState<Ingredient | null>(null);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { updateIngredientInCache } = useIngredientStore();

    useEffect(() => {
        const fetchIngredient = async () => {
            if (!id) return;
            try {
                setLoading(true);
                const response = await ingredientAPI.get(parseInt(id));
                setIngredient(response.data);
            } catch (err) {
                setError("Failed to load ingredient");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchIngredient();
    }, [id]);

    const handleSubmit = async (formData: FormData) => {
        if (!id) return;

        try {
            setIsSubmitting(true);
            setError(null);
            console.log("[IngredientEdit] Submitting form data...");
            const response = await ingredientAPI.update(
                parseInt(id),
                formData as any,
            );
            console.log(
                "[IngredientEdit] Success - updating cache and redirecting",
            );
            // Update only this ingredient in the store (no full re-fetch needed)
            updateIngredientInCache(response.data);
            navigate("/ingredients");
        } catch (err) {
            setError("Failed to update ingredient. Please try again.");
            console.error("[IngredientEdit] Error:", err);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div style={{ padding: "2rem", textAlign: "center" }}>
                ⏳ Loading ingredient...
            </div>
        );
    }

    if (!ingredient) {
        return (
            <div style={{ padding: "2rem" }}>
                <div
                    style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgb(239, 68, 68)",
                        color: "rgb(239, 68, 68)",
                        padding: "1rem",
                        borderRadius: "0.5rem",
                    }}
                >
                    Ingredient not found
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: "2rem" }}>
            <h1 style={{ marginBottom: "1rem" }}>✏️ Edit Ingredient</h1>
            {error && (
                <div
                    style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgb(239, 68, 68)",
                        color: "rgb(239, 68, 68)",
                        padding: "1rem",
                        borderRadius: "0.5rem",
                        marginBottom: "2rem",
                    }}
                >
                    {error}
                </div>
            )}
            <IngredientForm
                initialData={ingredient}
                onSubmit={handleSubmit}
                isLoading={isSubmitting}
            />
        </div>
    );
}
