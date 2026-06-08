/**
 * Payment service — refund request API.
 *
 * Usage in a component:
 *
 *   import { useRecaptcha } from '../hooks/useRecaptcha';
 *   import { requestRefund } from '../services/payment';
 *
 *   const { execute } = useRecaptcha();
 *
 *   const handleRefund = async () => {
 *     const token = await execute('refund');
 *     try {
 *       const result = await requestRefund({
 *         payment: paymentId,
 *         amount: refundAmount,
 *         reason: 'Customer request',
 *         recaptcha_token: token,
 *       });
 *       console.log('Refund submitted:', result.refund);
 *     } catch (err: any) {
 *       if (err.response?.status === 403) {
 *         // CAPTCHA failed — inform user to retry
 *         setError('Xác minh bảo mật thất bại. Vui lòng thử lại.');
 *       } else if (err.response?.status === 429) {
 *         setError('Quá nhiều yêu cầu. Vui lòng thử lại sau.');
 *       } else {
 *         setError(err.response?.data?.error ?? 'Đã xảy ra lỗi.');
 *       }
 *     }
 *   };
 */
import API from "./api";

export interface RefundRequest {
    /** ID of the Payment record to refund. */
    payment: number | string;
    /** Amount to refund (must be ≤ payment amount). */
    amount: number | string;
    /** Optional reason / notes. */
    reason?: string;
    /**
     * reCAPTCHA v3 token from useRecaptcha().execute('refund').
     * Omit (or pass '') in dev/test when RECAPTCHA_ENABLED=False on backend.
     */
    recaptcha_token?: string;
    /**
     * Optional idempotency key. If omitted, the backend auto-generates one
     * from (user_id + payment_id + amount) — safe for single-submit flows.
     * Supply an explicit key for retry-safe UX.
     */
    idempotency_key?: string;
}

export interface RefundResponse {
    refund: {
        id: number;
        status: string;
        amount: string;
        requested_at: string;
        [key: string]: unknown;
    };
    message: string;
}

/**
 * POST /api/payments/request-refund/
 *
 * Returns the created Refund object and a human-readable message.
 * Throws on 4xx/5xx — handle 403 (CAPTCHA fail) and 429 (rate limit) in caller.
 */
export async function requestRefund(
    data: RefundRequest,
): Promise<RefundResponse> {
    const payload: Record<string, unknown> = {
        payment: data.payment,
        amount: data.amount,
    };
    if (data.reason) payload.reason = data.reason;
    if (data.recaptcha_token) payload.recaptcha_token = data.recaptcha_token;
    if (data.idempotency_key) payload.idempotency_key = data.idempotency_key;

    const res = await API.post<RefundResponse>(
        "/payments/request-refund/",
        payload,
    );
    return res.data;
}
