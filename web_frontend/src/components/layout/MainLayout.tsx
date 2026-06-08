/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState } from "react";
import styles from "./MainLayout.module.scss";
import Header from "./Header";
import Sidebar from "./Sidebar";

interface MainLayoutProps {
    children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const handleSidebarToggle = () => {
        setSidebarOpen(!sidebarOpen);
    };

    const handleSidebarClose = () => {
        setSidebarOpen(false);
    };

    return (
        <div className={styles.mainLayout}>
            {/* Header */}
            <div className={styles.header}>
                <Header onMenuClick={handleSidebarToggle} />
            </div>

            {/* Main Content Area */}
            <div className={styles.content}>
                {/* Sidebar - Desktop only or Mobile overlay */}
                <div className={styles.sidebar}>
                    <Sidebar open={sidebarOpen} onClose={handleSidebarClose} />
                </div>

                {/* Content Area with proper scrolling */}
                <div className={styles.contentArea}>
                    {/* Scrollable Content */}
                    <div className={styles.scrollable}>
                        {/* Content Wrapper with Responsive Padding */}
                        <div className={styles.wrapper}>{children}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
