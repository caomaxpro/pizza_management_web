import styles from "./Auth.module.scss";

export default function Auth() {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>🔐 Authentication</h1>
                <p className={styles.subtitle}>
                    Manage authentication and security settings
                </p>
            </div>
            <div className={styles.content}>
                <p>Authentication settings page - Coming soon</p>
            </div>
        </div>
    );
}
