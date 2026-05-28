#!/bin/sh
set -e

mkdir -p /app/instance /app/attachments

exec gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
