#!/bin/bash

SCHEDULE=$(jq -r '.schedule' /app/config.json | tr -d '\r')

echo "$SCHEDULE /usr/local/bin/python3 /app/backup.py >> /app/cron.log 2>&1" > /etc/cron.d/mycron

crontab /etc/cron.d/mycron

cron -f