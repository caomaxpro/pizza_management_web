"""
Payment-specific ViewSet method decorators.

Usage — stack BELOW @jwt_authentication:

    @action(..., permission_classes=[])
    @jwt_authentication
    @captcha_required
    def request_refund(self, request, *args, **kwargs):
        rate = request._refund_rate  # {'allowed', 'count', 'limit', 'abuse'}
        ip   = request._refund_ip
        ...

What @captcha_required does (in order):
    1. Extracts real client IP.
    2. Logs the incoming request (IPLog).
    3. Increments & checks IP rate counter via helper.rate_helpers.check_rate
       — returns 429 if exceeded.
    4. Stores {'allowed', 'count', 'limit', 'abuse'} on request._refund_rate
       and the IP on request._refund_ip so the view can use them.
    5. Adaptively requires CAPTCHA when IP is approaching the rate limit.
       Returns 403 if the reCAPTCHA v3 token is missing or low-scored.

For a generic endpoint rate limiter without CAPTCHA, use:
    from helper.auth_decorators import rate_limit
    @rate_limit(limit=10, window=60, prefix='my_endpoint')
"""
import functools
import logging
from typing import cast, Callable, Any

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from helper.rate_helpers import check_rate, _get_ip
from .throttles import log_ip_request, _violation_key, _ABUSE_THRESHOLD, _WINDOW
from .captcha import verify_captcha, should_require_captcha

logger = logging.getLogger(__name__)

_LIMIT: int = getattr(settings, 'REFUND_RATE_LIMIT', 5)

_REFUND_RATE_PREFIX = 'refund_rate'


def captcha_required(method: Callable) -> Callable:
    """
    ViewSet method decorator — IP rate-limiting + abuse tracking + adaptive CAPTCHA.

    Must run AFTER @jwt_authentication (i.e. stacked below it):

        @jwt_authentication
        @captcha_required
        def my_view(self, request, ...): ...

    Side-effects on success:
        request._refund_ip   = str  — resolved client IP
        request._refund_rate = dict — {'allowed', 'count', 'limit', 'abuse'}

    Returns:
        429  if IP has exceeded the hourly refund rate limit.
        403  if adaptive CAPTCHA is required but token is missing/invalid.
    """
    @functools.wraps(method)
    def wrapper(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        ip = _get_ip(request)

        # ── 1. Audit log ──────────────────────────────────────────────────
        log_ip_request(request, ip)

        # ── 2. Rate limit via generic counter ─────────────────────────────
        from django.core.cache import cache
        cache_key = f'{_REFUND_RATE_PREFIX}:{ip}'
        rate_base = check_rate(cache_key, _LIMIT, _WINDOW)

        # Payment-specific: track violation streak for abuse detection
        abuse = False
        if not rate_base['allowed']:
            try:
                violations = cache.get(_violation_key(ip), 0) + 1
                cache.set(_violation_key(ip), violations, timeout=_WINDOW * 24)
                abuse = violations >= _ABUSE_THRESHOLD
            except Exception:
                pass

        rate = {**rate_base, 'abuse': abuse}
        request._refund_ip = ip      # type: ignore[attr-defined]
        request._refund_rate = rate  # type: ignore[attr-defined]

        if not rate['allowed']:
            logger.warning(
                f"[captcha_required] Rate limit exceeded for IP {ip} "
                f"(count={rate['count']}, limit={rate['limit']})"
            )
            if abuse:
                logger.warning(f"[captcha_required] IP {ip} flagged for abuse")
            return Response(
                {
                    'error': 'Too many refund requests. Please try again later.',
                    'retry_after_seconds': 3600,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # ── 3. Adaptive CAPTCHA ───────────────────────────────────────────
        if should_require_captcha(ip, rate['count'], rate['limit']):
            data = cast(dict, request.data)
            token = data.get('recaptcha_token')
            result = verify_captcha(token, remote_ip=ip)
            if not result['success']:
                logger.warning(
                    f"[captcha_required] CAPTCHA failed for IP {ip}: {result['error']}"
                )
                return Response(
                    {'error': 'CAPTCHA verification failed. Please complete the challenge.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return method(self, request, *args, **kwargs)

    return wrapper
