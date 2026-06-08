/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import styles from "./Login.module.scss";

export default function Login() {
    const navigate = useNavigate();
    const { login, isLoading, error, clearError, isAuthenticated } =
        useAuthStore();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [localError, setLocalError] = useState("");

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/dashboard");
        }
    }, [isAuthenticated, navigate]);

    const handleTogglePassword = () => {
        setShowPassword(!showPassword);
    };

    const handleClearError = () => {
        setLocalError("");
        clearError();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError("");

        // Validation
        if (!email.trim()) {
            setLocalError("Please enter your email");
            return;
        }

        if (!password.trim()) {
            setLocalError("Please enter your password");
            return;
        }

        if (!email.includes("@")) {
            setLocalError("Please enter a valid email");
            return;
        }

        try {
            await login({ email, password });
            navigate("/dashboard");
        } catch (err) {
            // Error is handled by the store
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div className={styles.header}>
                    <span className={styles.emoji}>🍕</span>
                    <h1 className={styles.title}>Welcome Back</h1>
                    <p className={styles.subtitle}>
                        Sign in to manage your pizzeria
                    </p>
                </div>

                <form className={styles.form} onSubmit={handleSubmit}>
                    {(error || localError) && (
                        <div className={styles.errorBox}>
                            <span>{error || localError}</span>
                            <button
                                type="button"
                                onClick={handleClearError}
                                className={styles.errorCloseBtn}
                            >
                                ✕
                            </button>
                        </div>
                    )}

                    <div className={styles.formGroup}>
                        <label className={styles.label}>
                            <span>📧</span>
                            Email
                        </label>
                        <input
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={isLoading}
                            className={styles.input}
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>
                            <span>🔐</span>
                            Password
                        </label>
                        <div className={styles.passwordWrapper}>
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isLoading}
                                className={styles.input}
                            />
                            <span className={styles.passwordIcon}>🔑</span>
                            <button
                                type="button"
                                onClick={handleTogglePassword}
                                disabled={isLoading}
                                className={styles.togglePasswordBtn}
                            >
                                {showPassword ? "👁️‍🗨️" : "👁️"}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className={styles.submitBtn}
                        onMouseEnter={(e) => {
                            if (!isLoading)
                                e.currentTarget.classList.add(styles.btnHover);
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.classList.remove(styles.btnHover);
                        }}
                    >
                        {isLoading ? (
                            <div className={styles.loadingBox}>
                                <span className={styles.spinner} />
                                Signing in...
                            </div>
                        ) : (
                            "Sign In"
                        )}
                    </button>
                </form>

                <div className={styles.demoInfo}>
                    <p>Demo credentials: admin@example.com / password</p>
                </div>
            </div>
        </div>
    );
}
