#!/bin/bash
cd "$(dirname "$0")"

# 既存のuvicornプロセスを全て停止
echo "既存のサーバーを停止中..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# ポートが空いているか確認
if lsof -i:8000 >/dev/null 2>&1; then
    echo "エラー: ポート8000がまだ使用中です。手動でプロセスを終了してください:"
    lsof -i:8000
    exit 1
fi

[ -f .env ] || cp .env.example .env

# キャッシュ削除
find . -path ./venv -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -path ./venv -prune -o -name "*.pyc" -delete 2>/dev/null || true

source venv/bin/activate 2>/dev/null || { python -m venv venv && source venv/bin/activate && pip install -r requirements.txt; }

echo "サーバー起動中 (ポート8000)..."
exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
