import { useState } from "react";
import { Input, Select, Button } from "../../components/ui";
import styles from "./UserForm.module.scss";
import type { User } from "../../types/user";

export interface UserFormData {
    email: string;
    username: string;
    password?: string;
    role: "admin" | "manager" | "staff" | "user";
    is_active: boolean;
}

export interface UserFormProps {
    /** Pass an existing user to enable edit mode; omit for create mode. */
    user?: User;
    onSubmit: (data: UserFormData) => void;
    onCancel: () => void;
}

export default function UserForm({ user, onSubmit, onCancel }: UserFormProps) {
    const isEdit = Boolean(user);
    const [email, setEmail] = useState(user?.email ?? "");
    const [username, setUsername] = useState(user?.username ?? "");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<UserFormData["role"]>(
        user?.role ?? "staff",
    );
    const [isActive, setIsActive] = useState(user?.is_active ?? true);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const data: UserFormData = {
            email,
            username,
            role,
            is_active: isActive,
        };
        if (!isEdit || password) data.password = password;
        onSubmit(data);
    };

    return (
        <form className={styles.form} onSubmit={handleSubmit}>
            <h3 className={styles.title}>
                {isEdit ? "Edit User" : "Create User"}
            </h3>

            <div className={styles.formGroup}>
                <label>Email</label>
                <Input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    type="email"
                    required
                />
            </div>

            <div className={styles.formGroup}>
                <label>Username</label>
                <Input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required={!isEdit}
                    placeholder={isEdit ? "Leave blank to keep unchanged" : ""}
                />
            </div>

            <div className={styles.formGroup}>
                <label>{isEdit ? "New Password (optional)" : "Password"}</label>
                <Input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    type="password"
                    required={!isEdit}
                    placeholder={isEdit ? "Leave blank to keep unchanged" : ""}
                />
            </div>

            <div className={styles.formGroup}>
                <label>Role</label>
                <Select
                    value={role}
                    onChange={(v) =>
                        setRole(
                            (typeof v === "string"
                                ? v
                                : v[0]) as UserFormData["role"],
                        )
                    }
                    options={[
                        { value: "admin", label: "Admin" },
                        { value: "manager", label: "Manager" },
                        { value: "staff", label: "Staff" },
                        { value: "user", label: "Customer" },
                    ]}
                />
            </div>

            <div className={styles.formGroup}>
                <label>Status</label>
                <Select
                    value={isActive ? "active" : "inactive"}
                    onChange={(v) => {
                        const val = typeof v === "string" ? v : v[0];
                        setIsActive(val === "active");
                    }}
                    options={[
                        { value: "active", label: "Active" },
                        { value: "inactive", label: "Inactive" },
                    ]}
                />
            </div>

            <div className={styles.actions}>
                <Button type="submit" variant="primary">
                    Save
                </Button>
                <Button type="button" variant="outline" onClick={onCancel}>
                    Cancel
                </Button>
            </div>
        </form>
    );
}
