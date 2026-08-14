#!/bin/bash

cd /app

# 获取服务端口和地址，默认为 0.0.0.0:7860
BIND_HOST=${HOST:-0.0.0.0}
BIND_PORT=${PORT:-7860}

echo "🚀 启动旅途星辰 AI 旅行助手..."
echo "   绑定的地址: ${BIND_HOST}:${BIND_PORT}"
echo "   工作目录: $(pwd)"

exec gunicorn backend.app.api.main:app \
  --bind ${BIND_HOST}:${BIND_PORT} \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 600 \
  --access-logfile - \
  --error-logfile -
