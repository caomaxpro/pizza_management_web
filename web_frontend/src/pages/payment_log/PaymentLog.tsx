import React, { useState, useEffect } from "react";
import styles from "./PaymentLog.module.scss";
import API from "../../services/api";
import PaymentPhaseTimeline from "../../components/payments/PaymentPhaseTimeline";
import type { PaymentPhase } from "../../components/payments/PaymentPhaseTimeline";

interface PaymentPhaseData extends PaymentPhase {}

interface Payment {
    id: number;
    order: number;
    method: string;
    method_display: string;
    status: string;
    status_display: string;
    amount: number;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    phases: PaymentPhaseData[];
}

export default function PaymentLog() {
    const [payments, setPayments] = useState<Payment[]>([]);
    const [selectedPayment, setSelectedPayment] = useState<Payment | null>(
        null,
    );
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        fetchPayments();
    }, []);

    const fetchPayments = async () => {
        try {
            setLoading(true);
            const response = await API.get("/payments/");
            setPayments(
                Array.isArray(response.data)
                    ? response.data
                    : response.data.results || [],
            );
            setError(null);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to fetch payments",
            );
            console.error("Error fetching payments:", err);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-CA", {
            style: "currency",
            currency: "CAD",
        }).format(amount);
    };

    const formatDate = (dateStr: string) => {
        return new Intl.DateTimeFormat("en-CA", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date(dateStr));
    };

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            pending: "#f59e0b",
            processing: "#3b82f6",
            completed: "#10b981",
            failed: "#ef4444",
            refunded: "#6366f1",
        };
        return colors[status] || "#6b7280";
    };

    const filteredPayments = payments.filter(
        (p) =>
            p.id.toString().includes(searchTerm) ||
            p.order.toString().includes(searchTerm) ||
            p.method_display.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.status_display.toLowerCase().includes(searchTerm.toLowerCase()),
    );

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <h1>💰 Payment Log</h1>
                </div>
                <div className={styles.loadingState}>Loading payments...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <h1>💰 Payment Log</h1>
                </div>
                <div className={styles.errorState}>{error}</div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>💰 Payment Log</h1>
                <p className={styles.subtitle}>
                    Track all payment transactions and their status history
                </p>
            </div>

            <div className={styles.content}>
                {!selectedPayment ? (
                    <>
                        <div className={styles.searchBar}>
                            <input
                                type="text"
                                placeholder="Search by payment ID, order ID, method, or status..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className={styles.searchInput}
                            />
                            <span className={styles.resultCount}>
                                {filteredPayments.length} payment
                                {filteredPayments.length !== 1 ? "s" : ""}
                            </span>
                        </div>

                        {filteredPayments.length === 0 ? (
                            <div className={styles.emptyState}>
                                <p>No payments found</p>
                            </div>
                        ) : (
                            <div className={styles.paymentsTable}>
                                <div className={styles.tableHeader}>
                                    <div className={styles.colId}>ID</div>
                                    <div className={styles.colOrder}>Order</div>
                                    <div className={styles.colMethod}>
                                        Method
                                    </div>
                                    <div className={styles.colAmount}>
                                        Amount
                                    </div>
                                    <div className={styles.colStatus}>
                                        Status
                                    </div>
                                    <div className={styles.colDate}>Date</div>
                                    <div className={styles.colAction}>
                                        Action
                                    </div>
                                </div>

                                <div className={styles.tableBody}>
                                    {filteredPayments.map((payment) => (
                                        <div
                                            key={payment.id}
                                            className={styles.tableRow}
                                        >
                                            <div className={styles.colId}>
                                                #{payment.id}
                                            </div>
                                            <div className={styles.colOrder}>
                                                #{payment.order}
                                            </div>
                                            <div className={styles.colMethod}>
                                                {payment.method_display}
                                            </div>
                                            <div className={styles.colAmount}>
                                                {formatCurrency(payment.amount)}
                                            </div>
                                            <div className={styles.colStatus}>
                                                <span
                                                    className={
                                                        styles.statusBadge
                                                    }
                                                    style={{
                                                        backgroundColor:
                                                            getStatusColor(
                                                                payment.status,
                                                            ) + "22",
                                                        color: getStatusColor(
                                                            payment.status,
                                                        ),
                                                    }}
                                                >
                                                    {payment.status_display}
                                                </span>
                                            </div>
                                            <div className={styles.colDate}>
                                                {formatDate(payment.created_at)}
                                            </div>
                                            <div className={styles.colAction}>
                                                <button
                                                    className={styles.detailBtn}
                                                    onClick={() =>
                                                        setSelectedPayment(
                                                            payment,
                                                        )
                                                    }
                                                >
                                                    View Details
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div className={styles.detailView}>
                        <button
                            className={styles.backBtn}
                            onClick={() => setSelectedPayment(null)}
                        >
                            ← Back to List
                        </button>

                        <div className={styles.detailCard}>
                            <div className={styles.detailHeader}>
                                <div>
                                    <h2>Payment #{selectedPayment.id}</h2>
                                    <p className={styles.detailSubtitle}>
                                        Order #{selectedPayment.order}
                                    </p>
                                </div>
                                <div className={styles.detailStatus}>
                                    <span
                                        className={styles.statusBadge}
                                        style={{
                                            backgroundColor:
                                                getStatusColor(
                                                    selectedPayment.status,
                                                ) + "22",
                                            color: getStatusColor(
                                                selectedPayment.status,
                                            ),
                                        }}
                                    >
                                        {selectedPayment.status_display}
                                    </span>
                                </div>
                            </div>

                            <div className={styles.detailInfo}>
                                <div className={styles.infoRow}>
                                    <span className={styles.label}>Amount</span>
                                    <span className={styles.value}>
                                        {formatCurrency(selectedPayment.amount)}
                                    </span>
                                </div>
                                <div className={styles.infoRow}>
                                    <span className={styles.label}>
                                        Payment Method
                                    </span>
                                    <span className={styles.value}>
                                        {selectedPayment.method_display}
                                    </span>
                                </div>
                                <div className={styles.infoRow}>
                                    <span className={styles.label}>
                                        Created
                                    </span>
                                    <span className={styles.value}>
                                        {formatDate(selectedPayment.created_at)}
                                    </span>
                                </div>
                                {selectedPayment.completed_at && (
                                    <div className={styles.infoRow}>
                                        <span className={styles.label}>
                                            Completed
                                        </span>
                                        <span className={styles.value}>
                                            {formatDate(
                                                selectedPayment.completed_at,
                                            )}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>

                        <PaymentPhaseTimeline
                            phases={selectedPayment.phases}
                            currentStatus={selectedPayment.status}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
