"""
Generic adaptive reCAPTCHA v3 verifier.

Used by:
  - payment_management/decorators.py  (@captcha_required)
  - helper/auth_decorators.py         (@captcha_guard)

Config (settings.py):
    RECAPTCHA_SECRET_KEY      = '<your secret key>'   # required for live verification
    RECAPTCHA_SCORE_THRESHOLD = 0.5                   # 0.0–1.0, default 0.5
    RECAPTCHA_ENABLED         = True                  # set False in dev/test to skip
"""
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

_SECRET: str = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
_THRESHOLD: float = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5)
_ENABLED: bool = getattr(settings, 'RECAPTCHA_ENABLED', True)


def verify_captcha(token: str | None, remote_ip: str = '') -> dict:
    """
    Verify a reCAPTCHA v3 token with Google's siteverify API.

    Returns::
        {
          'success':  bool,       # True if token is valid and score >= threshold
          'score':    float,      # 0.0–1.0 (1.0 = very likely human)
          'required': bool,       # False when CAPTCHA is disabled / no secret set
          'error':    str | None,
        }

    Fails open (returns success=True) on network / timeout errors so that a
    transient Google outage does not block legitimate users.
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
        # Network/timeout — fail open and log
        logger.error(f"reCAPTCHA verification error: {exc}")
        return {'success': True, 'score': 0.5, 'required': True, 'error': str(exc)}


def should_require_captcha(ip: str, count: int, limit: int) -> bool:
    """
    Adaptive trigger: require CAPTCHA when the IP is approaching the rate limit.

    Triggers at 60 % of *limit* (e.g. 3 out of 5 requests/hour).
    Returns False when CAPTCHA is disabled so pages stay smooth in dev.
    """
    if not _ENABLED or not _SECRET:
        return False
    threshold = max(1, int(limit * 0.6))
    return count >= threshold
