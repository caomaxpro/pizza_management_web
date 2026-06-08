"""
Schedule Mixin for User Management
Handles all WorkSchedule CRUD and slot-assignment operations.

Permission matrix:
  - list/retrieve    : admin | manager (own-created) | staff (own-assigned)
  - create           : admin (→ manager | staff)  |  manager (→ staff only)
  - assign_slot      : admin (any)  |  manager (staff only)
  - remove_slot      : admin (any)  |  manager (owner + staff-only target)
  - partial_update   : admin (any)  |  manager (owner + staff-only target)
  - destroy          : admin (any)  |  manager (owner + staff-only target)
"""
from typing import Any, cast, Optional

import datetime
import re
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.serializers import ListSerializer
from rest_framework.response import Response
from rest_framework.request import Request

from helper.auth_decorators import jwt_authentication, role_required
from ...models import User, WorkSchedule
from ...serializers import WorkScheduleSerializer

logger = logging.getLogger(__name__)


class ScheduleMixin:
    """Mixin that provides WorkSchedule CRUD and per-slot assignment endpoints."""

    # ---------------------------------------------------------------------- helpers

    def _get_schedule_queryset(self, user: User):
        """Return the queryset appropriate for the requesting user's role."""
        if user.is_admin_role:
            return WorkSchedule.objects.select_related('assigned_to', 'created_by').all()
        if user.is_manager_role:
            return WorkSchedule.objects.select_related('assigned_to', 'created_by').filter(
                created_by=user
            )
        # staff — can only see their own schedules
        return WorkSchedule.objects.select_related('assigned_to', 'created_by').filter(
            assigned_to=user
        )

    def _check_schedule_write_permission(
        self, request: Request, target_user: User, schedule: 'WorkSchedule | None' = None
    ) -> 'Response | None':
        """
        Validate role-based write permission and return a 403 Response if denied,
        or None if access is granted.
        """
        caller: User = cast(User, request.user)

        if caller.is_admin_role:
            if target_user.role not in ('manager', 'staff'):
                return Response(
                    {'detail': 'Schedules can only be assigned to managers or staff.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return None

        # Manager-level restrictions
        if not target_user.is_worker_role:
            return Response(
                {'detail': 'Managers can only assign schedules to staff members.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if schedule is not None and schedule.created_by_id != caller.id:
            return Response(
                {'detail': 'You can only modify schedules you created.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @staticmethod
    def _to_minutes(t: str) -> int:
        """Convert 'HH:MM' to total minutes since midnight."""
        h, m = map(int, t.split(':'))
        return h * 60 + m

    @staticmethod
    def _times_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
        """Return True if [start_a, end_a) overlaps [start_b, end_b).
        Handles cross-midnight shifts (e.g. 22:00-02:00) by normalising end
        time to be > start when it wraps past midnight.
        """
        a0 = ScheduleMixin._to_minutes(start_a)
        a1 = ScheduleMixin._to_minutes(end_a)
        b0 = ScheduleMixin._to_minutes(start_b)
        b1 = ScheduleMixin._to_minutes(end_b)
        # Normalise cross-midnight intervals
        if a1 <= a0:
            a1 += 24 * 60
        if b1 <= b0:
            b1 += 24 * 60
        return a0 < b1 and b0 < a1

    def _count_concurrent_staff(
        self,
        week_monday: datetime.date,
        day: str,
        start: str,
        end: str,
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Count active staff with overlapping shifts on the given day/week."""
        qs = WorkSchedule.objects.filter(week_start=week_monday, active=True)
        if exclude_user_id is not None:
            qs = qs.exclude(assigned_to_id=exclude_user_id)
        count = 0
        for sched in qs:
            entry_raw = sched.entries.get(day)
            if not entry_raw:
                continue
            shift_list = entry_raw if isinstance(entry_raw, list) else [entry_raw]
            for entry in shift_list:
                if entry.lower() == 'off':
                    continue
                try:
                    s, e = entry.split('-')
                    if ScheduleMixin._times_overlap(start, end, s.strip(), e.strip()):
                        count += 1
                        break  # count each person only once
                except ValueError:
                    continue
        return count

    def _count_concurrent_managers(
        self,
        week_monday: datetime.date,
        day: str,
        start: str,
        end: str,
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Count active managers with overlapping shifts on the given day/week."""
        qs = WorkSchedule.objects.select_related('assigned_to').filter(
            week_start=week_monday, active=True, assigned_to__role='manager'
        )
        if exclude_user_id is not None:
            qs = qs.exclude(assigned_to_id=exclude_user_id)
        count = 0
        for sched in qs:
            entry_raw = sched.entries.get(day)
            if not entry_raw:
                continue
            shift_list = entry_raw if isinstance(entry_raw, list) else [entry_raw]
            for entry in shift_list:
                if entry.lower() == 'off':
                    continue
                try:
                    s, e = entry.split('-')
                    if ScheduleMixin._times_overlap(start, end, s.strip(), e.strip()):
                        count += 1
                        break  # count each person only once
                except ValueError:
                    continue
        return count

    # ---------------------------------------------------------------------- list

    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def list(self, request: Request) -> Response:
        """
        GET /api/schedules/
        - admin   : all schedules
        - manager : schedules they created
        - staff   : own schedules

        Optional query param:
          ?week=YYYY-MM-DD  – filter by week_start (must be a Monday)
        """
        caller: User = cast(User, request.user)
        qs = self._get_schedule_queryset(caller)

        week_param = request.query_params.get('week')
        if week_param:
            try:
                week_date = datetime.date.fromisoformat(week_param)
                qs = qs.filter(week_start=week_date)
            except ValueError:
                return Response(
                    {'detail': 'Invalid week format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer_list = cast(ListSerializer, WorkScheduleSerializer(qs, many=True))
        return Response(serializer_list.data)

    # ---------------------------------------------------------------------- retrieve

    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def retrieve(self, request: Request, pk: Any = None) -> Response:
        """
        GET /api/schedules/<pk>/
        Same visibility rules as list.
        """
        caller: User = cast(User, request.user)
        qs = self._get_schedule_queryset(caller)
        schedule = get_object_or_404(qs, pk=pk)
        return Response(WorkScheduleSerializer(schedule).data)

    # ---------------------------------------------------------------------- create

    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request: Request) -> Response:
        """
        POST /api/schedules/
        Create a new weekly schedule for a manager or staff member.

        Body:
          assigned_to  : int (user id)
          week_start   : date (YYYY-MM-DD, must be a Monday)
          entries      : dict  e.g. {"mon": "08:00-16:00", "tue": "off"}
          notes?       : str
          active?      : bool  (default true)
        """
        from ... import tasks as um_tasks
        from typing import Any as _Any

        caller: User = cast(User, request.user)
        data_dict = cast(dict, request.data)
        assigned_to_id = data_dict.get('assigned_to')
        if not assigned_to_id:
            return Response(
                {'detail': 'assigned_to is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user = get_object_or_404(User, pk=assigned_to_id)
        denied = self._check_schedule_write_permission(request, target_user)
        if denied:
            return denied

        serializer_in = WorkScheduleSerializer(data=data_dict)
        if not serializer_in.is_valid():
            return Response(serializer_in.errors, status=status.HTTP_400_BAD_REQUEST)

        schedule = cast(WorkSchedule, serializer_in.save(
            created_by=caller,
            assigned_to=target_user,
        ))
        cast(_Any, um_tasks.send_schedule_assigned_email).delay(target_user.id, schedule.id)
        return Response(
            WorkScheduleSerializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )

    # ---------------------------------------------------------------------- partial_update

    @jwt_authentication
    @role_required(["admin", "manager"])
    def partial_update(self, request: Request, pk: Any = None) -> Response:
        """
        PATCH /api/schedules/<pk>/
        Update entries, notes, active, or week_start.
        Reassigning to a different user is not allowed via PATCH (use delete + create).
        """
        caller: User = cast(User, request.user)
        qs = self._get_schedule_queryset(caller)
        schedule = get_object_or_404(qs, pk=pk)

        denied = self._check_schedule_write_permission(request, schedule.assigned_to, schedule)
        if denied:
            return denied

        raw = cast(dict, request.data)
        data = {k: v for k, v in raw.items() if k != 'assigned_to'}
        serializer_up = WorkScheduleSerializer(schedule, data=data, partial=True)
        if not serializer_up.is_valid():
            return Response(serializer_up.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer_up.save()
        return Response(serializer_up.data)

    # ---------------------------------------------------------------------- destroy

    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request: Request, pk: Any = None) -> Response:
        """
        DELETE /api/schedules/<pk>/
        Admin: any schedule.  Manager: only schedules they created targeting staff.
        """
        caller: User = cast(User, request.user)
        qs = self._get_schedule_queryset(caller)
        schedule = get_object_or_404(qs, pk=pk)

        denied = self._check_schedule_write_permission(request, schedule.assigned_to, schedule)
        if denied:
            return denied

        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---------------------------------------------------------------------- assign_slot

    @action(detail=False, methods=['post'], url_path='assign_slot')
    @jwt_authentication
    @role_required(["admin", "manager"])
    def assign_slot(self, request: Request) -> Response:
        """
        POST /api/schedules/assign_slot/

        Assign a shift to one or more staff members for one specific day.
        Supports batch assignment: pass `assigned_to` as a single int or a
        list of ints.  Each user gets their own WorkSchedule upserted.

        Body:
          assigned_to : int | list[int]  – user id(s) of target staff/manager
          week_start  : str    – YYYY-MM-DD (any date in the target week; normalized to Monday)
          day         : str    – mon | tue | wed | thu | fri | sat | sun
          start       : str    – HH:MM  (shift start time)
          end         : str    – HH:MM  (shift end time)
          notes?      : str    – optional note attached to the schedule
          active?     : bool   – default true (only applied on creation)

        Response:
          { schedules: [...], errors?: {userId: message}, partial?: true }
        """
        from ... import tasks as um_tasks
        from typing import Any as _Any

        caller: User = cast(User, request.user)
        data = cast(dict, request.data)

        logger.info(f"assign_slot called with data: {data}")
        logger.info(f"Request user: {caller.id} ({caller.role})")

        # ── validate required fields ──────────────────────────────────────────
        errors: dict = {}
        assigned_to_raw = data.get('assigned_to')
        week_start_str: Optional[str] = data.get('week_start')
        day: Optional[str] = data.get('day')
        start: Optional[str] = data.get('start')
        end: Optional[str] = data.get('end')

        if not assigned_to_raw:
            errors['assigned_to'] = 'This field is required.'
        if not week_start_str:
            errors['week_start'] = 'This field is required.'
        if not day:
            errors['day'] = 'This field is required.'
        if not start:
            errors['start'] = 'This field is required.'
        if not end:
            errors['end'] = 'This field is required.'

        if errors:
            logger.warning(f"Validation errors: {errors}")
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Normalize assigned_to → list[int]
        if isinstance(assigned_to_raw, list):
            try:
                assigned_to_ids: list[int] = [int(i) for i in assigned_to_raw]
            except (TypeError, ValueError):
                return Response(
                    {'assigned_to': 'All values must be valid user IDs.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                assigned_to_ids = [int(cast(int | str, assigned_to_raw))]
            except (TypeError, ValueError):
                return Response(
                    {'assigned_to': 'Must be a valid user ID.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not assigned_to_ids:
            return Response(
                {'assigned_to': 'At least one staff member must be selected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── validate formats (shared for all assignments) ──────────────────────
        valid_days = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
        if day not in valid_days:
            logger.warning(f"Invalid day: {day}")
            return Response(
                {'day': f'Must be one of: {", ".join(sorted(valid_days))}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        time_re = re.compile(r'^\d{2}:\d{2}$')
        if not time_re.match(cast(str, start)) or not time_re.match(cast(str, end)):
            return Response(
                {'start': 'Must be HH:MM format.', 'end': 'Must be HH:MM format.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            week_date = datetime.date.fromisoformat(cast(str, week_start_str))
        except ValueError:
            return Response(
                {'week_start': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize to Monday (Sunday from frontend → advance to next day)
        if week_date.weekday() == 6:  # Sunday
            week_monday = week_date + datetime.timedelta(days=1)
        else:
            week_monday = week_date - datetime.timedelta(days=week_date.weekday())

        _day_offset = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        shift_date = week_monday + datetime.timedelta(days=_day_offset[cast(str, day)])
        start_hour, start_minute = map(int, cast(str, start).split(':'))
        shift_datetime = datetime.datetime.combine(shift_date, datetime.time(start_hour, start_minute))

        # ── validate 24-hour lead time requirement ────────────────────────────
        now = datetime.datetime.now()
        time_until_shift = shift_datetime - now
        if time_until_shift.total_seconds() < 86400:  # 24 hours
            logger.warning(f"Lead time check failed: {time_until_shift.total_seconds()}s < 86400")
            return Response(
                {'start': 'Shifts must be scheduled at least 24 hours in advance to give staff time to prepare.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── ensure at most 1 manager in the submitted list ────────────────────
        manager_count_in_request = sum(
            1 for uid in assigned_to_ids
            if User.objects.filter(pk=uid, role='manager').exists()
        )
        if manager_count_in_request > 1:
            return Response(
                {'detail': 'You can only assign 1 manager per shift.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── process each user ─────────────────────────────────────────────────
        results = []
        per_user_errors: dict[str, str] = {}
        entry_value = f'{start}-{end}'
        max_concurrent: int = getattr(settings, 'SCHEDULE_MAX_CONCURRENT_STAFF', 10)

        for uid in assigned_to_ids:
            target_user = get_object_or_404(User, pk=uid)

            denied = self._check_schedule_write_permission(request, target_user)
            if denied:
                per_user_errors[str(uid)] = cast(dict, denied.data).get('detail', 'Permission denied.')
                continue

            concurrent = self._count_concurrent_staff(
                week_monday, cast(str, day), cast(str, start), cast(str, end),
                exclude_user_id=target_user.id,
            )
            if concurrent >= max_concurrent:
                per_user_errors[str(uid)] = (
                    f'Slot already has {concurrent} staff assigned (max {max_concurrent}).'
                )
                continue

            if target_user.is_manager_role:
                concurrent_managers = self._count_concurrent_managers(
                    week_monday, cast(str, day), cast(str, start), cast(str, end),
                    exclude_user_id=target_user.id,
                )
                if concurrent_managers >= 1:
                    per_user_errors[str(uid)] = 'Each shift can only have 1 manager assigned.'
                    continue

            schedule, created = WorkSchedule.objects.get_or_create(
                assigned_to=target_user,
                week_start=week_monday,
                defaults={
                    'created_by': caller,
                    'entries':    {day: [entry_value]},
                    'notes':      data.get('notes') or '',
                    'active':     bool(data.get('active', True)),
                },
            )

            if not created:
                denied = self._check_schedule_write_permission(request, target_user, schedule)
                if denied:
                    per_user_errors[str(uid)] = cast(dict, denied.data).get('detail', 'Permission denied.')
                    continue
                # Normalize existing day entry to list (backward compat with old string format)
                existing_day = schedule.entries.get(day)
                if existing_day is None:
                    new_day_list = [entry_value]
                elif isinstance(existing_day, list):
                    new_day_list = existing_day if entry_value in existing_day else existing_day + [entry_value]
                else:
                    # Legacy string: keep both if different, or keep single
                    new_day_list = [existing_day] if existing_day == entry_value else [existing_day, entry_value]
                schedule.entries = {**schedule.entries, day: new_day_list}
                if data.get('notes'):
                    schedule.notes = data['notes']
                # Re-activate if it was previously deactivated (all entries removed)
                schedule.active = True
                schedule.save()

            if created:
                cast(_Any, um_tasks.send_schedule_assigned_email).delay(target_user.id, schedule.id)

            results.append(WorkScheduleSerializer(schedule).data)

        if per_user_errors and not results:
            return Response({'errors': per_user_errors}, status=status.HTTP_409_CONFLICT)

        response_data: dict = {'schedules': results}
        if per_user_errors:
            response_data['errors'] = per_user_errors
            response_data['partial'] = True

        return Response(
            response_data,
            status=status.HTTP_207_MULTI_STATUS if per_user_errors else status.HTTP_201_CREATED,
        )

    # ---------------------------------------------------------------------- remove_slot

    @action(detail=False, methods=['post'], url_path='remove_slot')
    @jwt_authentication
    @role_required(["admin", "manager"])
    def remove_slot(self, request: Request) -> Response:
        """
        POST /api/schedules/remove_slot/

        Remove a specific shift entry from a user's weekly schedule.
        If the schedule ends up with no entries it is deactivated but NOT
        deleted, preserving the audit trail.

        Body:
          assigned_to : int  – user id
          week_start  : str  – YYYY-MM-DD
          day         : str  – mon | tue | wed | thu | fri | sat | sun
          start       : str  – HH:MM  (shift start time to identify which entry to remove)
        """
        caller: User = cast(User, request.user)
        data = cast(dict, request.data)

        assigned_to_id: Optional[int] = data.get('assigned_to')
        week_start_str: Optional[str] = data.get('week_start')
        day: Optional[str] = data.get('day')
        start: Optional[str] = data.get('start')

        errors: dict = {}
        if not assigned_to_id:
            errors['assigned_to'] = 'This field is required.'
        if not week_start_str:
            errors['week_start'] = 'This field is required.'
        if not day:
            errors['day'] = 'This field is required.'
        if not start:
            errors['start'] = 'This field is required.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        valid_days = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
        if day not in valid_days:
            return Response(
                {'day': f'Must be one of: {", ".join(sorted(valid_days))}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            week_date = datetime.date.fromisoformat(cast(str, week_start_str))
        except ValueError:
            return Response(
                {'week_start': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize to Monday of the week containing week_start
        if week_date.weekday() == 6:  # Sunday → advance to next day (Monday)
            week_monday = week_date + datetime.timedelta(days=1)
        else:
            week_monday = week_date - datetime.timedelta(days=week_date.weekday())

        target_user = get_object_or_404(User, pk=assigned_to_id)
        denied = self._check_schedule_write_permission(request, target_user)
        if denied:
            return denied

        schedule = get_object_or_404(
            WorkSchedule, assigned_to=target_user, week_start=week_monday
        )
        denied = self._check_schedule_write_permission(request, target_user, schedule)
        if denied:
            return denied

        if day not in schedule.entries:
            return Response(
                {'detail': f'No shift entry for {day} in this schedule.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Normalize existing day entry to list (backward compat with old string format)
        existing_day = schedule.entries[day]
        existing_list: list = existing_day if isinstance(existing_day, list) else [existing_day]

        # Find the specific shift entry matching the requested start time
        removed_entry: Optional[str] = None
        for e in existing_list:
            try:
                entry_start = e.split('-')[0].strip()
                if entry_start == cast(str, start).strip():
                    removed_entry = e
                    break
            except (ValueError, AttributeError):
                continue

        if removed_entry is None:
            return Response(
                {'detail': f'No shift starting at {start} for {day} in this schedule.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_day_list = [e for e in existing_list if e != removed_entry]
        if new_day_list:
            new_entries: dict = {**schedule.entries, day: new_day_list}
        else:
            new_entries = {k: v for k, v in schedule.entries.items() if k != day}
        schedule.entries = new_entries
        if not new_entries:
            schedule.active = False
        schedule.save()

        response_data = dict(WorkScheduleSerializer(schedule).data)
        try:
            removed_start, removed_end = removed_entry.split('-')
            remaining = self._count_concurrent_staff(
                week_monday, cast(str, day), removed_start.strip(), removed_end.strip()
            )
            min_staff: int = getattr(settings, 'SCHEDULE_MIN_STAFF_PER_SHIFT', 3)
            if remaining < min_staff:
                response_data['_warning'] = (
                    f'Only {remaining} staff remain for this slot '
                    f'(recommended minimum is {min_staff}).'
                )
        except (ValueError, AttributeError):
            pass

        return Response(response_data)

    # ── Shift-scoped task permissions ─────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='assign_shift_task')
    @jwt_authentication
    @role_required(["admin", "manager"])
    def assign_shift_task(self, request: Request) -> Response:
        """
        POST /api/schedules/assign_shift_task/

        Assign task permissions scoped to a single shift entry for a user.
        This does NOT modify the user's global can_stock_take / can_receive_stock flags.
        The permission is automatically removed when the parent WorkSchedule is deleted.

        Body:
          {
            "user_id":     <int>,
            "week_start":  "YYYY-MM-DD",
            "day":         "mon"|"tue"|...|"sun",
            "shift_start": "HH:MM",
            "can_stock_take":    true|false,   // optional
            "can_receive_stock": true|false    // optional
          }
        """
        from ...models import ShiftTaskPermission
        from ...serializers import ShiftTaskPermissionSerializer

        caller: User = cast(User, request.user)
        data = cast(dict, request.data)

        user_id = data.get('user_id')
        week_start_str: Optional[str] = data.get('week_start')
        day: Optional[str] = data.get('day')
        shift_start: Optional[str] = data.get('shift_start')

        errors: dict = {}
        if not user_id:
            errors['user_id'] = 'This field is required.'
        if not week_start_str:
            errors['week_start'] = 'This field is required.'
        if not day:
            errors['day'] = 'This field is required.'
        if not shift_start:
            errors['shift_start'] = 'This field is required.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        valid_days = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
        if day not in valid_days:
            return Response(
                {'day': f'Must be one of: {", ".join(sorted(valid_days))}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            week_date = datetime.date.fromisoformat(cast(str, week_start_str))
        except ValueError:
            return Response(
                {'week_start': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if week_date.weekday() == 6:
            week_monday = week_date + datetime.timedelta(days=1)
        else:
            week_monday = week_date - datetime.timedelta(days=week_date.weekday())

        target_user = get_object_or_404(User, pk=user_id)
        schedule = get_object_or_404(WorkSchedule, assigned_to=target_user, week_start=week_monday)

        # Permission check: managers may only modify schedules they created
        if not caller.is_admin_role and schedule.created_by_id != caller.id:
            return Response(
                {'detail': 'You can only modify schedules you created.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify the specific shift entry exists in the schedule
        day_entry = schedule.entries.get(cast(str, day))
        if not day_entry:
            return Response(
                {'detail': f'No shift for day "{day}" in this schedule.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        shift_list: list = day_entry if isinstance(day_entry, list) else [day_entry]
        matching = next(
            (
                s for s in shift_list
                if isinstance(s, str) and s.split('-')[0].strip() == cast(str, shift_start).strip()
            ),
            None,
        )
        if matching is None:
            return Response(
                {'detail': f'No shift starting at {shift_start} for {day} in this schedule.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        perm, _ = ShiftTaskPermission.objects.get_or_create(
            work_schedule=schedule,
            day=cast(str, day),
            shift_start=cast(str, shift_start),
            defaults={'can_stock_take': False, 'can_receive_stock': False},
        )

        updated_fields: list[str] = []
        if 'can_stock_take' in data:
            perm.can_stock_take = bool(data['can_stock_take'])
            updated_fields.append('can_stock_take')
        if 'can_receive_stock' in data:
            perm.can_receive_stock = bool(data['can_receive_stock'])
            updated_fields.append('can_receive_stock')

        if updated_fields:
            perm.save(update_fields=updated_fields)

        return Response(ShiftTaskPermissionSerializer(perm).data)
