import React from "react";
import styles from "./Pagination.module.scss";

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    pageSizeOptions?: number[];
    /** How many page number buttons to show around the current page */
    siblingCount?: number;
}

function getPageRange(
    current: number,
    total: number,
    siblings: number,
): number[] {
    const delta = siblings + 1;
    const left = Math.max(1, current - delta);
    const right = Math.min(total, current + delta);
    const pages: number[] = [];
    for (let i = left; i <= right; i++) pages.push(i);
    return pages;
}

export default function Pagination({
    currentPage,
    totalPages,
    pageSize,
    totalCount,
    onPageChange,
    onPageSizeChange,
    pageSizeOptions = [10, 20, 50, 100],
    siblingCount = 1,
}: PaginationProps) {
    const startItem = totalCount > 0 ? (currentPage - 1) * pageSize + 1 : 0;
    const endItem = Math.min(currentPage * pageSize, totalCount);
    const pages = getPageRange(currentPage, totalPages, siblingCount);

    return (
        <div className={styles.pagination}>
            {/* Left: count info + page size */}
            <div className={styles.info}>
                <span className={styles.countText}>
                    Showing {startItem} &ndash; {endItem} of {totalCount} items
                </span>
                <select
                    className={styles.pageSizeSelect}
                    value={pageSize}
                    onChange={onPageSizeChange}
                >
                    {pageSizeOptions.map((s) => (
                        <option key={s} value={s}>
                            {s} per page
                        </option>
                    ))}
                </select>
            </div>

            {/* Right: prev / pages / next */}
            <div className={styles.controls}>
                <button
                    className={styles.navBtn}
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                >
                    &larr; Previous
                </button>

                {pages[0] > 1 && (
                    <>
                        <button
                            className={styles.pageBtn}
                            onClick={() => onPageChange(1)}
                        >
                            1
                        </button>
                        {pages[0] > 2 && (
                            <span className={styles.ellipsis}>&hellip;</span>
                        )}
                    </>
                )}

                {pages.map((p) => (
                    <button
                        key={p}
                        className={`${styles.pageBtn} ${
                            p === currentPage ? styles.active : ""
                        }`}
                        onClick={() => onPageChange(p)}
                    >
                        {p}
                    </button>
                ))}

                {pages[pages.length - 1] < totalPages && (
                    <>
                        {pages[pages.length - 1] < totalPages - 1 && (
                            <span className={styles.ellipsis}>&hellip;</span>
                        )}
                        <button
                            className={styles.pageBtn}
                            onClick={() => onPageChange(totalPages)}
                        >
                            {totalPages}
                        </button>
                    </>
                )}

                <button
                    className={styles.navBtn}
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                >
                    Next &rarr;
                </button>
            </div>
        </div>
    );
}
