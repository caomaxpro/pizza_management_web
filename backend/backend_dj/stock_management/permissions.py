"""
RBAC permission helpers for stock_management.

Role hierarchy:
  admin   → all 12 tasks including approve_override + takeover_session
  manager → operational tasks (no approve_override, no takeover_session)
  staff   → stock_take, receipt, view_logs (must hold an open session)
  customer→ no operations

Usage in views:
    from stock_management.permissions import has_permission, permission_denied

    if not has_permission(request.user, 'revert_logs'):
        return permission_denied()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import status
from rest_framework.response import Response

if TYPE_CHECKING:
    from user_management.models import User

# ---------------------------------------------------------------------------
# Permission map: role → set of allowed task types
# ---------------------------------------------------------------------------

TASK_PERMISSIONS: dict[str, set[str]] = {
    'admin': {
        # Operational
        'stock_take',
        'receipt',
        'receive_po',
        'inventory_edit',
        'delete_inventory',
        'revert_logs',
        'create_po',
        'view_logs',
        # Session management
        'manage_session',
        'assign_staff',
        # Admin-only gates
        'approve_override',   # bypass rollback time limits
        'takeover_session',   # forcibly take ownership of any open session
    },
    'manager': {
        # Operational
        'stock_take',
        'receipt',
        'receive_po',
        'inventory_edit',
        'delete_inventory',
        'revert_logs',
        'create_po',
        'view_logs',
        # Session management
        'manage_session',
        'assign_staff',
    },
    'staff': {
        'stock_take',
        'receipt',
        'view_logs',
    },
    'customer': set(),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_user_role(user: 'User') -> str:
    """Return the user's business role string (defaults to 'customer')."""
    return getattr(user, 'role', 'customer')


def has_permission(user: 'User', task_type: str) -> bool:
    """
    Return True if *user* is allowed to perform *task_type*.

    For 'staff' role the caller is responsible for verifying that an open
    StockTakeSession is assigned to the user — this function only checks the
    role-level allow-list.
    """
    if not user.is_authenticated:  # type: ignore[union-attr]
        return False
    role = get_user_role(user)
    return task_type in TASK_PERMISSIONS.get(role, set())


def can_approve_override(user: 'User') -> bool:
    """Only admins (role='admin') may bypass rollback time limits."""
    return has_permission(user, 'approve_override')


def permission_denied(message: str = 'You do not have permission to perform this action') -> Response:
    """Shortcut for a 403 response."""
    return Response({'error': message}, status=status.HTTP_403_FORBIDDEN)


def auth_required() -> Response:
    """Shortcut for a 401 response."""
    return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
