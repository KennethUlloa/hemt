#!/bin/sh
set -e

# Create instance dir only when using SQLite (needs a writable path)
if [ "$DATABASE_BACKEND" != "postgres" ]; then
  mkdir -p /app/instance
fi

# Create attachments dir only when using local file storage
if [ "$STORAGE_BACKEND" != "s3" ]; then
  mkdir -p /app/attachments
fi

exec gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
