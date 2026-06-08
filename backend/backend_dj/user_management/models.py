from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from typing import Optional


ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('manager', 'Manager'),
    ('staff', 'Staff'),
    ('customer', 'Customer'),
]


class User(AbstractUser):
    """
    Custom User model with basic OAuth support
    """
    id = models.AutoField(primary_key=True)
    
    # Email & Phone (for orders)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    
    # OAuth
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    facebook_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(default=timezone.now)

    # Business role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    # Per-staff flexible task permissions
    can_stock_take = models.BooleanField(default=False)
    can_receive_stock = models.BooleanField(default=False)

    @property
    def is_admin_role(self) -> bool:
        return self.role == 'admin'

    @property
    def is_manager_role(self) -> bool:
        return self.role == 'manager'

    @property
    def is_worker_role(self) -> bool:
        """True if this user is a front-line staff member."""
        return self.role == 'staff'

    @property
    def has_mgmt_access(self) -> bool:
        """Admin or manager can manage operations."""
        return self.role in ('admin', 'manager')

    def __str__(self):
        return self.email or self.username

    class Meta:  # type: ignore[misc]
        app_label = 'user_management'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']


class Address(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="addresses")
    street = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, default="Canada")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.street}, {self.city}"


class Task(models.Model):
    """A named operation that can be permitted per role."""
    codename = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'user_management'
        ordering = ['codename']

    def __str__(self):
        return self.codename


class RoleTask(models.Model):
    """Mapping of which tasks are allowed for each role."""
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='role_tasks')
    allowed = models.BooleanField(default=True)

    class Meta:
        app_label = 'user_management'
        unique_together = [('role', 'task')]
        ordering = ['role', 'task']

    def __str__(self):
        status = 'allow' if self.allowed else 'deny'
        return f"{self.role} → {self.task.codename} ({status})"


class WorkSchedule(models.Model):
    """
    Weekly work schedule assigned to a manager or staff member.

    Creation rules:
        admin   → may assign to 'manager' or 'staff'
        manager → may only assign to 'staff'

    Uniqueness: one active schedule per (assigned_to, week_start).
    """
    WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    id: models.BigAutoField = models.BigAutoField(primary_key=True)

    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules',
        help_text='Admin/Manager who created this schedule',
    )
    created_by_id: Optional[int]
    assigned_to = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='work_schedules',
        help_text='Manager or Staff member this schedule applies to',
    )
    assigned_to_id: int
    week_start = models.DateField(
        help_text='Monday of the week this schedule covers (YYYY-MM-DD)',
    )
    entries = models.JSONField(
        default=dict,
        help_text='Map weekday→shift, e.g. {"mon": "08:00-16:00", "tue": "off"}',
    )
    notes = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'user_management'
        ordering = ['-week_start', 'assigned_to']
        indexes = [
            models.Index(fields=['assigned_to', 'week_start']),
            models.Index(fields=['created_by', 'week_start']),
        ]

    def __str__(self) -> str:
        return f'Schedule #{self.id} → {self.assigned_to} week={self.week_start}'


class ShiftTaskPermission(models.Model):
    """
    Per-shift task permission for one staff member on one specific shift.
    Scoped to a single WorkSchedule entry (day + shift_start).
    Does NOT modify the User's global can_stock_take / can_receive_stock flags.
    Automatically deleted when the parent WorkSchedule is deleted (CASCADE).
    """
    work_schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.CASCADE,
        related_name='shift_task_perms',
    )
    day = models.CharField(max_length=3)          # mon / tue / … / sun
    shift_start = models.CharField(max_length=5)  # HH:MM
    can_stock_take = models.BooleanField(default=False)
    can_receive_stock = models.BooleanField(default=False)

    class Meta:
        app_label = 'user_management'
        unique_together = [('work_schedule', 'day', 'shift_start')]
        ordering = ['day', 'shift_start']

    def __str__(self) -> str:
        schedule_id = getattr(self, "work_schedule_id", None)
        return (
            f'ShiftTaskPerm #{self.pk} → schedule={schedule_id} '
            f'{self.day}@{self.shift_start}'
        )


class RoleChangeLog(models.Model):
    """Audit trail for every role assignment change."""
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_changes_made',
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_change_history',
    )
    old_role = models.CharField(max_length=20)
    new_role = models.CharField(max_length=20)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'user_management'
        ordering = ['-changed_at']

    def __str__(self):
        return (
            f"{self.changed_by} changed {self.target_user} "
            f"{self.old_role} → {self.new_role} at {self.changed_at:%Y-%m-%d %H:%M}"
        )
