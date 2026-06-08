"""
Generic sliding-window rate limiter backed by Django cache (Redis).

This is a low-level building block used by the @rate_limit decorator in
auth_decorators.py.  It has no knowledge of HTTP — it just increments a
counter in cache and checks it against a ceiling.

Falls back gracefully when cache is unavailable (allows request, logs warning).
"""
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def check_rate(cache_key: str, limit: int, window: int) -> dict:
    """
    Increment the counter for *cache_key* and check it against *limit*.

    Args:
        cache_key:  Unique string identifying this counter (e.g. 'login:ip:1.2.3.4').
        limit:      Maximum number of requests allowed within *window* seconds.
        window:     Sliding-window duration in seconds.

    Returns:
        {
          'allowed': bool,   # False → caller should return 429
          'count':   int,    # Current hit count after increment
          'limit':   int,    # The ceiling that was applied
          'window':  int,    # Window in seconds
        }
    """
    try:
        count: int = cache.get(cache_key, 0)
        count += 1
        cache.set(cache_key, count, timeout=window)
    except Exception as exc:
        logger.warning(
            f"[check_rate] Cache unavailable for key '{cache_key}': {exc} — allowing request"
        )
        return {'allowed': True, 'count': 0, 'limit': limit, 'window': window}

    return {'allowed': count <= limit, 'count': count, 'limit': limit, 'window': window}


def build_rate_key(prefix: str, scope: str, request) -> str:
    """
    Build a namespaced cache key from the request.

    Args:
        prefix:  Short string identifying the endpoint/decorator (e.g. 'login').
        scope:   One of 'ip', 'user', 'ip+user'.
        request: DRF / Django request object.

    Returns:
        A string like 'rl:login:ip:1.2.3.4'
                    or 'rl:login:user:42'
                    or 'rl:login:ip+user:1.2.3.4:42'
    """
    ip = _get_ip(request)
    user_id = (
        str(request.user.pk)
        if hasattr(request, 'user') and request.user and request.user.is_authenticated
        else 'anon'
    )

    if scope == 'user':
        return f'rl:{prefix}:user:{user_id}'
    if scope == 'ip+user':
        return f'rl:{prefix}:ip+user:{ip}:{user_id}'
    # default: 'ip'
    return f'rl:{prefix}:ip:{ip}'


def _get_ip(request) -> str:
    """Extract real client IP, honouring X-Forwarded-For."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
