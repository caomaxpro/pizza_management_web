import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')

app = Celery('pizza_ordering_app')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure Beat Schedule for Scheduled Tasks
app.conf.beat_schedule = {
    'cleanup-old-custom-items': {
        'task': 'pizza_management.tasks.cleanup_old_custom_items',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2:00 AM
        'options': {'queue': 'default'}
    },
}

# Additional Celery configurations
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
