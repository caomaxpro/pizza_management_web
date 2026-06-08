/**
 * JWT utility functions for token management
 */

export interface DecodedToken {
    sub?: string;
    email?: string;
    exp?: number;
    iat?: number;
    token_type?: string;
    [key: string]: unknown;
}

/**
 * Decode JWT token (without verification - only for client-side checks)
 * NOTE: This is NOT cryptographically verified, only for expiry checks
 */
export function decodeJWT(token: string): DecodedToken | null {
    try {
        const parts = token.split(".");
        if (parts.length !== 3) {
            console.warn("[JWT] Invalid token format");
            return null;
        }

        // JWT uses base64url encoding (- instead of +, _ instead of /)
        // atob() only handles standard base64, so we must convert first
        const base64url = parts[1];
        const base64 = base64url.replace(/-/g, "+").replace(/_/g, "/");
        const padded = base64.padEnd(
            base64.length + ((4 - (base64.length % 4)) % 4),
            "=",
        );
        const decoded = JSON.parse(atob(padded));
        return decoded;
    } catch (error) {
        console.error("[JWT] Failed to decode token:", error);
        return null;
    }
}

/**
 * Check if JWT token is expired
 */
export function isTokenExpired(token: string | null): boolean {
    if (!token) return true;

    const decoded = decodeJWT(token);
    if (!decoded || !decoded.exp) return true;

    // exp is in seconds, convert to milliseconds
    const expiryTime = decoded.exp * 1000;
    const currentTime = Date.now();

    return currentTime >= expiryTime;
}

/**
 * Get remaining time until token expires (in seconds)
 * Returns negative number if token is already expired
 */
export function getTokenExpiryTime(token: string | null): number {
    if (!token) return 0;

    const decoded = decodeJWT(token);
    if (!decoded || !decoded.exp) return 0;

    // exp is in seconds
    const expiryTime = (decoded.exp * 1000 - Date.now()) / 1000;
    return expiryTime;
}

/**
 * Check if token will expire soon (default: within 5 minutes)
 */
export function willTokenExpireSoon(
    token: string | null,
    thresholdSeconds: number = 300,
): boolean {
    const expiryTime = getTokenExpiryTime(token);
    return expiryTime <= thresholdSeconds;
}

/**
 * Get user info from token
 */
export function getUserFromToken(token: string | null) {
    if (!token) return null;
    const decoded = decodeJWT(token);
    return decoded
        ? {
              id: decoded.sub,
              email: decoded.email,
          }
        : null;
}

/**
 * Setup proactive token refresh
 * Refresh token before it expires (default: 1 minute before expiry)
 */
export function setupProactiveRefresh(
    token: string | null,
    onRefresh: () => void,
    beforeExpirySeconds: number = 60,
): (() => void) | null {
    if (!token) return null;

    const expiryTime = getTokenExpiryTime(token);

    if (expiryTime <= 0) {
        console.log(
            "[JWT] Token already expired, skipping proactive refresh setup",
        );
        return null;
    }

    // Calculate when to refresh (beforeExpirySeconds before expiry)
    const refreshTime = (expiryTime - beforeExpirySeconds) * 1000;

    if (refreshTime <= 0) {
        console.log(
            "[JWT] Token expires too soon, will refresh on next API call",
        );
        return null;
    }

    console.log(
        `[JWT] Setting up proactive refresh in ${Math.round(refreshTime / 1000)} seconds`,
    );

    const timeoutId = setTimeout(() => {
        console.log("[JWT] Proactive token refresh triggered");
        onRefresh();
    }, refreshTime);

    // Return cleanup function
    return () => {
        clearTimeout(timeoutId);
        console.log("[JWT] Proactive refresh cancelled");
    };
}
