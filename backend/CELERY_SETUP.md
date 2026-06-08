# Celery Setup Guide - Production Ready

## Overview
Celery is a distributed task queue library for Python that allows you to run long-running tasks asynchronously. We use it for:
- **Cleanup tasks**: Automatic removal of old custom pizza items
- **Background operations**: Any async operations that shouldn't block the API
- **Scheduling**: Tasks running on a schedule (equivalent to cron jobs)

---

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or manually:
```bash
pip install celery==5.4.0 celery-beat==2.5.0 redis==5.0.1
```

### 2. Setup Redis (Message Broker)

**Option A: Docker (Recommended)**
```bash
docker run -d -p 6379:6379 redis:latest
# Or with persistent storage:
docker run -d -p 6379:6379 -v redis_data:/data redis:latest
```

**Option B: Local Installation**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis
```

**Option C: Cloud Redis**
- AWS ElastiCache
- Azure Cache for Redis
- Google Cloud Memorystore

### 3. Environment Variables

Add to `.env`:
```bash
# Redis configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Production example (Azure Cache for Redis):
# CELERY_BROKER_URL=redis://:password@myredis.redis.cache.windows.net:6379/0?ssl_cert_reqs=required
```

---

## Running Celery Workers

### Development Mode

**Terminal 1 - Start Celery Worker:**
```bash
cd backend/backend_dj
source ../.venv/bin/activate
celery -A backend_dj worker -l info
```

**Terminal 2 - Start Celery Beat (Scheduler):**
```bash
cd backend/backend_dj
source ../.venv/bin/activate
celery -A backend_dj beat -l info
```

### Production Mode (Systemd)

**Create service files:**

`/etc/systemd/system/celery-worker.service`
```ini
[Unit]
Description=Celery Worker for Pizza Ordering
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/pizza_ordering_app/backend/backend_dj
Environment="PATH=/path/to/pizza_ordering_app/backend/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=backend_dj.settings"
ExecStart=/path/to/pizza_ordering_app/backend/.venv/bin/celery -A backend_dj worker \
    --loglevel=info \
    --logfile=/var/log/celery/celery-worker.log \
    --pidfile=/var/run/celery/celery-worker.pid \
    --concurrency=4

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=celery-worker

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/celery-beat.service`
```ini
[Unit]
Description=Celery Beat for Pizza Ordering
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/pizza_ordering_app/backend/backend_dj
Environment="PATH=/path/to/pizza_ordering_app/backend/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=backend_dj.settings"
ExecStart=/path/to/pizza_ordering_app/backend/.venv/bin/celery -A backend_dj beat \
    --loglevel=info \
    --logfile=/var/log/celery/celery-beat.log \
    --scheduler=django_celery_beat.schedulers:DatabaseScheduler

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=celery-beat

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown www-data:www-data /var/log/celery /var/run/celery

sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### Production Mode (Docker)

**Dockerfile snippet:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Worker
CMD["celery", "-A", "backend_dj", "worker", "--loglevel=info"]

# Beat (run separately):
# CMD["celery", "-A", "backend_dj", "beat", "--loglevel=info"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery-worker:
    build: ./backend
    command: celery -A backend_dj worker --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=backend_dj.settings
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./backend:/app

  celery-beat:
    build: ./backend
    command: celery -A backend_dj beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=backend_dj.settings
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./backend:/app

volumes:
  redis_data:
```

---

## Available Tasks

### Automatic Cleanup Task
```
Task: pizza_management.tasks.cleanup_old_custom_items
Schedule: Every Sunday at 2:00 AM UTC
Description: Removes custom pizza items not used in 90 days
```

**Manually trigger cleanup:**
```python
from pizza_management.tasks import cleanup_old_custom_items

# Execute now (async)
cleanup_old_custom_items.delay()

# Execute with custom days parameter
cleanup_old_custom_items.delay(days=60)

