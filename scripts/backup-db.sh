#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR="${BACKUP_DIR:-backups}"
mkdir -p "$BACKUP_DIR"

if ! docker compose ps --status running --services | grep -qx backend; then
    echo "backend 容器未运行，请先执行 make docker-up" >&2
    exit 1
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
target="schedules-${timestamp}.db"
container_tmp="/tmp/${target}"

cleanup() {
    docker compose exec -T backend rm -f "$container_tmp" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# 使用 SQLite 在线备份 API，避免直接复制正在写入的数据库文件。
docker compose exec -T -e BACKUP_PATH="$container_tmp" backend python -c '
import os
import sqlite3

url = os.environ.get("DATABASE_URL", "sqlite:////app/data/schedules.db")
if not url.startswith("sqlite:///"):
    raise SystemExit("当前备份脚本只支持 SQLite")

source_path = url.removeprefix("sqlite:///")
source = sqlite3.connect(source_path)
target = sqlite3.connect(os.environ["BACKUP_PATH"])
with target:
    source.backup(target)
target.close()
source.close()
'

docker compose cp "backend:${container_tmp}" "${BACKUP_DIR}/${target}"
echo "备份完成：${BACKUP_DIR}/${target}"
