import { useState } from "react";
import CustomForm2 from "../../components/form/CustomForm2";
import TextField from "../../components/form/fields/TextField";
import SelectField from "../../components/form/fields/SelectField";
import Modal from "../../components/layout/Modal";
import styles from "./Users.module.scss";
import { usersAPI } from "../../services/users";
import type { User } from "../../types/user";
import type { FormValues } from "../../components/form/formContext";

interface Props {
    isOpen: boolean;
    user?: User | null; // null/undefined → create mode
    onClose: () => void;
    onSuccess: (user: User) => void;
}

export default function UserFormModal({
    isOpen,
    user,
    onClose,
    onSuccess,
}: Props) {
    const isEdit = Boolean(user);
    const [actionError, setActionError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleClose = () => {
        setActionError(null);
        onClose();
    };

    const handleSubmit = async (values: FormValues) => {
        setActionError(null);
        setIsLoading(true);
        try {
            if (isEdit && user) {
                const payload: Parameters<typeof usersAPI.update>[1] = {
                    email: values.email,
                    role: values.role,
                    is_active: values.is_active === "active",
                };
                if (values.password) {
                    (payload as Record<string, unknown>).password =
                        values.password;
                }
                const res = await usersAPI.update(user.id, payload);
                onSuccess(res.data);
            } else {
                const res = await usersAPI.create({
                    email: values.email,
                    username: values.username,
                    password: values.password ?? "",
                    role: values.role,
                    is_active: values.is_active === "active",
                });
                onSuccess(res.data);
            }
            handleClose();
        } catch (err: unknown) {
            const apiErr = err as {
                response?: { data?: Record<string, unknown> };
            };
            const detail =
                apiErr?.response?.data?.detail ??
                Object.values(apiErr?.response?.data ?? {})[0];
            setActionError(
                typeof detail === "string"
                    ? detail
                    : isEdit
                      ? "Failed to update user."
                      : "Failed to create user.",
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            title={isEdit ? "Edit User" : "Create New User"}
            onClose={handleClose}
        >
            {actionError && (
                <div className={styles.error} style={{ marginBottom: 16 }}>
                    {actionError}
                </div>
            )}
            <CustomForm2
                fields={[
                    <TextField
                        key="email"
                        name="email"
                        label="Email"
                        type="email"
                        required
                        placeholder="user@example.com"
                        value=""
                        onChange={() => {}}
                    />,
                    <TextField
                        key="username"
                        name="username"
                        label="Username"
                        required={!isEdit}
                        placeholder={isEdit ? undefined : "john_doe"}
                        value=""
                        onChange={() => {}}
                    />,
                    <TextField
                        key="password"
                        name="password"
                        label={isEdit ? "New Password (optional)" : "Password"}
                        type="password"
                        required={!isEdit}
                        placeholder={
                            isEdit
                                ? "Leave blank to keep unchanged"
                                : "••••••••"
                        }
                        value=""
                        onChange={() => {}}
                    />,
                    <SelectField
                        key="role"
                        name="role"
                        label="Role"
                        value=""
                        onChange={() => {}}
                        options={[
                            { value: "admin", label: "Admin" },
                            { value: "manager", label: "Manager" },
                            { value: "staff", label: "Staff" },
                            { value: "user", label: "Customer" },
                        ]}
                    />,
                    <SelectField
                        key="is_active"
                        name="is_active"
                        label="Status"
                        value=""
                        onChange={() => {}}
                        options={[
                            { value: "active", label: "Active" },
                            { value: "inactive", label: "Inactive" },
                        ]}
                    />,
                ]}
                initialValues={{
                    email: user?.email ?? "",
                    username: user?.username ?? "",
                    password: "",
                    role: user?.role ?? "staff",
                    is_active: user
                        ? user.is_active
                            ? "active"
                            : "inactive"
                        : "active",
                }}
                onSubmit={handleSubmit}
                isLoading={isLoading}
                submitLabel={isEdit ? "Save" : "Create"}
                onCancel={handleClose}
            />
        </Modal>
    );
}
