"""
Adaptive reCAPTCHA v3 verifier for payment refund requests.

All verification logic now lives in helper/captcha_helpers.py so it can be
reused by any Django app.  This module re-exports the two public symbols so
existing imports continue to work without changes.
"""
# Re-export — keep all callers in payment_management pointing here as before.
from helper.captcha_helpers import verify_captcha, should_require_captcha  # noqa: F401
import logging
import urllib.request
import urllib.parse
import json

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

_SECRET: str = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
_THRESHOLD: float = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5)
_ENABLED: bool = getattr(settings, 'RECAPTCHA_ENABLED', True)


def verify_captcha(token: str | None, remote_ip: str = '') -> dict:
    """
    Verify a reCAPTCHA v3 token with Google.

    Returns:
        {
          'success': bool,      # True if token is valid and score >= threshold
          'score': float,       # 0.0 to 1.0 (1.0 = very likely human)
          'required': bool,     # False when CAPTCHA is disabled or no secret configured
          'error': str | None,
        }
    """
    if not _ENABLED or not _SECRET:
        return {'success': True, 'score': 1.0, 'required': False, 'error': None}

    if not token:
        return {'success': False, 'score': 0.0, 'required': True, 'error': 'Missing recaptcha_token'}

    try:
        data = urllib.parse.urlencode({
            'secret': _SECRET,
            'response': token,
            'remoteip': remote_ip,
        }).encode()

        with urllib.request.urlopen(VERIFY_URL, data=data, timeout=5) as resp:
            result = json.loads(resp.read().decode())

        success = result.get('success', False)
        score = result.get('score', 0.0)

        if not success:
            errors = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA failed for IP {remote_ip}: {errors}")
            return {'success': False, 'score': score, 'required': True, 'error': str(errors)}

        if score < _THRESHOLD:
            logger.warning(f"reCAPTCHA score too low ({score}) for IP {remote_ip}")
            return {'success': False, 'score': score, 'required': True, 'error': f'Score too low: {score}'}

        return {'success': True, 'score': score, 'required': True, 'error': None}

    except Exception as exc:
        # Network/timeout — fail open (allow request) and log
        logger.error(f"reCAPTCHA verification error: {exc}")
        return {'success': True, 'score': 0.5, 'required': True, 'error': str(exc)}


def should_require_captcha(ip: str, count: int, limit: int) -> bool:
    """
    Adaptive logic: only require CAPTCHA when IP is approaching rate limit
    or has a history of violations.

    Trigger at 60% of limit (e.g., 3 out of 5 requests/hour).
    """
    if not _ENABLED or not _SECRET:
        return False
    threshold = max(1, int(limit * 0.6))
    return count >= threshold
