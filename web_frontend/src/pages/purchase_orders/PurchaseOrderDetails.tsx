import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import purchaseOrderAPI from "../../services/purchaseOrder";
import type { PurchaseOrder } from "../../services/purchaseOrder";
import inventoryAPI from "../../services/inventory";
import CustomListTable, {
    type CustomListColumn,
} from "@components/ui/CustomListTable";
import { Button } from "@components/ui";
import POItemsTable from "./POItemsTable";
import type { POItemPayload } from "./POItemsTable";

export default function PurchaseOrderDetails() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [order, setOrder] = useState<PurchaseOrder | null>(null);
    const [addItemFormOpen, setAddItemFormOpen] = useState(false);
    const [isAddingItem, setIsAddingItem] = useState(false);
    const [inventoryOptions, setInventoryOptions] = useState<
        Array<{ value: string; label: string }>
    >([]);

    useEffect(() => {
        inventoryAPI
            .list()
            .then((items) =>
                setInventoryOptions(
                    items.map((item) => ({
                        label: `${item.name} (${item.current_stock} ${item.unit})`,
                        value: String(item.id),
                    })),
                ),
            )
            .catch(() => {});
    }, []);

    useEffect(() => {
        if (!id) return;
        let mounted = true;
        purchaseOrderAPI
            .get(Number(id))
            .then((data) => mounted && setOrder(data))
            .catch(() => {
                // on error, navigate back
                if (mounted) navigate("/purchase_orders");
            });
        return () => {
            mounted = false;
        };
    }, [id, navigate]);

    const handleAddItems = async (items: POItemPayload[]) => {
        if (!id) return;
        try {
            setIsAddingItem(true);
            await Promise.all(
                items.map((item) =>
                    purchaseOrderAPI.createItem(Number(id), item),
                ),
            );
            const updatedOrder = await purchaseOrderAPI.get(Number(id));
            setOrder(updatedOrder);
            setAddItemFormOpen(false);
        } catch (error) {
            console.error("Failed to add items:", error);
        } finally {
            setIsAddingItem(false);
        }
    };

    const items =
        ((order as unknown as Record<string, unknown>)?.items as unknown[]) ??
        [];

    const columns: CustomListColumn[] = useMemo(
        () => [
            {
                key: "inventory",
                title: "Item",
                render: (row: Record<string, unknown>) =>
                    ((row.inventory as Record<string, unknown>)
                        ?.name as string) || "-",
            },
            {
                key: "quantity",
                title: "Qty",
                render: (row: Record<string, unknown>) => String(row.quantity),
                align: "right",
            },
            {
                key: "unit_price",
                title: "Unit",
                render: (row: Record<string, unknown>) =>
                    row.actual_unit_price != null
                        ? (row.actual_unit_price as number).toLocaleString(
                              undefined,
                              { style: "currency", currency: "USD" },
                          )
                        : "-",
                align: "right",
            },
            {
                key: "total_price",
                title: "Total",
                render: (row: Record<string, unknown>) =>
                    ((row.total_price as number) ?? 0).toLocaleString(
                        undefined,
                        { style: "currency", currency: "USD" },
                    ),
                align: "right",
            },
            {
                key: "actions",
                title: "Actions",
                render: (row: Record<string, unknown>) => (
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                                navigate(
                                    `/items/${
                                        (
                                            row.inventory as Record<
                                                string,
                                                unknown
                                            >
                                        )?.id
                                    }`,
                                )
                            }
                        >
                            View Item
                        </Button>
                    </div>
                ),
                width: 140,
            },
        ],
        [navigate],
    );

    return (
        <div style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                    <h2>Purchase Order Details</h2>
                    <div>
                        <strong>PO:</strong> {order?.order_number}
                    </div>
                    <div>
                        <strong>Provider:</strong> {order?.provider?.name}
                    </div>
                    <div>
                        <strong>Status:</strong> {order?.status}
                    </div>
                    <div>
                        <strong>Order date:</strong>{" "}
                        {order?.order_date?.slice?.(0, 10)}
                    </div>
                    <div>
                        <strong>Expected delivery:</strong>{" "}
                        {order?.expected_delivery_date}
                    </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <Button variant="outline" onClick={() => navigate(-1)}>
                        Back
                    </Button>
                </div>
            </div>

            <div style={{ marginTop: 16 }}>
                <div
                    style={{ display: "flex", justifyContent: "space-between" }}
                >
                    <h3>Items</h3>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setAddItemFormOpen(true)}
                    >
                        + Add Item
                    </Button>
                </div>
                <CustomListTable
                    columns={columns}
                    data={items}
                    showCheckboxes={false}
                    pageSize={10}
                    currentPage={1}
                    totalPages={1}
                />
            </div>

            <div style={{ marginTop: 16 }}>
                <h3>Notes</h3>
                <div>{order?.notes || "-"}</div>
            </div>

            {order?.receipt_files && order.receipt_files.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <h3>Receipts</h3>
                    <ul>
                        {order.receipt_files.map((r, i) => (
                            <li key={i}>
                                <a href={r} target="_blank" rel="noreferrer">
                                    {r}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <POItemsTable
                key={addItemFormOpen ? "open" : "closed"}
                open={addItemFormOpen}
                onClose={() => setAddItemFormOpen(false)}
                onSubmit={handleAddItems}
                isLoading={isAddingItem}
                inventoryOptions={inventoryOptions}
            />
        </div>
    );
}
