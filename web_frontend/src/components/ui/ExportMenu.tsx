import { useState, useCallback } from "react";
import { CaretDown, FileText, Table } from "@phosphor-icons/react";
import * as XLSX from "xlsx";
import { Button } from "./index";

export interface ExportColumn {
    key: string;
    label: string;
    render?: (value: unknown) => string | number;
}

interface ExportMenuProps {
    data: unknown[];
    selectedIds: Set<number | string>;
    filenamePrefix: string;
    columns: ExportColumn[];
    buttonLabel?: string;
}

export default function ExportMenu({
    data,
    selectedIds,
    filenamePrefix,
    columns,
    buttonLabel = "Export",
}: ExportMenuProps) {
    const [showMenu, setShowMenu] = useState(false);

    const getExportData = useCallback(() => {
        // Export selected items if any, otherwise all items
        return selectedIds.size > 0
            ? (data as Array<{ id?: number | string }>).filter(
                  (item) => item.id && selectedIds.has(item.id),
              )
            : (data as Array<{ id?: number | string }>);
    }, [data, selectedIds]);

    const handleExportJSON = useCallback(() => {
        try {
            const itemsToExport = getExportData();
            const jsonData = JSON.stringify(itemsToExport, null, 2);
            const blob = new Blob([jsonData], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `${filenamePrefix}_${
                new Date().toISOString().split("T")[0]
            }.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            setShowMenu(false);
        } catch {
            alert("Failed to export JSON");
        }
    }, [getExportData, filenamePrefix]);

    const handleExportExcel = useCallback(() => {
        try {
            const itemsToExport = getExportData();

            // Create formatted data for Excel using column config
            const exportData = itemsToExport.map((item) => {
                const row: Record<string, unknown> = {};
                columns.forEach((col) => {
                    const value = (item as Record<string, unknown>)[col.key];
                    row[col.label] = col.render
                        ? col.render(value)
                        : value || "";
                });
                return row;
            });

            const worksheet = XLSX.utils.json_to_sheet(exportData);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, "Data");

            // Auto-size columns
            const maxWidth = 30;
            const colWidths = columns.map(() => maxWidth);
            worksheet["!cols"] = colWidths.map((width) => ({ wch: width }));

            XLSX.writeFile(
                workbook,
                `${filenamePrefix}_${
                    new Date().toISOString().split("T")[0]
                }.xlsx`,
            );
            setShowMenu(false);
        } catch {
            alert("Failed to export Excel");
        }
    }, [getExportData, columns, filenamePrefix]);

    return (
        <div style={{ position: "relative" }}>
            <Button
                variant="primary"
                size="md"
                onClick={() => setShowMenu(!showMenu)}
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                }}
            >
                {buttonLabel}
                <CaretDown
                    size={16}
                    weight="fill"
                    style={{
                        transform: showMenu ? "rotate(180deg)" : "rotate(0deg)",
                        transition: "transform 0.2s",
                    }}
                />
            </Button>
            {showMenu && (
                <div
                    style={{
                        position: "absolute",
                        top: "100%",
                        right: 0,
                        backgroundColor: "#ffffff",
                        border: "1px solid #ccc",
                        borderRadius: "4px",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                        zIndex: 1000,
                        minWidth: "150px",
                        marginTop: "4px",
                    }}
                >
                    <div
                        onClick={handleExportJSON}
                        style={{
                            padding: "10px 16px",
                            cursor: "pointer",
                            borderBottom: "1px solid #eee",
                            fontSize: "14px",
                            transition: "background-color 0.2s",
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                        }}
                        onMouseEnter={(e) =>
                            (e.currentTarget.style.backgroundColor = "#f5f5f5")
                        }
                        onMouseLeave={(e) =>
                            (e.currentTarget.style.backgroundColor =
                                "transparent")
                        }
                    >
                        <FileText size={16} weight="regular" />
                        JSON
                    </div>
                    <div
                        onClick={handleExportExcel}
                        style={{
                            padding: "10px 16px",
                            cursor: "pointer",
                            fontSize: "14px",
                            transition: "background-color 0.2s",
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                        }}
                        onMouseEnter={(e) =>
                            (e.currentTarget.style.backgroundColor = "#f5f5f5")
                        }
                        onMouseLeave={(e) =>
                            (e.currentTarget.style.backgroundColor =
                                "transparent")
                        }
                    >
                        <Table size={16} weight="regular" />
                        Excel
                    </div>
                </div>
            )}
        </div>
    );
}
