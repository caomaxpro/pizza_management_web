/**
 * useRecaptcha — reCAPTCHA v3 hook
 *
 * Dynamically loads the reCAPTCHA v3 script once and exposes `execute(action)`
 * to obtain a short-lived token to send with sensitive requests.
 *
 * Setup:
 *   Add to your .env:
 *     VITE_RECAPTCHA_SITE_KEY=<your_v3_site_key>
 *
 * Usage:
 *   const { execute, ready } = useRecaptcha();
 *
 *   const handleSubmit = async () => {
 *     const token = await execute('refund');   // '' on error/disabled
 *     await requestRefund({ ...formData, recaptcha_token: token });
 *   };
 *
 * Fallback behaviour:
 *   - If the site key is not configured, execute() resolves to '' (backend
 *     will skip CAPTCHA when RECAPTCHA_ENABLED=False or no secret key set).
 *   - If script fails to load, execute() resolves to '' (fail-open).
 *   - When backend returns 403 with CAPTCHA error, the caller receives the
 *     error and can display a retry prompt to the user.
 */
import { useEffect, useRef, useState } from "react";

const SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY as string | undefined;

// Extend Window with the grecaptcha API (loaded by Google's script)
declare global {
    interface Window {
        grecaptcha?: {
            ready: (cb: () => void) => void;
            execute: (
                siteKey: string,
                options: { action: string },
            ) => Promise<string>;
        };
    }
}

interface UseRecaptchaReturn {
    /** True once the reCAPTCHA script is loaded and ready. */
    ready: boolean;
    /**
     * Execute reCAPTCHA for the given action and return a token.
     * Returns an empty string if CAPTCHA is not configured or an error occurs.
     */
    execute: (action: string) => Promise<string>;
}

export function useRecaptcha(): UseRecaptchaReturn {
    const [ready, setReady] = useState(false);
    const loadingRef = useRef(false);

    useEffect(() => {
        if (!SITE_KEY) return; // not configured
        if (document.getElementById("recaptcha-script")) {
            // Script already injected (e.g. HMR re-mount) — just wait for ready
            window.grecaptcha?.ready(() => setReady(true));
            return;
        }
        if (loadingRef.current) return;
        loadingRef.current = true;

        const script = document.createElement("script");
        script.id = "recaptcha-script";
        script.src = `https://www.google.com/recaptcha/api.js?render=${SITE_KEY}`;
        script.async = true;
        script.defer = true;
        script.onload = () => {
            window.grecaptcha?.ready(() => setReady(true));
        };
        script.onerror = () => {
            console.warn("[useRecaptcha] Failed to load reCAPTCHA script");
        };
        document.head.appendChild(script);
    }, []);

    const execute = async (action: string): Promise<string> => {
        if (!SITE_KEY || !ready || !window.grecaptcha) return "";
        try {
            return await window.grecaptcha.execute(SITE_KEY, { action });
        } catch (err) {
            console.warn("[useRecaptcha] execute() failed:", err);
            return "";
        }
    };

    return { ready, execute };
}
