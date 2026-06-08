/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useMemo } from "react";
import styles from "./PaymentPhaseTimeline.module.scss";

export interface PaymentPhase {
    id: number;
    status: string;
    status_display: string;
    reason: string;
    metadata: Record<string, any>;
    created_at: string;
}

interface PaymentPhaseTimelineProps {
    phases: PaymentPhase[];
    currentStatus?: string;
    compact?: boolean;
}

const statusColorMap: Record<string, string> = {
    pending: "#f59e0b",
    processing: "#3b82f6",
    completed: "#10b981",
    failed: "#ef4444",
    refunded: "#6366f1",
};

const statusIconMap: Record<string, string> = {
    pending: "⏳",
    processing: "⚙️",
    completed: "✅",
    failed: "❌",
    refunded: "💰",
};

export const PaymentPhaseTimeline: React.FC<PaymentPhaseTimelineProps> = ({
    phases,
    currentStatus,
    compact = false,
}) => {
    const sortedPhases = useMemo(() => {
        return [...phases].sort(
            (a, b) =>
                new Date(a.created_at).getTime() -
                new Date(b.created_at).getTime(),
        );
    }, [phases]);

    if (!sortedPhases.length) {
        return (
            <div className={styles.emptyState}>
                <p>No payment phase history available</p>
            </div>
        );
    }

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat("en-CA", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            timeZone: "UTC",
        }).format(date);
    };

    const formatMetadata = (metadata: Record<string, any>) => {
        if (!metadata || Object.keys(metadata).length === 0) {
            return null;
        }

        const entries = Object.entries(metadata)
            .filter(([_, v]) => v !== null && v !== undefined)
            .map(([key, value]) => (
                <div key={key} className={styles.metadataEntry}>
                    <span className={styles.metadataKey}>{key}:</span>
                    <span className={styles.metadataValue}>
                        {typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value)}
                    </span>
                </div>
            ));

        return entries.length > 0 ? entries : null;
    };

    if (compact) {
        return (
            <div className={styles.compactTimeline}>
                {sortedPhases.map((phase, index) => (
                    <div key={phase.id} className={styles.compactItem}>
                        <div
                            className={styles.compactDot}
                            style={{
                                backgroundColor:
                                    statusColorMap[phase.status] || "#6b7280",
                            }}
                        />
                        <div className={styles.compactContent}>
                            <span className={styles.compactStatus}>
                                {phase.status_display}
                            </span>
                            <span className={styles.compactTime}>
                                {formatDate(phase.created_at)}
                            </span>
                            {phase.reason && (
                                <span className={styles.compactReason}>
                                    {phase.reason}
                                </span>
                            )}
                        </div>
                        {index < sortedPhases.length - 1 && (
                            <div className={styles.compactConnector} />
                        )}
                    </div>
                ))}
            </div>
        );
    }

    return (
        <div className={styles.timeline}>
            <div className={styles.header}>
                <h3>Payment History</h3>
                <span className={styles.phaseCount}>
                    {sortedPhases.length} phases
                </span>
            </div>

            <div className={styles.phases}>
                {sortedPhases.map((phase, index) => (
                    <div key={phase.id} className={styles.timelineItem}>
                        <div className={styles.leftSide}>
                            <div
                                className={styles.dot}
                                style={{
                                    backgroundColor:
                                        statusColorMap[phase.status] ||
                                        "#6b7280",
                                    boxShadow: `0 0 0 4px ${
                                        statusColorMap[phase.status] ||
                                        "#6b7280"
                                    }33`,
                                }}
                            >
                                {statusIconMap[phase.status] || "•"}
                            </div>
                            {index < sortedPhases.length - 1 && (
                                <div
                                    className={styles.connector}
                                    style={{
                                        backgroundColor: `${
                                            statusColorMap[phase.status] ||
                                            "#6b7280"
                                        }44`,
                                    }}
                                />
                            )}
                        </div>

                        <div className={styles.rightSide}>
                            <div className={styles.content}>
                                <div className={styles.header}>
                                    <h4 className={styles.status}>
                                        {phase.status_display}
                                    </h4>
                                    <span className={styles.timestamp}>
                                        {formatDate(phase.created_at)}
                                    </span>
                                </div>

                                {phase.reason && (
                                    <p className={styles.reason}>
                                        {phase.reason}
                                    </p>
                                )}

                                {formatMetadata(phase.metadata) && (
                                    <div className={styles.metadata}>
                                        {formatMetadata(phase.metadata)}
                                    </div>
                                )}
                            </div>

                            {index === sortedPhases.length - 1 &&
                                currentStatus && (
                                    <div className={styles.currentBadge}>
                                        Current
                                    </div>
                                )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PaymentPhaseTimeline;
