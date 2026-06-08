import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import styles from "./Sidebar.module.scss";
import {
    Pizza,
    Flask,
    ShoppingCart,
    ListBullets,
    ChartBar,
    Package,
    Receipt,
    User,
    CreditCard,
} from "@phosphor-icons/react";
import { Gear, SignOut, List } from "@phosphor-icons/react";
import * as customIcons from "@assets/icons";

import type { ReactNode } from "react";

interface MenuItemConfig {
    label: string;
    path: string;
    icon: ReactNode;
}

interface MenuSection {
    name: string;
    items: MenuItemConfig[];
}

const MENU_SECTIONS: MenuSection[] = [
    {
        name: "Dashboard",
        items: [
            {
                label: "Dashboard",
                path: "/dashboard",
                icon: <ChartBar size={18} />,
            },
        ],
    },
    {
        name: "Menu",
        items: [
            {
                label: "Ingredients",
                path: "/ingredients",
                icon: <Flask size={18} />,
            },
            { label: "Items", path: "/items", icon: <Pizza size={18} /> },
        ],
    },
    {
        name: "Order Management",
        items: [
            {
                label: "Orders",
                path: "/orders",
                icon: <ShoppingCart size={18} />,
            },
            {
                label: "Order Log",
                path: "/order_log",
                icon: <ListBullets size={18} />,
            },
        ],
    },
    {
        name: "Payment",
        items: [
            {
                label: "Payment Log",
                path: "/payment_log",
                icon: <CreditCard size={18} />,
            },
        ],
    },
    {
        name: "Inventory",
        items: [
            {
                label: "Inventory",
                path: "/inventory",
                icon: <Package size={18} />,
            },
            {
                label: "Purchase Orders",
                path: "/purchase_orders",
                icon: <Receipt size={18} />,
            },
        ],
    },
    {
        name: "Providers",
        items: [
            // example using local SVG exported from src/assets/icons/index.ts
            {
                label: "Providers",
                path: "/providers",
                icon: (
                    <img
                        src={customIcons.category}
                        alt="Providers"
                        width={18}
                        height={18}
                    />
                ),
            },
        ],
    },
    {
        name: "Reports",
        items: [
            {
                label: "Reports",
                path: "/reports",
                icon: <ChartBar size={18} />,
            },
        ],
    },
    {
        name: "User Management",
        items: [{ label: "Users", path: "/users", icon: <User size={18} /> }],
    },
];

interface SidebarProps {
    open: boolean;
    onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuthStore();

    const handleNavigation = (path: string) => {
        onClose();
        navigate(path);
    };

    const handleLogout = async () => {
        await logout();
        navigate("/login");
    };

    return (
        <>
            {/* Overlay for mobile */}
            {open && (
                <div
                    className={`${styles.overlay} ${!open ? styles.hidden : ""}`}
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`${styles.sidebar} ${open ? styles.open : styles.closed}`}
            >
                <div className={styles.scrollable}>
                    {/* Menu Sections */}
                    {MENU_SECTIONS.map((section, index) => (
                        <div key={section.name}>
                            {/* Section Items */}
                            <ul className={styles.nav}>
                                {section.items.map((item) => (
                                    <li
                                        key={item.path}
                                        className={styles.navItem}
                                    >
                                        <a
                                            href="#"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                handleNavigation(item.path);
                                            }}
                                            className={
                                                location.pathname === item.path
                                                    ? styles.active
                                                    : ""
                                            }
                                        >
                                            <span className={styles.icon}>
                                                {item.icon}
                                            </span>
                                            <span className={styles.label}>
                                                {item.label}
                                            </span>
                                        </a>
                                    </li>
                                ))}
                            </ul>

                            {/* Divider between sections (not after last section) */}
                            {index < MENU_SECTIONS.length - 1 && (
                                <div className={styles.divider} />
                            )}
                        </div>
                    ))}

                    {/* Divider before settings */}
                    <div className={styles.divider} />

                    {/* Settings & Logout */}
                    <ul className={styles.nav}>
                        <li className={styles.navItem}>
                            <a
                                href="#"
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleNavigation("/settings");
                                }}
                                className={
                                    location.pathname === "/settings"
                                        ? styles.active
                                        : ""
                                }
                            >
                                <span className={styles.icon}>
                                    <Gear size={18} />
                                </span>
                                <span className={styles.label}>Settings</span>
                            </a>
                        </li>
                        <li className={styles.navItem}>
                            <button onClick={handleLogout}>
                                <span className={styles.icon}>
                                    <SignOut size={18} />
                                </span>
                                <span className={styles.label}>Logout</span>
                            </button>
                        </li>
                    </ul>
                </div>
            </aside>
        </>
    );
}

interface SidebarToggleProps {
    onClick: () => void;
}

export function SidebarToggle({ onClick }: SidebarToggleProps) {
    return (
        <button
            className={styles.toggle}
            onClick={onClick}
            aria-label="Toggle sidebar"
        >
            <List size={18} />
        </button>
    );
}
