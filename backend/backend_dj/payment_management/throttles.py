"""
IP-based rate limiter for payment refund requests.

Uses Redis (via Django cache) as a sliding-window counter.
Falls back gracefully if cache is unavailable (allows request, logs warning).

Config (in settings.py):
    REFUND_RATE_LIMIT = 5          # max requests per window
    REFUND_RATE_WINDOW = 3600      # window in seconds (default 1 hour)
"""
import logging
from django.core.cache import cache
from django.conf import settings
from django.db import models as dj_models
from django.utils import timezone
from .model import IPLog, IPBlacklist

logger = logging.getLogger(__name__)

# Defaults — override in settings.py
_LIMIT: int = getattr(settings, 'REFUND_RATE_LIMIT', 5)
_WINDOW: int = getattr(settings, 'REFUND_RATE_WINDOW', 3600)
# After how many violations does the IP get flagged for abuse
_ABUSE_THRESHOLD: int = getattr(settings, 'REFUND_ABUSE_THRESHOLD', 3)


def get_client_ip(request) -> str:
    """Extract real client IP, respecting X-Forwarded-For if set."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _rate_key(ip: str) -> str:
    return f'refund_rate:{ip}'


def _violation_key(ip: str) -> str:
    return f'refund_violations:{ip}'


def is_ip_blacklisted(ip: str) -> bool:
    """
    Check persistent DB blacklist (with expiry support).
    Returns True if IP is actively blacklisted.
    """
    now = timezone.now()
    return IPBlacklist.objects.filter(
        ip_address=ip
    ).filter(
        dj_models.Q(expires_at__isnull=True) | dj_models.Q(expires_at__gt=now)
    ).exists()


def check_rate_limit(ip: str) -> dict:
    """
    Increment counter and check against limit.

    Returns:
        {
          'allowed': bool,
          'count': int,       # current hit count in window
          'limit': int,
          'abuse': bool,      # True when violation threshold crossed
        }
    """
    key = _rate_key(ip)
    try:
        count = cache.get(key, 0)
        count += 1
        cache.set(key, count, timeout=_WINDOW)
    except Exception:
        logger.warning(f"Cache unavailable — skipping rate limit check for IP {ip}")
        return {'allowed': True, 'count': 0, 'limit': _LIMIT, 'abuse': False}

    allowed = count <= _LIMIT
    abuse = False

    if not allowed:
        # Track violation streak
        try:
            violations = cache.get(_violation_key(ip), 0) + 1
            cache.set(_violation_key(ip), violations, timeout=_WINDOW * 24)
            abuse = violations >= _ABUSE_THRESHOLD
        except Exception:
            pass

    return {'allowed': allowed, 'count': count, 'limit': _LIMIT, 'abuse': abuse}


def log_ip_request(request, ip: str) -> None:
    """Persist an IPLog entry for audit trail (non-blocking)."""
    try:
        user = request.user if request.user.is_authenticated else None
        IPLog.objects.create(ip_address=ip, user=user)
    except Exception:
        logger.warning(f"Failed to save IPLog for {ip}")
