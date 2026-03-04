#!/bin/bash
# ポート8000で動いているサーバーを全て停止
echo "ポート8000のプロセスを停止中..."
pkill -f "uvicorn main:app" 2>/dev/null && echo "  uvicorn main:app を停止"
pkill -f "uvicorn.*8000" 2>/dev/null && echo "  uvicorn 8000 を停止"
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "  ポート8000のプロセスを強制終了"
sleep 1
if lsof -i:8000 >/dev/null 2>&1; then
    echo "まだ使用中:"
    lsof -i:8000
    exit 1
fi
echo "OK: ポート8000は解放されました"
