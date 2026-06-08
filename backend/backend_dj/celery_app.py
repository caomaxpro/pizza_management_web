# This file was previously named celery.py and has been renamed to avoid circular import issues with the celery package.
import os
import django
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Ensure Django is configured BEFORE creating Celery app
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')
django.setup()

# Create Celery app instance
app = Celery('backend_dj')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Verify Firebase is initialized when Celery starts
try:
    import firebase_admin
    default_app = firebase_admin.get_app()
    logger.info("[Celery Init] ✓ Firebase already initialized")
except ValueError:
    logger.warning("[Celery Init] Firebase not initialized (may use local storage mode)")

app.conf.beat_schedule = {
    # Example periodic task
    # 'sample_task': {
    #     'task': 'pizza_management.tasks.cleanup_old_custom_pizzas',
    #     'schedule': crontab(hour=3, minute=0),
    # },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
