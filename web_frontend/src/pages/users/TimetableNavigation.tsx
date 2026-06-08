import { Button } from "../../components/ui";
import { formatWeekRange } from "./helpers";
import styles from "./UserTimetable.module.scss";

interface TimetableNavigationProps {
    weekMonday: Date;
    onPrevWeek: () => void;
    onNextWeek: () => void;
    onToday: () => void;
}

export default function TimetableNavigation({
    weekMonday,
    onPrevWeek,
    onNextWeek,
    onToday,
}: TimetableNavigationProps) {
    return (
        <div className={styles.nav}>
            <Button variant="secondary" onClick={onPrevWeek}>
                ← Prev
            </Button>
            <span className={styles.weekLabel}>
                {formatWeekRange(weekMonday)}
            </span>
            <Button variant="secondary" onClick={onNextWeek}>
                Next →
            </Button>
            <Button
                variant="secondary"
                onClick={onToday}
                className={styles.todayBtn}
            >
                Today
            </Button>
        </div>
    );
}
