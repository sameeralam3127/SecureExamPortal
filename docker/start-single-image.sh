#!/bin/sh
set -eu

gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --workers "${WEB_CONCURRENCY:-3}" &

backend_pid="$!"

term_handler() {
  kill "$backend_pid" 2>/dev/null || true
  nginx -s quit 2>/dev/null || true
  wait "$backend_pid" 2>/dev/null || true
}

trap term_handler INT TERM

nginx -g "daemon off;" &
nginx_pid="$!"

wait "$nginx_pid"
