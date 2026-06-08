import { useRef, useEffect } from "react";
import type { ReactNode } from "react";
import styles from "../../pages/users/Users.module.scss";

interface ModalProps {
    isOpen: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
    width?: string;
    titleStyle?: React.CSSProperties;
}

export default function Modal({
    isOpen,
    title,
    children,
    onClose,
    width = "90%",
    titleStyle,
}: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;

        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };

        document.addEventListener("keydown", handleEscape);
        document.body.style.overflow = "hidden";

        return () => {
            document.removeEventListener("keydown", handleEscape);
            document.body.style.overflow = "";
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className={styles.modalBackdrop} onClick={onClose}>
            <div
                className={styles.modalContent}
                onClick={(e) => e.stopPropagation()}
                ref={modalRef}
                style={{ width, maxWidth: "1400px" }}
            >
                <div className={styles.modalHeader}>
                    <h2 className={styles.modalTitle} style={titleStyle}>
                        {title}
                    </h2>
                    <button
                        className={styles.modalClose}
                        onClick={onClose}
                        aria-label="Close modal"
                    >
                        ✕
                    </button>
                </div>
                <div className={styles.modalBody}>{children}</div>
            </div>
        </div>
    );
}
