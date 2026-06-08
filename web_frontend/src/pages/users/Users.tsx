import { useState } from "react";
import {
    Users as UsersIcon,
    User as UserIcon,
    Calendar as CalendarIcon,
} from "@phosphor-icons/react";
import styles from "./Users.module.scss";
import UserListTab from "./UserListTab";
import UserTimetable from "./UserTimetable";

export default function Users() {
    const [activeTab, setActiveTab] = useState<"list" | "timetable">("list");

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h1>
                        <UsersIcon size={24} weight="bold" /> Users
                    </h1>
                    <p className={styles.subtitle}>
                        Manage users and permissions
                    </p>
                </div>
            </div>

            {/* ── Tabs ── */}
            <div className={styles.tabs}>
                <button
                    className={`${styles.tab} ${activeTab === "list" ? styles.tabActive : ""}`}
                    onClick={() => setActiveTab("list")}
                >
                    <UserIcon size={16} /> User List
                </button>
                <button
                    className={`${styles.tab} ${activeTab === "timetable" ? styles.tabActive : ""}`}
                    onClick={() => setActiveTab("timetable")}
                >
                    <CalendarIcon size={16} /> Timetable
                </button>
            </div>

            {activeTab === "timetable" ? <UserTimetable /> : <UserListTab />}
        </div>
    );
}
