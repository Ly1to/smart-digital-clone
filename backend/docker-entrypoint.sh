#!/bin/sh
set -eu

echo "[entrypoint] 执行数据库迁移"
alembic upgrade head

echo "[entrypoint] 启动 FastAPI"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
