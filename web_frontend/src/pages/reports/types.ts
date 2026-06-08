export interface OrdersReport {
    total_orders: number;
    status_breakdown: { status: string; count: number }[];
    average_order_value: number;
    orders_last_30_days: { date: string; count: number }[];
}

export interface TopItem {
    item_name: string;
    total_quantity: number;
    times_ordered: number;
    total_revenue: number;
    avg_unit_price: number;
}

export interface ItemsReport {
    top_items: TopItem[];
    total_items_ordered: number;
    total_unique_items_ordered: number;
}

export interface RevenueByStatus {
    status: string;
    total: number;
    count: number;
    average: number;
}

export interface RevenueReport {
    period_days: number;
    total_revenue: number;
    net_revenue: number;
    total_cancellation_fees: number;
    total_orders: number;
    average_order_value: number;
    revenue_by_status: RevenueByStatus[];
    daily_revenue: { date: string; total: number; order_count: number }[];
    cancelled_orders: {
        count: number;
        total_order_value: number;
        total_cancellation_fees: number;
    };
}

export interface PaymentMethodBreakdown {
    method: string;
    label: string;
    count: number;
    total: number;
}

export interface PaymentStatusBreakdown {
    status: string;
    count: number;
    total: number;
}

export interface RefundStats {
    total_refunds: number;
    total_amount: number;
    requested_count: number;
    pending_count: number;
    processing_count: number;
    processed_count: number;
    rejected_count: number;
}

export interface PaymentReport {
    period_days: number;
    total_payments: number;
    payment_method_breakdown: PaymentMethodBreakdown[];
    payment_status_breakdown: PaymentStatusBreakdown[];
    refund_stats: RefundStats;
    report_date: string;
}
