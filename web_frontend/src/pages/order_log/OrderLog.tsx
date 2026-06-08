import styles from "./OrderLog.module.scss";

export default function OrderLog() {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>📋 Order Log</h1>
                <p className={styles.subtitle}>
                    View detailed order history and logs
                </p>
            </div>
            <div className={styles.content}>
                <p>Order log page - Coming soon</p>
            </div>
        </div>
    );
}
