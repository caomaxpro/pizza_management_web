#!/bin/bash

# Cron Setup Script for Automatic Cleanup of Old Custom Items
# Usage: ./setup_cron.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/cao-le/Flutter Projects/pizza_ordering_app/backend"
BACKEND_DJ="$PROJECT_ROOT/backend_dj"
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/cleanup_cron.log"

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo -e "${GREEN}✓ Created logs directory${NC}"
fi

# Cron job command (runs every Sunday at 2:00 AM)
CRON_COMMAND="0 2 * * 0 cd $BACKEND_DJ && source $VENV_ACTIVATE && python manage.py cleanup_old_custom_items >> $LOG_FILE 2>&1"

# Check if cron job already exists
if (crontab -l 2>/dev/null | grep -q "cleanup_old_custom_items"); then
    echo -e "${YELLOW}⚠ Cron job already exists${NC}"
    echo "Existing entry:"
    crontab -l | grep "cleanup_old_custom_items"
    echo ""
    read -p "Do you want to remove and reinstall it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        (crontab -l 2>/dev/null | grep -v "cleanup_old_custom_items" | crontab -) 2>/dev/null
        echo -e "${GREEN}✓ Removed old cron job${NC}"
    else
        echo -e "${YELLOW}Skipping installation${NC}"
        exit 0
    fi
fi

# Install new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
CHECK=$?

if [ $CHECK -eq 0 ]; then
    echo -e "${GREEN}✓ Cron job installed successfully!${NC}"
    echo ""
    echo "Schedule: Every Sunday at 2:00 AM"
    echo "Command: cleanup_old_custom_items"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "To view installed cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To remove the cron job:"
    echo "  crontab -e  # then delete the line with 'cleanup_old_custom_items'"
    echo "  or: crontab -r  # removes all cron jobs"
else
    echo -e "${RED}✗ Failed to install cron job${NC}"
    exit 1
fi
