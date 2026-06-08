"""
DRF permission class for auto-mapped role-task checks.

Auto-derives a codename from viewset basename + action:
  codename = "{basename}.{action}"
  e.g. UserViewSet (basename="users") + action="destroy" → "users.destroy"

Usage on a ViewSet:

    from user_management.permissions import AutoRoleTaskPermission

    class UserViewSet(ViewSet):
        task_bypass_actions = {'create'}        # skip task check for these

        def get_permissions(self):
            if self.action == 'create':
                return [AllowAny()]
            return [IsAuthenticated(), AutoRoleTaskPermission()]
"""
from rest_framework.permissions import BasePermission

from .role_permissions import has_task


class AutoRoleTaskPermission(BasePermission):
    """
    Checks whether the authenticated user holds a Task mapping that allows
    the current action (derived via codename = basename.action).

    - Unauthenticated users: deferred to IsAuthenticated (returns True here).
    - Actions listed in view.task_bypass_actions: always allowed.
    - Admin role: always allowed (handled inside has_task).
    - No matching RoleTask rule: determined by ROLETASK_DEFAULT_ALLOW.
    """

    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):  # type: ignore[override]
        # If the user isn't authenticated yet, defer to IsAuthenticated.
        if not request.user or not request.user.is_authenticated:
            return True

        # Derive action string
        action: str = getattr(view, 'action', None) or request.method.lower()

        # Actions the ViewSet explicitly opts out of task-checking
        bypass = getattr(view, 'task_bypass_actions', {'create'})
        if action in bypass:
            return True

        # Derive basename (registered router basename, e.g. "users")
        basename: str = (
            getattr(view, 'basename', None)
            or view.__class__.__name__.lower().replace('viewset', '')
        )

        codename = f'{basename}.{action}'
        return has_task(request.user, codename)
