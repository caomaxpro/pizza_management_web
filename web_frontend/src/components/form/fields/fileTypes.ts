// Predefined file types for FileField component
export const FILE_TYPES = {
    image: {
        label: "Images",
        mime: [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        ext: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
    },
    document: {
        label: "Documents",
        mime: [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
        ext: [".pdf", ".doc", ".docx", ".xls", ".xlsx"],
    },
    video: {
        label: "Videos",
        mime: ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"],
        ext: [".mp4", ".webm", ".mov", ".avi"],
    },
    audio: {
        label: "Audio",
        mime: ["audio/mpeg", "audio/wav", "audio/ogg", "audio/webm"],
        ext: [".mp3", ".wav", ".ogg", ".m4a"],
    },
    archive: {
        label: "Archives",
        mime: [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
        ],
        ext: [".zip", ".rar", ".7z"],
    },
    any: {
        label: "All Files",
        mime: [],
        ext: [],
    },
} as const;

export type FileTypeKey = keyof typeof FILE_TYPES;
