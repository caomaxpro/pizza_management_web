import { Gear } from "@phosphor-icons/react";
import styles from "./Settings.module.scss";

export default function Settings() {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>
                    <Gear size={24} /> Settings
                </h1>
                <p className={styles.subtitle}>
                    Manage system settings and preferences
                </p>
            </div>
            <div className={styles.content}>
                <p>Settings page - Coming soon</p>
            </div>
        </div>
    );
}
