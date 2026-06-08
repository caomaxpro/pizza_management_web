from django.db import models
from django.utils import timezone


SESSION_TASK_CHOICES = [
    ('stock_take', 'Stock Take'),
    ('receipt', 'Receipt'),
]

SESSION_STATUS_CHOICES = [
    ('open', 'Open'),
    ('closed', 'Closed'),
    ('expired', 'Expired'),
]


class StockTakeSession(models.Model):
    """
    Represents an active stock-management session (stock take or receipt entry).

    Concurrency rule: only one session with status='open' should exist at a time.
    A manager/admin opens a session and can assign it to a staff user.
    Staff can only do stock_take / receipt entries while they hold an open session.

    Lifecycle:
        open  →  closed   (normal finish)
        open  →  expired  (auto-expiry via task / manual check)
        open  →  open     (assignment transferred or taken over)
    """

    id = models.AutoField(primary_key=True)

    started_by = models.ForeignKey(
        'user_management.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='started_sessions',
        help_text='Manager/admin who opened the session',
    )

    assigned_to = models.ForeignKey(
        'user_management.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sessions',
        help_text='Staff member currently responsible for the session',
    )

    task_type = models.CharField(
        max_length=30,
        choices=SESSION_TASK_CHOICES,
        default='stock_take',
    )

    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='open',
    )

    notes = models.TextField(null=True, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional hard deadline; null = no expiry',
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'stock_management'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self) -> str:
        assignee = self.assigned_to.username if self.assigned_to else 'unassigned'
        return f'Session #{self.id} [{self.task_type}] {self.status} → {assignee}'

    # ------------------------------------------------------------------ helpers

    def close(self) -> None:
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])

    def expire(self) -> None:
        self.status = 'expired'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])
