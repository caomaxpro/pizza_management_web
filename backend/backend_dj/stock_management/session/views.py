"""
Session management views for StockTakeSession.

Endpoints:
    POST   /api/stock-take/            start   – open a new session (manager+)
    GET    /api/stock-take/            list    – list sessions (manager+)
    GET    /api/stock-take/active/     active  – get the single open session
    POST   /api/stock-take/<pk>/assign/  assign  – assign session to a staff user (manager+)
    POST   /api/stock-take/<pk>/close/   close   – close session (assigned user or manager+)
    POST   /api/stock-take/<pk>/takeover/ takeover – admin takes over open session
"""

from typing import cast

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from stock_management.session.model import StockTakeSession
from stock_management.session.serializers import StockTakeSessionSerializer
from stock_management.permissions import (
    has_permission,
    permission_denied, auth_required,
)
from user_management.models import User


def _authenticate(request) -> 'tuple[User, None] | tuple[None, Response]':
    """Return (user, error_response).  error_response is None on success."""
    if not request.user.is_authenticated:
        return None, auth_required()
    return cast(User, request.user), None


class StockTakeSessionViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet for StockTakeSession management.
    """
    queryset = StockTakeSession.objects.select_related('started_by', 'assigned_to').all()
    serializer_class = StockTakeSessionSerializer

    # ------------------------------------------------------------------ list

    def list(self, request, *args, **kwargs):
        """GET /api/stock-take/ – list all sessions (manager+ only)."""
        user, err = _authenticate(request)
        if err:
            return err
        assert user is not None
        if not has_permission(user, 'manage_session'):
            return permission_denied()
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ start

    @action(detail=False, methods=['post'], url_path='start')
    def start(self, request) -> Response:
        """
        POST /api/stock-take/start/
        Open a new session.  Fails if another session is already open.

        Body:
            { "task_type": "stock_take"|"receipt", "notes": "...", "expires_at": "ISO8601|null" }
        """
        user, err = _authenticate(request)
        if err:
            return err
        assert user is not None
        if not has_permission(user, 'manage_session'):
            return permission_denied('Only managers/admins can start a session')

        with transaction.atomic():
            open_session = StockTakeSession.objects.select_for_update().filter(status='open').first()
            if open_session:
                ser = self.get_serializer(open_session)
                return Response(
                    {
                        'error': 'A session is already open. Close it first or use takeover.',
                        'active_session': ser.data,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            task_type = request.data.get('task_type', 'stock_take')
            if task_type not in dict(StockTakeSession._meta.get_field('task_type').choices):  # type: ignore[arg-type]
                return Response(
                    {'error': f'Invalid task_type. Choices: stock_take, receipt'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session = StockTakeSession.objects.create(
                started_by=user,
                task_type=task_type,
                notes=request.data.get('notes', ''),
                expires_at=request.data.get('expires_at') or None,
            )

        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------ active

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request) -> Response:
        """GET /api/stock-take/active/ – returns the current open session or 404."""
        user, err = _authenticate(request)
        if err:
            return err

        session = StockTakeSession.objects.filter(status='open').select_related(
            'started_by', 'assigned_to'
        ).first()

        if not session:
            return Response({'detail': 'No active session.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(session).data)

    # ------------------------------------------------------------------ assign

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None) -> Response:
        """
        POST /api/stock-take/<pk>/assign/
        Assign (or re-assign) the session to a staff user.

        Body: { "user_id": 42 }
        """
        user, err = _authenticate(request)
        if err:
            return err
        assert user is not None
        if not has_permission(user, 'assign_staff'):
            return permission_denied('Only managers/admins can assign sessions')

        session = self._get_open_session(pk)
        if isinstance(session, Response):
            return session

        target_user_id = request.data.get('user_id')
        if not target_user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        session.assigned_to = target_user
        session.save(update_fields=['assigned_to'])
        return Response(self.get_serializer(session).data)

    # ------------------------------------------------------------------ close

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None) -> Response:
        """
        POST /api/stock-take/<pk>/close/
        Close a session.  The assigned user or any manager/admin may close it.
        """
        user, err = _authenticate(request)
        if err:
            return err
        assert user is not None

        session = self._get_open_session(pk)
        if isinstance(session, Response):
            return session

        is_assignee = session.assigned_to_id == user.pk  # type: ignore[attr-defined]
        is_mgmt = has_permission(user, 'manage_session')

        if not (is_assignee or is_mgmt):
            return permission_denied('Only the assigned user or a manager/admin can close this session')

        session.close()
        return Response(self.get_serializer(session).data)

    # ------------------------------------------------------------------ takeover

    @action(detail=True, methods=['post'], url_path='takeover')
    def takeover(self, request, pk=None) -> Response:
        """
        POST /api/stock-take/<pk>/takeover/
        Admin takes ownership of an open session (re-assigns it to themselves).
        """
        user, err = _authenticate(request)
        if err:
            return err
        assert user is not None

        if not has_permission(user, 'takeover_session'):
            return permission_denied('Only admins can take over a session')

        session = self._get_open_session(pk)
        if isinstance(session, Response):
            return session

        session.assigned_to = user
        session.notes = (
            f'[Takeover by {user.username} at {timezone.now().isoformat()}] '
            + (session.notes or '')
        )
        session.save(update_fields=['assigned_to', 'notes'])
        return Response(self.get_serializer(session).data)

    # ------------------------------------------------------------------ helpers

    def _get_open_session(self, pk) -> 'StockTakeSession | Response':
        try:
            session = StockTakeSession.objects.select_related(
                'started_by', 'assigned_to'
            ).get(pk=pk)
        except StockTakeSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        if session.status != 'open':
            return Response(
                {'error': f'Session is already {session.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return session
