"""
Role-based task permission helpers.

Codename convention:  "{viewset_basename}.{action}"
  e.g.  "users.destroy"   "users.create_staff"   "users.*"

Wildcard support (stored as Task codenames in DB):
  "users.*"   – all actions on the 'users' resource
  "*.destroy" – 'destroy' on any resource
  "*.*"       – everything

Resolution order for has_task(user, codename):
  1. Admin role          → always allowed   (bypass)
  2. Explicit deny rule  → False
  3. Explicit allow rule → True
  4. No rule found       → ROLETASK_DEFAULT_ALLOW  (default: True = open)
"""
from __future__ import annotations

import logging
from typing import Optional, Set

from django.core.cache import cache

logger = logging.getLogger('user_management')

# ── tunables ──────────────────────────────────────────────────────────────────
CACHE_TTL = 300          # seconds per role cache entry
_PREFIX   = 'roletask:'

# True  = allow when no rule is found  (open-by-default, restrict explicitly)
# False = deny  when no rule is found  (closed-by-default, grant explicitly)
ROLETASK_DEFAULT_ALLOW: bool = True


# ── private helpers ───────────────────────────────────────────────────────────

def _cache_key(role: str) -> str:
    return f'{_PREFIX}{role}'


def _load_rules(role: str) -> dict:
    """Query DB for all RoleTask rows for this role. Returns {'allowed': set, 'denied': set}."""
    from user_management.models import RoleTask
    qs = RoleTask.objects.filter(role=role).select_related('task')
    allowed: Set[str] = set()
    denied:  Set[str] = set()
    for rt in qs:
        (allowed if rt.allowed else denied).add(rt.task.codename)
    return {'allowed': allowed, 'denied': denied}


def _get_rules(role: str) -> dict:
    """Return cached rules for the role, loading from DB on miss."""
    key = _cache_key(role)
    try:
        rules = cache.get(key)
    except Exception:
        rules = None

    if rules is None:
        rules = _load_rules(role)
        try:
            cache.set(key, rules, CACHE_TTL)
        except Exception:
            pass  # cache unavailable — degrade gracefully

    return rules  # type: ignore[return-value]


def _matches(rule_set: Set[str], codename: str) -> bool:
    """
    True if codename matches any pattern in rule_set.

    Patterns checked (in order):
      exact       "users.destroy"
      prefix      "users.*"
      suffix      "*.destroy"
      global      "*.*"
    """
    if codename in rule_set:
        return True
    parts = codename.split('.', 1)
    if len(parts) == 2:
        basename, action = parts
        if f'{basename}.*' in rule_set:
            return True
        if f'*.{action}' in rule_set:
            return True
    return '*.*' in rule_set


# ── public API ────────────────────────────────────────────────────────────────

def has_task(user, codename: str) -> bool:
    """
    Return True if the user is allowed to perform `codename`.

    Usage:
        from user_management.role_permissions import has_task

        if not has_task(request.user, 'users.destroy'):
            return Response({'error': '...'}, status=403)
    """
    if not user or not getattr(user, 'role', None):
        return False

    # Admins bypass all task restrictions
    if getattr(user, 'is_admin_role', False):
        return True

    rules = _get_rules(user.role)

    # Deny wins over allow
    if _matches(rules['denied'], codename):
        logger.debug('[has_task] DENY  %s → %s', user.role, codename)
        return False

    if _matches(rules['allowed'], codename):
        logger.debug('[has_task] ALLOW %s → %s', user.role, codename)
        return True

    logger.debug(
        '[has_task] NO_RULE %s → %s  (default=%s)',
        user.role, codename, ROLETASK_DEFAULT_ALLOW,
    )
    return ROLETASK_DEFAULT_ALLOW


def invalidate_role_cache(role: str) -> None:
    """
    Bust the cache entry for `role`.
    Call this whenever a RoleTask row for that role is created, updated, or deleted.
    """
    try:
        cache.delete(_cache_key(role))
        logger.debug('[role_permissions] Cache invalidated for role: %s', role)
    except Exception:
        pass
