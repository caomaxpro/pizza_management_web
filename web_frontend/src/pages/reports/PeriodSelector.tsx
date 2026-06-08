import styles from "./Reports.module.scss";
import { PERIOD_OPTIONS } from "./helpers";

interface PeriodSelectorProps {
    value: string;
    onChange: (v: string) => void;
}

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
    return (
        <div className={styles.timeSelector}>
            <label>Period:</label>
            <div className={styles.buttonGroup}>
                {PERIOD_OPTIONS.map((d) => (
                    <button
                        key={d.key}
                        className={`${styles.timePeriodBtn} ${value === d.key ? styles.active : ""}`}
                        onClick={() => onChange(d.key)}
                    >
                        {d.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
