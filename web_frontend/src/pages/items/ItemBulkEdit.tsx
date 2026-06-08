import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { Target } from "@phosphor-icons/react";

export default function ItemBulkEdit() {
    const navigate = useNavigate();
    const location = useLocation();
    const [loading, setLoading] = useState(false);

    const selectedIds: number[] =
        (location.state as { selectedIds?: number[] })?.selectedIds || [];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            // TODO: Replace with actual API call
            console.log("Bulk edit items:", selectedIds);
            navigate("/items");
        } catch {
            alert("Failed to bulk edit items");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: "2rem" }}>
            <h1>
                <Target size={24} /> Bulk Edit Items
            </h1>
            <p>Editing {selectedIds.length} items</p>
            <p>Bulk edit form implementation will go here</p>
            <button onClick={() => navigate("/items")}>Back to Items</button>
        </div>
    );
}
