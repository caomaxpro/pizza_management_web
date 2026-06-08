# Custom Items Cleanup Process

## Overview
Automatic cleanup of old custom pizza items that haven't been used in 90 days.

## Setup

### Automatic Setup (Recommended)
```bash
cd /home/cao-le/Flutter\ Projects/pizza_ordering_app/backend
chmod +x setup_cron.sh
./setup_cron.sh
```

This will:
- Create a `logs/` directory for cleanup logs
- Install a cron job to run cleanup every Sunday at 2:00 AM
- Show you the installed job

### Manual Setup
If automatic setup fails, add this to your crontab:

```bash
crontab -e
```

Add this line (runs every Sunday at 2 AM):
```
0 2 * * 0 cd /home/cao-le/Flutter\ Projects/pizza_ordering_app/backend/backend_dj && source ../.venv/bin/activate && python manage.py cleanup_old_custom_items >> ../logs/cleanup_cron.log 2>&1
```

## Usage

### Run Manually (Immediate)
```bash
cd backend/backend_dj
source ../.venv/bin/activate
python manage.py cleanup_old_custom_items
```

### Dry Run (Preview what would be deleted)
```bash
python manage.py cleanup_old_custom_items --dry-run
```

### Custom Retention Period
```bash
# Delete items not used in 60 days
python manage.py cleanup_old_custom_items --days 60
```

### View Logs
```bash
tail -f backend/logs/cleanup_cron.log
```

## How It Works

1. **Tracks `last_used_at`** - Updated when an OrderItem references a custom Item
2. **Cleanup Schedule** - Runs every Sunday at 2:00 AM
3. **Retention Policy** - Keeps custom items for 90 days of inactivity
4. **Preservation** - Data in OrderItems is preserved (via `customizations` JSON)
5. **Logging** - All cleanups are logged to `backend/logs/cleanup_cron.log`

## Database Impact

When a custom Item is deleted:
- ✓ OrderItem.item FK becomes NULL (SET_NULL on_delete)
- ✓ OrderItem.customizations JSON retains item data
- ✓ Full audit trail preserved for analysis

## Cron Management

**View installed jobs:**
```bash
crontab -l
```

**Edit cron jobs:**
```bash
crontab -e
```

**Remove specific job:**
```bash
crontab -e  # then delete the cleanup line
```

**Remove all jobs:**
```bash
crontab -r
```

## Troubleshooting

**Cron job not running?**
1. Check cron service: `sudo systemctl status cron`
2. View system logs: `sudo tail -f /var/log/syslog | grep CRON`
3. Verify paths exist and are accessible
4. Test command manually first

**Permission issues?**
- Make sure `.venv/bin/activate` is readable
- Django settings must be accessible
- Log directory must be writable

**Check if cron ran:**
```bash
tail -20 backend/logs/cleanup_cron.log
```
