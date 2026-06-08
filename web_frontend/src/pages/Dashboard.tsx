import { useEffect, useMemo } from "react";
import {
    Dot,
    CheckCircle,
    XCircle,
    PlusCircle,
    Gear,
} from "@phosphor-icons/react";
import { useAuthStore } from "../store/authStore";
import { useItemStore } from "../store/itemStore";
import { useIngredientStore } from "../store/ingredientStore";
import styles from "./dashboard/Dashboard.module.scss";

export default function Dashboard() {
    const { user } = useAuthStore();
    const { items: cacheItems, fetchAllItems } = useItemStore();
    const { ingredients: cacheIngredients, fetchAllIngredients } =
        useIngredientStore();

    // Fetch data on mount
    useEffect(() => {
        fetchAllItems();
        fetchAllIngredients();
    }, [fetchAllItems, fetchAllIngredients]);

    // Calculate stats with useMemo
    const stats = useMemo(() => {
        const activeItems = cacheItems.filter((item) => item.is_active).length;
        const inactiveItems = cacheItems.filter(
            (item) => !item.is_active,
        ).length;

        return {
            totalItems: cacheItems.length,
            totalIngredients: cacheIngredients.length,
            activeItems,
            inactiveItems,
        };
    }, [cacheItems, cacheIngredients]);

    // User initials
    const userInitials = user
        ? `${user.email?.split("@")[0]?.charAt(0) || "?"}`.toUpperCase()
        : "?";

    // User display name
    const userName = user?.email?.split("@")[0] || "User";
    const userRole = user?.is_superuser ? "Administrator" : "Staff Member";

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h1>📊 Dashboard</h1>
                    <p className={styles.subtitle}>
                        Welcome back to Pizza Admin Panel
                    </p>
                </div>
            </div>

            {/* User Profile Card */}
            {user && (
                <div className={styles.userProfileCard}>
                    <div className={styles.profileContent}>
                        <div className={styles.avatar}>{userInitials}</div>
                        <div className={styles.userInfo}>
                            <h2 className={styles.userName}>{userName}</h2>
                            <p className={styles.userEmail}>{user.email}</p>
                            <div className={styles.roleContainer}>
                                <span
                                    className={`${styles.roleBadge} ${user.is_superuser ? styles.admin : styles.staff}`}
                                >
                                    {user.is_superuser
                                        ? "👤 Admin"
                                        : "👥 Staff"}
                                </span>
                                <p className={styles.roleText}>{userRole}</p>
                            </div>
                        </div>
                    </div>
                    <div className={styles.profileStats}>
                        <div className={styles.stat}>
                            <span className={styles.statLabel}>Status</span>
                            <span className={styles.statValue}>
                                <Dot size={16} weight="fill" /> Active
                            </span>
                        </div>
                        <div className={styles.stat}>
                            <span className={styles.statLabel}>Last Login</span>
                            <span className={styles.statValue}>Today</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Stats Grid */}
            <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <div className={styles.statIcon}>🍕</div>
                    <div className={styles.statDetails}>
                        <h3>Total Items</h3>
                        <p className={styles.statNumber}>{stats.totalItems}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon}>🥘</div>
                    <div className={styles.statDetails}>
                        <h3>Ingredients</h3>
                        <p className={styles.statNumber}>
                            {stats.totalIngredients}
                        </p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                        <CheckCircle size={32} weight="fill" />
                    </div>
                    <div className={styles.statDetails}>
                        <h3>Active Items</h3>
                        <p className={styles.statNumber}>{stats.activeItems}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                        <XCircle size={32} weight="fill" />
                    </div>
                    <div className={styles.statDetails}>
                        <h3>Inactive Items</h3>
                        <p className={styles.statNumber}>
                            {stats.inactiveItems}
                        </p>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className={styles.quickActionsSection}>
                <h2>Quick Actions</h2>
                <div className={styles.actionButtons}>
                    <a href="/items/create" className={styles.actionBtn}>
                        <span className={styles.actionIcon}>
                            <PlusCircle size={20} weight="fill" />
                        </span>
                        <span className={styles.actionLabel}>New Item</span>
                    </a>
                    <a href="/ingredients/create" className={styles.actionBtn}>
                        <span className={styles.actionIcon}>
                            <PlusCircle size={20} weight="fill" />
                        </span>
                        <span className={styles.actionLabel}>
                            New Ingredient
                        </span>
                    </a>
                    <a href="/items" className={styles.actionBtn}>
                        <span className={styles.actionIcon}>📋</span>
                        <span className={styles.actionLabel}>View Items</span>
                    </a>
                    <a href="/ingredients" className={styles.actionBtn}>
                        <span className={styles.actionIcon}>📋</span>
                        <span className={styles.actionLabel}>
                            View Ingredients
                        </span>
                    </a>
                </div>
            </div>

            {/* Overview Cards */}
            <div className={styles.overviewSection}>
                <h2>Overview</h2>
                <div className={styles.overviewCards}>
                    <div className={styles.overviewCard}>
                        <h3>📊 Menu Management</h3>
                        <p>
                            Manage all pizza items and ingredients in your menu.
                            Total items: <strong>{stats.totalItems}</strong>
                        </p>
                        <a href="/items" className={styles.cardLink}>
                            Go to Items →
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>🥘 Ingredient Inventory</h3>
                        <p>
                            Track and manage your ingredient stock. Total
                            ingredients:
                            <strong> {stats.totalIngredients}</strong>
                        </p>
                        <a href="/ingredients" className={styles.cardLink}>
                            Go to Ingredients →
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>🛒 Orders</h3>
                        <p>
                            View and manage customer orders in real-time. Stay
                            on top of your business.
                        </p>
                        <a href="/orders" className={styles.cardLink}>
                            Go to Orders →
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>
                            <Gear size={20} /> Settings
                        </h3>
                        <p>
                            Configure your admin preferences, update profile
                            information, and manage account settings.
                        </p>
                        <a href="/settings" className={styles.cardLink}>
                            Go to Settings →
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
