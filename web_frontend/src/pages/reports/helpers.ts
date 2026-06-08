export const STATUS_COLORS: Record<string, string> = {
    pending: "#f59e0b",
    confirmed: "#3b82f6",
    preparing: "#8b5cf6",
    ready: "#06b6d4",
    delivered: "#10b981",
    cancelled: "#ef4444",
};

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
    credit_card: "Credit Card",
    debit_card: "Debit Card",
    paypal: "PayPal",
    bank_transfer: "Bank Transfer",
    cash: "Cash",
};

export const PAYMENT_METHOD_COLORS: Record<string, string> = {
    credit_card: "#6366f1",
    debit_card: "#8b5cf6",
    paypal: "#0ea5e9",
    bank_transfer: "#10b981",
    cash: "#f59e0b",
};

export const PAYMENT_STATUS_COLORS: Record<string, string> = {
    pending: "#f59e0b",
    processing: "#3b82f6",
    completed: "#10b981",
    failed: "#ef4444",
    refunded: "#8b5cf6",
};

export const getPaymentStatusColor = (s: string) =>
    PAYMENT_STATUS_COLORS[s] ?? "#6b7280";

export const getPaymentMethodColor = (m: string) =>
    PAYMENT_METHOD_COLORS[m] ?? "#6b7280";

export const getStatusColor = (s: string) => STATUS_COLORS[s] ?? "#6b7280";

export const getStockColor = (pct: number) =>
    pct < 30 ? "#ef4444" : pct < 60 ? "#f59e0b" : "#10b981";

export const fmt = (n: number) =>
    new Intl.NumberFormat("en-CA", {
        style: "currency",
        currency: "CAD",
    }).format(n);

export const PERIOD_OPTIONS = [
    { key: "7", label: "7 Days" },
    { key: "30", label: "30 Days" },
    { key: "90", label: "3 Months" },
];