# Or from Django shell:
python manage.py shell
>>> from pizza_management.tasks import cleanup_old_custom_items
>>> cleanup_old_custom_items.delay(days=90)
```

---

## Monitoring

### View Active Tasks
```python
from celery.app.control import Control
from backend_dj.celery import app

# Get active tasks
active = app.control.inspect().active()
print(active)
```

### Check Task Status
```python
from pizza_management.tasks import cleanup_old_custom_items

result = cleanup_old_custom_items.delay()
print(result.id)              # Task ID
print(result.state)           # Task state (PENDING, STARTED, SUCCESS, FAILURE)
print(result.result)          # Task result
print(result.ready())         # Is task complete?
print(result.successful())    # Did task succeed?
```

### View Logs
```bash
# Development
tail -f celery.log

# Production (systemd)
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f
```

### Flower - Celery Monitoring UI (Optional)
```bash
# Install
pip install flower

# Run
celery -A backend_dj flower

# Access at http://localhost:5555
```

---

## Scheduled Tasks Configuration

Tasks are defined in `backend_dj/celery.py`:

```python
app.conf.beat_schedule = {
    'cleanup-old-custom-items': {
        'task': 'pizza_management.tasks.cleanup_old_custom_items',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
    },
}
```

**Cron expressions:**
```python
from celery.schedules import crontab

crontab(hour=2, minute=0, day_of_week=0)  # Sunday 2:00 AM
crontab(hour='*/3')                        # Every 3 hours
crontab(hour=0, minute=0)                  # Daily at midnight
crontab(minute='*/15')                     # Every 15 minutes
crontab(hour=0, minute=0, day_of_month=1) # Monthly on 1st
```

---

## Configuration Options (.env)

```bash
# Redis Broker
CELERY_BROKER_URL=redis://localhost:6379/0

# Result Backend
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_TIME_LIMIT=1800  # 30 minutes
CELERY_WORKER_SOFT_TIME_LIMIT=1500  # 25 minutes
```

---

## Troubleshooting

### Worker not picking up tasks
```bash
# Check Redis connection
redis-cli ping
# Should return: PONG

# Check Celery worker logs
celery -A backend_dj worker -l debug
```

### Tasks not executing on schedule
```bash
# Verify Beat is running
ps aux | grep celery

# Check Beat log
sudo journalctl -u celery-beat -n 50

# Restart Beat
sudo systemctl restart celery-beat
```

### Connection errors
```bash
# Test Redis connection from Python
python manage.py shell
>>> import redis
>>> r = redis.Redis(host='localhost', port=6379, db=0)
>>> r.ping()
```

### Clear task queue
```bash
# Purge all messages from broker
celery -A backend_dj purge

# Or from shell
python manage.py shell
>>> from backend_dj.celery import app
>>> app.control.purge()
```

---

## Migration from Cron

**Old method (removed):**
- `setup_cron.sh` - ❌ Removed
- System crontab - ❌ No longer needed
- `CLEANUP_README.md` - ❌ Removed

**New method:**
- ✅ Celery Worker & Beat
- ✅ Redis Message Broker
- ✅ Centralized task management
- ✅ Better monitoring & retry logic

To disable old cron:
```bash
# If you had set it up
crontab -e
# Remove any lines with "cleanup_old_custom_items"
```

---

## Security Notes

1. **Redis Security:**
   - Use Redis with authentication in production
   - Restrict network access to Redis
   - Consider using Redis Cluster for high availability

2. **Task Security:**
   - Tasks are serialized as JSON (be careful with sensitive data)
   - Use task signatures for additional security

3. **Worker Security:**
   - Run workers as non-root user (www-data, celery, etc.)
   - Restrict file permissions on task logs

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Setup Redis broker
3. ✅ Add `.env` variables
4. ✅ Run Celery Worker & Beat
5. ✅ Monitor tasks via logs or Flower
6. ✅ (Optional) Deploy to production with systemd/Docker

For more info: https://docs.celeryproject.io/
