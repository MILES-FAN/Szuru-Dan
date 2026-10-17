#!/bin/sh
set -e

# Generate config.ini from environment variables
cat > /app/config.ini << EOF
[API]
backend_url=${BACKEND_URL:-http://127.0.0.1:8080/}
port=${PORT:-9000}
reverse_proxy_mode=${REVERSE_PROXY_MODE:-false}
enable_timing_logs=${ENABLE_TIMING_LOGS:-false}
EOF

exec gunicorn --bind "0.0.0.0:${PORT:-9000}" --workers "${WORKERS:-2}" "app:create_app()"
