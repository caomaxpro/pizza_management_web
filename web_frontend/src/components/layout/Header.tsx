import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { SidebarToggle } from "./Sidebar";
import styles from "./Header.module.scss";

interface HeaderProps {
    onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);

    const userInitials = user
        ? `${user.email?.split("@")[0]?.charAt(0) || "?"}`.toUpperCase()
        : "?";
    const getRoleDisplay = (role?: string) => {
        switch (role) {
            case "admin":
                return { emoji: "👤", label: "Admin" };
            case "manager":
                return { emoji: "🎯", label: "Manager" };
            case "staff":
                return { emoji: "👥", label: "Staff" };
            case "user":
                return { emoji: "👤", label: "User" };
            default:
                return { emoji: "👤", label: "User" };
        }
    };

    const roleDisplay = getRoleDisplay(user?.role);
    const handleLogout = async () => {
        setMenuOpen(false);
        await logout();
        navigate("/login");
    };

    const handleSettings = () => {
        setMenuOpen(false);
        navigate("/settings");
    };

    return (
        <header className={styles.header}>
            {/* Left: Logo */}
            <div className={styles.logo}>
                <span className={styles.emoji}>🍕</span>
                <span className={styles.text}>Pizza Admin</span>
            </div>

            {/* Center: Navigation */}
            <nav className={styles.nav}>
                {/* This space can be used for main navigation items if needed */}
            </nav>

            {/* Right: User Section */}
            <div className={styles.userSection}>
                {user && (
                    <>
                        <div className={styles.userBadge}>
                            {roleDisplay.emoji} {roleDisplay.label}
                        </div>

                        <div className={styles.userMenu}>
                            <button
                                className={styles.menuButton}
                                onClick={() => setMenuOpen(!menuOpen)}
                                aria-expanded={menuOpen}
                            >
                                <div className={styles.avatar}>
                                    {userInitials}
                                </div>
                                <div className={styles.userInfo}>
                                    <p className={styles.name}>
                                        {user.email?.split("@")[0]}
                                    </p>
                                    <p className={styles.role}>
                                        {roleDisplay.label}
                                    </p>
                                </div>
                                <span
                                    className={`${styles.dropdownIcon} ${menuOpen ? styles.open : ""}`}
                                >
                                    ▼
                                </span>
                            </button>

                            {/* Dropdown Menu */}
                            <div
                                className={`${styles.dropdown} ${menuOpen ? "" : styles.hidden}`}
                            >
                                <ul className={styles.dropdownMenu}>
                                    <li className={styles.dropdownItem}>
                                        <button onClick={handleSettings}>
                                            Settings
                                        </button>
                                    </li>
                                    <li className={styles.dropdownItem}>
                                        <button onClick={handleLogout}>
                                            Logout
                                        </button>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </>
                )}

                {/* Mobile Menu Toggle */}
                <SidebarToggle onClick={onMenuClick} />
            </div>
        </header>
    );
}
