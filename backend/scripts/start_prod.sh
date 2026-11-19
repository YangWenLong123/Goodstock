#!/usr/bin/env bash
set -euo pipefail

GOODSTOCK_BACKEND_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$GOODSTOCK_BACKEND_DIR"

if [[ ! -f .env.production ]]; then
    echo "缺少 backend/.env.production，请上传生产配置或运行 scripts/setup_env.py --production。" >&2
    exit 1
fi

export APP_ENV=production
export PYTHONUNBUFFERED=1

exec "$GOODSTOCK_BACKEND_DIR/.venv/bin/python" -m uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8001 \
    --workers 2 \
    --proxy-headers \
    --forwarded-allow-ips 127.0.0.1
