"""
User Management Celery Tasks
Background tasks for user-related async operations.
"""
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_schedule_assigned_email(self, user_id: int, schedule_id: int) -> dict:
    """
    Send a notification email to the user who has been assigned a work schedule.

    Args:
        user_id    : PK of the User who was assigned the schedule.
        schedule_id: PK of the WorkSchedule that was created/updated.

    Returns:
        dict with status and a short message.
    """
    try:
        from user_management.models import User, WorkSchedule  # late import to avoid circular

        user = User.objects.get(pk=user_id)
        schedule = WorkSchedule.objects.select_related('created_by').get(pk=schedule_id)

        if not user.email:
            logger.warning(
                'send_schedule_assigned_email: user %s has no email — skipping.', user_id
            )
            return {'status': 'skipped', 'reason': 'no email address'}

        creator_name = (
            schedule.created_by.get_full_name() or schedule.created_by.username
            if schedule.created_by
            else 'Management'
        )
        subject = f'[Pizza Admin] New work schedule for week of {schedule.week_start}'
        body = (
            f'Hi {user.get_full_name() or user.username},\n\n'
            f'A new weekly schedule has been assigned to you by {creator_name}.\n\n'
            f'Week starting : {schedule.week_start}\n'
            f'Schedule ID   : {schedule.id}\n\n'
        )
        if schedule.entries:
            body += 'Shifts:\n'
            day_labels = {
                'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
                'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday',
            }
            for day, shift in schedule.entries.items():
                label = day_labels.get(day, day)
                body += f'  {label}: {shift}\n'
        if schedule.notes:
            body += f'\nNotes: {schedule.notes}\n'
        body += '\nPlease log in to the admin portal for full details.\n'

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pizzaadmin.local')
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(
            'send_schedule_assigned_email: sent to %s for schedule #%s', user.email, schedule_id
        )
        return {'status': 'sent', 'recipient': user.email}

    except Exception as exc:  # noqa: BLE001
        logger.error(
            'send_schedule_assigned_email failed for user=%s schedule=%s: %s',
            user_id, schedule_id, exc,
        )
        raise self.retry(exc=exc)
