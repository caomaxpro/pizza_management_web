/* eslint-disable @typescript-eslint/no-explicit-any */
import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { ingredientAPI } from "../../services/ingredients";
import { ProgressBar } from "../../components/ui/ProgressBar";
import Modal from "@components/layout/Modal";
import IngredientForm from "./IngredientForm";

export default function IngredientCreate() {
    const navigate = useNavigate();
    const location = useLocation();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(true);

    // Get imported data from navigation state (if user imported JSON)
    const importedData = (location.state as any)?.importedData || null;
    const isImporting = !!importedData;

    const handleModalClose = () => {
        setIsModalOpen(false);
        navigate("/ingredients");
    };

    const handleSubmit = async (formData: FormData) => {
        try {
            setIsLoading(true);
            setError(null);
            console.log("[IngredientCreate] Submitting form data...");

            // Log what we're sending
            console.log("[IngredientCreate] FormData contents:");
            for (const [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(
                        `  ${key}: File(${value.name}, ${value.size} bytes)`,
                    );
                } else {
                    console.log(`  ${key}: ${value}`);
                }
            }

            const response = await ingredientAPI.create(formData as any);
            console.log(
                "[IngredientCreate] ✅ Success response:",
                response.data,
            );

            // Extract created ingredient ID from response
            const createdId = response.data?.id;
            if (!createdId) {
                console.error(
                    "[IngredientCreate] No ID in response:",
                    response.data,
                );
                setError("Created ingredient but no ID returned from server");
                return;
            }

            console.log(
                `[IngredientCreate] Created ingredient ID: ${createdId}`,
            );
            console.log("[IngredientCreate] Navigating to detail page...");

            // Navigate to detail page with success message
            navigate(`/ingredients/${createdId}`, {
                state: {
                    successMessage: `Ingredient "${response.data?.name || "New"}" created successfully! 🎉`,
                    newData: response.data,
                },
            });
        } catch (err: any) {
            // Detailed error logging
            console.error("[IngredientCreate] ❌ Error details:", err);

            let errorMessage = "Failed to create ingredient. Please try again.";

            // Try to extract backend error message
            if (err.response?.data?.error) {
                errorMessage = err.response.data.error;
            } else if (err.response?.data?.message) {
                errorMessage = err.response.data.message;
            } else if (err.response?.status === 400) {
                errorMessage = `Validation error: ${JSON.stringify(err.response.data)}`;
            } else if (err.response?.status === 401) {
                errorMessage = "Unauthorized - please login again";
            } else if (err.response?.status === 403) {
                errorMessage = "Forbidden - you don't have permission";
            } else if (err.response?.status === 500) {
                errorMessage = `Server error: ${err.response?.data?.error || err.message}`;
            } else if (err.message) {
                errorMessage = err.message;
            }

            console.error(
                "[IngredientCreate] Final error message:",
                errorMessage,
            );
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isModalOpen}
            title={isImporting ? "Import Ingredient" : "Create New Ingredient"}
            onClose={handleModalClose}
            width="70%"
        >
            {error && (
                <div
                    style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgb(239, 68, 68)",
                        color: "rgb(239, 68, 68)",
                        padding: "1rem",
                        borderRadius: "0.5rem",
                        marginBottom: "2rem",
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                        fontFamily: "monospace",
                        fontSize: "0.9rem",
                    }}
                >
                    {error}
                </div>
            )}
            {isLoading ? (
                <div style={{ marginTop: "3rem", marginBottom: "3rem" }}>
                    <ProgressBar
                        label={
                            isImporting
                                ? "📤 Importing ingredient..."
                                : "✨ Creating ingredient..."
                        }
                    />
                </div>
            ) : (
                <IngredientForm
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    initialData={importedData}
                    onCancel={handleModalClose}
                />
            )}
        </Modal>
    );
}
