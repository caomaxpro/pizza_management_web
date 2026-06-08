import { useEffect, useMemo } from "react";
import { useAuthStore } from "../../store/authStore";
import { useItemStore } from "../../store/itemStore";
import { useIngredientStore } from "../../store/ingredientStore";
import {
    User,
    Pizza,
    Flask,
    CheckCircle,
    XCircle,
    PlusCircle,
    ListBullets,
    ShoppingCart,
    Gear,
    CaretRight,
    ChartPieSlice,
    Clock,
    Dot,
} from "@phosphor-icons/react";
import * as customIcons from "@assets/icons";
import styles from "./Dashboard.module.scss";

export default function Dashboard() {
    const { user, getCurrentUser } = useAuthStore();
    const { items: cacheItems, fetchAllItems } = useItemStore();
    const { ingredients: cacheIngredients, fetchAllIngredients } =
        useIngredientStore();

    // Fetch data on mount
    useEffect(() => {
        fetchAllItems();
        fetchAllIngredients();
        getCurrentUser(); // Ensure we have the latest user data with all fields
    }, [fetchAllItems, fetchAllIngredients, getCurrentUser]);

    // Debug: Log user data to console
    useEffect(() => {
        if (user) {
            console.log("[Dashboard] User object:", user);
            console.log("[Dashboard] is_superuser:", user.is_superuser);
            console.log("[Dashboard] is_staff:", user.is_staff);
            console.log("[Dashboard] role:", user.role);
        }
    }, [user]);

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
    const userRole =
        user?.role === "admin"
            ? "Administrator"
            : user?.role === "manager"
              ? "Manager"
              : "Staff Member";

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h1>
                        <ChartPieSlice
                            size={40}
                            weight="fill"
                            className={styles.titleIcon}
                        />{" "}
                        Dashboard
                    </h1>
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
                                    className={`${styles.roleBadge} ${user.role === "admin" ? styles.admin : styles.staff}`}
                                >
                                    <User size={14} weight="bold" />{" "}
                                    {user.role === "admin"
                                        ? "Admin"
                                        : user.role === "manager"
                                          ? "Manager"
                                          : "Staff"}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className={styles.profileStats}>
                        <div className={styles.stat}>
                            <span className={styles.statLabel}>Role</span>
                            <span className={styles.statValue}>
                                <Dot
                                    size={12}
                                    weight="fill"
                                    color={
                                        user.role === "admin"
                                            ? "#667eea"
                                            : user.role === "manager"
                                              ? "#f59e0b"
                                              : "#10b981"
                                    }
                                />
                                {userRole}
                            </span>
                        </div>
                        <div className={styles.stat}>
                            <span className={styles.statLabel}>Last Login</span>
                            <span className={styles.statValue}>
                                <Clock size={16} /> Today
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Stats Grid */}
            <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <div
                        className={styles.statIcon}
                        style={{
                            background: "rgba(234, 88, 12, 0.1)",
                            color: "#ea580c",
                        }}
                    >
                        <img
                            src={customIcons.pizza}
                            width={32}
                            height={32}
                            alt="Pizza"
                        />
                    </div>
                    <div className={styles.statDetails}>
                        <h3>Total Items</h3>
                        <p className={styles.statNumber}>{stats.totalItems}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div
                        className={styles.statIcon}
                        style={{
                            background: "rgba(16, 185, 129, 0.1)",
                            color: "#10b981",
                        }}
                    >
                        <img
                            src={customIcons.ingredient}
                            width={32}
                            height={32}
                            alt="Ingredient"
                        />
                    </div>
                    <div className={styles.statDetails}>
                        <h3>Ingredients</h3>
                        <p className={styles.statNumber}>
                            {stats.totalIngredients}
                        </p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div
                        className={styles.statIcon}
                        style={{
                            background: "rgba(59, 130, 246, 0.1)",
                            color: "#3b82f6",
                        }}
                    >
                        <CheckCircle size={32} weight="duotone" />
                    </div>
                    <div className={styles.statDetails}>
                        <h3>Active Items</h3>
                        <p className={styles.statNumber}>{stats.activeItems}</p>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div
                        className={styles.statIcon}
                        style={{
                            background: "rgba(239, 68, 68, 0.1)",
                            color: "#ef4444",
                        }}
                    >
                        <XCircle size={32} weight="duotone" />
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
                        <PlusCircle size={24} weight="duotone" />
                        <span className={styles.actionLabel}>New Item</span>
                    </a>
                    <a href="/ingredients/create" className={styles.actionBtn}>
                        <PlusCircle size={24} weight="duotone" />
                        <span className={styles.actionLabel}>
                            New Ingredient
                        </span>
                    </a>
                    <a href="/items" className={styles.actionBtn}>
                        <ListBullets size={24} weight="duotone" />
                        <span className={styles.actionLabel}>View Items</span>
                    </a>
                    <a href="/ingredients" className={styles.actionBtn}>
                        <ListBullets size={24} weight="duotone" />
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
                        <h3>
                            <Pizza size={24} weight="duotone" /> Menu Management
                        </h3>
                        <p>
                            Manage all pizza items and ingredients in your menu.
                            Total items: <strong>{stats.totalItems}</strong>
                        </p>
                        <a href="/items" className={styles.cardLink}>
                            Go to Items <CaretRight size={16} />
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>
                            <Flask size={24} weight="duotone" /> Ingredient
                            Inventory
                        </h3>
                        <p>
                            Track and manage your ingredient stock. Total
                            ingredients:
                            <strong> {stats.totalIngredients}</strong>
                        </p>
                        <a href="/ingredients" className={styles.cardLink}>
                            Go to Ingredients <CaretRight size={16} />
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>
                            <ShoppingCart size={24} weight="duotone" /> Orders
                        </h3>
                        <p>
                            View and manage customer orders in real-time. Stay
                            on top of your business.
                        </p>
                        <a href="/orders" className={styles.cardLink}>
                            Go to Orders <CaretRight size={16} />
                        </a>
                    </div>

                    <div className={styles.overviewCard}>
                        <h3>
                            <Gear size={24} weight="duotone" /> Settings
                        </h3>
                        <p>
                            Configure your admin preferences, update profile
                            information, and manage account settings.
                        </p>
                        <a href="/settings" className={styles.cardLink}>
                            Go to Settings <CaretRight size={16} />
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
